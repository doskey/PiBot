#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import os
from enum import Enum
from vosk import Model, KaldiRecognizer, SetLogLevel

from modules.audio_recorder import AudioRecorder


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
    语音唤醒模块，负责处理语音唤醒
    使用vosk在本地进行唤醒词识别
    """
    
    def __init__(self, audio_recorder=None):
        """
        初始化语音唤醒模块
        
        Args:
            audio_recorder: 音频录制模块实例，如果为None则创建新实例
        """
        # 音频录制模块
        self.audio_recorder = audio_recorder if audio_recorder else AudioRecorder()
        
        # 控制运行状态的标志
        self.running = True
        
        # 初始化唤醒词列表
        self.wake_words = [
            {'word': '你好机器人', 'cmd': WakeWord.WAKE_LLM},
            {'word': '机器人这是什么', 'cmd': WakeWord.WAKE_TAKEPHOTO},
            {'word': '机器人出发', 'cmd': WakeWord.WAKE_MOVE}
        ]
        
        # 初始化Vosk模型
        self._init_vosk_model()
    
    def _init_vosk_model(self):
        """初始化Vosk模型"""
        try:
            # 设置Vosk日志级别
            SetLogLevel(-1)
            
            # 检查模型目录是否存在
            model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vosk_models", "vosk-model-small-cn-0.22")
            if not os.path.exists(model_dir):
                print(f"警告：Vosk模型不存在于{model_dir}，请下载模型")
                print("您可以从 https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip 下载模型")
                print("然后解压到 models/vosk-model-small-cn-0.22 目录")
                self.vosk_enabled = False
            else:
                # 初始化Vosk模型
                self.vosk_model = Model(model_dir)
                self.vosk_enabled = True
                print("Vosk模型加载成功，将使用本地语音唤醒")
        except Exception as e:
            print(f"Vosk模型初始化失败: {e}")
            self.vosk_enabled = False
    
    def wait_for_wake_word(self):
        """
        等待唤醒词，这是一个阻塞方法，直到检测到唤醒词或出错才会返回
        
        Returns:
            WakeWord: 检测到的唤醒词类型
        """
        print("\n等待唤醒词...")
        
        # 如果Vosk不可用，直接返回
        if not hasattr(self, 'vosk_enabled') or not self.vosk_enabled:
            print("Vosk模型不可用，无法进行本地唤醒")
            return WakeWord.WAKE_NONE
        
        # 创建识别器
        recognizer = KaldiRecognizer(self.vosk_model, self.audio_recorder.sample_rate)
        
        # 创建音频流
        stream = self.audio_recorder.create_stream(use_callback=False)
        
        try:
            # 持续循环处理音频数据
            while self.running:
                # 读取音频数据
                data = stream.read(self.audio_recorder.chunk_size, exception_on_overflow=False)
                
                # 送入Vosk识别
                if recognizer.AcceptWaveform(data):
                    # 获取识别结果
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    text = text.replace(" ", "")

                    if text:
                        print(f"Vosk识别结果: {text}")
                    
                        # 检查是否包含唤醒词
                        for wake_word in self.wake_words:
                            keyword = wake_word['word'].lower()
                            if keyword in text.lower():
                                print(f"[Vosk] 检测到唤醒词: {wake_word['word']}")
                                return wake_word['cmd']
                
                time.sleep(0.1)
        
        except Exception as e:
            print(f"唤醒词监听出错: {e}")
            return WakeWord.WAKE_NONE
        finally:
            stream.stop_stream()
            stream.close()
        
        return WakeWord.WAKE_NONE
    
    def cleanup(self):
        """清理资源"""
        print("清理语音唤醒资源...")
        self.running = False 