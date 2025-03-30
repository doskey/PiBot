#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import wave
from dotenv import load_dotenv
import nls
from modules.speech_recognition import SpeechRecognition
from modules.llm import LLMModule
from modules.text_to_speech import TextToSpeech
from modules.logger import logger


class VoiceAssistant:
    """
    集成语音识别、LLM和语音合成模块的语音助手
    
    功能:
    - 语音唤醒（通过唤醒词）
    - 语音指令识别
    - LLM回答生成
    - 语音合成回复
    """

    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 获取主模块日志器
        self.log = logger.get_logger("voice_assistant")
        
        # 功能配置
        self.enable_voice_response = True  # 是否启用语音回答
        self.wake_word = os.getenv("WAKE_WORD", "你好机器人")  # 唤醒词
        
        # 初始化各个模块
        self.speech_recognition = SpeechRecognition(wake_word=self.wake_word, callback=self.on_wake_word)
        self.llm = LLMModule()
        self.tts = TextToSpeech()
        
        # 状态变量
        self.is_listening = False
        
        self.log.info("语音助手初始化完成")
    
    def on_wake_word(self):
        """唤醒词被检测到时的回调函数"""
        self.is_listening = True
        self.log.info("唤醒成功，准备处理指令...")
        
        # 在检测到唤醒词后播放提示音
        try:
            self.tts.text_to_speech("我在，您请提问：")
        except Exception as e:
            self.log.error(f"语音播放失败，但唤醒成功: {e}")
    
    def save_audio(self, frames, filename="recorded_command.wav"):
        """保存录制的音频（可选功能）"""
        if not frames:
            return
        
        # 合并所有帧
        audio_data = b''.join(frames)
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(16000)
        wf.writeframes(audio_data)
        wf.close()
        self.log.info(f"已保存录音到 {filename}")
    
    def run(self):
        """运行语音助手"""
        self.log.info("语音助手已启动")
        self.log.info(f"使用阿里云语音识别")
        self.log.info(f"使用阿里云百炼DeepSeek模型: {self.llm.llm_model}")
        self.log.info(f"唤醒词: {self.wake_word}")
        
        # 检查麦克风是否正常工作
        self.speech_recognition._check_microphone()
        
        while True:
            try:
                # 等待唤醒词
                self.is_listening = False
                self.speech_recognition.wait_for_wake_word()
                
                if not self.is_listening:
                    self.log.warning("未能检测到唤醒词，重新尝试...")
                    continue
                
                # 录制用户命令
                query, frames = self.speech_recognition.record_command()
                if not query:
                    self.log.warning("未能识别您的问题，请重试")
                    continue
                
                self.log.info(f"用户输入: {query}")
                
                # 获取LLM回答
                response = self.llm.get_response(query)
                self.log.info(f"回答: {response}")
                
                # 语音输出回答
                if self.enable_voice_response:
                    self.tts.text_to_speech(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log.error(f"发生错误: {e}")
                self.is_listening = False
    
    def cleanup(self):
        """清理资源"""
        self.speech_recognition.cleanup()
        self.log.info("资源已清理完毕")


def main():
    """主函数"""
    # 初始化日志系统
    log = logger.get_logger("main")
    
    # 关闭nls的日志跟踪
    nls.enableTrace(False)
    
    # 正常模式
    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        log.info("\n程序已退出") 
    finally:
        assistant.cleanup()


if __name__ == "__main__":
    main()
