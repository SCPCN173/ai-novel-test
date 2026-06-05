"""
剧本生成模块 - 调用AI模型将小说转换为剧本YAML
"""

import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from .ai_client import AIClient, AIClientError
from .yaml_schema import validate_script_yaml, merge_scripts, create_empty_script
from .utils import (
    format_scene_id,
    format_character_id,
    get_timestamp,
    save_yaml,
)


class ScriptGeneratorError(Exception):
    """剧本生成错误"""
    pass


class ScriptGenerator:
    """
    剧本生成器

    将解析后的小说数据转换为YAML格式剧本
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化剧本生成器

        Args:
            config_path: 配置文件路径
        """
        self.ai_client = AIClient(config_path)
        self.config = self.ai_client.config

    def generate(
        self,
        parsed_novel: Dict[str, Any],
        output_path: Optional[str] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        生成剧本

        Args:
            parsed_novel: 解析后的小说数据
            output_path: 输出路径（可选）
            verbose: 详细输出

        Returns:
            剧本YAML数据
        """
        # 准备基本信息
        title = parsed_novel["title"]
        total_chapters = parsed_novel["total_chapters"]

        if verbose:
            print(f"开始生成剧本: {title}")
            print(f"总章节数: {total_chapters}")

        # 分章节生成剧本
        chapter_scripts = []
        for i, chapter in enumerate(parsed_novel["chapters"]):
            if verbose:
                print(f"\n处理第{chapter['number']}章: {chapter['title']}...")

            chapter_script = self._generate_chapter_script(
                chapter,
                title,
                i + 1,
                verbose
            )
            chapter_scripts.append(chapter_script)

        # 合并所有章节剧本
        final_script = merge_scripts(chapter_scripts)

        # 添加完整元数据
        final_script["script"]["metadata"]["title"] = title
        final_script["script"]["metadata"]["original_novel"] = title
        final_script["script"]["metadata"]["author"] = "AI生成"
        final_script["script"]["metadata"]["created_date"] = get_timestamp()
        final_script["script"]["metadata"]["total_chapters"] = total_chapters

        # 验证剧本
        try:
            validate_script_yaml(final_script)
            if verbose:
                print("\n✓ 剧本Schema验证通过")
        except Exception as e:
            if verbose:
                print(f"\n✗ 剧本验证失败: {str(e)}")

        # 保存输出
        if output_path:
            save_yaml(final_script, output_path)
            if verbose:
                print(f"\n✓ 剧本已保存: {output_path}")

        return final_script

    def _generate_chapter_script(
        self,
        chapter: Dict[str, Any],
        novel_title: str,
        chapter_index: int,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        生成单个章节的剧本

        Args:
            chapter: 章节数据
            novel_title: 小说标题
            chapter_index: 章节索引
            verbose: 详细输出

        Returns:
            章节剧本数据
        """
        # 构建提示词
        prompt = self._build_prompt(chapter, novel_title)

        # 调用AI生成
        try:
            response = self.ai_client.chat(
                prompt,
                system_prompt="你是一个专业的剧本改编师。",
                retry_count=3,
                retry_delay=2
            )

            if verbose:
                print(f"  AI生成完成 ({len(response)} 字符)")

            # 解析AI返回的YAML
            chapter_script = self._parse_ai_response(response, chapter, chapter_index)

            return chapter_script

        except AIClientError as e:
            raise ScriptGeneratorError(f"AI生成失败: {str(e)}")

    def _build_prompt(self, chapter: Dict[str, Any], novel_title: str) -> str:
        """
        构建提示词

        Args:
            chapter: 章节数据
            novel_title: 小说标题

        Returns:
            提示词文本
        """
        # 从配置读取Prompt模板（如果存在）
        config = self.ai_client.config
        prompt_template = config.get("script_generation", {}).get(
            "prompt_template",
            self._get_default_prompt_template()
        )

        # 准备章节内容
        chapter_content = f"""
第{chapter['number']}章 {chapter['title']}

{chapter['content']}
"""

        # 替换模板变量
        prompt = prompt_template.replace("{chapter_content}", chapter_content)

        return prompt

    def _get_default_prompt_template(self) -> str:
        """获取默认提示词模板"""
        return """
你是一个专业的剧本改编师。请将以下小说章节转换为YAML格式的剧本。

要求：
1. 识别所有角色并分配唯一ID（格式：char_XXX，如char_001, char_002）
2. 将叙述文本转换为场景描述和动作指示
3. 提取对话并标注说话角色
4. 添加必要的舞台指示和情感描述
5. 保持故事节奏和情感张力
6. 场景ID格式：scene_XXX（如scene_001, scene_002）
7. 每个场景包含地点、时间、描述和动作序列
8. 动作类型：dialogue（对话）、action（动作）、transition（转场）、direction（舞台指示）
9. 对话必须包含character_id字段

章节内容：
{chapter_content}

请严格按照以下YAML Schema输出剧本（不要添加额外解释文字，只输出YAML）：

```yaml
script:
  metadata:
    title: "剧本标题"
    original_novel: "原小说名"
    chapter: 章节号
  characters:
    - id: "char_001"
      name: "角色名"
      role: "主角"  # 或"配角"、"龙套"、"客串"
      description: "简短描述"
  scenes:
    - id: "scene_001"
      location: "场景地点"
      time: "日"  # 或"夜"、"黄昏"、"清晨"、"午后"、"深夜"、"不限"
      description: "场景描述"
      actions:
        - type: "dialogue"
          character_id: "char_001"
          content: "对话内容"
          note: "情感或动作指示"
        - type: "action"
          content: "动作描述"
        - type: "transition"
          content: "转场指示"
  outline:
    - chapter: 章节号
      title: "章节标题"
      summary: "章节概要"
      key_events: ["关键事件1", "关键事件2"]
```
"""

    def _parse_ai_response(
        self,
        response: str,
        chapter: Dict[str, Any],
        chapter_index: int,
    ) -> Dict[str, Any]:
        """
        解析AI返回的YAML

        Args:
            response: AI返回文本
            chapter: 章节数据
            chapter_index: 章节索引

        Returns:
            剧本数据
        """
        # 提取YAML内容（去除代码块标记）
        yaml_content = response
        if "```yaml" in response:
            yaml_content = response.split("```yaml")[1].split("```")[0]
        elif "```" in response:
            yaml_content = response.split("```")[1].split("```")[0]

        # 解析YAML
        try:
            script_data = yaml.safe_load(yaml_content.strip())
            return script_data
        except yaml.YAMLError as e:
            raise ScriptGeneratorError(f"YAML解析失败: {str(e)}")

    def validate_only(self, yaml_path: str) -> bool:
        """
        仅验证YAML文件（不生成）

        Args:
            yaml_path: YAML文件路径

        Returns:
            验证是否通过
        """
        from .utils import load_yaml

        yaml_data = load_yaml(yaml_path)

        try:
            validate_script_yaml(yaml_data)
            return True
        except Exception:
            return False


def generate_script_from_file(
    novel_path: str,
    output_path: str,
    config_path: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    从小说文件生成剧本

    Args:
        novel_path: 小说文件路径
        output_path: 输出剧本路径
        config_path: 配置文件路径
        verbose: 详细输出

    Returns:
        剧本数据
    """
    from .novel_parser import parse_from_file

    # 解析小说
    parsed_novel = parse_from_file(novel_path, min_chapters=3)

    if verbose:
        from .novel_parser import NovelParser
        parser = NovelParser()
        print(parser.get_summary(parsed_novel))

    # 生成剧本
    generator = ScriptGenerator(config_path)
    return generator.generate(parsed_novel, output_path, verbose)


if __name__ == "__main__":
    # 测试剧本生成
    test_novel_path = "examples/sample_novel.txt"

    if Path(test_novel_path).exists():
        print("开始测试剧本生成...")
        result = generate_script_from_file(
            test_novel_path,
            "output/test_script.yaml",
            verbose=True
        )
        print(f"\n生成完成，共{len(result['script']['scenes'])}个场景")
    else:
        print(f"测试文件不存在: {test_novel_path}")