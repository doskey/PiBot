#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from dotenv import load_dotenv
import nls

# 导入自定义模块
from modules.license_manager import LicenseManager
from modules.voice_wakeup import VoiceWakeup, WakeWord
from modules.tts import TextToSpeech
from modules.llm import LLMService
from modules.vision_llm import VisionLLM
from modules.oss import OSSService
from modules.mecanum import MecanumWheels
from modules.camera import Camera


class VoiceAssistant:
    """
    基于阿里云语音服务和阿里云百炼DeepSeek的语音助手
    
    功能:
    - 语音唤醒（通过唤醒词）
    - 语音指令识别
    - LLM回答生成
    - 语音合成回复
    """

    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 初始化各个模块
        print("正在初始化语音助手组件...")
        
        # 初始化License管理器
        self.license_manager = LicenseManager()
        
        # 初始化阿里云AppKey
        self.ali_appkey = os.getenv("ALI_APPKEY", "")
        if not self.ali_appkey or self.ali_appkey == "":
            print("警告：未设置阿里云Appkey，请在.env文件中设置ALI_APPKEY")
            print("获取Appkey请前往控制台：https://nls-portal.console.aliyun.com/applist")
        
        # 初始化语音唤醒模块
        self.voice_wakeup = VoiceWakeup(self.license_manager)
        self.voice_wakeup.set_appkey(self.ali_appkey)
        
        # 初始化语音合成模块
        self.tts = TextToSpeech(self.license_manager)
        self.tts.set_appkey(self.ali_appkey)
        
        # 初始化文本LLM服务
        self.llm_service = LLMService()
        
        # 初始化多模态LLM服务
        self.vision_llm = VisionLLM()
        
        # 初始化OSS服务
        self.oss_service = OSSService()
        
        # 初始化摄像头模块
        self.camera = Camera()
        
        # 初始化麦克纳姆轮模块（在树莓派环境下）
        self.mecanum_wheels = MecanumWheels() if self.camera.is_raspberry_pi else None
        
        # 功能配置
        self.enable_voice_response = True  # 是否启用语音回答
    
    def run(self):
        """运行语音助手"""
        print("语音助手已启动")
        print(f"使用阿里云语音识别，Appkey: {self.ali_appkey}")
        print(f"使用阿里云百炼模型: {self.llm_service.llm_model}")
        
        # 初始欢迎语
        self.tts.text_to_speech("你好，我是机器人。"
                            "我已经准备就绪，请给我指令。"
                            "可以说：你好机器人。然后向我提问。"
                            "也可以说：机器人出发，然后我会开始移动。"
                            "还可以说：机器人这是什么，然后我会拍一张照片，并识别照片中的主要物品。")
        
        while True:
            try:
                # 等待唤醒词
                self.voice_wakeup.reset_listening_state()
                cmd = self.voice_wakeup.wait_for_wake_word()
                
                if not self.voice_wakeup.is_listening or cmd == WakeWord.WAKE_NONE:
                    print("未能检测到唤醒词，重新尝试...")
                    continue
                
                # 根据不同的唤醒词处理不同的功能
                if cmd == WakeWord.WAKE_LLM:
                    self.handle_wake_llm()
                elif cmd == WakeWord.WAKE_TAKEPHOTO:
                    self.handle_wake_takephoto()
                elif cmd == WakeWord.WAKE_MOVE:
                    self.handle_wake_move()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"发生错误: {e}")
                self.voice_wakeup.reset_listening_state()
                
        # 清理资源
        self.cleanup()

    def handle_wake_llm(self):
        """处理LLM对话唤醒"""
        if self.enable_voice_response:
            self.tts.text_to_speech("你好，请提问：")

        # 录制用户命令
        prompt, frames = self.voice_wakeup.record_command()
        if prompt:
            print(f"您说: {prompt}")
            
            # 获取LLM回答
            response = self.llm_service.get_llm_response(
                prompt, 
                system_prompt="你是一个有用的助手，请简洁地回答用户的问题。用户问的问题可能是中文，也可能是英文。"
                              "但是由于语音识别的缘故，用户的问题可能会有语音识别错误，请尽可能的理解问题，并给出回答。")
            print(f"回答: {response}")
            
            # 语音输出回答
            if self.enable_voice_response:
                self.tts.text_to_speech(response)
        else:
            print("未能识别您的问题，请重试")

    def handle_wake_takephoto(self):
        """处理环境识别唤醒"""
        try:
            self.tts.text_to_speech("正在拍摄环境照片")
            
            # 拍照
            temp_image = self.camera.capture_image()
            if not temp_image:
                raise Exception("拍照失败")
            
            # 上传到OSS
            self.tts.text_to_speech("正在上传图片到云端")
            oss_url = self.oss_service.upload_file(temp_image)
            if not oss_url:
                raise Exception("图片上传失败")
            
            # 删除本地临时文件
            os.remove(temp_image)
            print("已清理本地临时文件")

            # 使用OSS URL进行识别
            self.tts.text_to_speech("开始分析图像内容，请稍候")
            
            # 使用回调进行语音播报
            def tts_callback(text):
                self.tts.text_to_speech(text)
                
            # 分析图像
            result = self.vision_llm.analyze_image(oss_url, callback=tts_callback)
            print("\n分析完成")

        except Exception as e:
            print(f"环境识别失败: {e}")
            self.tts.text_to_speech("分析过程出现错误，请重试")

    def handle_wake_move(self):
        """处理移动指令，控制电机"""
        if not self.mecanum_wheels:
            self.tts.text_to_speech("抱歉，移动功能只在树莓派环境下可用")
            return
            
        if self.enable_voice_response:
            self.tts.text_to_speech("好的，如何移动？")

        prompt, frames = self.voice_wakeup.record_command()
        if prompt:
            print(f"您说: {prompt}")
            response = self.llm_service.get_llm_response(
                prompt, 
                system_prompt="你是一个机器人控制助手，请解析用户的指令，给出移动方向。把结果分解为：方向和时间。"
                             "方向必须是：前、后、左转、右转、左、右、左前、右前、左后、右后其中的一个，不要用其他词。"
                             "时间单位为秒，必须是数字。"
                             "格式必须是两行：第一行为方向，第二行为时间（只要数字）。"
                             "例如：\n左\n20")
            print(f"回答: {response}")

            # 解析方向和时间
            response_lines = response.strip().split("\n")
            if len(response_lines) >= 2:
                direction = response_lines[0]
                try:
                    duration = float(response_lines[1])
                except ValueError:
                    self.tts.text_to_speech("无法解析移动时间，请重试")
                    return

                self.tts.text_to_speech(f"向{direction}移动{int(duration)}秒")

                # 根据方向控制移动
                if direction == "前":
                    self.mecanum_wheels.move_forward(duration)
                elif direction == "后":
                    self.mecanum_wheels.move_backward(duration)
                elif direction == "左":
                    self.mecanum_wheels.move_left(duration)
                elif direction == "右":
                    self.mecanum_wheels.move_right(duration)
                elif direction == "左前":
                    self.mecanum_wheels.move_left_forward(duration)
                elif direction == "右前":
                    self.mecanum_wheels.move_right_forward(duration)
                elif direction == "左后":
                    self.mecanum_wheels.move_left_backward(duration)
                elif direction == "右后":
                    self.mecanum_wheels.move_right_backward(duration)    
                elif direction == "左转":
                    self.mecanum_wheels.rotate_left(duration)
                elif direction == "右转":
                    self.mecanum_wheels.rotate_right(duration)
                else:
                    self.tts.text_to_speech("移动方向错误，请重试")
            else:
                self.tts.text_to_speech("无法解析移动指令，请重试")
        else:
            self.tts.text_to_speech("未能识别您的指令，请重试")
    
    def cleanup(self):
        """清理资源"""
        print("正在清理资源...")
        # 清理语音唤醒模块资源
        self.voice_wakeup.cleanup() 