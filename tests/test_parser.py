"""
单元测试 - 小说解析模块
"""

import pytest
from src.novel_parser import NovelParser, NovelParserError, parse_from_file
from src.utils import detect_chapter_pattern, extract_chapter_title


class TestNovelParser:
    """小说解析器测试"""

    def setup_method(self):
        """测试前准备"""
        self.parser = NovelParser(min_chapters=3)

    def test_detect_chapter_pattern(self):
        """测试章节模式检测"""
        text1 = "第一章 初遇\n内容..."
        assert detect_chapter_pattern(text1) is not None

        text2 = "Chapter 1\n内容..."
        assert detect_chapter_pattern(text2) is not None

        text3 = "这是普通文本"
        assert detect_chapter_pattern(text3) is None

    def test_extract_chapter_title(self):
        """测试章节标题提取"""
        assert extract_chapter_title("第一章 初遇") == "初遇"
        assert extract_chapter_title("Chapter 1 The Beginning") == "The Beginning"

    def test_parse_simple_novel(self):
        """测试简单小说解析"""
        test_novel = """
第一章 测试标题

这是第一章的内容。

第二章 第二标题

这是第二章的内容。

第三章 第三标题

这是第三章的内容。
"""
        result = self.parser.parse(test_novel, "测试小说")

        assert result["title"] == "测试小说"
        assert result["total_chapters"] == 3
        assert len(result["chapters"]) == 3
        assert result["chapters"][0]["number"] == 1
        assert result["chapters"][0]["title"] == "测试标题"

    def test_parse_novel_with_characters(self):
        """测试包含角色的小说解析"""
        test_novel = """
第一章 对话

李明说："你好，王芳。"
王芳回答："你好，李明。"

第二章 继续对话

李明问："今天天气如何？"
王芳笑道："天气很好。"

第三章 结束

张老师说："同学们下课了。"
李明说："再见，王芳。"
"""
        result = self.parser.parse(test_novel, "测试小说")

        assert result["total_chapters"] == 3
        assert len(result["all_characters"]) >= 2
        assert "李明" in result["all_characters"]
        assert "王芳" in result["all_characters"]

    def test_min_chapters_requirement(self):
        """测试最少章节要求"""
        short_novel = """
第一章 第一章

内容

第二章 第二章

内容
"""
        with pytest.raises(NovelParserError):
            self.parser.parse(short_novel, "短小说")

    def test_no_chapter_pattern(self):
        """测试无章节模式的情况"""
        text_no_pattern = "这是没有章节标题的普通文本内容。"
        with pytest.raises(NovelParserError):
            self.parser.parse(text_no_pattern)

    def test_word_count_calculation(self):
        """测试字数计算"""
        test_novel = """
第一章 测试

这是测试内容，有十个字。

第二章 测试2

内容也很少。

第三章 测试3

结束内容。
"""
        result = self.parser.parse(test_novel)
        assert result["chapters"][0]["word_count"] > 0

    def test_get_summary(self):
        """测试摘要生成"""
        test_novel = """
第一章 标题一

内容一

第二章 标题二

内容二

第三章 标题三

内容三
"""
        result = self.parser.parse(test_novel, "测试小说")
        summary = self.parser.get_summary(result)

        assert "测试小说" in summary
        assert "总章节数" in summary
        assert "第1章" in summary


class TestChapterDetection:
    """章节检测测试"""

    def test_chinese_chapters(self):
        """测试中文章节识别"""
        text = "第一章\n第二章\n第三章\n第十章\n第二十一章"
        pattern = detect_chapter_pattern(text)
        assert pattern is not None

    def test_english_chapters(self):
        """测试英文章节识别"""
        text = "Chapter 1\nChapter 2\nChapter 10"
        pattern = detect_chapter_pattern(text)
        assert pattern is not None

    def test_mixed_content(self):
        """测试混合内容"""
        text = """
第一章 开始

这是内容。

中间有一些叙述。

第二章 继续

更多内容。

第三章 结束

最后的内容。
"""
        result = NovelParser().parse(text)
        assert result["total_chapters"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])