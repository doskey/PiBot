#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import wave
import pyaudio
import whisper
import ollama
from dotenv import load_dotenv
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import tempfile
import numpy as np

# 加载环境变量
load_dotenv()

class VoiceAssistant:
    def __init__(self):
        # 配置参数
        self.sample_rate = 16000
        self.silence_threshold = 2.0  # 句子结束后的静默时间阈值（秒）
        self.enable_voice_response = True  # 是否启用语音回答
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")  # 使用环境变量或默认值
        
        # 初始化Ollama客户端（不需要额外初始化，直接使用ollama库即可）
        
        # 初始化麦克风和音频处理
        self.audio = pyaudio.PyAudio()
        
        # 初始化Whisper模型
        try:
            print("正在加载Whisper模型...")
            # 使用openai-whisper加载base模型
            self.model = whisper.load_model("small")
            print("成功加载Whisper模型")
        except Exception as e:
            print(f"加载Whisper模型失败: {e}")
            exit(1)
    
    def wait_for_start(self):
        """等待用户按下回车键开始录音"""
        print("\n准备就绪。按回车键开始录音...")
        input()
        print("开始录音")
    
    def record_command(self):
        """录制用户命令直到句子结束"""
        print("请说出您的问题...")
        
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
        last_audio_level = 0
        
        try:
            while True:
                data = stream.read(1024)
                frames.append(data)
                
                # 计算当前音频帧的音量级别
                audio_data = np.frombuffer(data, dtype=np.int16)
                current_level = np.abs(audio_data).mean()
                
                # 检测是否开始说话
                if current_level > 1000:  # 音量阈值，可以根据需要调整
                    speaking_started = True
                    silence_frames = 0
                elif speaking_started:
                    # 如果音量低于阈值，增加静默帧计数
                    if current_level < 500:  # 静默阈值，可以根据需要调整
                        silence_frames += 1
                    else:
                        silence_frames = 0
                
                # 如果连续多帧静默，认为句子结束
                if speaking_started and silence_frames > int(self.silence_threshold * self.sample_rate / 1024):
                    print("检测到句子结束")
                    break
        
        finally:
            stream.close()
        
        # 保存录音到临时文件，因为whisper需要文件路径
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_filename = temp_file.name
            
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # 使用Whisper进行语音识别
        try:
            print("正在识别语音...")
            # 使用openai-whisper的transcribe方法
            result = self.model.transcribe(temp_filename, language="zh")
            text = result["text"]
            print(f"识别结果: {text}")
            
            # 删除临时文件
            os.unlink(temp_filename)
            
            return text, frames
        except Exception as e:
            print(f"语音识别错误: {e}")
            
            # 删除临时文件
            os.unlink(temp_filename)
            
            return "", frames
    
    def save_audio(self, frames, filename="recorded_command.wav"):
        """保存录制的音频（可选功能）"""
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"已保存录音到 {filename}")
    
    def get_llm_response(self, query):
        """从Ollama获取回答"""
        try:
            print(f"正在使用Ollama模型 {self.ollama_model} 处理问题...")
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {"role": "system", "content": "你是一个有用的助手，请简洁地回答用户的问题。"},
                    {"role": "user", "content": query}
                ]
            )
            answer = response['message']['content']
            return answer
        except Exception as e:
            print(f"LLM响应错误: {e}")
            return "抱歉，我无法处理您的请求。"
    
    def text_to_speech(self, text):
        """将文本转换为语音并播放"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
            
            # 文字转语音
            tts = gTTS(text=text, lang='zh-cn')
            tts.save(temp_filename)
            
            # 播放语音
            sound = AudioSegment.from_mp3(temp_filename)
            play(sound)
            
            # 删除临时文件
            os.unlink(temp_filename)
        except Exception as e:
            print(f"语音合成错误: {e}")
    
    def run(self):
        """运行语音助手"""
        print("语音助手已启动")
        
        while True:
            try:
                # 等待用户按键启动
                self.wait_for_start()
                
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
    
    def cleanup(self):
        """清理资源"""
        self.audio.terminate()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    try:
        assistant.run()
    finally:
        assistant.cleanup() 