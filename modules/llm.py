#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from openai import OpenAI
from modules.logger import logger

class LLMModule:
    """
    LLM模块，负责与大语言模型交互
    
    支持:
    - 阿里云百炼DeepSeek模型
    - 可扩展添加其他兼容OpenAI API的模型
    """
    
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 获取模块专用日志器
        self.log = logger.get_logger("llm")
        
        # LLM配置
        self.llm_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.llm_model = os.getenv("ALIYUN_LLM_MODEL", "deepseek-v3")
        
        # 检查API配置
        if not self.llm_api_key or self.llm_api_key == "":
            self.log.warning("未设置阿里云百炼API密钥，请在.env文件中设置DASHSCOPE_API_KEY")
        
        # 初始化OpenAI客户端
        self.openai_client = OpenAI(
            api_key=self.llm_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        self.log.info(f"LLM模块初始化完成，使用模型: {self.llm_model}")
    
    def get_response(self, query, system_prompt=None):
        """从阿里云百炼DeepSeek获取回答"""
        try:
            self.log.info(f"正在使用阿里云百炼模型 {self.llm_model} 处理问题...")
            
            # 设置默认系统提示词
            if system_prompt is None:
                system_prompt = "你是一个有用的助手，请简洁地回答用户的问题。用户问的问题可能是中文，也可能是英文。"\
                              "但是由于语音识别的缘故，用户的问题可能会有语音识别错误，请尽可能的理解问题，并给出回答。"
            
            completion = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.6,
                max_tokens=4096
            )
            
            # 提取模型回答
            answer = completion.choices[0].message.content
            
            # 如果有推理过程，记录日志（仅供调试）
            if hasattr(completion.choices[0].message, 'reasoning_content') and completion.choices[0].message.reasoning_content:
                self.log.debug(f"模型推理过程: {completion.choices[0].message.reasoning_content}")
            
            return answer
                
        except Exception as e:
            self.log.error(f"LLM响应错误: {e}")
            return "抱歉，我无法处理您的请求。"
    
    def set_model(self, model_name):
        """设置使用的模型"""
        self.llm_model = model_name
        self.log.info(f"已设置为使用模型: {self.llm_model}")
    
    def set_api_key(self, api_key):
        """设置API密钥"""
        self.llm_api_key = api_key
        
        # 更新客户端
        self.openai_client = OpenAI(
            api_key=self.llm_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.log.info("已更新API密钥")
