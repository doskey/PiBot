#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

# 条件导入BuildHAT库
try:
    from buildhat import PassiveMotor
    BUILDHAT_AVAILABLE = True
except ImportError:
    BUILDHAT_AVAILABLE = False
    print("警告: BuildHAT库未安装，电机控制功能将不可用")


class MecanumWheels:
    """
    麦克纳姆轮控制模块，用于控制机器人移动
    """
    
    def __init__(self):
        """初始化麦克纳姆轮控制器"""
        if not BUILDHAT_AVAILABLE:
            print("麦克纳姆轮控制器初始化失败: BuildHAT库未安装")
            self.motors_available = False
            return
            
        try:
            # 初始化四个电机，根据实际接口调整
            self.front_left = PassiveMotor('A')
            self.front_right = PassiveMotor('B')
            self.rear_left = PassiveMotor('C')
            self.rear_right = PassiveMotor('D')
            
            # 设置默认电机速度（-100到100）
            self.speed = 50
            
            # 标记电机为可用
            self.motors_available = True
            
            print("麦克纳姆轮控制器初始化成功")
        except Exception as e:
            print(f"麦克纳姆轮控制器初始化失败: {e}")
            self.motors_available = False
    
    def _check_motors(self):
        """检查电机是否可用"""
        if not self.motors_available:
            print("电机不可用，无法执行移动操作")
            return False
        return True
    
    def stop(self):
        """停止所有电机"""
        if not self._check_motors():
            return
            
        self.front_left.stop()
        self.front_right.stop()
        self.rear_left.stop()
        self.rear_right.stop()
        print("停止移动")
    
    def move_forward(self, duration=1.0):
        """
        向前移动
        
        Args:
            duration: 移动持续时间，单位秒
        """
        if not self._check_motors():
            return
            
        print(f"向前移动 {duration} 秒")
        self.front_left.start(self.speed)
        self.front_right.start(self.speed)
        self.rear_left.start(self.speed)
        self.rear_right.start(self.speed)
        
        time.sleep(duration)
        self.stop()
    
    def move_backward(self, duration=1.0):
        """
        向后移动
        
        Args:
            duration: 移动持续时间，单位秒
        """
        if not self._check_motors():
            return
            
        print(f"向后移动 {duration} 秒")
        self.front_left.start(-self.speed)
        self.front_right.start(-self.speed)
        self.rear_left.start(-self.speed)
        self.rear_right.start(-self.speed)
        
        time.sleep(duration)
        self.stop()
    
    def move_left(self, duration=1.0):
        """
        向左移动（横向）
        
        Args:
            duration: 移动持续时间，单位秒
        """
        if not self._check_motors():
            return
            
        print(f"向左移动 {duration} 秒")
        self.front_left.start(-self.speed)
        self.front_right.start(self.speed)
        self.rear_left.start(self.speed)
        self.rear_right.start(-self.speed)
        
        time.sleep(duration)
        self.stop()
    
    def move_right(self, duration=1.0):
        """
        向右移动（横向）
        
        Args:
            duration: 移动持续时间，单位秒
        """
        if not self._check_motors():
            return
            
        print(f"向右移动 {duration} 秒")
        self.front_left.start(self.speed)
        self.front_right.start(-self.speed)
        self.rear_left.start(-self.speed)
        self.rear_right.start(self.speed)
        
        time.sleep(duration)
        self.stop()
    
    def move_left_forward(self, duration=1.0):
        """
        向左前方移动（对角线）
        
        Args:
            duration: 移动持续时间，单位秒
        """
        if not self._check_motors():
            return
            
        print(f"向左前方移动 {duration} 秒")
        self.front_left.start(0)
        self.front_right.start(self.speed)
        self.rear_left.start(self.speed)
        self.rear_right.start(0)
        
        time.sleep(duration)
        self.stop()
    
    def move_right_forward(self, duration=1.0):
        """
        向右前方移动（对角线）
        
        Args:
            duration: 移动持续时间，单位秒
        """
        if not self._check_motors():
            return
            
        print(f"向右前方移动 {duration} 秒")
        self.front_left.start(self.speed)
        self.front_right.start(0)
        self.rear_left.start(0)
        self.rear_right.start(self.speed)
        
        time.sleep(duration)
        self.stop()
    
    def move_left_backward(self, duration=1.0):
        """
        向左后方移动（对角线）
        
        Args:
            duration: 移动持续时间，单位秒
        """
        if not self._check_motors():
            return
            
        print(f"向左后方移动 {duration} 秒")
        self.front_left.start(-self.speed)
        self.front_right.start(0)
        self.rear_left.start(0)
        self.rear_right.start(-self.speed)
        
        time.sleep(duration)
        self.stop()
    
    def move_right_backward(self, duration=1.0):
        """
        向右后方移动（对角线）
        
        Args:
            duration: 移动持续时间，单位秒
        """
        if not self._check_motors():
            return
            
        print(f"向右后方移动 {duration} 秒")
        self.front_left.start(0)
        self.front_right.start(-self.speed)
        self.rear_left.start(-self.speed)
        self.rear_right.start(0)
        
        time.sleep(duration)
        self.stop()
    
    def rotate_left(self, duration=1.0):
        """
        向左旋转
        
        Args:
            duration: 移动持续时间，单位秒
        """
        if not self._check_motors():
            return
            
        print(f"向左旋转 {duration} 秒")
        self.front_left.start(-self.speed)
        self.front_right.start(self.speed)
        self.rear_left.start(-self.speed)
        self.rear_right.start(self.speed)
        
        time.sleep(duration)
        self.stop()
    
    def rotate_right(self, duration=1.0):
        """
        向右旋转
        
        Args:
            duration: 移动持续时间，单位秒
        """
        if not self._check_motors():
            return
            
        print(f"向右旋转 {duration} 秒")
        self.front_left.start(self.speed)
        self.front_right.start(-self.speed)
        self.rear_left.start(self.speed)
        self.rear_right.start(-self.speed)
        
        time.sleep(duration)
        self.stop()
    
    def set_speed(self, speed):
        """
        设置电机速度
        
        Args:
            speed: 速度值（0-100）
        """
        if speed < 0 or speed > 100:
            print(f"无效的速度值: {speed}，应在0-100范围内")
            return
            
        self.speed = speed
        print(f"电机速度设置为: {speed}") 