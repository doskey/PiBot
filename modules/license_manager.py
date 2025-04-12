#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest


class LicenseManager:
    """
    阿里云License管理模块，负责获取和管理阿里云Token
    """
    
    def __init__(self):
        """初始化License管理器"""
        self.ali_token = os.getenv("ALI_TOKEN", "")
        self.ali_ak_id = os.getenv("ALIYUN_AK_ID", "")
        self.ali_ak_secret = os.getenv("ALIYUN_AK_SECRET", "")
        self.token_expire_time = 0
        
        # 如果没有设置token但设置了AK，自动获取token
        if (not self.ali_token or self.ali_token == "") and self.ali_ak_id and self.ali_ak_secret:
            print("正在获取阿里云Token...")
            self.get_ali_token()
        elif not self.ali_token or self.ali_token == "":
            print("警告：未设置阿里云Token或AccessKey，请在.env文件中设置ALI_TOKEN或ALIYUN_AK_ID和ALIYUN_AK_SECRET")
    
    def get_ali_token(self):
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
                print(f"成功获取阿里云Token，将在 {self.token_expire_time} 过期")
                return True
            else:
                print("获取阿里云Token失败：无法解析响应")
                return False
        except Exception as e:
            print(f"获取阿里云Token错误: {e}")
            return False
    
    def check_token(self):
        """检查Token是否过期，如果过期则重新获取"""
        current_time = int(time.time())
        
        # 检查token是否即将过期（提前10分钟刷新）
        if self.token_expire_time - current_time < 600:
            print("Token即将过期，正在刷新...")
            self.get_ali_token()
        
    def get_token(self):
        """获取当前的Token"""
        self.check_token()  # 检查并确保Token有效
        return self.ali_token 