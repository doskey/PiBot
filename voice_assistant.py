#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import wave
import numpy as np
import sounddevice as sd
import whisper
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
        self.wake_word = "小肚小肚"  # 使用语音识别来检测唤醒词
        self.silence_threshold = 2.0  # 句子结束后的静默时间阈值（秒）
        self.enable_voice_response = True  # 是否启用语音回答
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama2")  # 使用环境变量或默认值
        
        # 初始化Whisper模型
        print("正在加载Whisper模型，这可能需要一些时间...")
        # 模型大小选项: tiny, base, small, medium, large
        self.whisper_model = whisper.load_model("base")
        print("成功加载Whisper模型")
        
    def transcribe_audio(self, audio_data):
        """使用Whisper转录音频"""
        # 保存音频到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_filename = temp_file.name
        
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(self.sample_rate)
        wf.writeframes(audio_data.tobytes())
        wf.close()
        
        # 使用Whisper转录
        try:
            result = self.whisper_model.transcribe(temp_filename, language="zh")
            os.unlink(temp_filename)  # 删除临时文件
            return result["text"]
        except Exception as e:
            print(f"转录错误: {e}")
            os.unlink(temp_filename)  # 确保删除临时文件
            return ""
    
    def listen_for_wake_word(self):
        """监听唤醒词"""
        print("正在监听唤醒词...")
        print(f"唤醒词为: '{self.wake_word}', 请对着麦克风说这个词")
        
        wake_word_detected = False
        max_wait_time = 60  # 最多等待60秒
        start_time = time.time()
        audio_buffer = []
        
        def audio_callback(indata, frames, time, status):
            nonlocal audio_buffer
            if status:
                print(f"音频状态: {status}")
            
            # 检查声音音量
            rms = np.sqrt(np.mean(indata**2))
            if rms > 0.01:  # 如果有声音输入
                print(f"检测到声音输入，音量: {rms:.4f}")
                audio_buffer.append(indata.copy())
        
        # 持续监听5秒钟，然后处理
        try:
            while not wake_word_detected and time.time() - start_time < max_wait_time:
                audio_buffer = []  # 清空缓冲区
                
                # 录制5秒音频
                with sd.InputStream(
                    callback=audio_callback,
                    channels=1,
                    samplerate=self.sample_rate,
                    blocksize=4000
                ):
                    # 录制大约5秒
                    sd.sleep(5000)
                
                # 如果有足够的音频数据，进行转录
                if len(audio_buffer) > 0:
                    audio_data = np.concatenate(audio_buffer)
                    
                    # 转录音频
                    transcription = self.transcribe_audio(audio_data)
                    print(f"识别到: '{transcription}'")
                    
                    # 检查是否包含唤醒词
                    if self.wake_word in transcription:
                        print(f"匹配到唤醒词: '{self.wake_word}'")
                        wake_word_detected = True
                        break
            
            if wake_word_detected:
                print("检测到唤醒词!")
                return True
            else:
                print("等待唤醒词超时，请重新运行程序")
                return False
                
        except Exception as e:
            print(f"监听唤醒词时发生错误: {e}")
            return False
    
    def record_command(self):
        """录制用户命令"""
        print("请说出您的问题...")
        
        audio_buffer = []
        recording_duration = 10  # 录制最长10秒
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(status)
            audio_buffer.append(indata.copy())
            
            # 打印音量，方便调试
            rms = np.sqrt(np.mean(indata**2))
            if rms > 0.01:
                print(f"录音中，音量: {rms:.4f}")
        
        # 录制用户命令
        with sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=4000
        ):
            print("开始录音，请说话...")
            # 等待用户说话并录制
            sd.sleep(int(recording_duration * 1000))
        
        print("录音完成，正在处理...")
        
        if len(audio_buffer) > 0:
            audio_data = np.concatenate(audio_buffer)
            # 转录音频
            transcription = self.transcribe_audio(audio_data)
            return transcription, audio_buffer
        else:
            return "", []
    
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
                if not self.listen_for_wake_word():
                    continue  # 如果没有检测到唤醒词，重新开始循环
                
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

if __name__ == "__main__":
    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\n程序已退出") 