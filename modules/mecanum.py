#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys

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
    
    def __init__(self, auto_init=True):
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
        
    def test_all_movements(self):
        """测试所有移动方式"""
        duration = 1.0  # 每个动作持续1秒
        
        print("开始测试各种移动方式...")
        
        self.move_forward(duration)
        time.sleep(0.5)
        
        self.move_backward(duration)
        time.sleep(0.5)
        
        self.move_right(duration)
        time.sleep(0.5)
        
        self.move_left(duration)
        time.sleep(0.5)
        
        self.move_right_forward(duration)
        time.sleep(0.5)
        
        self.move_left_forward(duration)
        time.sleep(0.5)
        
        self.move_right_backward(duration)
        time.sleep(0.5)
        
        self.move_left_backward(duration)
        time.sleep(0.5)
        
        self.rotate_right(duration)
        time.sleep(0.5)
        
        self.rotate_left(duration)
        
        print("测试完成")
    
    def test_individual_motor(self, motor_name):
        """测试单个电机
        
        Args:
            motor_name: 电机名称 (front_left, front_right, rear_left, rear_right)
        """
        if not self._check_motors():
            return
            
        motors = {
            'front_left': self.front_left,
            'front_right': self.front_right,
            'rear_left': self.rear_left,
            'rear_right': self.rear_right
        }
        
        if motor_name not in motors:
            print(f"电机名称错误: {motor_name}，可用值为: front_left, front_right, rear_left, rear_right")
            return
            
        motor = motors[motor_name]
        print(f"测试{motor_name}电机...")
        
        # 输出电机连接状态
        print(f"电机连接状态: {motor.connected}")
        
        # 向前转1秒
        print(f"{motor_name}电机向前")
        motor.start(self.speed)
        time.sleep(1)
        motor.stop()
        
        time.sleep(0.5)
        
        # 向后转1秒
        print(f"{motor_name}电机向后")
        motor.start(-self.speed)
        time.sleep(1)
        motor.stop()
        
        print(f"{motor_name}电机测试完成")
    
    def cleanup(self):
        """清理资源，停止所有电机"""
        if not self._check_motors():
            return
            
        self.front_left.stop()
        self.front_right.stop()
        self.rear_left.stop()
        self.rear_right.stop()
        print("所有电机已停止")


def run_menu_system():
    """运行交互菜单系统"""
    try:
        # 创建麦克纳姆轮控制对象
        if not BUILDHAT_AVAILABLE:
            print("错误: BuildHAT库不可用，无法启动菜单系统")
            return
            
        wheels = MecanumWheels()
        
        # 菜单系统
        while True:
            print("\n==== 麦克纳姆轮控制系统 ====")
            print("1. 向前移动")
            print("2. 向后移动")
            print("3. 向右移动")
            print("4. 向左移动")
            print("5. 向右前方移动")
            print("6. 向左前方移动")
            print("7. 向右后方移动")
            print("8. 向左后方移动")
            print("9. 向右旋转")
            print("10. 向左旋转")
            print("11. 测试所有移动")
            print("A. 测试左前轮")
            print("B. 测试右前轮")
            print("C. 测试左后轮")
            print("D. 测试右后轮")
            print("S. 设置速度")
            print("0. 退出")
            
            choice = input("请选择操作 [0-11/A-D/S]: ").strip().upper()
            
            if choice == '1':
                duration = float(input("持续时间(秒): "))
                wheels.move_forward(duration)
            elif choice == '2':
                duration = float(input("持续时间(秒): "))
                wheels.move_backward(duration)
            elif choice == '3':
                duration = float(input("持续时间(秒): "))
                wheels.move_right(duration)
            elif choice == '4':
                duration = float(input("持续时间(秒): "))
                wheels.move_left(duration)
            elif choice == '5':
                duration = float(input("持续时间(秒): "))
                wheels.move_right_forward(duration)
            elif choice == '6':
                duration = float(input("持续时间(秒): "))
                wheels.move_left_forward(duration)
            elif choice == '7':
                duration = float(input("持续时间(秒): "))
                wheels.move_right_backward(duration)
            elif choice == '8':
                duration = float(input("持续时间(秒): "))
                wheels.move_left_backward(duration)
            elif choice == '9':
                duration = float(input("持续时间(秒): "))
                wheels.rotate_right(duration)
            elif choice == '10':
                duration = float(input("持续时间(秒): "))
                wheels.rotate_left(duration)
            elif choice == '11':
                wheels.test_all_movements()
            elif choice == 'A':
                wheels.test_individual_motor('front_left')
            elif choice == 'B':
                wheels.test_individual_motor('front_right')
            elif choice == 'C':
                wheels.test_individual_motor('rear_left')
            elif choice == 'D':
                wheels.test_individual_motor('rear_right')
            elif choice == 'S':
                speed = int(input("输入速度值(0-100): "))
                wheels.set_speed(speed)
            elif choice == '0':
                print("退出程序")
                break
            else:
                print("无效的选择!")
    
    except KeyboardInterrupt:
        print("\n程序被中断")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if 'wheels' in locals():
            wheels.cleanup()
        print("程序已退出")


if __name__ == "__main__":
    run_menu_system() 