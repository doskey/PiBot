#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
import subprocess
import cv2


class Camera:
    """
    摄像头模块，负责图像捕获功能
    """
    
    def __init__(self):
        """初始化摄像头模块"""
        # 检测是否为树莓派环境
        self.is_raspberry_pi = self._check_raspberry_pi()
        
        # 摄像头设备ID，默认为0，可以通过环境变量覆盖
        self.capture_device = os.getenv("CAPTURE_DEVICE", 0)
        
        if isinstance(self.capture_device, str) and self.capture_device.isdigit():
            self.capture_device = int(self.capture_device)
            
        print(f"摄像头初始化完成，设备ID: {self.capture_device}, " +
              f"运行环境: {'树莓派' if self.is_raspberry_pi else '普通PC'}")
    
    def _check_raspberry_pi(self):
        """检测是否为树莓派环境"""
        try:
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read()
                    if 'Raspberry Pi' in model:
                        print("检测到树莓派环境:", model.strip())
                        return True
            return False
        except Exception as e:
            print(f"检测树莓派环境出错: {e}")
            return False
    
    def _take_photo_with_libcamera(self):
        """使用libcamera工具拍照（树莓派专用）"""
        # 生成唯一的临时文件名
        temp_image = f"/tmp/capture_{uuid.uuid4().hex[:8]}.jpg"
        
        # 使用libcamera命令拍照
        print("正在使用libcamera拍照...")
        cmd = f"libcamera-jpeg -o {temp_image} --width 1920 --height 1080 --nopreview -t 2000"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "未知错误"
            raise Exception(f"libcamera拍照失败: {error_msg}")
        
        if not os.path.exists(temp_image):
            raise Exception("拍照成功但未生成图片文件")
        
        print(f"libcamera拍照成功，保存至: {temp_image}")
        return temp_image
    
    def _take_photo_with_opencv(self):
        """使用OpenCV拍照"""
        print("正在使用OpenCV拍照...")
        cap = cv2.VideoCapture(self.capture_device)
        if not cap.isOpened():
            raise Exception(f"无法打开摄像头 {self.capture_device}")
        
        # 摄像头预热
        print("摄像头预热中...")
        warmup_frames = 10
        for _ in range(warmup_frames):
            ret, _ = cap.read()
            if not ret:
                break
        
        # 拍照
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise Exception("OpenCV拍照失败")
        
        # 保存临时文件
        temp_image = f"/tmp/opencv_capture_{uuid.uuid4().hex[:8]}.jpg"
        cv2.imwrite(temp_image, frame)
        print(f"OpenCV拍照成功，保存至: {temp_image}")
        
        return temp_image
    
    def capture_image(self):
        """
        捕获一张图像
        
        Returns:
            str: 临时图像文件路径
        """
        try:
            # 根据环境选择拍照方式
            if self.is_raspberry_pi:
                try:
                    return self._take_photo_with_libcamera()
                except Exception as e:
                    print(f"libcamera拍照失败: {e}, 尝试使用OpenCV拍照...")
                    return self._take_photo_with_opencv()
            else:
                return self._take_photo_with_opencv()
                
        except Exception as e:
            print(f"拍照失败: {e}")
            return None 