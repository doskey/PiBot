#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

# 导入我们的模块
from modules.audio_recorder import AudioRecorder
from modules.voice_wakeup import VoiceWakeup, WakeWord
from modules.voice_recognition import VoiceRecognition
from modules.license_manager import LicenseManager


def execute_llm_command(voice_recognition):
    """执行LLM对话命令"""
    print("执行LLM对话命令...")
    # 使用语音识别模块进行短句识别
    text, frames = voice_recognition.recognize_speech()
    if text:
        print(f"您说的是: {text}")
        print("这里可以继续处理语音识别结果，例如发送到LLM进行回答")
        # TODO: 添加调用LLM处理文本并返回回答的逻辑
        # TODO: 添加文本转语音播放回答的逻辑
    else:
        print("未能识别您的问题")


def execute_photo_command():
    """执行拍照命令"""
    print("执行拍照命令...")
    # 这里添加拍照相关的逻辑
    # TODO: 添加调用相机拍照的逻辑
    # TODO: 添加图像处理或保存的逻辑
    time.sleep(1)  # 模拟拍照操作耗时
    print("拍照完成")


def execute_move_command():
    """执行移动命令"""
    print("执行移动命令...")
    # 这里添加移动相关的逻辑
    # TODO: 添加控制机器人移动的逻辑
    time.sleep(1)  # 模拟移动操作耗时
    print("移动完成")


def main():
    """主函数，展示模块使用方法"""
    # 初始化License管理器
    license_manager = LicenseManager()
    
    # 创建共享的音频录制器
    audio_recorder = AudioRecorder()
    
    try:
        # 初始化语音唤醒模块
        voice_wakeup = VoiceWakeup(audio_recorder=audio_recorder)
        
        # 初始化语音识别模块
        voice_recognition = VoiceRecognition(license_manager, audio_recorder=audio_recorder)
        
        print("=== 语音唤醒与识别示例 ===")
        print("请尝试说出以下唤醒词:")
        for wake_word in voice_wakeup.wake_words:
            print(f"  - {wake_word['word']}")
        print("按Ctrl+C可随时退出程序")
        
        while True:
            print("\n等待唤醒词...")
            
            # 1. 监听唤醒词（≈阻塞直到被唤醒）
            wake_cmd = voice_wakeup.wait_for_wake_word()
            
            if wake_cmd == WakeWord.WAKE_NONE:
                print("未检测到唤醒词，继续等待...")
                continue
            
            # 2. 被唤醒后执行相应的命令
            print(f"检测到唤醒词，命令类型: {wake_cmd}")
            
            # 3. 执行相应的命令
            if wake_cmd == WakeWord.WAKE_LLM:
                # LLM对话命令
                execute_llm_command(voice_recognition)
            elif wake_cmd == WakeWord.WAKE_TAKEPHOTO:
                # 拍照命令
                execute_photo_command()
            elif wake_cmd == WakeWord.WAKE_MOVE:
                # 移动命令
                execute_move_command()
            
            # 添加短暂延迟，确保系统稳定
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n程序被用户终止")
    finally:
        # 清理资源
        voice_wakeup.cleanup()
        audio_recorder.cleanup()
        print("资源已清理，程序结束")


if __name__ == "__main__":
    main() 