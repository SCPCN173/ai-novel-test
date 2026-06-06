# AI小说转剧本工具

一个AI辅助的剧本创作工具，帮助小说作者将作品自动转换为结构化剧本（YAML格式）。

## 功能特点

- ✨ **智能转换**：使用AI模型将小说文本自动转换为结构化剧本
- 📖 **多章节支持**：处理3个章节以上的长篇小说
- 🎭 **角色识别**：自动识别和标注小说中的角色
- 📝 **场景分割**：基于时空转换智能分割场景
- 🔧 **可编辑输出**：生成YAML格式剧本，便于后续编辑和打磨
- 🔄 **多模型支持**：支持Claude、OpenAI、Ollama等多个AI提供商
- 🎯 **CLI友好**：简单易用的命令行界面

## 快速开始

### 安装

```bash
# 克隆项目（如果需要）
git clone <repository-url>
cd ai-novel-test

# 安装依赖 （此处根据需求自行配置，requirements文件仅仅给出版本要求）
pip install -r requirements.txt
```

### 配置

编辑 `config.yaml` 文件，配置你选择的AI模型：

```yaml
ai_provider: "claude"  # 选择：claude, openai, ollama

providers:
  claude:
    api_key: "${ANTHROPIC_API_KEY}"  # 从环境变量读取
    model: "claude-sonnet-4-6"
```

### 使用

```bash
# 基本用法：转换小说为剧本
python -m src.main examples/sample_novel.txt -o output/my_script.yaml

# 指定AI模型
python -m src.main input.txt --model openai -o output.yaml

# 详细输出模式
python -m src.main input.txt --verbose

# 仅验证YAML格式
python -m src.main output.yaml --validate-only
```

## 项目结构

```
ai-novel-to-script/
├── README.md              # 项目说明
├── requirements.txt       # Python依赖
├── config.yaml           # 配置文件
├── docs/
│   └── yaml_schema.md    # 剧本YAML Schema设计文档
├── examples/
│   └── sample_novel.txt  # 示例小说
├── src/
│   ├── main.py           # CLI入口
│   ├── novel_parser.py   # 小说解析
│   ├── script_generator.py  # 剧本生成
│   ├── ai_client.py      # AI模型客户端
│   ├── yaml_schema.py    # Schema定义
│   └── utils.py          # 工具函数
├── tests/                 # 测试代码
└── output/               # 输出目录
```

## YAML Schema设计

剧本采用YAML格式存储，结构清晰、易于编辑。详见 [docs/yaml_schema.md](docs/yaml_schema.md)。

核心结构：

```yaml
script:
  metadata:      # 元数据（标题、作者等）
  characters:    # 角色列表
  scenes:        # 场景和动作序列
  outline:       # 剧情大纲
```

## 示例

查看 `examples/sample_novel.txt` 和 `output/sample_script.yaml` 了解转换效果。

## 环境要求

- Python 3.8+
- API密钥（取决于选择的AI提供商）

## 配置说明

### Claude API

```yaml
ai_provider: "claude"
providers:
  claude:
    api_key: "${ANTHROPIC_API_KEY}"  # 或直接填写密钥
    model: "claude-sonnet-4-6"
    max_tokens: 4096
```

设置环境变量：
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### OpenAI API

```yaml
ai_provider: "openai"
providers:
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4"
```

### Ollama本地模型

```yaml
ai_provider: "ollama"
providers:
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3"
```

## 开发与测试

```bash
# 运行单元测试
python -m pytest tests/

# 测试转换功能
python -m src.main examples/sample_novel.txt -o output/test.yaml --verbose
```

## 许可证

无

## 作者

15601837090 - 暑训营项目 - AI小说转剧本工具

## 反馈与贡献

欢迎提交Issue和Pull Request！
