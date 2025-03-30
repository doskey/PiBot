#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import numpy as np
import pyaudio
import nls  # 阿里云语音识别SDK
from dotenv import load_dotenv
from modules.ali_token import token_manager
from modules.logger import logger

class SpeechRecognition:
    """
    阿里云语音识别模块
    
    功能:
    - 语音唤醒（通过唤醒词）
    - 语音指令识别
    """

    def __init__(self, wake_word=None, callback=None):
        # 加载环境变量
        load_dotenv()
        
        # 获取模块专用日志器
        self.log = logger.get_logger("speech_recognition")
        
        # 音频参数配置
        self.sample_rate = 16000
        self.silence_threshold = 1.0  # 从2.0秒降低到1.0秒，更快检测到句子结束
        self.silence_level = 300  # 静默音量阈值，低于此值被视为静默
        self.speaking_level = 800  # 说话音量阈值，高于此值被视为说话
        
        # 功能配置
        self.wake_word = wake_word or os.getenv("WAKE_WORD", "你好机器人")  # 唤醒词
        self.is_listening = False  # 是否处于主动监听状态
        self.callback = callback  # 唤醒后的回调函数
        
        # 初始化麦克风和音频处理
        self.audio = pyaudio.PyAudio()
        
        # 用于阿里云识别结果的变量
        self.recognition_result = ""
        self.recognition_completed = False
        
        self.log.info(f"语音识别模块初始化完成，唤醒词：{self.wake_word}")
    
    # ===== 语音识别回调函数 =====
    
    def on_recognition_start(self, message, *args):
        """当一句话识别就绪时的回调函数"""
        self.log.debug("识别开始")
        self.recognition_result = ""
        self.recognition_completed = False
    
    def on_recognition_result_changed(self, message, *args):
        """当一句话识别返回中间结果时的回调函数"""
        result = json.loads(message)
        
        # 正确提取result字段
        recognition_text = ""
        if "payload" in result and "result" in result["payload"]:
            recognition_text = result["payload"]["result"]
        elif "result" in result:
            recognition_text = result["result"]
        else:
            return
            
        self.recognition_result = recognition_text
        self.log.debug(f"中间结果: {recognition_text}")
            
        # 在回调中检查唤醒词，提高响应速度
        if not self.is_listening and self.wake_word.lower() in recognition_text.lower():
            self.log.info(f"[精确匹配成功] 检测到唤醒词: {self.wake_word}")
            self.handle_wake_word("中间结果回调")
    
    def on_recognition_completed(self, message, *args):
        """当一句话识别返回最终识别结果时的回调函数"""
        result = json.loads(message)
        
        # 正确提取result字段
        recognition_text = ""
        if "payload" in result and "result" in result["payload"]:
            recognition_text = result["payload"]["result"]
        elif "result" in result:
            recognition_text = result["result"] 
        else:
            self.log.warning("无法解析完成结果")
            recognition_text = ""
            
        self.recognition_result = recognition_text
        self.log.info(f"识别完成: {recognition_text}")
            
        # 在完成回调中也检查唤醒词
        if not self.is_listening and self.wake_word.lower() in recognition_text.lower():
            self.log.info(f"[完成回调-精确匹配] 检测到唤醒词: {self.wake_word}")
            self.handle_wake_word("完成回调")
                
        self.recognition_completed = True
    
    def on_recognition_error(self, message, *args):
        """当SDK或云端出现错误时的回调函数"""
        self.log.error(f"识别错误: {message}")
        self.recognition_completed = True
    
    def on_recognition_close(self, *args):
        """当和云端连接断开时的回调函数"""
        self.log.debug("识别连接关闭")
    
    # ===== 唤醒词处理 =====
    
    def handle_wake_word(self, detected_from="未知位置"):
        """统一处理唤醒词被检测到的情况"""
        if not self.is_listening:  # 防止重复唤醒
            self.is_listening = True
            self.log.info(f"唤醒成功! [{detected_from}] 即将开始聆听指令...")
            
            # 如果设置了回调函数，调用它
            if self.callback:
                self.callback()
                
            return True
        return False
    
    # ===== 核心功能 =====
    
    def wait_for_wake_word(self):
        """使用阿里云一句话识别监听唤醒词"""
        self.log.info("\n正在等待唤醒词...")
        self.log.info(f"当您说'{self.wake_word}'时，我会开始聆听您的指令")
        self.log.info("(也可以说'机器人'或类似的词语来唤醒)")
        
        # 检查token是否有效
        token_manager.check_token()
        
        # 创建阿里云识别器
        recognizer = self._create_recognizer()
        
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=2048
        )
        
        try:
            # 开始识别
            recognizer.start(
                aformat="pcm",
                sample_rate=self.sample_rate,
                enable_intermediate_result=True,
                enable_punctuation_prediction=True
            )
            
            self.recognition_completed = False
            recognition_restart_count = 0
            max_recognition_restarts = 50  # 最多重启50次，防止无限循环
            
            while not self.is_listening and recognition_restart_count < max_recognition_restarts:
                try:
                    data = stream.read(2048)
                    # 发送音频数据给阿里云识别器
                    recognizer.send_audio(data)
                    
                    # 检查是否包含唤醒词
                    if not self.is_listening and self.wake_word.lower() in self.recognition_result.lower():
                        self.log.info(f"[主循环-精确匹配] 检测到唤醒词: {self.wake_word}")
                        self.handle_wake_word("主循环检测")
                        break
                    
                    # 如果一段语音识别完成，清空结果并重新开始
                    if self.recognition_completed:
                        self.log.debug(f"一段识别完成，结果: {self.recognition_result}")
                        
                        # 再次检查唤醒词，防止漏掉
                        if not self.is_listening and self.wake_word.lower() in self.recognition_result.lower():
                            self.log.info(f"[重启前-精确匹配] 检测到唤醒词: {self.wake_word}")
                            self.handle_wake_word("重启前检测")
                            break
                        
                        # 重新开始识别
                        recognizer.stop()
                        recognizer = self._create_recognizer()
                        recognizer.start(
                            aformat="pcm",
                            sample_rate=self.sample_rate,
                            enable_intermediate_result=True,
                            enable_punctuation_prediction=True
                        )
                        self.recognition_result = ""
                        self.recognition_completed = False
                        recognition_restart_count += 1
                        self.log.debug(f"重新开始识别 (第{recognition_restart_count}次)")
                except Exception as e:
                    self.log.error(f"读取麦克风数据时出错: {e}")
                    time.sleep(0.1)
            
            if recognition_restart_count >= max_recognition_restarts:
                self.log.warning("达到最大重启次数，请检查麦克风和网络连接")
        
        finally:
            try:
                recognizer.stop()
            except:
                pass
            stream.close()
    
    def _create_recognizer(self):
        """创建并返回阿里云识别器实例"""
        return nls.NlsSpeechRecognizer(
            url=token_manager.get_url(),
            token=token_manager.get_token_str(),
            appkey=token_manager.get_appkey(),
            on_start=self.on_recognition_start,
            on_result_changed=self.on_recognition_result_changed,
            on_completed=self.on_recognition_completed,
            on_error=self.on_recognition_error,
            on_close=self.on_recognition_close
        )
    
    def record_command(self):
        """使用阿里云一句话识别录制用户命令"""
        self.log.info("请说出您的问题...")
        
        # 检查token是否有效
        token_manager.check_token()
        
        # 创建阿里云识别器
        recognizer = self._create_recognizer()
        
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
        no_speech_timeout = int(5 * self.sample_rate / 1024)  # 5秒无语音则超时
        no_speech_counter = 0
        
        try:
            # 开始识别
            recognizer.start(
                aformat="pcm",
                sample_rate=self.sample_rate,
                enable_intermediate_result=True,
                enable_punctuation_prediction=True,
                enable_inverse_text_normalization=True  # 启用数字转换功能
            )
            
            self.recognition_completed = False
            self.recognition_result = ""
            last_result_length = 0
            no_new_result_counter = 0
            
            while True:
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
                
                # 计算当前音频帧的音量级别
                audio_data = np.frombuffer(data, dtype=np.int16)
                current_level = np.abs(audio_data).mean()
                
                # 检测是否开始说话
                if current_level > self.speaking_level:  # 音量高于阈值，认为开始说话
                    speaking_started = True
                    silence_frames = 0
                    no_speech_counter = 0
                elif speaking_started:
                    # 如果音量低于阈值，增加静默帧计数
                    if current_level < self.silence_level:
                        silence_frames += 1
                    else:
                        silence_frames = max(0, silence_frames - 1)  # 如果又检测到声音，减少静默计数
                else:
                    # 如果还没开始说话，检查超时
                    no_speech_counter += 1
                    if no_speech_counter >= no_speech_timeout:
                        self.log.warning("等待说话超时")
                        if self.recognition_result:  # 如果有识别结果，也返回
                            recognizer.stop()
                            break
                        recognizer.stop()
                        return "", []
                
                # 发送音频数据给阿里云识别器
                recognizer.send_audio(data)
                
                # 检查识别结果是否有更新
                if len(self.recognition_result) > last_result_length:
                    last_result_length = len(self.recognition_result)
                    no_new_result_counter = 0
                else:
                    no_new_result_counter += 1
                
                # 满足以下任一条件则结束录制：
                # 1. 连续静默帧超过阈值
                # 2. 阿里云识别完成
                # 3. 识别结果长时间没有更新且已经有内容
                silence_threshold_frames = int(self.silence_threshold * self.sample_rate / 1024)
                no_update_threshold = int(2 * self.sample_rate / 1024)
                
                if (speaking_started and silence_frames > silence_threshold_frames) or \
                   self.recognition_completed or \
                   (speaking_started and no_new_result_counter > no_update_threshold and self.recognition_result):
                    self.log.debug("检测到句子结束")
                    recognizer.stop()
                    break
        
        except Exception as e:
            self.log.error(f"录制命令时出错: {e}")
            try:
                recognizer.stop()
            except:
                pass
            return "", []
        
        finally:
            # 确保关闭流
            stream.close()
        
        # 等待识别完成
        timeout = 0
        while not self.recognition_completed and timeout < 20:
            time.sleep(0.1)
            timeout += 1
        
        result_text = self.recognition_result
        self.log.info(f"阿里云识别结果: {result_text}")
        
        return result_text, frames
    
    def _check_microphone(self):
        """检查麦克风是否正常工作"""
        self.log.info("检查麦克风...")
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            data = stream.read(1024)
            if data:
                self.log.info("麦克风正常工作")
            stream.close()
        except Exception as e:
            self.log.error(f"麦克风可能有问题: {e}")
    
    def cleanup(self):
        """清理资源"""
        self.audio.terminate()
        self.log.debug("语音识别资源已释放")

    def set_callback(self, callback):
        """设置唤醒后的回调函数"""
        self.callback = callback
        
    def set_wake_word(self, wake_word):
        """设置唤醒词"""
        self.wake_word = wake_word
        self.log.info(f"唤醒词已设置为: {self.wake_word}")
