#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PiBot 智能语音助手入口程序
"""

import sys
import os
import argparse
import logging
import nls
from voice_assistant import VoiceAssistant

def setup_logging(verbose=False):
    """
    设置日志级别
    
    Args:
        verbose: 是否启用详细日志
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def parse_args():
    """
    解析命令行参数
    
    Returns:
        解析后的参数
    """
    parser = argparse.ArgumentParser(description='PiBot 智能语音助手')
    parser.add_argument('-v', '--verbose', action='store_true', help='启用详细日志输出')
    parser.add_argument('--no-voice', action='store_true', help='禁用语音响应')
    parser.add_argument('--debug-asr', action='store_true', help='启用语音识别调试')
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 设置日志级别
    setup_logging(args.verbose)
    
    # 控制是否启用阿里云NLS SDK的调试日志
    nls.enableTrace(args.debug_asr)
    
    try:
        # 创建语音助手实例
        assistant = VoiceAssistant()
        
        # 根据命令行参数配置语音助手
        if args.no_voice:
            assistant.enable_voice_response = False
            print("已禁用语音响应，将仅使用文本交互")
        
        # 运行语音助手
        print("PiBot 智能语音助手启动中...")
        assistant.run()
        
    except KeyboardInterrupt:
        print("\n程序已被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        return 1
    finally:
        # 清理资源
        if 'assistant' in locals():
            assistant.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 