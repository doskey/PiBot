#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from openai import OpenAI


class VisionLLM:
    """
    多模态LLM服务，负责图像分析和响应
    """
    
    def __init__(self):
        """初始化多模态LLM服务"""
        # 获取API密钥
        self.llm_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.vision_model = os.getenv("ALIYUN_VISION_MODEL", "qwen2.5-vl-32b-instruct")
        
        # 检查阿里云百炼API配置
        if not self.llm_api_key or self.llm_api_key == "":
            print("警告：未设置阿里云百炼API密钥，请在.env文件中设置DASHSCOPE_API_KEY")
            
        # 初始化OpenAI客户端
        self.openai_client = OpenAI(
            api_key=self.llm_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    
    def analyze_image(self, image_url, prompt=None, callback=None):
        """
        分析图像内容
        
        Args:
            image_url: 图像URL地址
            prompt: 提示文本，默认为识别主要物体
            callback: 用于处理流式响应的回调函数
            
        Returns:
            str: 分析结果
        """
        try:
            # 如果未提供提示，使用默认提示
            if not prompt:
                prompt = "请告诉我这张图片的最主要的物品是什么，只说名字，不要其它任何额外说明"
            
            # 创建聊天请求
            completion = self.openai_client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": [{
                            "type": "text", 
                            "text": "图像识别工具，只能识别图片主体内容，不会识别其它不重要的内容。"
                        }],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "high"  # 高详细度
                                }
                            },
                            {
                                "type": "text", 
                                "text": prompt
                            }
                        ],
                    }
                ],
                stream=True,
                temperature=0.3,  # 更低的随机性保证描述准确性
                max_tokens=4096
            )

            # 初始化变量
            reasoning_content = ""
            answer_content = ""
            is_answering = False
            response_buffer = ""  # 用于累积语音合成的文本
            
            print("\n" + "="*20 + "思考过程" + "="*20)
            for chunk in completion:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                
                # 实时打印思考内容
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    print(delta.reasoning_content, end='', flush=True)
                    reasoning_content += delta.reasoning_content
                    
                    # 累积到一定长度再处理
                    response_buffer += delta.reasoning_content
                    if len(response_buffer) > 30 and callback:
                        callback(response_buffer)
                        response_buffer = ""
                
                # 处理最终回答
                if delta.content:
                    if not is_answering:
                        print("\n" + "="*20 + "最终回答" + "="*20)
                        is_answering = True
                        if response_buffer and callback:
                            callback(response_buffer)
                            response_buffer = ""
                    
                    print(delta.content, end='', flush=True)
                    answer_content += delta.content
                    response_buffer += delta.content

            # 处理剩余内容
            if response_buffer and callback:
                callback(response_buffer)

            print("\n分析完成")
            
            # 返回分析结果
            return answer_content
            
        except Exception as e:
            print(f"图像分析错误: {e}")
            return "抱歉，图像分析过程出现错误。" 