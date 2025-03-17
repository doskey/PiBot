# PiBot 语音助手

这是一个运行在树莓派5上的语音助手系统，通过USB麦克风实时监听声音，检测唤醒词后接收用户指令，并使用本地大语言模型(LLM)提供回答。

## 功能特点

- 使用USB麦克风实时监听声音
- 检测唤醒词（默认为"小肚小肚"）
- 使用OpenAI的Whisper模型进行高精度语音识别
- 使用本地Ollama服务运行的LLM模型生成回答
- 使用gTTS将回答转换为语音并朗读出来（需要互联网连接，可选功能）

## 安装步骤

### 1. 安装Ollama

首先，请确保您已经安装了Ollama并下载了所需模型：

```bash
# 安装Ollama（如果尚未安装）
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型（例如llama2）
ollama pull llama2
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

### 3. 安装系统依赖

```bash
# 安装音频相关库
sudo apt-get update
sudo apt-get install -y mpg123 portaudio19-dev

# 如果使用树莓派，可能需要安装额外的依赖
sudo apt-get install -y libopenblas-dev python3-full
```

### 4. 创建虚拟环境并安装依赖

在树莓派上，直接安装PyTorch可能会比较困难，建议使用官方的预编译包：

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 树莓派上的PyTorch安装说明

对于树莓派等ARM设备，可能需要使用特定的预编译包安装PyTorch：

```bash
# 示例：在树莓派上安装PyTorch
pip install https://github.com/Kashu7100/pytorch-armv7l/raw/main/torch-2.0.0a0+gite9ebda2-cp39-cp39-linux_armv7l.whl
```

请访问[PyTorch官网](https://pytorch.org/get-started/locally/)获取最新的安装指南。

### 5. 配置环境变量

将`.env.example`文件复制为`.env`，并填入您的配置：

```bash
cp .env.example .env
# 然后编辑.env文件，填入您的配置
```

您可以设置以下环境变量：
- `OLLAMA_MODEL`: 使用的Ollama模型名称（默认为"llama2"）

### 6. 运行助手

```bash
python voice_assistant.py
```

## 使用方法

1. 启动程序后，等待初始化完成（Whisper模型首次运行时需要下载，请耐心等待）
2. 说出唤醒词"小肚小肚"（您可以在代码中修改为其他词语）
3. 当助手被唤醒后，说出您的问题或指令
4. 系统会使用Whisper模型进行语音识别，并通过Ollama的LLM模型生成回答
5. 回答会以文本形式显示，并可选择通过语音朗读出来

## 自定义设置

您可以在`voice_assistant.py`文件中修改以下参数：

- `wake_word`: 更改唤醒词
- `silence_threshold`: 调整语音录制的时间阈值
- `enable_voice_response`: 设置为False可以禁用语音回答
- `ollama_model`: 可以在.env文件中修改使用的Ollama模型名称
- `whisper_model`: 可以选择不同大小的Whisper模型（"tiny", "base", "small", "medium", "large"）

## 关于Whisper语音识别

Whisper是OpenAI开发的先进语音识别模型，具有以下特点：

- 多语言支持，对中文识别效果出色
- 较高的准确率，特别是在嘈杂环境中
- 可以选择不同大小的模型以平衡准确性和性能：
  - tiny: 约39MB，速度最快但准确度较低
  - base: 约142MB
  - small: 约465MB
  - medium: 约1.5GB
  - large: 约3GB，准确度最高但需要更多计算资源

对于树莓派，建议使用tiny或base模型以获得更好的性能。

## 关于Ollama

Ollama是一个在本地运行大型语言模型的开源工具。本项目默认使用llama2模型，但您可以根据需要使用其他Ollama支持的模型：

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

- 如果PyTorch安装困难，请尝试使用预编译的wheel包

## 注意事项

- Whisper需要在首次运行时下载模型，请确保有网络连接
- Whisper模型将保存在本地，之后可以离线使用
- 本地LLM（Ollama）不需要互联网连接
- gTTS语音合成仍然需要互联网连接，如果需要完全离线解决方案，可以考虑使用其他本地TTS库

## 许可证

本项目采用MIT许可证 