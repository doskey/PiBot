#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyaudio
import numpy as np
import json
import time
import nls
from enum import Enum


class WakeWord(Enum):
    """
    唤醒词枚举类
    """
    WAKE_NONE = 0
    WAKE_LLM = 1
    WAKE_TAKEPHOTO = 2
    WAKE_MOVE = 3


class VoiceWakeup:
    """
    语音唤醒模块，负责处理语音唤醒和命令识别
    """
    
    def __init__(self, license_manager):
        """
        初始化语音唤醒模块
        
        Args:
            license_manager: 阿里云License管理器实例
        """
        # 保存License管理器引用
        self.license_manager = license_manager
        
        # 阿里云语音识别配置
        self.ali_url = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
        self.ali_appkey = ""
        
        # 音频参数配置
        self.sample_rate = 16000
        self.silence_threshold = 1.0  # 从2.0秒降低到1.0秒，更快检测到句子结束
        self.silence_level = 300  # 静默音量阈值，低于此值被视为静默
        self.speaking_level = 800  # 说话音量阈值，高于此值被视为说话
        
        # 初始化PyAudio
        self.audio = pyaudio.PyAudio()
        
        # 用于阿里云识别结果的变量
        self.recognition_result = ""
        self.recognition_cmd = WakeWord.WAKE_NONE
        self.recognition_completed = False
        
        # 唤醒状态
        self.is_listening = False
        
        # 初始化唤醒词列表
        self.wake_words = [
            {'word': '你好机器人', 'cmd': WakeWord.WAKE_LLM},
            {'word': '机器人这是什么', 'cmd': WakeWord.WAKE_TAKEPHOTO},
            {'word': '机器人出发', 'cmd': WakeWord.WAKE_MOVE}
        ]
    
    def set_appkey(self, appkey):
        """设置阿里云AppKey"""
        self.ali_appkey = appkey
    
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
                print(f"未检测到唤醒词")
            
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
    
    def _process_audio_chunk(self, audio_data):
        """处理单个语音片段"""
        # 获取当前Token
        ali_token = self.license_manager.get_token()
        
        # 直接创建识别器实例
        recognizer = nls.NlsSpeechRecognizer(
            url=self.ali_url,
            token=ali_token,
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
                enable_inverse_text_normalization=True # 启用数字转换功能
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

                time.sleep(0.01)

        finally:
            stream.close()

        return result
    
    def record_command(self):
        """使用阿里云一句话识别录制用户命令"""
        print("请说出您的问题...")
        
        # 获取当前Token
        ali_token = self.license_manager.get_token()
        
        # 创建阿里云识别器（直接实例化）
        recognizer = nls.NlsSpeechRecognizer(
            url=self.ali_url,
            token=ali_token,
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

                time.sleep(0.01)
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
    
    def reset_listening_state(self):
        """重置监听状态"""
        self.is_listening = False
        self.recognition_cmd = WakeWord.WAKE_NONE
    
    def cleanup(self):
        """清理资源"""
        self.audio.terminate() 