#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import io
import pyaudio
import nls  # 阿里云语音合成SDK
from dotenv import load_dotenv
from modules.ali_token import token_manager
from modules.logger import logger

class TextToSpeech:
    """
    阿里云语音合成模块
    
    功能:
    - 文本转语音
    - 播放合成的语音
    """
    
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 获取模块专用日志器
        self.log = logger.get_logger("text_to_speech")
        
        # 音频参数配置
        self.sample_rate = 16000
        
        # 初始化语音合成相关变量
        self.tts_buffer = None
        self.tts_completed = False
        
        self.log.info("语音合成模块初始化完成")
    
    # ===== 语音合成回调函数 =====
    
    def on_tts_metainfo(self, message, *args):
        """语音合成元信息回调函数"""
        self.log.debug(f"合成元信息: {message}")
    
    def on_tts_data(self, data, *args):
        """语音合成数据回调函数"""
        # 将音频数据写入缓冲区
        if hasattr(self, 'tts_buffer') and self.tts_buffer:
            self.tts_buffer.write(data)
    
    def on_tts_completed(self, message, *args):
        """语音合成完成回调函数"""
        self.log.debug("语音合成完成")
        self.tts_completed = True
    
    def on_tts_error(self, message, *args):
        """语音合成错误回调函数"""
        self.log.error(f"语音合成错误: {message}")
        self.tts_completed = True
    
    def on_tts_close(self, *args):
        """语音合成连接关闭回调函数"""
        self.log.debug("语音合成连接关闭")
    
    # ===== 核心功能 =====
    
    def synthesize_speech(self, text, voice="aicheng", volume=50, speech_rate=0, pitch_rate=0):
        """
        使用阿里云语音合成将文本转换为语音并播放
        
        参数:
        - text: 要合成的文本
        - voice: 音色，默认为"aicheng"
        - volume: 音量，取值范围0~100，默认50
        - speech_rate: 语速，取值范围-500~500，默认0
        - pitch_rate: 语调，取值范围-500~500，默认0
        """
        try:
            # 检查token是否有效
            token_manager.check_token()
            
            # 准备一个内存缓冲区来存储音频数据
            self.tts_buffer = io.BytesIO()
            self.tts_completed = False
            
            # 创建阿里云语音合成器
            tts = nls.NlsSpeechSynthesizer(
                url=token_manager.get_url(),
                token=token_manager.get_token_str(),
                appkey=token_manager.get_appkey(),
                on_metainfo=self.on_tts_metainfo,
                on_data=self.on_tts_data,
                on_completed=self.on_tts_completed,
                on_error=self.on_tts_error,
                on_close=self.on_tts_close
            )
            
            # 开始语音合成
            self.log.info("开始语音合成...")
            tts.start(
                text,
                aformat="wav",  # 使用wav格式
                voice=voice,  
                sample_rate=self.sample_rate,
                volume=volume,  
                speech_rate=speech_rate,  
                pitch_rate=pitch_rate
            )
            
            # 等待语音合成完成
            timeout = 0
            while not self.tts_completed and timeout < 30:  # 最多等待30秒
                time.sleep(0.1)
                timeout += 1
            
            if timeout >= 30:
                self.log.warning("语音合成超时")
                return False
            
            # 合成成功
            return True
            
        except Exception as e:
            self.log.error(f"语音合成错误: {e}")
            return False
    
    def play_audio(self):
        """播放合成的音频"""
        if self.tts_buffer is None:
            self.log.warning("没有可播放的音频")
            return False
            
        try:
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
            
            self.log.info("语音播放完成")
            return True
            
        except Exception as e:
            self.log.error(f"语音播放错误: {e}")
            return False
    
    def text_to_speech(self, text, voice="aicheng", volume=50, speech_rate=0, pitch_rate=0):
        """
        将文本转换为语音并直接播放（合成和播放的组合）
        
        参数:
        - text: 要合成的文本
        - voice: 音色，默认为"aicheng"
        - volume: 音量，取值范围0~100，默认50
        - speech_rate: 语速，取值范围-500~500，默认0
        - pitch_rate: 语调，取值范围-500~500，默认0
        """
        if self.synthesize_speech(text, voice, volume, speech_rate, pitch_rate):
            return self.play_audio()
        return False
    
    def get_audio_buffer(self):
        """获取合成的音频缓冲区，可以用于保存等操作"""
        if self.tts_buffer:
            self.tts_buffer.seek(0)
            return self.tts_buffer
        return None
