#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import pyaudio
import numpy as np
import io
from dotenv import load_dotenv
import nls  # 阿里云语音识别SDK
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from openai import OpenAI
from enum import Enum
import cv2
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
import uuid
import datetime
import subprocess
import re  # 用于正则表达式处理
from mecanum_wheels import MecanumWheels

# 条件导入BuildHAT库
try:
    from buildhat import PassiveMotor
    BUILDHAT_AVAILABLE = True
except ImportError:
    BUILDHAT_AVAILABLE = False
    print("警告: BuildHAT库未安装，电机控制功能将不可用")


class WakeWord(Enum):
    """
    唤醒词枚举类
    """
    WAKE_NONE = 0
    WAKE_LLM = 1
    WAKE_TAKEPHOTO = 2
    WAKE_MOVE = 3

class VoiceAssistant:
    """
    基于阿里云语音服务和阿里云百炼DeepSeek的语音助手
    
    功能:
    - 语音唤醒（通过唤醒词）
    - 语音指令识别
    - LLM回答生成
    - 语音合成回复
    """

    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 音频参数配置
        self.sample_rate = 16000
        self.silence_threshold = 1.0  # 从2.0秒降低到1.0秒，更快检测到句子结束
        self.silence_level = 300  # 静默音量阈值，低于此值被视为静默
        self.speaking_level = 800  # 说话音量阈值，高于此值被视为说话
        
        # 功能配置
        self.enable_voice_response = True  # 是否启用语音回答
        self.llm_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.llm_model = os.getenv("ALIYUN_LLM_MODEL", "deepseek-v3")

        self.wake_words = [
            {'word': '你好机器人', 'handler': self.handle_wake_llm, 'cmd': WakeWord.WAKE_LLM},
            {'word': '机器人这是什么', 'handler': self.handle_wake_takephoto, 'cmd': WakeWord.WAKE_TAKEPHOTO},
            {'word': '机器人出发', 'handler': self.handle_wake_move, 'cmd': WakeWord.WAKE_MOVE}
        ]

        self.is_listening = False  # 是否处于主动监听状态
        
        # 检查阿里云百炼API配置
        if not self.llm_api_key or self.llm_api_key == "":
            print("警告：未设置阿里云百炼API密钥，请在.env文件中设置DASHSCOPE_API_KEY")
        
        # 初始化OpenAI客户端
        self.openai_client = OpenAI(
            api_key=self.llm_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 阿里云语音识别配置
        self.ali_url = os.getenv("ALI_URL", "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1")
        self.ali_token = os.getenv("ALI_TOKEN", "")
        self.ali_appkey = os.getenv("ALI_APPKEY", "")
        self.ali_ak_id = os.getenv("ALIYUN_AK_ID", "")
        self.ali_ak_secret = os.getenv("ALIYUN_AK_SECRET", "")
        self.token_expire_time = 0
        
        # 如果没有设置token但设置了AK，自动获取token
        if (not self.ali_token or self.ali_token == "") and self.ali_ak_id and self.ali_ak_secret:
            print("正在获取阿里云Token...")
            self.get_ali_token()
        elif not self.ali_token or self.ali_token == "":
            print("警告：未设置阿里云Token或AccessKey，请在.env文件中设置ALI_TOKEN或ALIYUN_AK_ID和ALIYUN_AK_SECRET")
        
        if not self.ali_appkey or self.ali_appkey == "":
            print("警告：未设置阿里云Appkey，请在.env文件中设置ALI_APPKEY")
            print("获取Appkey请前往控制台：https://nls-portal.console.aliyun.com/applist")
        
        # 初始化麦克风和音频处理
        self.audio = pyaudio.PyAudio()
        
        # 用于阿里云识别结果的变量
        self.recognition_result = ""
        self.recognition_cmd = WakeWord.WAKE_NONE
        self.recognition_completed = False
        
        # 初始化语音合成相关变量
        self.tts_buffer = None
        self.tts_completed = False
        
        # 图像识别配置
        self.is_raspberry_pi = self._check_raspberry_pi()  # 检测是否为树莓派环境
        self.capture_device = os.getenv("CAPTURE_DEVICE", 0)  # 摄像头设备索引
        self.image_path = "captured_image.jpg"  # 临时保存路径
        self.vision_model = "qwen2.5-vl-32b-instruct"  # 视觉模型名称

        # 初始化麦克纳姆轮
        self.mecanum_wheels = None
        if self.is_raspberry_pi and BUILDHAT_AVAILABLE:
            try:
                self.mecanum_wheels = MecanumWheels()
                print("成功初始化麦克纳姆轮控制")
            except Exception as e:
                print(f"初始化麦克纳姆轮控制失败: {e}")
        
        # 添加OSS配置
        self.oss_auth = oss2.ProviderAuthV4(EnvironmentVariableCredentialsProvider())
        self.oss_endpoint = "https://oss-cn-beijing.aliyuncs.com"  # Endpoint包含region
        self.oss_region = "cn-beijing"  # 纯region代码
        self.oss_bucket_name = "rspioss"
        self.oss_bucket = oss2.Bucket(
            self.oss_auth,
            self.oss_endpoint,
            self.oss_bucket_name,
            region=self.oss_region  # 这里传入纯region代码
        )
    
    # ===== 阿里云Token管理 =====
    
    def get_ali_token(self):
        """获取阿里云Token"""
        try:
            # 创建AcsClient实例
            client = AcsClient(self.ali_ak_id, self.ali_ak_secret, "cn-shanghai")

            # 创建request，并设置参数
            request = CommonRequest()
            request.set_method('POST')
            request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
            request.set_version('2019-02-28')
            request.set_action_name('CreateToken')

            response = client.do_action_with_exception(request)
            response_json = json.loads(response)
            
            if 'Token' in response_json and 'Id' in response_json['Token']:
                self.ali_token = response_json['Token']['Id']
                self.token_expire_time = response_json['Token']['ExpireTime']
                print(f"成功获取阿里云Token，将在 {self.token_expire_time} 过期")
                return True
            else:
                print("获取阿里云Token失败：无法解析响应")
                return False
        except Exception as e:
            print(f"获取阿里云Token错误: {e}")
            return False
    
    def check_token(self):
        """检查Token是否过期，如果过期则重新获取"""
        current_time = int(time.time())
        
        # 检查token是否即将过期（提前10分钟刷新）
        if self.token_expire_time - current_time < 600:
            print("Token即将过期，正在刷新...")
            self.get_ali_token()
    
    # ===== 语音识别回调函数 =====
    
    def on_recognition_start(self, message, *args):
        """当一句话识别就绪时的回调函数"""
        print("识别开始:")
        self.recognition_result = ""
        self.recognition_completed = False
    
    def on_recognition_result_changed(self, message, *args):
        """当一句话识别返回中间结果时的回调函数"""
        try:
            result = json.loads(message)
            
            # 统一从payload.result字段获取结果
            if "payload" in result and "result" in result["payload"]:
                recognition_text = result["payload"]["result"]
                self.recognition_result = recognition_text
                print(f"中间结果: {recognition_text}")
            
            # 移除这里的唤醒词检测逻辑
        except Exception as e:
            print(f"解析中间结果出错: {e}, 原始消息: {message}")
    
    def on_recognition_completed(self, message, *args):
        """当一句话识别返回最终识别结果时的回调函数"""
        try:
            result = json.loads(message)
            
            # 根据阿里云文档，最终结果可能在不同位置
            recognition_text = ""
            if "payload" in result and "result" in result["payload"]:
                recognition_text = result["payload"]["result"]
            elif "result" in result:
                recognition_text = result["result"]
            
            if recognition_text:
                self.recognition_result = recognition_text
                print(f"识别完成: {recognition_text}")
                
                # 仅在最终结果中检测唤醒词（增加精确匹配逻辑）
                if not self.is_listening:
                    for wake_word in self.wake_words:
                        if wake_word['word'].lower() in recognition_text.strip().lower():
                            print(f"[完成回调-精确匹配] 检测到唤醒词: {wake_word['word']}")

                            self.recognition_cmd = wake_word['cmd']

                            if not self.is_listening:
                                self.is_listening = True
                                print(f"唤醒成功! [{wake_word['word']}]")
                                
                                # 重置识别结果
                                self.recognition_result = ""
                                self.recognition_completed = False

                            break
            else:
                print(f"无法从完成结果中提取文本，原始消息: {message}")
            
            self.recognition_completed = True
        except Exception as e:
            print(f"解析完成结果出错: {e}, 原始消息: {message}")
            self.recognition_completed = True
    
    def on_recognition_error(self, message, *args):
        """当SDK或云端出现错误时的回调函数"""
        print(f"识别错误: {message}")
        self.recognition_completed = True
    
    def on_recognition_close(self, *args):
        """当和云端连接断开时的回调函数"""
        print("识别连接关闭")
    
    # ===== 语音合成回调函数 =====
    
    def on_tts_metainfo(self, message, *args):
        """语音合成元信息回调函数"""
        print(f"合成元信息: {message}")
    
    def on_tts_data(self, data, *args):
        """语音合成数据回调函数"""
        # 将音频数据写入缓冲区
        if hasattr(self, 'tts_buffer') and self.tts_buffer:
            self.tts_buffer.write(data)
    
    def on_tts_completed(self, message, *args):
        """语音合成完成回调函数"""
        print("语音合成完成")
        self.tts_completed = True
    
    def on_tts_error(self, message, *args):
        """语音合成错误回调函数"""
        print(f"语音合成错误: {message}")
        self.tts_completed = True
    
    def on_tts_close(self, *args):
        """语音合成连接关闭回调函数"""
        print("语音合成连接关闭")
    
    # ===== 核心功能 =====
    
    def wait_for_wake_word(self):
        """使用本地VAD检测唤醒词"""
        print("\n正在等待唤醒词...")

        result = WakeWord.WAKE_NONE
        
        # 创建本地音频流
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024
        )
        
        audio_buffer = []
        is_speaking = False
        
        try:
            while not self.is_listening:
                data = stream.read(1024, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                current_level = np.abs(audio_data).mean()
                
                # 语音活动检测
                if current_level > self.speaking_level:
                    if not is_speaking:  # 检测到语音开始
                        print("检测到语音开始")
                        is_speaking = True
                        audio_buffer = [data]  # 重置缓冲区
                    else:
                        audio_buffer.append(data)
                elif is_speaking:
                    # 持续静默检测
                    silent_frames = 0
                    while silent_frames < int(self.silence_threshold * self.sample_rate / 1024):
                        data = stream.read(1024, exception_on_overflow=False)
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        current_level = np.abs(audio_data).mean()
                        
                        if current_level < self.silence_level:
                            silent_frames += 1
                        else:
                            audio_buffer.append(data)
                            silent_frames = 0  # 重置静默计数器
                    
                    # 发送完整语音段到阿里云识别
                    print("检测到语音结束，开始识别...")
                    self._process_audio_chunk(b''.join(audio_buffer))
                    
                    result = self.recognition_cmd

                    # 重置状态
                    is_speaking = False
                    audio_buffer = []
                
                time.sleep(0.1)

        finally:
            stream.close()

        return result
    
    def _process_audio_chunk(self, audio_data):
        """处理单个语音片段"""
        # 检查token是否有效
        self.check_token()

        # 直接创建识别器实例（原_create_recognizer方法的逻辑内联）
        recognizer = nls.NlsSpeechRecognizer(
            url=self.ali_url,
            token=self.ali_token,
            appkey=self.ali_appkey,
            on_start=self.on_recognition_start,
            on_result_changed=self.on_recognition_result_changed,
            on_completed=self.on_recognition_completed,
            on_error=self.on_recognition_error,
            on_close=self.on_recognition_close
        )
        
        try:
            # 开始识别
            recognizer.start(
                aformat="pcm",
                sample_rate=self.sample_rate,
                enable_intermediate_result=True
            )
            
            # 分片发送音频数据（模拟实时流）
            chunk_size = 1024
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                recognizer.send_audio(chunk)
                time.sleep(0.01)  # 模拟实时流间隔
            
            # 停止识别
            recognizer.stop()
            
            # 等待结果
            timeout = 0
            while not self.recognition_completed and timeout < 5:
                time.sleep(0.1)
                timeout += 1
                        
        except Exception as e:
            print(f"语音段处理失败: {e}")
        finally:
            recognizer.shutdown()
    
    def record_command(self):
        """使用阿里云一句话识别录制用户命令"""
        print("请说出您的问题...")
        
        # 检查token是否有效
        self.check_token()
        
        # 创建阿里云识别器（直接实例化）
        recognizer = nls.NlsSpeechRecognizer(
            url=self.ali_url,
            token=self.ali_token,
            appkey=self.ali_appkey,
            on_start=self.on_recognition_start,
            on_result_changed=self.on_recognition_result_changed,
            on_completed=self.on_recognition_completed,
            on_error=self.on_recognition_error,
            on_close=self.on_recognition_close
        )
        
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024
        )
        
        frames = []
        silence_frames = 0
        speaking_started = False
        no_speech_timeout = int(5 * self.sample_rate / 1024)  # 5秒无语音则超时
        no_speech_counter = 0
        
        try:
            # 开始识别
            recognizer.start(
                aformat="pcm",
                sample_rate=self.sample_rate,
                enable_intermediate_result=True,
                enable_punctuation_prediction=True,
                enable_inverse_text_normalization=True  # 启用数字转换功能
            )
            
            self.recognition_completed = False
            self.recognition_result = ""
            last_result_length = 0
            no_new_result_counter = 0
            
            while True:
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
                
                # 计算当前音频帧的音量级别
                audio_data = np.frombuffer(data, dtype=np.int16)
                current_level = np.abs(audio_data).mean()
                
                # 检测是否开始说话
                if current_level > self.speaking_level:  # 音量高于阈值，认为开始说话
                    speaking_started = True
                    silence_frames = 0
                    no_speech_counter = 0
                elif speaking_started:
                    # 如果音量低于阈值，增加静默帧计数
                    if current_level < self.silence_level:
                        silence_frames += 1
                    else:
                        silence_frames = max(0, silence_frames - 1)  # 如果又检测到声音，减少静默计数
                else:
                    # 如果还没开始说话，检查超时
                    no_speech_counter += 1
                    if no_speech_counter >= no_speech_timeout:
                        print("等待说话超时")
                        if self.recognition_result:  # 如果有识别结果，也返回
                            recognizer.stop()
                            break
                        recognizer.stop()
                        return "", []
                
                # 发送音频数据给阿里云识别器
                recognizer.send_audio(data)
                
                # 检查识别结果是否有更新
                if len(self.recognition_result) > last_result_length:
                    last_result_length = len(self.recognition_result)
                    no_new_result_counter = 0
                else:
                    no_new_result_counter += 1
                
                # 满足以下任一条件则结束录制：
                # 1. 连续静默帧超过阈值
                # 2. 阿里云识别完成
                # 3. 识别结果长时间没有更新且已经有内容
                silence_threshold_frames = int(self.silence_threshold * self.sample_rate / 1024)
                no_update_threshold = int(2 * self.sample_rate / 1024)
                
                if (speaking_started and silence_frames > silence_threshold_frames) or \
                   self.recognition_completed or \
                   (speaking_started and no_new_result_counter > no_update_threshold and self.recognition_result):
                    print("检测到句子结束")
                    recognizer.stop()
                    break

                time.sleep(0.1)
        except Exception as e:
            print(f"录制命令时出错: {e}")
            try:
                recognizer.stop()
            except:
                pass
            return "", []
        
        finally:
            # 确保关闭流
            stream.close()
        
        # 等待识别完成
        timeout = 0
        while not self.recognition_completed and timeout < 20:
            time.sleep(0.1)
            timeout += 1
        
        result_text = self.recognition_result
        print(f"阿里云识别结果: {result_text}")
        
        return result_text, frames
    
    def get_llm_response(self, prompt, system_prompt=None):
        """从阿里云百炼DeepSeek获取回答"""
        try:
            print(f"正在使用阿里云百炼模型 {self.llm_model} 处理问题...")
            
            completion = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=4096
            )
            
            # 提取模型回答
            answer = completion.choices[0].message.content
            
            # 如果有推理过程，打印出来（仅供调试）
            if hasattr(completion.choices[0].message, 'reasoning_content') and completion.choices[0].message.reasoning_content:
                print(f"模型推理过程: {completion.choices[0].message.reasoning_content}")
            
            return answer
                
        except Exception as e:
            print(f"LLM响应错误: {e}")
            return "抱歉，我无法处理您的请求。"
    
    def text_to_speech(self, text):
        """使用阿里云语音合成将文本转换为语音并播放"""
        try:
            # 检查token是否有效
            self.check_token()
            
            # 准备一个内存缓冲区来存储音频数据
            self.tts_buffer = io.BytesIO()
            self.tts_completed = False
            
            # 创建阿里云语音合成器
            tts = nls.NlsSpeechSynthesizer(
                url=self.ali_url,
                token=self.ali_token,
                appkey=self.ali_appkey,
                on_metainfo=self.on_tts_metainfo,
                on_data=self.on_tts_data,
                on_completed=self.on_tts_completed,
                on_error=self.on_tts_error,
                on_close=self.on_tts_close
            )
            
            # 开始语音合成
            print("开始语音合成...")
            tts.start(
                text,
                aformat="wav",  # 使用wav格式
                voice="aicheng",  # 默认使用小云音色
                sample_rate=self.sample_rate,
                volume=80,  # 音量，取值范围0~100
                speech_rate=0,  # 语速，取值范围-500~500
                pitch_rate=0  # 语调，取值范围-500~500
            )
            
            # 等待语音合成完成
            timeout = 0
            while not self.tts_completed and timeout < 30:  # 最多等待30秒
                time.sleep(0.1)
                timeout += 1
            
            if timeout >= 30:
                print("语音合成超时")
                return
            
            # 准备播放音频
            self.tts_buffer.seek(0)
            
            # 创建播放器
            p = pyaudio.PyAudio()
            
            # 打开流进行播放
            stream = p.open(
                format=p.get_format_from_width(2),  # 16位音频
                channels=1,
                rate=self.sample_rate,
                output=True
            )
            
            # 读取数据播放
            data = self.tts_buffer.read(1024)
            while data:
                stream.write(data)
                data = self.tts_buffer.read(1024)

            time.sleep(0.5)
            
            # 关闭资源
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            print("语音播放完成")
            
        except Exception as e:
            print(f"语音合成错误: {e}")
    
    def run(self):
        """运行语音助手"""
        print("语音助手已启动")
        self.text_to_speech("机器人已启动")
        print(f"使用阿里云语音识别，Appkey: {self.ali_appkey}")
        print(f"使用阿里云百炼模型: {self.llm_model}")
        for wake_word in self.wake_words:
            print(f"唤醒词: {wake_word['word']}")
        print(f"阿里云语音服务URL: {self.ali_url}")
        
        # 检查麦克风是否正常工作
        self.text_to_speech("正在检查系统...")
        self._check_microphone()
        self.text_to_speech("所有功能正常")


        self.text_to_speech("你好，我是机器人。"
                            "我已经准备就绪，请给我指令。")
        
        while True:
            try:
                # 检查token是否有效
                self.check_token()

                # 等待唤醒词
                self.is_listening = False
                cmd = self.wait_for_wake_word()
                
                if not self.is_listening or cmd == WakeWord.WAKE_NONE:
                    print("未能检测到唤醒词，重新尝试...")
                    continue
                
                for wake_word in self.wake_words:
                    if wake_word['cmd'] == cmd:
                        self.text_to_speech(f"检测到唤醒词: {wake_word['word']}")
                        wake_word['handler']()
                        break
                
                time.sleep(0.1)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"发生错误: {e}")
                self.is_listening = False

    def _check_microphone(self):
        """检查麦克风是否正常工作"""
        print("检查麦克风...")
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            data = stream.read(1024)
            if data:
                print("麦克风正常工作")
            stream.close()
        except Exception as e:
            print(f"麦克风可能有问题: {e}")
            self.text_to_speech("麦克风可能有问题")
    
    def cleanup(self):
        """清理资源"""
        self.audio.terminate()

    # ===== 唤醒词处理 =====
    
    def handle_wake_llm(self):
        """处理唤醒词被检测到的情况"""

        self.text_to_speech("你好，请提问：")

        # 录制用户命令
        prompt, frames = self.record_command()
        if prompt:
            self.text_to_speech(f"您说: {prompt}。请让我思考一下。")
            # 获取LLM回答
            response = self.get_llm_response(
                prompt, 
                system_prompt="你是一个有用的助手，请简洁地回答用户的问题。用户问的问题可能是中文，也可能是英文。"
                                  "但是由于语音识别的缘故，用户的问题可能会有语音识别错误，请尽可能的理解问题，并给出回答。")
            print(f"回答: {response}")
            
            # 语音输出回答
            if self.enable_voice_response:
                self.text_to_speech(response)
        else:
            self.text_to_speech("未能识别您的问题，请重试")

    def _upload_to_oss(self, local_path):
        """使用预签名URL上传并返回可访问链接"""
        try:
            # 生成唯一文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            object_name = f"captured_images/{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
            
            # 上传文件
            self.oss_bucket.put_object_from_file(object_name, local_path)
            print(f"文件已上传至OSS: {object_name}")

            # 生成预签名URL（有效期1小时）
            signed_url = self.oss_bucket.sign_url(
                'GET',
                object_name,
                3600  # 过期时间（秒）
            )
            print(f"生成预签名URL: {signed_url}")
            
            return signed_url
            
        except Exception as e:
            print(f"OSS操作失败: {e}")
            return None

    def _check_raspberry_pi(self):
        """检测是否为树莓派环境"""
        try:
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read()
                    if 'Raspberry Pi' in model:
                        print("检测到树莓派环境:", model.strip())
                        return True
            return False
        except Exception as e:
            print(f"检测树莓派环境出错: {e}")
            return False
    
    def _take_photo_with_libcamera(self):
        """使用libcamera工具拍照（树莓派专用）"""
        # 生成唯一的临时文件名
        temp_image = f"/tmp/capture_{uuid.uuid4().hex[:8]}.jpg"
        
        # 使用libcamera命令拍照
        print("正在使用libcamera拍照...")
        cmd = f"libcamera-jpeg -o {temp_image} --width 1920 --height 1080 --nopreview -t 2000"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "未知错误"
            raise Exception(f"libcamera拍照失败: {error_msg}")
        
        if not os.path.exists(temp_image):
            raise Exception("拍照成功但未生成图片文件")
        
        print(f"libcamera拍照成功，保存至: {temp_image}")
        return temp_image
    
    def _take_photo_with_opencv(self):
        """使用OpenCV拍照"""
        print("正在使用OpenCV拍照...")
        cap = cv2.VideoCapture(self.capture_device)
        if not cap.isOpened():
            raise Exception(f"无法打开摄像头 {self.capture_device}")
        
        # 摄像头预热
        print("摄像头预热中...")
        time.sleep(3)
        
        # 拍照
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise Exception("OpenCV拍照失败")
        
        # 保存临时文件
        temp_image = f"/tmp/opencv_capture_{uuid.uuid4().hex[:8]}.jpg"
        cv2.imwrite(temp_image, frame)
        print(f"OpenCV拍照成功，保存至: {temp_image}")
        
        return temp_image
    
    def handle_wake_takephoto(self):
        """处理环境识别唤醒（集成OSS上传）"""
        try:
            self.text_to_speech("准备拍照，请把需要拍照的物品放在摄像头前")
            
            # 根据环境选择拍照方式
            temp_image = None
            if self.is_raspberry_pi:
                try:
                    temp_image = self._take_photo_with_libcamera()
                except Exception as e:
                    print(f"libcamera拍照失败: {e}, 尝试使用OpenCV拍照...")
                    temp_image = self._take_photo_with_opencv()
            else:
                temp_image = self._take_photo_with_opencv()

            self.text_to_speech("拍照完成，正在处理图片...")
            
            # 上传到OSS
            oss_url = self._upload_to_oss(temp_image)
            if not oss_url:
                raise Exception("图片上传失败")
            
            # 删除本地临时文件
            os.remove(temp_image)
            print("已清理本地临时文件")

            # 使用OSS URL进行识别
            self.text_to_speech("开始分析图片内容，请稍候")
            completion = self.openai_client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": [{
                            "type": "text", 
                            "text": "图像识别工具，只能识别图片主体内容，不会识别其它不重要的内容。"
                        }],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": oss_url,
                                    "detail": "high"  # 新增细节控制参数
                                }
                            },
                            {
                                "type": "text", 
                                "text": "请告诉我这张图片的最主要的物品是什么，只说名字，不要其它任何额外说明"
                            }
                        ],
                    }
                ],
                stream=True,
                temperature=0.3,  # 更低的随机性保证描述准确性
                max_tokens=4096
            )

            # 初始化变量
            reasoning_content = ""
            answer_content = ""
            is_answering = False
            response_buffer = ""  # 用于累积语音合成的文本
            
            print("\n" + "="*20 + "思考过程" + "="*20)
            for chunk in completion:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                
                # 实时打印思考内容
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    print(delta.reasoning_content, end='', flush=True)
                    reasoning_content += delta.reasoning_content
                    
                    # 累积到一定长度再合成语音
                    response_buffer += delta.reasoning_content
                    if len(response_buffer) > 30:
                        self.text_to_speech(response_buffer)
                        response_buffer = ""
                
                # 处理最终回答
                if delta.content:
                    if not is_answering:
                        print("\n" + "="*20 + "最终回答" + "="*20)
                        is_answering = True
                        if response_buffer:  # 清空剩余思考内容
                            self.text_to_speech(response_buffer)
                            response_buffer = ""
                    
                    print(delta.content, end='', flush=True)
                    answer_content += delta.content
                    response_buffer += delta.content

            # 合成剩余内容
            if response_buffer:
                self.text_to_speech(f"分析完成，这个是 {response_buffer}")

            print("\n分析完成")

        except Exception as e:
            print(f"环境识别失败: {e}")
            self.text_to_speech("分析过程出现错误，请重试")
            # 确保清理本地文件
            if os.path.exists(self.image_path):
                os.remove(self.image_path)

    def handle_wake_move(self):
        """处理移动指令，控制电机"""
        if self.enable_voice_response:
            self.text_to_speech("好的，如何移动？")

        prompt, frames = self.record_command()
        if prompt:
            print(f"您说: {prompt}")
            response = self.get_llm_response(
                prompt, 
                system_prompt="你是一个机器人控制助手，请解析用户的指令，给出移动方向。把结果分解为：方向和时间。"
                             "方向必须是：前、后、左转、右转、左、右、左前、右前、左后、右后其中的一个，不要用其他词。"
                             "时间单位为秒，必须是数字。"
                             "格式必须是两行：第一行为方向，第二行为时间（只要数字）。"
                             "例如：\n左\n20")
            print(f"回答: {response}")

            response = response.split("\n")
            direction = response[0]
            duration = float(response[1])

            self.text_to_speech(f"向{direction}移动{int(duration)}秒")

            if direction == "前":
                self.mecanum_wheels.move_forward(duration)
            elif direction == "后":
                self.mecanum_wheels.move_backward(duration)
            elif direction == "左":
                self.mecanum_wheels.move_left(duration)
            elif direction == "右":
                self.mecanum_wheels.move_right(duration)
            elif direction == "左前":
                self.mecanum_wheels.move_left_forward(duration)
            elif direction == "右前":
                self.mecanum_wheels.move_right_forward(duration)
            elif direction == "左后":
                self.mecanum_wheels.move_left_backward(duration)
            elif direction == "右后":
                self.mecanum_wheels.move_right_backward(duration)    
            elif direction == "左转":
                self.mecanum_wheels.rotate_left(duration)
            elif direction == "右转":
                self.mecanum_wheels.rotate_right(duration)
            else:
                self.text_to_speech("移动方向错误，请重试")

def main():
    """主函数"""
    # 关闭nls的日志跟踪
    nls.enableTrace(False)

    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\n程序已退出") 
    finally:
        assistant.cleanup()


if __name__ == "__main__":
    main() 
