#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import wave
import pyaudio
import ollama
import numpy as np
import io
from dotenv import load_dotenv
import nls  # 阿里云语音识别SDK
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest


class VoiceAssistant:
    """
    基于阿里云语音服务和Ollama的语音助手
    
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
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")  # 使用环境变量或默认值
        self.wake_word = os.getenv("WAKE_WORD", "你好机器人")  # 唤醒词
        self.is_listening = False  # 是否处于主动监听状态
        
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
        self.recognition_completed = False
        
        # 初始化语音合成相关变量
        self.tts_buffer = None
        self.tts_completed = False
    
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
        result = json.loads(message)
        
        # 正确提取result字段
        recognition_text = ""
        if "payload" in result and "result" in result["payload"]:
            recognition_text = result["payload"]["result"]
        elif "result" in result:
            recognition_text = result["result"]
        else:
            return
            
        self.recognition_result = recognition_text
        print(f"中间结果: {recognition_text}")
            
        # 在回调中检查唤醒词，提高响应速度
        if not self.is_listening and self.wake_word.lower() in recognition_text.lower():
            print(f"[精确匹配成功] 检测到唤醒词: {self.wake_word}")
            self.handle_wake_word("中间结果回调")
    
    def on_recognition_completed(self, message, *args):
        """当一句话识别返回最终识别结果时的回调函数"""
        result = json.loads(message)
        
        # 正确提取result字段
        recognition_text = ""
        if "payload" in result and "result" in result["payload"]:
            recognition_text = result["payload"]["result"]
        elif "result" in result:
            recognition_text = result["result"] 
        else:
            print("无法解析完成结果")
            recognition_text = ""
            
        self.recognition_result = recognition_text
        print(f"识别完成: {recognition_text}")
            
        # 在完成回调中也检查唤醒词
        if not self.is_listening and self.wake_word.lower() in recognition_text.lower():
            print(f"[完成回调-精确匹配] 检测到唤醒词: {self.wake_word}")
            self.handle_wake_word("完成回调")
                
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
    
    # ===== 唤醒词处理 =====
    
    def handle_wake_word(self, detected_from="未知位置"):
        """统一处理唤醒词被检测到的情况"""
        if not self.is_listening:  # 防止重复唤醒
            self.is_listening = True
            print(f"唤醒成功! [{detected_from}] 即将开始聆听指令...")
            # 在检测到唤醒词后播放提示音
            try:
                self.text_to_speech("我在，您请提问：")
            except Exception as e:
                print(f"语音播放失败，但唤醒成功: {e}")
            return True
        return False
    
    # ===== 核心功能 =====
    
    def wait_for_wake_word(self):
        """使用阿里云一句话识别监听唤醒词"""
        print("\n正在等待唤醒词...")
        print(f"当您说'{self.wake_word}'时，我会开始聆听您的指令")
        print(f"(也可以说'机器人'或类似的词语来唤醒)")
        
        # 检查token是否有效
        self.check_token()
        
        # 创建阿里云识别器
        recognizer = self._create_recognizer()
        
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=2048
        )
        
        try:
            # 开始识别
            recognizer.start(
                aformat="pcm",
                sample_rate=self.sample_rate,
                enable_intermediate_result=True,
                enable_punctuation_prediction=True
            )
            
            self.recognition_completed = False
            recognition_restart_count = 0
            max_recognition_restarts = 50  # 最多重启50次，防止无限循环
            
            while not self.is_listening and recognition_restart_count < max_recognition_restarts:
                try:
                    data = stream.read(2048)
                    # 发送音频数据给阿里云识别器
                    recognizer.send_audio(data)
                    
                    # 检查是否包含唤醒词
                    if not self.is_listening and self.wake_word.lower() in self.recognition_result.lower():
                        print(f"[主循环-精确匹配] 检测到唤醒词: {self.wake_word}")
                        self.handle_wake_word("主循环检测")
                        break
                    
                    # 如果一段语音识别完成，清空结果并重新开始
                    if self.recognition_completed:
                        print(f"一段识别完成，结果: {self.recognition_result}")
                        
                        # 再次检查唤醒词，防止漏掉
                        if not self.is_listening and self.wake_word.lower() in self.recognition_result.lower():
                            print(f"[重启前-精确匹配] 检测到唤醒词: {self.wake_word}")
                            self.handle_wake_word("重启前检测")
                            break
                        
                        # 重新开始识别
                        recognizer.stop()
                        recognizer = self._create_recognizer()
                        recognizer.start(
                            aformat="pcm",
                            sample_rate=self.sample_rate,
                            enable_intermediate_result=True,
                            enable_punctuation_prediction=True
                        )
                        self.recognition_result = ""
                        self.recognition_completed = False
                        recognition_restart_count += 1
                        print(f"重新开始识别 (第{recognition_restart_count}次)")
                except Exception as e:
                    print(f"读取麦克风数据时出错: {e}")
                    time.sleep(0.1)
            
            if recognition_restart_count >= max_recognition_restarts:
                print("达到最大重启次数，请检查麦克风和网络连接")
        
        finally:
            try:
                recognizer.stop()
            except:
                pass
            stream.close()
    
    def _create_recognizer(self):
        """创建并返回阿里云识别器实例"""
        return nls.NlsSpeechRecognizer(
            url=self.ali_url,
            token=self.ali_token,
            appkey=self.ali_appkey,
            on_start=self.on_recognition_start,
            on_result_changed=self.on_recognition_result_changed,
            on_completed=self.on_recognition_completed,
            on_error=self.on_recognition_error,
            on_close=self.on_recognition_close
        )
    
    def record_command(self):
        """使用阿里云一句话识别录制用户命令"""
        print("请说出您的问题...")
        
        # 检查token是否有效
        self.check_token()
        
        # 创建阿里云识别器
        recognizer = self._create_recognizer()
        
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
    
    def save_audio(self, frames, filename="recorded_command.wav"):
        """保存录制的音频（可选功能）"""
        if not frames:
            return
        
        # 将frames列表转换为bytes对象的列表
        byte_frames = []
        for frame in frames:
            if isinstance(frame, np.ndarray):
                byte_frames.append(frame.tobytes())
            else:
                byte_frames.append(frame)
        
        # 合并所有帧
        audio_data = b''.join(byte_frames)
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(self.sample_rate)
        wf.writeframes(audio_data)
        wf.close()
        print(f"已保存录音到 {filename}")
    
    def get_llm_response(self, query):
        """从Ollama获取回答"""
        try:
            print(f"正在使用Ollama模型 {self.ollama_model} 处理问题...")
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个有用的助手，请简洁地回答用户的问题。用户问的问题可能是中文，也可能是英文。"
                                  "但是由于语音识别的缘故，用户的问题可能会有一些错误，比如语音识别错误，请根据错误进行纠正。"
                    },
                    {"role": "user", "content": query}
                ]
            )
            answer = response['message']['content']
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
                volume=50,  # 音量，取值范围0~100
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
        print(f"使用阿里云语音识别，Appkey: {self.ali_appkey}")
        print(f"唤醒词: {self.wake_word}")
        print(f"阿里云URL: {self.ali_url}")
        
        # 检查麦克风是否正常工作
        self._check_microphone()
        
        while True:
            try:
                # 等待唤醒词
                self.is_listening = False
                self.wait_for_wake_word()
                
                if not self.is_listening:
                    print("未能检测到唤醒词，重新尝试...")
                    continue
                
                # 录制用户命令
                query, frames = self.record_command()
                if not query:
                    print("未能识别您的问题，请重试")
                    continue
                
                print(f"您说: {query}")
                
                # 获取LLM回答
                response = self.get_llm_response(query)
                print(f"回答: {response}")
                
                # 语音输出回答
                if self.enable_voice_response:
                    self.text_to_speech(response)
                
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
    
    def cleanup(self):
        """清理资源"""
        self.audio.terminate()


class TestState:
    """用于测试模式的状态类"""
    result = ""
    completed = False


def run_test_mode():
    """运行测试模式，测试阿里云语音识别"""
    print("======= 测试模式 =======")
    print("测试阿里云一句话识别")
    
    # 创建助手实例
    assistant = VoiceAssistant()
    
    # 检查配置
    print(f"阿里云配置情况:")
    print(f"  Token: {'已设置' if assistant.ali_token else '未设置'}")
    print(f"  Appkey: {'已设置' if assistant.ali_appkey else '未设置'}")
    print(f"  URL: {assistant.ali_url}")
    
    # 回调函数
    def test_start(message, *args):
        print(f"测试识别开始:")
    
    def test_result_changed(message, *args):
        result = json.loads(message)
        if "result" in result:
            TestState.result = result["result"]
            print(f"测试中间结果: {TestState.result}")
    
    def test_completed(message, *args):
        result = json.loads(message)
        if "result" in result:
            TestState.result = result["result"]
        print(f"测试识别完成: {TestState.result}")
        TestState.completed = True
    
    def test_error(message, *args):
        print(f"测试识别错误: {message}")
        TestState.completed = True
    
    def test_close(*args):
        print("测试识别连接关闭")
    
    try:
        # 创建识别器
        recognizer = nls.NlsSpeechRecognizer(
            url=assistant.ali_url,
            token=assistant.ali_token,
            appkey=assistant.ali_appkey,
            on_start=test_start,
            on_result_changed=test_result_changed,
            on_completed=test_completed,
            on_error=test_error,
            on_close=test_close
        )
        
        print("创建麦克风流...")
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        print("开始测试识别...")
        recognizer.start(
            aformat="pcm",
            sample_rate=16000,
            enable_intermediate_result=True,
            enable_punctuation_prediction=True
        )
        
        print("请说话...")
        # 记录30秒
        for i in range(300):  # 30秒 = 300 * 0.1
            data = stream.read(1024)
            recognizer.send_audio(data)
            print(".", end="", flush=True)
            if i % 10 == 0:
                print(f" {i//10}s", end="", flush=True)
            if TestState.completed:
                print("\n识别已完成")
                break
            time.sleep(0.1)
        
        print("\n停止识别...")
        recognizer.stop()
        stream.close()
        p.terminate()
        
        print(f"\n最终识别结果: {TestState.result}")
        print("测试完成!")
    
    except Exception as e:
        print(f"测试时出错: {e}")


def main():
    """主函数"""
    # 关闭nls的日志跟踪
    nls.enableTrace(False)
    
    # 检查是否为测试模式
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
    if test_mode:
        run_test_mode()
    else:
        # 正常模式
        assistant = VoiceAssistant()
        try:
            assistant.run()
        except KeyboardInterrupt:
            print("\n程序已退出") 
        finally:
            assistant.cleanup()


if __name__ == "__main__":
    main() 