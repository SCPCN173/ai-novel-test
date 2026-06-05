"""
工具函数模块
"""

import re
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path


def clean_text(text: str) -> str:
    """
    清理文本格式

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    # 标准化引号（将各种引号统一为标准引号）
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("'", "'").replace("'", "'")

    # 移除多余空行（保留段落分隔）
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 移除行首行尾空格
    text = '\n'.join(line.strip() for line in text.split('\n'))

    return text.strip()


def detect_chapter_pattern(text: str) -> Optional[str]:
    """
    检测章节标题的模式

    Args:
        text: 小说文本

    Returns:
        章节模式字符串（如："第X章"）或None
    """
    # 常见章节模式
    patterns = [
        r'第[一二三四五六七八九十百零\d]+章',  # 中文：第一章、第十章等
        r'Chapter\s+\d+',  # 英文：Chapter 1, Chapter 10等
        r'CHAPTER\s+\d+',  # 英文大写
        r'第[一二三四五六七八九十百零\d]+节',  # 节
        r'Part\s+\d+',  # Part 1
        r'卷[一二三四五六七八九十百零\d]+',  # 卷一、卷二
    ]

    for pattern in patterns:
        if re.search(pattern, text):
            return pattern

    return None


def extract_chapter_title(text: str) -> str:
    """
    从章节行提取标题

    Args:
        text: 章节行文本（如："第一章 初遇"）

    Returns:
        章节标题
    """
    # 移除章节编号，保留标题文字
    patterns = [
        r'第[一二三四五六七八九十百零\d]+章[：:\s]*(.+)',
        r'Chapter\s+\d+[：:\s]*(.+)',
        r'第[一二三四五六七八九十百零\d]+节[：:\s]*(.+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    return text.strip()


def chinese_num_to_int(chinese_num: str) -> int:
    """
    中文数字转阿拉伯数字

    Args:
        chinese_num: 中文数字（如："一"、"十"）

    Returns:
        阿拉伯数字
    """
    mapping = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '百': 100, '千': 1000
    }

    # 简单情况：单个数字
    if chinese_num in mapping:
        return mapping[chinese_num]

    # 复杂情况：组合数字（如："二十一"、"一百二十"）
    result = 0
    temp = 0
    for char in chinese_num:
        if char not in mapping:
            continue
        num = mapping[char]
        if num >= 10:
            if temp == 0:
                temp = 1
            result += temp * num
            temp = 0
        else:
            temp = num

    result += temp
    return result


def extract_dialogue(text: str) -> List[Dict[str, str]]:
    """
    提取对话片段

    Args:
        text: 文本段落

    Returns:
        对话列表 [{"speaker": "说话人", "content": "对话内容"}]
    """
    dialogues = []

    # 匹配引号对话（支持中文和英文引号）
    patterns = [
        r'([^"""'']+)[：:]\s*["'"'](.+?)["'"']',  # 名字：对话
        r'["'"'](.+?)["'"']\s*[（(]([^）)]+)[）)]',  # "对话"（名字）
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            if len(match.groups()) == 2:
                dialogues.append({
                    "speaker": match.group(1).strip(),
                    "content": match.group(2).strip()
                })

    return dialogues


def split_into_paragraphs(text: str) -> List[str]:
    """
    将文本分割为段落

    Args:
        text: 文本

    Returns:
        段落列表
    """
    # 按空行分割
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def extract_characters_from_text(text: str) -> List[str]:
    """
    从文本提取角色名称

    Args:
        text: 小说文本

    Returns:
        角色名称列表
    """
    characters = set()

    # 方法1：从对话提取
    dialogues = extract_dialogue(text)
    for d in dialogues:
        if d["speaker"]:
            characters.add(d["speaker"])

    # 方法2：从常见格式提取（如："李明说"、"王芳笑道"）
    patterns = [
        r'([^\s，。！？"""']+)(说|道|问|答|喊|叫|笑|哭)',
        r'([^\s，。！？"""']+)[的]?(心中|心里|想)',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            name = match.group(1).strip()
            # 过滤掉常见的非角色词
            if name not in ["他", "她", "它", "我", "你", "大家", "众人", "人们"]:
                characters.add(name)

    return sorted(list(characters))


def save_yaml(data: Dict, output_path: str):
    """
    保存YAML文件

    Args:
        data: 数据字典
        output_path: 输出路径
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def load_yaml(yaml_path: str) -> Dict:
    """
    加载YAML文件

    Args:
        yaml_path: YAML文件路径

    Returns:
        数据字典
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def format_scene_id(index: int) -> str:
    """格式化场景ID"""
    return f"scene_{str(index).zfill(3)}"


def format_character_id(index: int) -> str:
    """格式化角色ID"""
    return f"char_{str(index).zfill(3)}"


def get_timestamp() -> str:
    """获取当前时间戳（YYYY-MM-DD格式）"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    截断文本（用于显示）

    Args:
        text: 文本
        max_length: 最大长度

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."