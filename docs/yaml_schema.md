# 剧本YAML Schema设计文档

## 概述

本文档定义了AI小说转剧本工具输出的YAML格式剧本的Schema设计，说明了各字段的含义、设计原因以及使用方法。

## 设计目标

### 核心设计原则

1. **模块化结构**：将剧本分为元数据、角色、场景、大纲等独立模块，便于分块编辑和维护
2. **可扩展性**：使用ID引用系统，支持跨章节的角色和场景关联，便于后续扩展
3. **可读性**：采用清晰的层级结构，YAML格式天然易于人工阅读和编辑
4. **兼容性**：结构设计便于转换为其他格式（JSON、XML、Final Draft格式等）
5. **专业性**：符合剧本创作的行业标准和最佳实践

### 为什么选择YAML？

- **易读性**：YAML的缩进和层级结构比JSON更易人工阅读和编辑
- **注释支持**：YAML允许添加注释，便于作者标注和说明
- **灵活性**：YAML支持多行文本，适合存储对话和描述内容
- **工具支持**：Python、JavaScript等主流语言都有成熟的YAML库
- **行业趋势**：现代配置文件和结构化数据存储越来越多采用YAML格式

## Schema结构定义

### 顶层结构

```yaml
script:
  metadata:      # 元数据部分
  characters:    # 角色列表
  scenes:        # 场景序列
  outline:       # 剧情大纲
```

### 1. Metadata（元数据）

**位置**：`script.metadata`

**设计原因**：
- 记录剧本的基本信息，便于管理和检索
- 提供溯源信息，关联原小说作品
- 支持版本管理，便于追踪修改历史

**字段定义**：

```yaml
metadata:
  title:              # 剧本标题
    type: string
    required: true
    description: "剧本的标题名称"

  original_novel:     # 原小说名称
    type: string
    required: true
    description: "改编来源的小说名称"

  author:             # 作者
    type: string
    required: true
    description: "剧本改编者/原小说作者"

  created_date:       # 创建日期
    type: string (YYYY-MM-DD格式)
    required: true
    description: "剧本创建/生成日期"

  version:            # 版本号
    type: string
    required: false
    default: "1.0"
    description: "剧本版本号，用于追踪修改"

  total_chapters:     # 总章节数
    type: integer
    required: false
    description: "原小说总章节数"

  notes:              # 备注
    type: string
    required: false
    description: "其他备注信息"
```

**示例**：

```yaml
metadata:
  title: "青春的序曲"
  original_novel: "李明的青春故事"
  author: "张三"
  created_date: "2026-06-05"
  version: "1.0"
  total_chapters: 3
  notes: "初稿，需要打磨对话和舞台指示"
```

---

### 2. Characters（角色列表）

**位置**：`script.characters`

**设计原因**：
- 集中管理所有角色，便于查找和修改角色信息
- 使用唯一ID标识角色，支持跨场景引用
- 区分角色重要性（主角、配角、龙套），便于剧本分析
- 记录首次出场，便于角色出场管理

**字段定义**：

```yaml
characters:          # 角色列表（数组）
  - id:              # 角色唯一标识
      type: string
      required: true
      pattern: "char_XXX"
      description: "角色唯一ID，格式：char_001, char_002等"

    name:            # 角色名称
      type: string
      required: true
      description: "角色在剧本中的名称"

    role:            # 角色类型
      type: string
      required: true
      enum: ["主角", "配角", "龙套", "客串"]
      description: "角色重要性分类"

    description:     # 角色描述
      type: string
      required: false
      description: "角色的外貌、性格等特征描述"

    first_appearance: # 首次出场
      type: string
      required: false
      pattern: "scene_XXX"
      description: "角色首次出现的场景ID"

    aliases:         # 别名/昵称
      type: array[string]
      required: false
      description: "角色的其他称呼或昵称"

    age:             # 年龄
      type: integer or string
      required: false
      description: "角色年龄"

    gender:          # 性别
      type: string
      required: false
      description: "角色性别"
```

**示例**：

```yaml
characters:
  - id: "char_001"
    name: "李明"
    role: "主角"
    description: "高中生，阳光开朗，热爱篮球"
    first_appearance: "scene_001"
    aliases: ["小明", "明哥"]
    age: 17
    gender: "男"

  - id: "char_002"
    name: "王芳"
    role: "主角"
    description: "高中生，温柔善良，李明的同班同学"
    first_appearance: "scene_002"
    age: 17
    gender: "女"

  - id: "char_003"
    name: "张老师"
    role: "配角"
    description: "班主任，严厉但关心学生"
    first_appearance: "scene_003"
```

---

### 3. Scenes（场景序列）

**位置**：`script.scenes`

**设计原因**：
- 场景是剧本的核心单元，按时间顺序排列形成故事线
- 分离场景信息（地点、时间）和动作序列，结构清晰
- 支持多种动作类型（对话、动作、转场），覆盖剧本创作需求
- 添加舞台指示（note），增强表演指导

**字段定义**：

```yaml
scenes:              # 场景列表（数组）
  - id:              # 场景唯一标识
      type: string
      required: true
      pattern: "scene_XXX"
      description: "场景唯一ID"

    location:        # 场景地点
      type: string
      required: true
      description: "场景发生的地点，如：教室、操场、家中"

    time:            # 场景时间
      type: string
      required: true
      enum: ["日", "夜", "黄昏", "清晨", "午后", "深夜", "不限"]
      description: "场景的时间设定"

    description:     # 场景描述
      type: string
      required: false
      description: "场景的环境描述、氛围设定"

    chapter:         # 所属章节
      type: integer
      required: false
      description: "该场景对应的原小说章节"

    actions:         # 动作序列（数组）
      type: array
      required: true
      description: "场景内的对话、动作、转场等序列"
      items:
        - type:      # 动作类型
            type: string
            required: true
            enum: ["dialogue", "action", "transition", "direction"]
            description: "动作类型：对话(dialogue)、动作(action)、转场(transition)、舞台指示(direction)"

          character_id: # 角色（仅对话）
            type: string
            required: false (仅dialogue时required)
            description: "说话角色的ID（仅对话类型需要）"

          content:    # 内容
            type: string
            required: true
            description: "对话文本或动作描述"

          note:       # 舞台指示
            type: string
            required: false
            description: "情感、语调、动作细节等舞台指示"

          duration:   # 持续时间（可选）
            type: string
            required: false
            description: "动作持续时间，如：'2秒', '片刻'"
```

**动作类型说明**：

- **dialogue**：角色对话，必须包含`character_id`
- **action**：动作描述，叙述性动作
- **transition**：转场指示，如"切至"、"淡出"
- **direction**：舞台指示，导演备注

**示例**：

```yaml
scenes:
  - id: "scene_001"
    location: "教室"
    time: "日"
    description: "阳光明媚的教室，学生们正在自习"
    chapter: 1
    actions:
      - type: "action"
        content: "李明坐在后排，专注地看着窗外"
        note: "(沉思)"

      - type: "dialogue"
        character_id: "char_001"
        content: "今天的天气真好啊。"
        note: "语气轻松，望向窗外"

      - type: "dialogue"
        character_id: "char_002"
        content: "是啊，放学后我们去操场打篮球吧。"
        note: "热情地"

      - type: "action"
        content: "王芳微笑着看向李明"

      - type: "transition"
        content: "切至：操场"

  - id: "scene_002"
    location: "操场"
    time: "午后"
    description: "夕阳西下，操场上有几个学生在打篮球"
    chapter: 1
    actions:
      - type: "action"
        content: "李明投篮，球进了"
        note: "(兴奋)"

      - type: "dialogue"
        character_id: "char_001"
        content: "漂亮！"
```

---

### 4. Outline（剧情大纲）

**位置**：`script.outline`

**设计原因**：
- 提供整体故事脉络，便于编剧把握剧本结构
- 总结各章节关键事件，便于剧情调整
- 支持剧本分析和修改决策

**字段定义**：

```yaml
outline:             # 剧情大纲（数组）
  - chapter:         # 章节号
      type: integer
      required: true
      description: "对应的章节编号"

    title:           # 章节标题
      type: string
      required: true
      description: "章节标题"

    summary:         # 章节概要
      type: string
      required: true
      description: "章节剧情总结"

    key_events:      # 关键事件
      type: array[string]
      required: false
      description: "章节中的关键事件列表"

    scenes:          # 包含场景
      type: array[string]
      required: false
      description: "该章节包含的场景ID列表"
```

**示例**：

```yaml
outline:
  - chapter: 1
    title: "初遇"
    summary: "李明和王芳在教室相遇，约定放学后打篮球"
    key_events:
      - "李明和王芳初次对话"
      - "约定放学后活动"
    scenes: ["scene_001", "scene_002"]

  - chapter: 2
    title: "篮球场上的友谊"
    summary: "李明和王芳在操场打篮球，友谊加深"
    key_events:
      - "一起打篮球"
      - "分享生活经历"
    scenes: ["scene_003", "scene_004"]

  - chapter: 3
    title: "告别与承诺"
    summary: "学期结束，两人约定保持联系"
    key_events:
      - "期末考试"
      - "交换联系方式"
      - "约定假期见面"
    scenes: ["scene_005"]
```

---

## 完整示例

以下是一个完整的剧本YAML示例：

```yaml
script:
  metadata:
    title: "青春的序曲"
    original_novel: "李明的青春故事"
    author: "张三"
    created_date: "2026-06-05"
    version: "1.0"
    total_chapters: 3
    notes: "初稿，需要打磨对话细节"

  characters:
    - id: "char_001"
      name: "李明"
      role: "主角"
      description: "高中生，阳光开朗，热爱篮球"
      first_appearance: "scene_001"
      age: 17

    - id: "char_002"
      name: "王芳"
      role: "主角"
      description: "高中生，温柔善良，李明的同班同学"
      first_appearance: "scene_001"
      age: 17

    - id: "char_003"
      name: "张老师"
      role: "配角"
      description: "班主任，严厉但关心学生"
      first_appearance: "scene_003"

  scenes:
    - id: "scene_001"
      location: "教室"
      time: "日"
      description: "阳光明媚的教室"
      chapter: 1
      actions:
        - type: "action"
          content: "李明坐在后排，专注地看着窗外"
        - type: "dialogue"
          character_id: "char_001"
          content: "今天的天气真好啊。"
          note: "语气轻松"
        - type: "dialogue"
          character_id: "char_002"
          content: "是啊，放学后去打球吧。"

    - id: "scene_002"
      location: "操场"
      time: "午后"
      chapter: 1
      actions:
        - type: "action"
          content: "两人打篮球"
        - type: "transition"
          content: "淡出"

    - id: "scene_003"
      location: "办公室"
      time: "日"
      chapter: 2
      actions:
        - type: "dialogue"
          character_id: "char_003"
          content: "李明，最近学习要抓紧啊。"

  outline:
    - chapter: 1
      title: "初遇"
      summary: "李明和王芳相遇，约定打篮球"
      scenes: ["scene_001", "scene_002"]
    - chapter: 2
      title: "篮球场上的友谊"
      summary: "友谊加深"
      scenes: ["scene_003"]
```

---

## Schema扩展性说明

### 如何扩展Schema？

**添加新字段**：

可以在各模块中添加新字段，例如：

```yaml
metadata:
  genre: "青春校园"      # 新增：剧本类型
  rating: "PG-13"        # 新增：观众分级

characters:
  - id: "char_001"
    occupation: "学生"   # 新增：职业
```

**添加新动作类型**：

扩展actions的type字段：

```yaml
actions:
  - type: "music"        # 新增：音乐指示
    content: "播放轻快背景音乐"
```

### 兼容性设计

**转换为其他格式**：

- **JSON**：YAML可直接转为JSON，兼容性100%
- **XML**：可通过转换脚本转为XML格式
- **Final Draft格式**：可导出为.fdx文件（需额外工具）
- **PDF剧本**：可转换为标准剧本PDF格式

**数据验证**：

使用Pydantic或JSON Schema进行验证：

```python
from pydantic import BaseModel
from typing import List, Optional

class Metadata(BaseModel):
    title: str
    original_novel: str
    author: str
    created_date: str
    version: Optional[str] = "1.0"
```

---

## 使用建议

### 对于编剧

1. **优先编辑metadata**：完善标题、作者、备注等信息
2. **调整角色描述**：根据演员特点修改角色描述
3. **打磨对话**：重点优化dialogue类型的内容和note
4. **调整场景顺序**：根据拍摄需求调整scenes顺序

### 对于AI工具开发者

1. **严格遵循Schema**：确保输出符合Schema定义
2. **使用ID引用**：角色和场景使用唯一ID
3. **填充所有required字段**：保证数据完整性
4. **提供合理的默认值**：对于optional字段提供默认值

---

## Schema版本管理

当前版本：**v1.0**

未来版本可能扩展：
- v1.1：增加道具、服装设计字段
- v1.2：增加音效、特效指示
- v2.0：支持多语言、多版本剧本

---

## 参考资源

- [YAML官方规范](https://yaml.org/spec/)
- [剧本写作标准](https://www.finaldraft.com/)
- [Pydantic文档](https://docs.pydantic.dev/)

---

**文档作者**：暑训营项目 - AI小说转剧本工具
**最后更新**：2026-06-05