#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from openai import OpenAI


class LLMService:
    """
    文本LLM服务模块，负责文本LLM的提问和响应
    """
    
    def __init__(self):
        """初始化LLM服务"""
        # 获取API密钥和模型名称
        self.llm_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.llm_model = os.getenv("ALIYUN_LLM_MODEL", "deepseek-v3")
        
        # 检查阿里云百炼API配置
        if not self.llm_api_key or self.llm_api_key == "":
            print("警告：未设置阿里云百炼API密钥，请在.env文件中设置DASHSCOPE_API_KEY")
            
        # 初始化OpenAI客户端
        self.openai_client = OpenAI(
            api_key=self.llm_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    
    def get_llm_response(self, prompt, system_prompt=None):
        """
        从阿里云百炼DeepSeek获取回答
        
        Args:
            prompt: 用户问题
            system_prompt: 系统提示
            
        Returns:
            str: 模型回答
        """
        try:
            print(f"正在使用阿里云百炼模型 {self.llm_model} 处理问题...")
            
            # 创建消息列表
            messages = []
            
            # 添加系统提示
            if system_prompt:
                messages.append({
                    "role": "system", 
                    "content": system_prompt
                })
            
            # 添加用户问题
            messages.append({"role": "user", "content": prompt})
            
            # 调用模型API
            completion = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=0.6,
                max_tokens=4096
            )
            
            # 提取模型回答
            answer = completion.choices[0].message.content
            
            # 如果有推理过程，打印出来（仅供调试）
            if hasattr(completion.choices[0].message, 'reasoning_content') and completion.choices[0].message.reasoning_content:
                print(f"模型推理过程: {completion.choices[0].message.reasoning_content}")
            
            return answer
                
        except Exception as e:
            print(f"LLM响应错误: {e}")
            return "抱歉，我无法处理您的请求。" 