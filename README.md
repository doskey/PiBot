# 语音助手

基于阿里云语音服务和阿里云百炼DeepSeek大语言模型的智能语音助手。

## 功能特点

- **语音唤醒**：通过唤醒词（默认"你好机器人"）激活助手
- **语音指令识别**：使用阿里云语音识别服务转录用户语音
- **智能问答**：利用阿里云百炼DeepSeek大语言模型生成回答
- **语音合成回复**：将文本回答转换为语音输出

## 系统要求

- Python 3.8+
- 麦克风和扬声器
- 阿里云账号（用于语音识别和语音合成）
- 阿里云百炼账号（用于大语言模型访问）

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

# 可选配置
WAKE_WORD=你好机器人
```

## 使用方法

1. 运行语音助手：
```bash
python voice_assistant.py
```

2. 当助手启动后，说出唤醒词（默认"你好机器人"）唤醒助手
3. 听到提示音后，说出您的问题
4. 助手会通过语音回答您的问题

## 获取API密钥

- 阿里云语音服务AppKey：在[阿里云智能语音交互控制台](https://nls-portal.console.aliyun.com/applist)创建应用并获取AppKey
- 阿里云百炼API密钥：在[阿里云百炼控制台](https://bailian.console.aliyun.com/)获取API密钥

## 自定义配置

您可以通过修改`.env`文件来自定义以下配置：

- `WAKE_WORD`：更改唤醒词
- `ALIYUN_LLM_MODEL`：更换大语言模型（支持deepseek-v3, deepseek-r1等）

## 问题排查

- 如果遇到麦克风问题，请确保系统默认麦克风正常工作
- 如果语音识别不准确，请确保在安静环境中使用，并且清晰发音
- 如果API调用失败，请检查API密钥和网络连接

## 许可证

[适用的开源许可证] 