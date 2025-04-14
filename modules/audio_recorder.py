#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyaudio
import numpy as np
import time
import queue
import threading


class AudioRecorder:
    """
    音频录制公共模块，提供录音相关功能
    """
    
    def __init__(self):
        """初始化音频录制模块"""
        # 音频参数配置
        self.sample_rate = 16000
        self.silence_threshold = 1.0  # 静默阈值（秒）
        self.chunk_size = 1024  # 音频数据块大小
        
        # 音量阈值
        self.speaking_level = 800  # 说话音量阈值
        self.silence_level = 300   # 静默音量阈值
        
        # 初始化PyAudio
        self.audio = pyaudio.PyAudio()
        
        # 音频数据队列
        self.audio_queue = queue.Queue()
        
        # 运行状态
        self.running = True
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """音频回调函数，将音频数据放入队列"""
        self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    def create_stream(self, use_callback=False):
        """
        创建音频流
        
        Args:
            use_callback: 是否使用回调方式创建流
            
        Returns:
            创建的音频流对象
        """
        if use_callback:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
        else:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
        
        return stream
    
    def record_audio_until_silence(self, stream):
        """
        录制音频直到检测到静默
        
        Args:
            stream: 音频流对象
            
        Returns:
            tuple: (音频帧列表, 是否检测到语音)
        """
        frames = []
        is_speaking = False
        speaking_started = False
        silence_frames = 0
        no_speech_timeout = int(5 * self.sample_rate / self.chunk_size)  # 5秒无语音则超时
        no_speech_counter = 0
        
        try:
            while True:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                
                # 计算当前音频帧的音量级别
                audio_data = np.frombuffer(data, dtype=np.int16)
                current_level = np.abs(audio_data).mean()
                
                # 检测是否开始说话
                if current_level > self.speaking_level:  # 音量高于阈值，认为开始说话
                    if not is_speaking:
                        print("检测到语音开始")
                        is_speaking = True
                        speaking_started = True
                    
                    frames.append(data)
                    silence_frames = 0
                    no_speech_counter = 0
                elif speaking_started:
                    # 如果音量低于阈值，增加静默帧计数
                    frames.append(data)
                    if current_level < self.silence_level:
                        silence_frames += 1
                    else:
                        silence_frames = max(0, silence_frames - 1)  # 如果又检测到声音，减少静默计数
                    
                    # 静默超过阈值，结束录制
                    silence_threshold_frames = int(self.silence_threshold * self.sample_rate / self.chunk_size)
                    if silence_frames > silence_threshold_frames:
                        print("检测到语音结束")
                        break
                else:
                    # 如果还没开始说话，检查超时
                    no_speech_counter += 1
                    if no_speech_counter >= no_speech_timeout:
                        print("等待说话超时")
                        return frames, False
                
                time.sleep(0.01)
                
        except Exception as e:
            print(f"录制音频时出错: {e}")
            return frames, False
        
        return frames, speaking_started
    
    def clear_queue(self):
        """清空音频队列"""
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
    
    def cleanup(self):
        """清理资源"""
        print("清理音频录制资源...")
        self.running = False
        self.audio.terminate() 