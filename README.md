# PiBot 语音助手

这是一个运行在树莓派5上的语音助手系统，通过USB麦克风监听用户语音指令，并使用本地大语言模型(LLM)提供回答。

## 功能特点

- 使用USB麦克风实时监听声音
- 使用Vosk本地模型检测唤醒词（默认为"你好机器人"）
- 使用Vosk进行语音识别，完全离线运行
- 使用本地Ollama服务运行的大语言模型生成回答
- 使用pyttsx3将回答转换为语音并朗读出来（完全离线）

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
sudo apt-get install -y python3-full espeak
```

### 4. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 5. 下载Vosk模型

您需要下载Vosk模型用于语音识别：

```bash
# 创建模型目录
mkdir -p model

# 下载中文小型模型
wget https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip
unzip vosk-model-small-cn-0.22.zip -d model
mv model/vosk-model-small-cn-0.22/* model/
rm -r model/vosk-model-small-cn-0.22
rm vosk-model-small-cn-0.22.zip
```

### 6. 配置环境变量

将`.env.example`文件复制为`.env`，并填入您的配置：

```bash
cp .env.example .env
# 然后编辑.env文件，填入您的配置
```

您需要：
- Ollama模型名称（默认为qwen2.5:3b）
- Vosk模型路径（默认为"model"）
- 唤醒词设置（默认为"你好机器人"）

### 7. 运行助手

```bash
python voice_assistant.py
```

## 使用方法

1. 启动程序后，等待Vosk模型初始化完成
2. 说出唤醒词"你好机器人"（您可以在.env文件中修改为其他词语）
3. 听到"我在听"的提示后，说出您的问题或指令
4. 系统会使用Vosk模型进行语音识别，并通过Ollama模型生成回答
5. 回答会以文本形式显示，并通过语音朗读出来

## 自定义设置

您可以在`.env`文件中修改以下参数：

- `WAKE_WORD`: 更改唤醒词
- `VOSK_MODEL_PATH`: Vosk模型路径
- `OLLAMA_MODEL`: 使用的Ollama模型名称

您也可以在`voice_assistant.py`文件中修改以下参数：
- `silence_threshold`: 调整句子结束检测的静默时间阈值
- `enable_voice_response`: 设置为False可以禁用语音回答

## 语音识别系统

本项目完全使用Vosk进行语音识别，有以下特点：
- 完全离线运行，无需互联网连接
- 资源占用低，适合在树莓派等设备上运行
- 支持自定义唤醒词，无需特殊训练
- 唤醒速度快，延迟低
- 多语言支持，支持中文识别
- 适合在资源受限的环境中使用

Vosk模型有多种尺寸可供选择：
- small：更快的处理速度，占用内存更少
- large：更高的准确性，但需要更多内存

## 关于Ollama

Ollama是一个在本地运行大型语言模型的开源工具。本项目默认使用qwen2.5:3b模型，但您可以根据需要使用其他Ollama支持的模型：

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

- 如果找不到Vosk模型，请确保已正确下载并解压到model目录中

## 注意事项

- Vosk模型需要在首次运行时下载，请确保有网络连接
- 模型将保存在本地，之后可以离线使用
- 本地LLM（Ollama）不需要互联网连接
- 使用pyttsx3的语音合成可以完全离线工作

## 许可证

本项目采用MIT许可证 