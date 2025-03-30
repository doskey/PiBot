#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
麦克纳姆轮控制程序

轮子配置:
- 右前轮(RF): Port A
- 左前轮(LF): Port B
- 右后轮(RR): Port C
- 左后轮(LR): Port D

"""

import time
import sys

# 检查BuildHAT库是否可用
try:
    from buildhat import PassiveMotor
    BUILDHAT_AVAILABLE = True
except ImportError:
    BUILDHAT_AVAILABLE = False
    print("警告: BuildHAT库未安装，请运行 'pip install buildhat'")
    # 不再强制退出，允许作为模块导入
    # sys.exit(1)

class MecanumWheels:
    """麦克纳姆轮控制类"""
    
    def __init__(self, auto_init=True):
        """初始化四个轮子电机
        
        Args:
            auto_init: 是否自动初始化电机，默认为True。
                       如果设为False，则需要手动调用_init_motors()
        """
        self.motor_config = {
            'RF': {'port': 'A', 'motor': None},  # 右前轮
            'LF': {'port': 'B', 'motor': None},  # 左前轮
            'RR': {'port': 'C', 'motor': None},  # 右后轮
            'LR': {'port': 'D', 'motor': None}   # 左后轮
        }
        self.default_speed = 75  # 默认速度 (0-100)
        
        # 检查BuildHAT库是否可用
        if not BUILDHAT_AVAILABLE:
            print("错误: BuildHAT库不可用，麦克纳姆轮将无法工作")
            return
            
        # 初始化所有电机
        if auto_init:
            self._init_motors()
    
    def _init_motors(self):
        """初始化所有电机"""
        if not BUILDHAT_AVAILABLE:
            print("错误: BuildHAT库不可用，无法初始化电机")
            return False
            
        for position, config in self.motor_config.items():
            try:
                # 根据BuildHAT文档，PassiveMotor只接受port一个参数
                motor = PassiveMotor(config['port'])
                # 使用set_default_speed方法设置默认速度
                motor.set_default_speed(self.default_speed)
                self.motor_config[position]['motor'] = motor
                print(f"成功初始化{position}轮 (Port {config['port']})")
            except Exception as e:
                print(f"初始化{position}轮失败 (Port {config['port']}): {e}")
                self.cleanup()
                return False
        return True
    
    def _set_motor(self, position, direction, speed=None):
        """控制指定电机
        
        Args:
            position: 电机位置 (RF, LF, RR, LR)
            direction: 方向 (1=正向, -1=反向, 0=停止)
            speed: 速度 (默认使用self.default_speed)
        """
        motor = self.motor_config[position]['motor']
        if motor is None:
            print(f"警告: {position}轮未初始化")
            return
            
        if direction == 0:
            motor.stop()
        else:
            # 如果指定了速度，则使用指定速度；否则使用默认速度
            motor_speed = speed if speed is not None else self.default_speed
            # 应用方向系数
            motor.start(direction * motor_speed)
    
    def stop(self):
        """停止所有轮子"""
        for position in self.motor_config:
            self._set_motor(position, 0)
        print("所有轮子已停止")
    
    def move_forward(self, duration=1.0, speed=None):
        """向前移动
        四个轮子都向前转动（LF和LR电机因反装使用-1方向）
        """
        print(f"向前移动 {duration}秒")
        self._set_motor('RF', 1, speed)   # 右前轮向前（正转）
        self._set_motor('LF', -1, speed)  # 左前轮向前（反转实现）
        self._set_motor('RR', 1, speed)   # 右后轮向前（正转）
        self._set_motor('LR', -1, speed)  # 左后轮向前（反转实现）
        
        time.sleep(duration)
        self.stop()
    
    def move_backward(self, duration=1.0, speed=None):
        """向后移动
        四个轮子都向后转动（LF和LR电机因反装使用1方向）
        """
        print(f"向后移动 {duration}秒")
        self._set_motor('RF', -1, speed)  # 右前轮向后（反转）
        self._set_motor('LF', 1, speed)   # 左前轮向后（正转实现）
        self._set_motor('RR', -1, speed)  # 右后轮向后（反转）
        self._set_motor('LR', 1, speed)   # 左后轮向后（正转实现）
        
        time.sleep(duration)
        self.stop()
    
    def move_right(self, duration=1.0, speed=None):
        """向右横向移动
        左前轮向前，左后轮向后，右前轮向后，右后轮向前
        （LF/LR电机方向需反向）
        """
        print(f"向右横向移动 {duration}秒")
        self._set_motor('RF', -1, speed)  # 右前轮向后（反转）
        self._set_motor('LF', -1, speed)  # 左前轮向前（反转实现）
        self._set_motor('RR', 1, speed)   # 右后轮向前（正转）
        self._set_motor('LR', 1, speed)   # 左后轮向后（正转实现）
        
        time.sleep(duration)
        self.stop()
    
    def move_left(self, duration=1.0, speed=None):
        """向左横向移动
        左前轮向后，左后轮向前，右前轮向前，右后轮向后
        （LF/LR电机方向需反向）
        """
        print(f"向左横向移动 {duration}秒")
        self._set_motor('RF', 1, speed)   # 右前轮向前（正转）
        self._set_motor('LF', 1, speed)   # 左前轮向后（正转实现）
        self._set_motor('RR', -1, speed)  # 右后轮向后（反转）
        self._set_motor('LR', -1, speed)  # 左后轮向前（反转实现）
        
        time.sleep(duration)
        self.stop()
    
    def move_right_forward(self, duration=1.0, speed=None):
        """向右前方移动
        左前轮向前，右后轮向前
        """
        print(f"向右前方移动 {duration}秒")
        self._set_motor('RF', 0, 0)      # 右前轮停止
        self._set_motor('LF', -1, speed)  # 左前轮向前
        self._set_motor('RR', -1, speed)  # 右后轮向前
        self._set_motor('LR', 0, 0)      # 左后轮停止
        
        time.sleep(duration)
        self.stop()
    
    def move_left_forward(self, duration=1.0, speed=None):
        """向左前方移动
        右前轮向前，左后轮向前
        """
        print(f"向左前方移动 {duration}秒")
        self._set_motor('RF', 1, speed)  # 右前轮向前
        self._set_motor('LF', 0, 0)      # 左前轮停止
        self._set_motor('RR', 0, 0)      # 右后轮停止
        self._set_motor('LR', -1, speed)  # 左后轮向前
        
        time.sleep(duration)
        self.stop()
    
    def move_right_backward(self, duration=1.0, speed=None):
        """向右后方移动
        左前轮向后，右后轮向后
        """
        print(f"向右后方移动 {duration}秒")
        self._set_motor('RF', 0, 0)      # 右前轮停止
        self._set_motor('LF', 1, speed)  # 左前轮向后
        self._set_motor('RR', -1, speed)  # 右后轮向后
        self._set_motor('LR', 0, 0)      # 左后轮停止
        
        time.sleep(duration)
        self.stop()
    
    def move_left_backward(self, duration=1.0, speed=None):
        """向左后方移动
        右前轮向后，左后轮向后
        """
        print(f"向左后方移动 {duration}秒")
        self._set_motor('RF', -1, speed)  # 右前轮向后
        self._set_motor('LF', 0, 0)      # 左前轮停止
        self._set_motor('RR', 0, 0)      # 右后轮停止
        self._set_motor('LR', 1, speed)  # 左后轮向后
        
        time.sleep(duration)
        self.stop()
    
    def rotate_right(self, duration=1.0, speed=None):
        """顺时针旋转
        右轮向后，左轮向前
        """
        print(f"顺时针旋转 {duration}秒")
        self._set_motor('RF', -1, speed)  # 右前轮向后
        self._set_motor('LF', -1, speed)   # 左前轮向前
        self._set_motor('RR', -1, speed)  # 右后轮向后
        self._set_motor('LR', -1, speed)   # 左后轮向前
        
        time.sleep(duration)
        self.stop()
    
    def rotate_left(self, duration=1.0, speed=None):
        """逆时针旋转
        右轮向前，左轮向后
        """
        print(f"逆时针旋转 {duration}秒")
        self._set_motor('RF', 1, speed)   # 右前轮向前
        self._set_motor('LF', 1, speed)  # 左前轮向后
        self._set_motor('RR', 1, speed)   # 右后轮向前
        self._set_motor('LR', 1, speed)  # 左后轮向后
        
        time.sleep(duration)
        self.stop()
    
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
    
    def test_individual_motor(self, position):
        """测试单个电机
        
        Args:
            position: 电机位置 (RF, LF, RR, LR)
        """
        if position not in self.motor_config:
            print(f"位置错误: {position}，可用值为: RF, LF, RR, LR")
            return
            
        motor = self.motor_config[position]['motor']
        if motor is None:
            print(f"警告: {position}轮未初始化")
            return
            
        print(f"测试{position}轮...")
        
        # 输出电机连接状态
        print(f"电机连接状态: {motor.connected}")
        
        # 向前转1秒
        print(f"{position}轮向前")
        motor.start(self.default_speed)  # 使用正向速度
        time.sleep(1)
        motor.stop()
        
        time.sleep(0.5)
        
        # 向后转1秒
        print(f"{position}轮向后")
        motor.start(-self.default_speed)  # 使用负向速度
        time.sleep(1)
        motor.stop()
        
        print(f"{position}轮测试完成")
    
    def cleanup(self):
        """清理资源，停止所有电机"""
        for position, config in self.motor_config.items():
            if config['motor'] is not None:
                try:
                    config['motor'].stop()
                    print(f"停止{position}轮电机")
                except Exception as e:
                    print(f"停止{position}轮电机时出错: {e}")

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
            print("3. 向右横向移动")
            print("4. 向左横向移动")
            print("5. 向右前方移动")
            print("6. 向左前方移动")
            print("7. 向右后方移动")
            print("8. 向左后方移动")
            print("9. 顺时针旋转")
            print("10. 逆时针旋转")
            print("11. 测试所有移动")
            print("A. 测试右前轮")
            print("B. 测试左前轮")
            print("C. 测试右后轮")
            print("D. 测试左后轮")
            print("0. 退出")
            
            choice = input("请选择操作 [0-11/A-D]: ").strip().upper()
            
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
                wheels.test_individual_motor('RF')
            elif choice == 'B':
                wheels.test_individual_motor('LF')
            elif choice == 'C':
                wheels.test_individual_motor('RR')
            elif choice == 'D':
                wheels.test_individual_motor('LR')
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
