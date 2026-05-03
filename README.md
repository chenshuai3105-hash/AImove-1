# AImove-1 家庭教育短视频制作工具

基于 AI 的全流程短视频自动化制作系统，专为家庭教育场景设计。从选题生成到视频合成，一站式完成短视频创作。

## 功能特性

- **AI 选题生成** — 基于 IP 人格设定自动生成热门选题
- **智能脚本创作** — 支持多版本迭代，自动优化文案结构
- **分镜设计** — 自动生成分镜描述与画面提示词
- **AI 绘画** — 集成 MiniMax Token Plan API 与 Qwen Image 2.0
- **TTS 语音合成** — 支持多种音色选择
- **背景音乐生成** — 自动生成匹配视频主题的 BGM
- **字幕引擎** — 旁白/金句双层字幕，支持字体与位置自定义
- **视频合成** — 基于 FFmpeg 的图片转场与音画同步

## 技术栈

- **语言**: Python 3.10+
- **UI 框架**: Tkinter
- **AI API**: MiniMax Token Plan API、Qwen Image 2.0
- **语音合成**: edge-tts（备选）
- **视频处理**: FFmpeg
- **图像处理**: Pillow

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- FFmpeg（系统 PATH 可访问）

### 安装

```bash
# 克隆仓库
git clone https://github.com/chenshuai3105-hash/AImove-1.git
cd AImove-1

# 安装依赖
pip install -r requirements.txt
```

### 配置 API 密钥

首次启动会自动生成 `api_config.json` 配置文件，或在程序菜单中打开 **API 配置** 填入以下密钥：

- **MiniMax Token Plan API Key** — 用于文本生成、语音合成、绘画与音乐生成
- **Qwen Image API Key** — 用于备选图片生成

### 运行

```bash
python video_maker_ai.py
```

## 使用流程

程序采用 Step-by-Step 向导模式，共 7 个步骤：

1. **IP 模板设置** — 配置 IP 名称、人设、语气风格等
2. **选题生成** — AI 自动生成热门选题列表
3. **脚本创作** — 基于选题自动生成短视频脚本
4. **分镜设计** — 自动拆分脚本为分镜画面
5. **图片生成** — 根据分镜描述生成对应图片
6. **音频制作** — 语音旁白 + 背景音乐合成
7. **视频合成** — 图片 + 音频 + 字幕合并输出最终视频

## 项目结构

```
├── video_maker_ai.py          # 主程序（核心）
├── parenting_video_maker.py   # 旧版程序
├── parenting_video_gui.py     # 旧版 GUI 实现
├── .gitignore                 # 排除规则
└── 程序详细说明.md             # 详细文档
```

## 注意

- API 密钥请通过程序界面配置，不要直接写入代码文件
- 程序运行时会生成 images/、audio/、output/ 等目录，已在 .gitignore 中排除
