#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vosk语音唤醒测试程序
用于测试使用Vosk进行本地唤醒词识别的功能
"""

import os
import sys
import time
from dotenv import load_dotenv

# 导入自定义模块
from modules.license_manager import LicenseManager
from modules.voice_wakeup import VoiceWakeup, WakeWord

def main():
    """主测试函数"""
    # 加载环境变量
    load_dotenv()
    
    print("=== Vosk语音唤醒测试程序 ===")
    print("这个测试程序会使用Vosk在本地识别唤醒词")
    print("支持的唤醒词: '你好机器人', '机器人这是什么', '机器人出发'")
    print("按Ctrl+C退出程序")
    
    # 检查models目录是否存在Vosk模型
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "vosk-model-small-cn-0.22")
    if not os.path.exists(model_dir):
        print(f"\n错误: 没有找到Vosk模型，请先下载并解压模型到 {model_dir}")
        print("您可以从以下链接下载模型: https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip")
        print("然后解压到models/vosk-model-small-cn-0.22目录")
        return 1
    
    try:
        # 初始化License管理器
        license_manager = LicenseManager()
        
        # 初始化语音唤醒模块
        print("\n初始化Vosk语音唤醒模块...")
        voice_wakeup = VoiceWakeup(license_manager)
        
        # 设置阿里云AppKey（虽然Vosk不使用，但模块初始化需要）
        ali_appkey = os.getenv("ALI_APPKEY", "")
        voice_wakeup.set_appkey(ali_appkey)
        
        # 循环等待唤醒词
        while True:
            print("\n=== 开始新一轮唤醒测试 ===")
            
            # 重置监听状态
            voice_wakeup.reset_listening_state()
            
            # 等待唤醒词
            cmd = voice_wakeup.wait_for_wake_word()
            
            # 处理唤醒结果
            if voice_wakeup.is_listening:
                wake_cmd = "未知"
                if cmd == WakeWord.WAKE_LLM:
                    wake_cmd = "与LLM对话"
                elif cmd == WakeWord.WAKE_TAKEPHOTO:
                    wake_cmd = "拍照分析"
                elif cmd == WakeWord.WAKE_MOVE:
                    wake_cmd = "机器人移动"
                
                print(f"\n=== 成功唤醒! 指令: {wake_cmd} ===")
                
                # 模拟命令录制
                print("请说出您的指令...")
                text, _ = voice_wakeup.record_command()
                print(f"您说: {text}")
                print("命令处理完成")
                
                # 暂停一下，准备下一轮唤醒
                time.sleep(1)
            else:
                print("未能成功唤醒，请再试一次")
    
    except KeyboardInterrupt:
        print("\n程序已被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        return 1
    finally:
        # 清理资源
        voice_wakeup.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 