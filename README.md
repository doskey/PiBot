# PiBot 语音助手

这是一个运行在树莓派5上的语音助手系统，通过USB麦克风实时监听声音，检测唤醒词后接收用户指令，并使用本地大语言模型(LLM)提供回答。

## 功能特点

- 使用USB麦克风实时监听声音
- 检测唤醒词（默认为"picovoice"）
- 使用Vosk本地模型进行语音识别，无需互联网
- 使用本地Ollama服务运行的llama3.2模型生成回答
- 使用gTTS将回答转换为语音并朗读出来（需要互联网连接，可选功能）

## 安装步骤

### 1. 安装Ollama

首先，请确保您已经安装了Ollama并下载了llama3.2模型：

```bash
# 安装Ollama（如果尚未安装）
curl -fsSL https://ollama.com/install.sh | sh

# 下载llama3.2模型
ollama pull llama3.2
```

确认Ollama服务正在运行：

```bash
ollama serve
```

### 2. 克隆仓库

```bash
git clone https://github.com/yourusername/PiBot.git
cd PiBot
```

### 3. 下载Vosk模型

下载中文Vosk语音识别模型：

```bash
# 创建模型目录
mkdir -p model

# 下载中文模型（根据您的需要选择不同大小的模型）
# 小型模型（约42MB）
wget https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip
unzip vosk-model-small-cn-0.22.zip -d .
mv vosk-model-small-cn-0.22/* model/
rm -rf vosk-model-small-cn-0.22*

# 或者下载更大更准确的模型
# wget https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip
```

### 4. 安装依赖

```bash
# 安装portaudio开发库（PyAudio的依赖）
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio

# 安装mpg123（用于播放MP3文件）
sudo apt-get install mpg123

# 安装Python依赖
pip install -r requirements.txt
```

### 5. 配置环境变量

将`.env.example`文件复制为`.env`，并填入您的配置：

```bash
cp .env.example .env
# 然后编辑.env文件，填入您的配置
```

您需要：
- Picovoice访问密钥（从[https://picovoice.ai/](https://picovoice.ai/)获取，用于唤醒词检测）
- Ollama模型名称（默认为llama3.2）
- Vosk模型路径（默认为"model"）

### 6. 运行助手

```bash
python voice_assistant.py
```

## 使用方法

1. 启动程序后，等待初始化完成
2. 说出唤醒词"picovoice"（您可以在代码中修改为其他受支持的唤醒词）
3. 听到提示后，说出您的问题或指令
4. 系统会使用本地Vosk模型进行语音识别，并通过Ollama的llama3.2模型生成回答
5. 回答会以文本形式显示，并可选择通过语音朗读出来

## 自定义设置

您可以在`voice_assistant.py`文件中修改以下参数：

- `wake_word`: 更改唤醒词（需要是Porcupine支持的词）
- `silence_threshold`: 调整句子结束检测的静默时间阈值
- `enable_voice_response`: 设置为False可以禁用语音回答
- `ollama_model`: 可以在.env文件中修改使用的Ollama模型名称

## 关于离线语音识别

Vosk提供了完全离线的语音识别功能，您可以根据需要选择不同大小的模型：

- 小型模型(vosk-model-small-cn-0.22)：约42MB，速度快但准确度较低
- 标准模型(vosk-model-cn-0.22)：约1.5GB，准确度更高但需要更多资源

对于树莓派，建议使用小型模型以获得更好的性能。

## 关于Ollama

Ollama是一个在本地运行大型语言模型的开源工具。本项目默认使用llama3.2模型，但您可以根据需要使用其他Ollama支持的模型：

```bash
# 查看可用模型
ollama list

# 下载其他模型
ollama pull mistral
```

## 故障排除

- 如果麦克风无法正常工作，请检查USB连接并确认设备被正确识别：
  ```
  arecord -l
  ```
  
- 如果遇到权限问题，请确保当前用户在音频组中：
  ```
  sudo usermod -a -G audio $USER
  ```

- 如果无法播放声音，请确保音频输出设备正常工作：
  ```
  # 测试音频输出
  speaker-test -t wav
  ```

- 如果Ollama服务无法连接，请确保Ollama服务正在运行：
  ```
  ollama serve
  ```

## 注意事项

- 本地语音识别（Vosk）不需要互联网连接
- 本地LLM（Ollama）不需要互联网连接
- gTTS语音合成仍然需要互联网连接，如果需要完全离线解决方案，可以考虑使用其他本地TTS库

## 许可证

本项目采用MIT许可证 