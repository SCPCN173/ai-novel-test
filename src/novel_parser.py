"""
小说解析模块 - 将原始小说文本解析为结构化数据
"""

import re
from typing import Dict, List, Any, Optional
from .utils import (
    clean_text,
    detect_chapter_pattern,
    extract_chapter_title,
    chinese_num_to_int,
    extract_characters_from_text,
    split_into_paragraphs,
    truncate_text,
)


class NovelParserError(Exception):
    """小说解析错误"""
    pass


class NovelParser:
    """
    小说解析器

    将小说文本解析为结构化数据，包括章节、角色、段落等
    """

    def __init__(self, min_chapters: int = 3):
        """
        初始化解析器

        Args:
            min_chapters: 最少章节要求（默认：3）
        """
        self.min_chapters = min_chapters

    def parse(self, novel_text: str, novel_title: Optional[str] = None) -> Dict[str, Any]:
        """
        解析小说文本

        Args:
            novel_text: 小说文本
            novel_title: 小说标题（可选）

        Returns:
            结构化数据：
            {
                "title": "小说标题",
                "chapters": [
                    {
                        "number": 1,
                        "title": "章节标题",
                        "content": "章节内容",
                        "characters": ["角色列表"],
                        "paragraphs": ["段落列表"],
                        "word_count": 字数
                    }
                ],
                "total_chapters": 章节总数,
                "all_characters": ["所有角色列表"]
            }
        """
        # 清理文本
        clean_novel_text = clean_text(novel_text)

        # 检测章节模式
        chapter_pattern = detect_chapter_pattern(clean_novel_text)
        if not chapter_pattern:
            raise NovelParserError("无法识别章节标题模式")

        # 分割章节
        chapters = self._split_chapters(clean_novel_text, chapter_pattern)

        # 检查章节数量
        if len(chapters) < self.min_chapters:
            raise NovelParserError(
                f"章节数量不足：需要至少{self.min_chapters}章，当前只有{len(chapters)}章"
            )

        # 解析每个章节
        parsed_chapters = []
        all_characters = set()

        for chapter_text in chapters:
            parsed_chapter = self._parse_chapter(chapter_text)
            parsed_chapters.append(parsed_chapter)
            all_characters.update(parsed_chapter["characters"])

        # 构建结果
        result = {
            "title": novel_title or "未命名小说",
            "chapters": parsed_chapters,
            "total_chapters": len(parsed_chapters),
            "all_characters": sorted(list(all_characters)),
        }

        return result

    def _split_chapters(self, text: str, pattern: str) -> List[str]:
        """
        根据章节标题模式分割章节

        Args:
            text: 文本
            pattern: 章节模式

        Returns:
            章节文本列表
        """
        # 找到所有章节标题位置
        chapter_matches = list(re.finditer(pattern, text))

        if not chapter_matches:
            return [text]

        # 按章节标题分割
        chapters = []
        for i, match in enumerate(chapter_matches):
            start = match.start()

            # 结束位置是下一个章节标题的开始，或者文本末尾
            if i < len(chapter_matches) - 1:
                end = chapter_matches[i + 1].start()
            else:
                end = len(text)

            chapter_text = text[start:end].strip()
            if chapter_text:
                chapters.append(chapter_text)

        return chapters

    def _parse_chapter(self, chapter_text: str) -> Dict[str, Any]:
        """
        解析单个章节

        Args:
            chapter_text: 章节文本

        Returns:
            章节结构数据
        """
        # 提取章节编号和标题
        lines = chapter_text.split('\n')
        first_line = lines[0]

        # 提取章节编号
        chapter_number = self._extract_chapter_number(first_line)

        # 提取章节标题
        chapter_title = extract_chapter_title(first_line)

        # 提取章节内容（去掉标题行）
        content_lines = lines[1:] if len(lines) > 1 else []
        content = '\n'.join(content_lines).strip()

        # 分割段落
        paragraphs = split_into_paragraphs(content)

        # 提取角色
        characters = extract_characters_from_text(content)

        # 计算字数
        word_count = len(content.replace('\n', '').replace(' ', ''))

        return {
            "number": chapter_number,
            "title": chapter_title,
            "content": content,
            "characters": characters,
            "paragraphs": paragraphs,
            "word_count": word_count,
        }

    def _extract_chapter_number(self, title_line: str) -> int:
        """
        从章节标题提取章节编号

        Args:
            title_line: 章节标题行

        Returns:
            章节编号
        """
        # 匹配章节编号模式
        patterns = [
            r'第([一二三四五六七八九十百零\d]+)章',
            r'Chapter\s+(\d+)',
            r'第([一二三四五六七八九十百零\d]+)节',
        ]

        for pattern in patterns:
            match = re.search(pattern, title_line)
            if match:
                num_str = match.group(1)
                # 如果是中文数字，转换为阿拉伯数字
                if re.match(r'[一二三四五六七八九十百零]+', num_str):
                    return chinese_num_to_int(num_str)
                else:
                    return int(num_str)

        return 0

    def get_summary(self, parsed_data: Dict) -> str:
        """
        获取解析结果的摘要

        Args:
            parsed_data: 解析后的数据

        Returns:
            摘要文本
        """
        summary_lines = [
            f"小说标题：{parsed_data['title']}",
            f"总章节数：{parsed_data['total_chapters']}",
            f"总角色数：{len(parsed_data['all_characters'])}",
            "",
            "章节概览：",
        ]

        for chapter in parsed_data['chapters']:
            summary_lines.append(
                f"  第{chapter['number']}章 {chapter['title']} "
                f"({chapter['word_count']}字, {len(chapter['characters'])}个角色)"
            )

        summary_lines.extend([
            "",
            f"主要角色：{', '.join(parsed_data['all_characters'][:10])}",
        ])

        return '\n'.join(summary_lines)


def parse_from_file(file_path: str, min_chapters: int = 3) -> Dict[str, Any]:
    """
    从文件解析小说

    Args:
        file_path: 小说文件路径
        min_chapters: 最少章节要求

    Returns:
        结构化数据
    """
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        raise NovelParserError(f"文件不存在: {file_path}")

    # 读取文件
    with open(path, "r", encoding="utf-8") as f:
        novel_text = f.read()

    # 从文件名提取标题
    novel_title = path.stem

    # 解析
    parser = NovelParser(min_chapters=min_chapters)
    return parser.parse(novel_text, novel_title)


if __name__ == "__main__":
    # 测试解析器
    test_novel = """
第一章 初遇

阳光明媚的教室里，李明坐在后排，专注地看着窗外。

李明说："今天的天气真好啊。"

王芳笑道："是啊，放学后我们去操场打篮球吧。"

李明点点头，心中充满期待。

第二章 篮球场上的友谊

操场上，夕阳西下，几个学生在打篮球。

李明投篮，球进了。

王芳说："漂亮！你的篮球技术真好。"

李明笑着说："谢谢，我经常练习。"

第三章 告别与承诺

学期即将结束，教室里弥漫着离别的气氛。

张老师说："同学们，学期结束了，希望大家假期愉快。"

李明对王芳说："假期我们保持联系。"

王芳点头："一定，我们下次再一起打篮球。"
"""

    parser = NovelParser(min_chapters=3)
    result = parser.parse(test_novel, "测试小说")
    print(parser.get_summary(result))