#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
import datetime
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider


class OSSService:
    """
    阿里云OSS服务封装模块
    """
    
    def __init__(self):
        """初始化OSS服务"""
        # 获取OSS配置
        self.oss_endpoint = os.getenv("OSS_ENDPOINT", "https://oss-cn-beijing.aliyuncs.com")
        self.oss_region = os.getenv("OSS_REGION", "cn-beijing")
        self.oss_bucket_name = os.getenv("OSS_BUCKET", "rspioss")
        
        try:
            # 使用环境变量凭证提供器
            self.oss_auth = oss2.ProviderAuthV4(EnvironmentVariableCredentialsProvider())
            
            # 创建Bucket实例
            self.oss_bucket = oss2.Bucket(
                self.oss_auth,
                self.oss_endpoint,
                self.oss_bucket_name,
                region=self.oss_region
            )
            
            print(f"OSS服务初始化成功，Bucket: {self.oss_bucket_name}")
        except Exception as e:
            print(f"OSS服务初始化失败: {e}")
            self.oss_bucket = None
    
    def upload_file(self, local_path, object_prefix="captured_images"):
        """
        上传文件到OSS并返回可访问链接
        
        Args:
            local_path: 本地文件路径
            object_prefix: 对象前缀
            
        Returns:
            str: 预签名URL或None(如果上传失败)
        """
        try:
            if not self.oss_bucket:
                raise Exception("OSS服务未初始化")
                
            # 确保文件存在
            if not os.path.exists(local_path):
                raise Exception(f"文件不存在: {local_path}")
                
            # 生成唯一文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            object_name = f"{object_prefix}/{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
            
            # 上传文件
            self.oss_bucket.put_object_from_file(object_name, local_path)
            print(f"文件已上传至OSS: {object_name}")

            # 生成预签名URL（有效期1小时）
            signed_url = self.oss_bucket.sign_url(
                'GET',
                object_name,
                3600  # 过期时间（秒）
            )
            print(f"生成预签名URL: {signed_url}")
            
            return signed_url
            
        except Exception as e:
            print(f"OSS操作失败: {e}")
            return None 