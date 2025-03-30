#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime
from dotenv import load_dotenv

class LoggerManager:
    """
    统一日志管理模块
    
    功能:
    - 控制台日志输出
    - 文件日志输出
    - 日志级别控制
    - 日志格式控制
    """
    
    _instance = None
    
    def __new__(cls):
        # 单例模式实现
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        # 避免重复初始化
        if self.initialized:
            return
            
        # 加载环境变量
        load_dotenv()
        
        # 日志配置
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
        self.log_file_path = os.getenv("LOG_FILE_PATH", "logs")
        self.log_file_max_size = int(os.getenv("LOG_FILE_MAX_SIZE", "1048576"))  # 默认1MB
        self.log_file_backup_count = int(os.getenv("LOG_FILE_BACKUP_COUNT", "3"))  # 默认保留3个备份
        
        # 创建日志文件目录
        if self.log_to_file and not os.path.exists(self.log_file_path):
            os.makedirs(self.log_file_path)
        
        # 初始化主日志器
        self.logger = logging.getLogger("voice_assistant")
        self.logger.setLevel(self._get_log_level(self.log_level))
        self.logger.propagate = False  # 防止日志重复输出
        
        # 清除已有的处理器
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self._get_log_level(self.log_level))
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 添加文件处理器
        if self.log_to_file:
            log_file = os.path.join(
                self.log_file_path, 
                f"voice_assistant_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.log_file_max_size,
                backupCount=self.log_file_backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self._get_log_level(self.log_level))
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        self.initialized = True
        self.info(f"日志系统初始化完成，级别：{self.log_level}，文件输出：{self.log_to_file}")
    
    def _get_log_level(self, level_str):
        """根据字符串获取日志级别"""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return levels.get(level_str, logging.INFO)
    
    def get_logger(self, name=None):
        """获取指定名称的日志器"""
        if name:
            child_logger = logging.getLogger(f"voice_assistant.{name}")
            child_logger.propagate = True  # 继承父日志器的处理器
            child_logger.setLevel(self._get_log_level(self.log_level))
            return child_logger
        return self.logger
    
    def debug(self, msg, *args, **kwargs):
        """输出DEBUG级别日志"""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """输出INFO级别日志"""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """输出WARNING级别日志"""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """输出ERROR级别日志"""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """输出CRITICAL级别日志"""
        self.logger.critical(msg, *args, **kwargs)
    
    def set_level(self, level):
        """设置日志级别"""
        log_level = self._get_log_level(level.upper())
        self.logger.setLevel(log_level)
        for handler in self.logger.handlers:
            handler.setLevel(log_level)
        self.info(f"日志级别已设置为: {level.upper()}")

# 创建全局单例实例
logger = LoggerManager() 