#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import struct
import wave
import pyaudio
import pvporcupine
from vosk import Model, KaldiRecognizer
import ollama
from dotenv import load_dotenv
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import tempfile

# 加载环境变量
load_dotenv()

class VoiceAssistant:
    def __init__(self):
        # 配置参数
        self.sample_rate = 16000
        self.frame_length = 512
        self.wake_word = "picovoice"  # 默认唤醒词，您可以根据porcupine支持的唤醒词修改
        self.silence_threshold = 2.0  # 句子结束后的静默时间阈值（秒）
        self.enable_voice_response = True  # 是否启用语音回答
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")  # 使用环境变量或默认值
        
        # 初始化Ollama客户端（不需要额外初始化，直接使用ollama库即可）
        
        # 初始化麦克风和音频处理
        self.audio = pyaudio.PyAudio()
        
        # 初始化Vosk语音识别模型
        model_path = os.getenv("VOSK_MODEL_PATH", "model")
        if not os.path.exists(model_path):
            print(f"请下载Vosk模型并放置在 {model_path} 目录")
            print("您可以从 https://alphacephei.com/vosk/models 下载中文模型")
            exit(1)
        
        try:
            self.model = Model(model_path)
            print("成功加载Vosk模型")
        except Exception as e:
            print(f"加载Vosk模型失败: {e}")
            exit(1)
        
        # 初始化唤醒词检测器
        access_key = os.getenv("PICOVOICE_ACCESS_KEY", "")
        try:
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=[self.wake_word]
            )
        except Exception as e:
            print(f"初始化唤醒词检测器失败: {e}")
            print("请确保您有有效的Picovoice访问密钥")
            exit(1)
    
    def listen_for_wake_word(self):
        """监听唤醒词"""
        print("正在监听唤醒词...")
        
        stream = self.audio.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )
        
        try:
            while True:
                pcm = stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                result = self.porcupine.process(pcm)
                if result >= 0:
                    print("检测到唤醒词!")
                    break
        finally:
            stream.close()
    
    def record_command(self):
        """录制用户命令直到句子结束"""
        print("请说出您的问题...")
        
        rec = KaldiRecognizer(self.model, self.sample_rate)
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=4000
        )
        
        frames = []
        silence_frames = 0
        speaking_started = False
        last_text = ""
        result_text = ""
        
        try:
            while True:
                data = stream.read(4000)
                frames.append(data)
                
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if result.get("text", ""):
                        speaking_started = True
                        silence_frames = 0
                        result_text = result["text"]
                        print(f"识别中: {result_text}")
                
                # 检测静默以结束录音
                if speaking_started:
                    # 简单的静默检测 - 可以改进为基于音量的检测
                    partial = json.loads(rec.PartialResult())
                    if partial.get("partial") == last_text:
                        silence_frames += 1
                    else:
                        last_text = partial.get("partial", "")
                        silence_frames = 0
                    
                    # 如果连续多帧没有新内容，认为句子结束
                    if silence_frames > int(self.silence_threshold * self.sample_rate / 4000):
                        print("检测到句子结束")
                        break
        
        finally:
            stream.close()
            
        # 最后再处理一次剩余音频
        rec.FinalResult()
        
        print("录音完成，正在处理...")
        return result_text, frames
    
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
        print("语音助手已启动，等待唤醒...")
        
        while True:
            try:
                # 等待唤醒词
                self.listen_for_wake_word()
                
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
        self.porcupine.delete()
        self.audio.terminate()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    try:
        assistant.run()
    finally:
        assistant.cleanup() 