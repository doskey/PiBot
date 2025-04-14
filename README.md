# PiBot 智能语音助手

基于阿里云语音服务和阿里云百炼DeepSeek的智能语音助手，实现了语音唤醒、语音识别、LLM对话、视觉识别和机器人控制等功能。
支持使用Vosk在本地离线进行唤醒词识别，提高隐私性和稳定性。

## 项目结构

项目被重构为多个模块化组件，每个组件负责特定功能：

```
PiBot/
├── modules/                      # 模块目录
│   ├── __init__.py               # 包初始化文件
│   ├── license_manager.py        # 阿里云Token管理
│   ├── voice_wakeup.py           # 语音唤醒模块
│   ├── tts.py                    # 文本到语音合成
│   ├── llm.py                    # 文本LLM对话
│   ├── vision_llm.py             # 多模态视觉识别
│   ├── oss.py                    # 阿里云OSS服务
│   ├── mecanum.py                # 麦克纳姆轮控制
│   └── camera.py                 # 摄像头图像捕获
├── models/                       # 语音模型目录
│   └── vosk-model-small-cn-0.22/ # Vosk中文识别模型
├── main.py                       # 程序入口点
├── test_vosk_wake.py             # Vosk唤醒词测试程序
├── voice_assistant.py            # 语音助手核心实现
└── requirements.txt              # 依赖管理
```

## 功能说明

1. **语音唤醒**：通过特定唤醒词激活助手
   - "你好机器人"：进入LLM对话模式
   - "机器人这是什么"：进入环境识别模式
   - "机器人出发"：进入运动控制模式
   - **支持使用Vosk进行离线本地唤醒识别，无需云端依赖**

2. **语音对话**：通过阿里云语音识别和百炼DeepSeek LLM提供智能对话

3. **环境识别**：拍照并使用视觉LLM分析环境中的物体

4. **移动控制**：通过语音命令控制机器人移动方向和时间

## 环境配置

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 创建`.env`文件，设置以下环境变量：

```
# 阿里云语音服务配置
ALI_APPKEY=你的阿里云AppKey
ALI_TOKEN=你的阿里云Token
# 或者使用AccessKey
ALIYUN_AK_ID=你的AccessKey ID
ALIYUN_AK_SECRET=你的AccessKey Secret

# 阿里云百炼LLM配置
DASHSCOPE_API_KEY=你的百炼API密钥
ALIYUN_LLM_MODEL=deepseek-v3
ALIYUN_VISION_MODEL=qwen2.5-vl-32b-instruct

# OSS配置
OSS_ENDPOINT=https://oss-cn-beijing.aliyuncs.com
OSS_REGION=cn-beijing
OSS_BUCKET=你的Bucket名称

# 摄像头配置
CAPTURE_DEVICE=0
```

3. 下载Vosk离线语音识别模型

```bash
# 创建models目录
mkdir -p models

# 下载Vosk中文小型模型
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip

# 解压模型
unzip vosk-model-small-cn-0.22.zip

# 返回项目目录
cd ..
```

## 运行

项目提供了多种启动方式：

### 方式一：使用main.py（完整语音助手）

```bash
# 基本启动
python main.py

# 启用详细日志
python main.py -v

# 禁用语音响应（仅文本交互）
python main.py --no-voice

# 启用语音识别调试
python main.py --debug-asr

# 查看所有可用选项
python main.py --help
```

### 方式二：直接使用voice_assistant.py

```bash
python voice_assistant.py
```

### 方式三：测试Vosk离线唤醒功能

```bash
python test_vosk_wake.py
```

## 模块详解

### license_manager.py

管理阿里云Token获取和刷新。从环境变量中获取配置，支持Token直接传入或通过AccessKey获取。

### voice_wakeup.py

语音唤醒和命令录制模块。支持两种唤醒模式：
- **Vosk离线唤醒**：使用Vosk语音识别库在本地实时识别唤醒词，无需联网
- **阿里云唤醒**：使用阿里云的语音识别服务进行唤醒词识别（作为备选方案）

命令识别仍使用阿里云语音识别服务以保证准确性。

### tts.py 

文本到语音合成模块。使用阿里云语音服务合成和播放语音。

### llm.py

文本LLM服务模块。封装了阿里云百炼的DeepSeek LLM服务，提供智能对话能力。

### vision_llm.py

多模态LLM服务模块。处理图像识别和分析功能，支持实时语音播报分析过程。

### oss.py

阿里云对象存储服务模块。负责上传图像并生成预签名URL。

### mecanum.py

麦克纳姆轮控制模块。提供各种移动方式，包括全向移动和旋转。

### camera.py

摄像头模块。负责图像捕获，同时支持树莓派libcamera和OpenCV两种拍照方式。

## Vosk离线唤醒功能

Vosk是一个离线的语音识别工具包，具有以下特点：
- 完全离线工作，不需要网络连接
- 模型体积小（约50-100MB），适合在树莓派等设备上运行
- 支持多种语言，包括中文
- 实时流式处理，低延迟

本项目通过以下方式实现离线唤醒：
1. 创建单独的唤醒监听线程，持续采集音频
2. 使用线程安全队列传递音频数据
3. 实时分析语音内容，识别是否包含唤醒词
4. 一旦检测到唤醒词，唤醒主程序进行后续处理

## 注意事项

1. 树莓派环境下需要安装buildhat库以支持电机控制
2. 确保麦克风和扬声器正常配置
3. 使用前请确保阿里云服务配置正确
4. 如果要使用Vosk离线唤醒，请确保已下载并放置好语音模型

## 获取API密钥

- 阿里云语音服务AppKey：在[阿里云智能语音交互控制台](https://nls-portal.console.aliyun.com/applist)创建应用并获取AppKey
- 阿里云百炼API密钥：在[阿里云百炼控制台](https://bailian.console.aliyun.com/)获取API密钥
- 阿里云OSS：在[阿里云OSS控制台](https://oss.console.aliyun.com/)创建存储桶并获取密钥

## 自定义配置

您可以通过修改`.env`文件来自定义配置：

- 修改唤醒词和对应功能
- 更换大语言模型（支持deepseek-v3, deepseek-r1, qwen2.5-vl-32b-instruct等）
- 配置摄像头设备

## 硬件连接（麦克纳姆轮）

如果要使用移动控制功能，需要：
1. 树莓派配备BuildHAT扩展板
2. 连接四个LEGO Technic电机到麦克纳姆轮
3. 电机接口分配见代码中的MecanumWheels类

## 问题排查

- 如果遇到麦克风问题，请确保系统默认麦克风正常工作
- 如果本地唤醒不工作，请确认Vosk模型已正确安装
- 如果语音识别不准确，请确保在安静环境中使用，并且清晰发音
- 如果API调用失败，请检查API密钥和网络连接
- 如果移动控制不工作，请检查BuildHAT连接和电机供电

## 许可证

[适用的开源许可证] 