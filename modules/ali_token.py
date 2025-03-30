#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from dotenv import load_dotenv
from modules.logger import logger

class AliTokenManager:
    """
    阿里云Token管理模块
    
    用于管理阿里云语音服务所需的Token，支持自动获取和刷新
    """
    
    _instance = None
    
    def __new__(cls):
        # 单例模式实现
        if cls._instance is None:
            cls._instance = super(AliTokenManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        # 避免重复初始化
        if self.initialized:
            return
            
        # 加载环境变量
        load_dotenv()
        
        # 获取模块专用日志器
        self.log = logger.get_logger("ali_token")
        
        # 配置参数
        self.ali_url = os.getenv("ALI_URL", "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1")
        self.ali_token = os.getenv("ALI_TOKEN", "")
        self.ali_appkey = os.getenv("ALI_APPKEY", "")
        self.ali_ak_id = os.getenv("ALIYUN_AK_ID", "")
        self.ali_ak_secret = os.getenv("ALIYUN_AK_SECRET", "")
        self.token_expire_time = 0
        
        # 如果没有设置token但设置了AK，自动获取token
        if (not self.ali_token or self.ali_token == "") and self.ali_ak_id and self.ali_ak_secret:
            self.log.info("正在获取阿里云Token...")
            self.get_token()
        elif not self.ali_token or self.ali_token == "":
            self.log.warning("未设置阿里云Token或AccessKey，请在.env文件中设置ALI_TOKEN或ALIYUN_AK_ID和ALIYUN_AK_SECRET")
        
        if not self.ali_appkey or self.ali_appkey == "":
            self.log.warning("未设置阿里云Appkey，请在.env文件中设置ALI_APPKEY")
            self.log.info("获取Appkey请前往控制台：https://nls-portal.console.aliyun.com/applist")
            
        self.initialized = True
    
    def get_token(self):
        """获取阿里云Token"""
        try:
            # 创建AcsClient实例
            client = AcsClient(self.ali_ak_id, self.ali_ak_secret, "cn-shanghai")

            # 创建request，并设置参数
            request = CommonRequest()
            request.set_method('POST')
            request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
            request.set_version('2019-02-28')
            request.set_action_name('CreateToken')

            response = client.do_action_with_exception(request)
            response_json = json.loads(response)
            
            if 'Token' in response_json and 'Id' in response_json['Token']:
                self.ali_token = response_json['Token']['Id']
                self.token_expire_time = response_json['Token']['ExpireTime']
                self.log.info(f"成功获取阿里云Token，将在 {self.token_expire_time} 过期")
                return True
            else:
                self.log.error("获取阿里云Token失败：无法解析响应")
                return False
        except Exception as e:
            self.log.error(f"获取阿里云Token错误: {e}")
            return False
    
    def check_token(self):
        """检查Token是否过期，如果过期则重新获取"""
        current_time = int(time.time())
        
        # 检查token是否即将过期（提前10分钟刷新）
        if self.token_expire_time - current_time < 600:
            self.log.info("Token即将过期，正在刷新...")
            self.get_token()
    
    def get_token_info(self):
        """获取当前Token信息"""
        self.check_token()  # 确保Token有效
        
        return {
            "url": self.ali_url,
            "token": self.ali_token,
            "appkey": self.ali_appkey,
            "expire_time": self.token_expire_time
        }
    
    def get_url(self):
        """获取阿里云服务URL"""
        return self.ali_url
    
    def get_token_str(self):
        """获取Token字符串"""
        self.check_token()  # 确保Token有效
        return self.ali_token
    
    def get_appkey(self):
        """获取AppKey"""
        return self.ali_appkey

# 创建全局单例实例
token_manager = AliTokenManager() 