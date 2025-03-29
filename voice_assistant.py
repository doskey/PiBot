#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import wave
import pyaudio
import ollama
from dotenv import load_dotenv
import pyttsx3
import numpy as np
from vosk import Model, KaldiRecognizer, SetLogLevel

# 加载环境变量
load_dotenv()

class VoiceAssistant:
    def __init__(self):
        # 配置参数
        self.sample_rate = 16000
        self.silence_threshold = 2.0  # 句子结束后的静默时间阈值（秒）
        self.enable_voice_response = True  # 是否启用语音回答
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")  # 使用环境变量或默认值
        self.vosk_model_path = os.getenv("VOSK_MODEL_PATH", "model")  # Vosk模型路径
        self.wake_word = os.getenv("WAKE_WORD", "你好机器人")  # 唤醒词
        self.is_listening = False  # 是否处于主动监听状态
        
        # 禁用Vosk日志
        SetLogLevel(-1)
        
        # 初始化Vosk模型（用于唤醒词检测和语音识别）
        try:
            print("正在加载Vosk模型，这可能需要一些时间...")
            self.vosk_model = Model(self.vosk_model_path)
            print("成功加载Vosk模型")
        except Exception as e:
            print(f"加载Vosk模型失败: {e}")
            print("请确保已下载Vosk模型并设置了正确的VOSK_MODEL_PATH环境变量")
            exit(1)
        
        # 初始化麦克风和音频处理
        self.audio = pyaudio.PyAudio()
    
    def wait_for_wake_word(self):
        """监听唤醒词"""
        print("\n正在等待唤醒词...")
        
        # 创建Vosk识别器
        rec = KaldiRecognizer(self.vosk_model, self.sample_rate)
        
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=2048
        )
        
        try:
            while not self.is_listening:
                data = stream.read(2048)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").lower()
                    text = text.replace(" ", "")

                    print(f"Vosk检测: {text}")
                    
                    # 检查唤醒词是否在识别结果中
                    if self.wake_word.lower() in text:
                        print(f"检测到唤醒词: {self.wake_word}")
                        self.is_listening = True
                        # 播放提示音或反馈
                        print("我在听...")
                else:
                    # 可以检查部分结果，提高响应速度
                    partial = json.loads(rec.PartialResult())
                    partial_text = partial.get("partial", "").lower()
                    if self.wake_word.lower() in partial_text:
                        print(f"检测到唤醒词: {self.wake_word}")
                        self.is_listening = True
                        # 播放提示音或反馈
                        self.text_to_speech("我在听")
        
        finally:
            stream.close()
    
    def record_command(self):
        """录制用户命令"""
        print("请说出您的问题...")
        
        # 创建Vosk识别器
        rec = KaldiRecognizer(self.vosk_model, self.sample_rate)
        
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
        result_text = ""
        
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
                
                # 将音频数据传递给Vosk识别器
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if result.get("text", ""):
                        result_text += " " + result.get("text", "")
                
                # 如果连续多帧静默，认为句子结束
                if speaking_started and silence_frames > int(self.silence_threshold * self.sample_rate / 1024):
                    # 获取最后的识别结果
                    result = json.loads(rec.FinalResult())
                    if result.get("text", ""):
                        result_text += " " + result.get("text", "")
                    print("检测到句子结束")
                    break
        
        finally:
            stream.close()
        
        # 处理识别结果
        result_text = result_text.replace(" ", "")
        result_text = result_text.strip()
        print(f"Vosk识别结果: {result_text}")
        
        return result_text, frames
    
    def save_audio(self, frames, filename="recorded_command.wav"):
        """保存录制的音频（可选功能）"""
        audio_data = np.concatenate(frames, axis=0)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(self.sample_rate)
        wf.writeframes(audio_data.tobytes())
        wf.close()
        print(f"已保存录音到 {filename}")
    
    def get_llm_response(self, query):
        """从Ollama获取回答"""
        try:
            print(f"正在使用Ollama模型 {self.ollama_model} 处理问题...")
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {"role": "system", "content": "你是一个有用的助手，请简洁地回答用户的问题。用户问的问题可能是中文，也可能是英文。但是由于语音识别的缘故，用户的问题可能会有一些错误，比如语音识别错误，请根据错误进行纠正。"},
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
            # 初始化 pyttsx3 引擎
            engine = pyttsx3.init('espeak')
            
            # 设置中文语音
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'chinese' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            # 设置语速
            engine.setProperty('rate', 150)
            
            # 播放语音
            engine.say(text)
            engine.runAndWait()
            
        except Exception as e:
            print(f"语音合成错误: {e}")
    
    def run(self):
        """运行语音助手"""
        print("语音助手已启动")
        
        while True:
            try:
                # 等待唤醒词
                self.is_listening = False
                self.wait_for_wake_word()
                
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
                # if self.enable_voice_response:
                #     self.text_to_speech(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"发生错误: {e}")
                self.is_listening = False
    
    def cleanup(self):
        """清理资源"""
        self.audio.terminate()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\n程序已退出") 