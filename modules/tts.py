#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import time
import pyaudio
import nls


class TextToSpeech:
    """
    语音播放模块，负责文本转语音服务
    """
    
    def __init__(self, license_manager):
        """
        初始化语音播放模块
        
        Args:
            license_manager: 阿里云License管理器实例
        """
        # 保存License管理器引用
        self.license_manager = license_manager
        
        # 阿里云语音合成配置
        self.ali_url = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
        self.ali_appkey = ""
        
        # 音频参数配置
        self.sample_rate = 16000
        
        # 初始化语音合成相关变量
        self.tts_buffer = None
        self.tts_completed = False
    
    def set_appkey(self, appkey):
        """设置阿里云AppKey"""
        self.ali_appkey = appkey
    
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
    
    def text_to_speech(self, text):
        """使用阿里云语音合成将文本转换为语音并播放"""
        try:
            # 获取当前Token
            ali_token = self.license_manager.get_token()
            
            # 准备一个内存缓冲区来存储音频数据
            self.tts_buffer = io.BytesIO()
            self.tts_completed = False
            
            # 创建阿里云语音合成器
            tts = nls.NlsSpeechSynthesizer(
                url=self.ali_url,
                token=ali_token,
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