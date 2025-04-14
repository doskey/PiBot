#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import nls
import numpy as np

from modules.audio_recorder import AudioRecorder


class VoiceRecognition:
    """
    语音识别模块，负责将语音转换为文字
    使用阿里云进行短句云端识别
    """
    
    def __init__(self, license_manager, audio_recorder=None):
        """
        初始化语音识别模块
        
        Args:
            license_manager: 阿里云License管理器实例
            audio_recorder: 音频录制模块实例，如果为None则创建新实例
        """
        # 保存License管理器引用
        self.license_manager = license_manager
        
        # 阿里云语音识别配置
        self.ali_url = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
        self.ali_appkey = ""
        
        # 音频录制模块
        self.audio_recorder = audio_recorder if audio_recorder else AudioRecorder()
        
        # 用于阿里云识别结果的变量
        self.recognition_result = ""
        self.recognition_completed = False
    
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
            else:
                print(f"未检测到结果")
            
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
        """处理单个语音片段（使用阿里云识别）"""
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
    
    def recognize_speech(self):
        """
        录制并识别短句语音，使用阿里云自动检测语音开始和结束
        
        Returns:
            tuple: (识别结果文本, 音频帧列表)
        """
        print("请说出您的问题...")
        
        # 创建本地音频流
        stream = self.audio_recorder.create_stream(use_callback=False)
        
        # 重置识别结果
        self.recognition_completed = False
        self.recognition_result = ""
        
        # 准备存储音频帧
        frames = []
        
        try:
            # 获取当前Token
            ali_token = self.license_manager.get_token()
            
            # 创建阿里云识别器
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
            
            # 开始识别
            recognizer.start(
                enable_inverse_text_normalization=True,  # 启用数字转换功能
                enable_voice_detection=True              # 启用语音活动检测
            )
            
            # 设置最大录音时间（安全保障）
            max_recording_time = 15  # 秒
            start_time = time.time()
            
            # 开始录音并发送到阿里云，直到识别完成或超时
            while not self.recognition_completed and (time.time() - start_time) < max_recording_time:
                # 读取音频数据
                data = stream.read(self.audio_recorder.chunk_size, exception_on_overflow=False)
                frames.append(data)
                
                # 发送音频数据给阿里云识别器
                recognizer.send_audio(data)
                
                # 短暂休眠，减少CPU占用
                time.sleep(0.01)
            
            # 停止识别
            recognizer.stop()
            
            # 如果是因为超时退出的，而不是正常识别完成，额外等待一下结果
            if not self.recognition_completed:
                print("录音达到最大时长，等待最终识别结果...")
                wait_timeout = 5  # 最多再等待5秒
                wait_start = time.time()
                while not self.recognition_completed and (time.time() - wait_start) < wait_timeout:
                    time.sleep(0.1)
            
            # 获取最终结果
            result_text = self.recognition_result
            print(f"阿里云识别结果: {result_text}")
            
            return result_text, frames
            
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
    
    def process_audio_file(self, audio_data):
        """
        处理已有的音频数据
        
        Args:
            audio_data: 音频数据（二进制）
            
        Returns:
            str: 识别结果文本
        """
        # 重置状态
        self.recognition_result = ""
        self.recognition_completed = False
        
        # 处理音频
        self._process_audio_chunk(audio_data)
        
        return self.recognition_result 