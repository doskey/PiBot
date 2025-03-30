# 智能语音助手机器人

基于阿里云语音服务和阿里云百炼DeepSeek大语言模型的智能语音助手机器人，支持图像识别和麦克纳姆轮移动控制。

## 功能特点

- **语音唤醒**：通过多种唤醒词激活不同功能
  - "你好机器人"：激活对话功能
  - "机器人这是什么"：激活图像识别功能
  - "机器人出发"：激活移动控制功能
- **语音指令识别**：使用阿里云语音识别服务转录用户语音
- **智能问答**：利用阿里云百炼DeepSeek大语言模型生成回答
- **语音合成回复**：将文本回答转换为语音输出
- **图像识别**：拍照并识别图像内容，支持树莓派和普通摄像头
- **移动控制**：通过语音指令控制麦克纳姆轮移动

## 系统要求

- Python 3.8+
- 麦克风和扬声器
- 摄像头（用于图像识别）
- 阿里云账号（用于语音识别和语音合成）
- 阿里云百炼账号（用于大语言模型访问）
- 树莓派BuildHAT（可选，用于电机控制）

## 安装步骤

1. 克隆本仓库：
```bash
git clone <仓库地址>
cd <仓库文件夹>
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

```bash
git clone https://github.com/aliyun/alibabacloud-nls-python-sdk
cd alibabacloud-nls-python-sdk
python -m pip install -r requirements.txt
python -m pip install .
```

3. 创建配置文件：
在项目根目录创建`.env`文件，填入以下信息：
```
# 阿里云语音服务配置
ALI_APPKEY=<您的阿里云语音服务AppKey>
ALI_TOKEN=<您的阿里云语音服务Token>
# 或者使用AccessKey认证
ALIYUN_AK_ID=<您的阿里云AccessKey ID>
ALIYUN_AK_SECRET=<您的阿里云AccessKey Secret>

# 阿里云百炼大语言模型配置
DASHSCOPE_API_KEY=<您的阿里云百炼API密钥>
ALIYUN_LLM_MODEL=deepseek-v3

# 阿里云OSS配置（用于图像识别）
OSS_ACCESS_KEY_ID=<您的OSS AccessKey ID>
OSS_ACCESS_KEY_SECRET=<您的OSS AccessKey Secret>
OSS_BUCKET=<您的OSS Bucket名称>
OSS_ENDPOINT=<您的OSS访问域名>

# 可选配置
CAPTURE_DEVICE=0  # 摄像头设备索引
```

## 使用方法

1. 运行语音助手：
```bash
python voice_assistant.py
```

2. 通过不同的唤醒词启动不同功能：
   - 说出"你好机器人"启动智能对话功能
   - 说出"机器人这是什么"启动图像识别功能
   - 说出"机器人出发"启动移动控制功能
   
3. 根据助手的提示进行交互

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
- 如果语音识别不准确，请确保在安静环境中使用，并且清晰发音
- 如果API调用失败，请检查API密钥和网络连接
- 如果移动控制不工作，请检查BuildHAT连接和电机供电

## 许可证

[适用的开源许可证] 