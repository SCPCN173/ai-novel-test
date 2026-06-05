"""
单元测试 - 剧本生成模块
"""

import pytest
import yaml
from pathlib import Path
from src.yaml_schema import (
    Metadata,
    Character,
    Action,
    Scene,
    Outline,
    Script,
    validate_script_yaml,
    create_empty_script,
    merge_scripts,
)
from src.script_generator import ScriptGenerator


class TestYAMLSchema:
    """YAML Schema验证测试"""

    def test_metadata_validation(self):
        """测试元数据验证"""
        metadata = Metadata(
            title="测试剧本",
            original_novel="测试小说",
            author="测试作者"
        )
        assert metadata.title == "测试剧本"

    def test_character_validation(self):
        """测试角色验证"""
        character = Character(
            id="char_001",
            name="李明",
            role="主角",
            description="高中生"
        )
        assert character.id == "char_001"
        assert character.role == "主角"

    def test_character_role_validation(self):
        """测试角色类型验证"""
        with pytest.raises(ValueError):
            Character(
                id="char_001",
                name="李明",
                role="未知角色类型",  # 错误的角色类型
            )

    def test_action_validation(self):
        """测试动作验证"""
        action = Action(
            type="dialogue",
            content="你好",
            character_id="char_001"
        )
        assert action.type == "dialogue"

    def test_action_type_validation(self):
        """测试动作类型验证"""
        with pytest.raises(ValueError):
            Action(
                type="unknown_type",  # 错误的动作类型
                content="内容"
            )

    def test_dialogue_requires_character(self):
        """测试对话必须包含角色ID"""
        with pytest.raises(ValueError):
            Action(
                type="dialogue",
                content="对话内容",
                # 缺少character_id
            )

    def test_scene_validation(self):
        """测试场景验证"""
        scene = Scene(
            id="scene_001",
            location="教室",
            time="日",
            actions=[
                Action(
                    type="dialogue",
                    content="你好",
                    character_id="char_001"
                )
            ]
        )
        assert scene.id == "scene_001"

    def test_time_validation(self):
        """测试时间类型验证"""
        with pytest.raises(ValueError):
            Scene(
                id="scene_001",
                location="教室",
                time="未知时间",  # 错误的时间类型
                actions=[]
            )

    def test_full_script_validation(self):
        """测试完整剧本验证"""
        script_data = {
            "script": {
                "metadata": {
                    "title": "测试剧本",
                    "original_novel": "测试小说",
                    "author": "测试作者",
                },
                "characters": [
                    {
                        "id": "char_001",
                        "name": "李明",
                        "role": "主角",
                    }
                ],
                "scenes": [
                    {
                        "id": "scene_001",
                        "location": "教室",
                        "time": "日",
                        "actions": [
                            {
                                "type": "dialogue",
                                "character_id": "char_001",
                                "content": "你好",
                            }
                        ],
                    }
                ],
            }
        }

        script = validate_script_yaml(script_data)
        assert script.metadata.title == "测试剧本"
        assert len(script.characters) == 1
        assert len(script.scenes) == 1


class TestScriptMerge:
    """剧本合并测试"""

    def test_create_empty_script(self):
        """测试创建空剧本"""
        empty_script = create_empty_script("标题", "小说", "作者")
        assert empty_script["script"]["metadata"]["title"] == "标题"
        assert len(empty_script["script"]["characters"]) == 0
        assert len(empty_script["script"]["scenes"]) == 0

    def test_merge_scripts(self):
        """测试剧本合并"""
        script1 = {
            "script": {
                "metadata": {
                    "title": "剧本1",
                    "original_novel": "小说1",
                    "author": "作者1",
                },
                "characters": [
                    {"id": "char_001", "name": "李明", "role": "主角"}
                ],
                "scenes": [
                    {
                        "id": "scene_001",
                        "location": "教室",
                        "time": "日",
                        "actions": [
                            {"type": "dialogue", "character_id": "char_001", "content": "你好"}
                        ],
                    }
                ],
                "outline": [
                    {"chapter": 1, "title": "第一章", "summary": "概要"}
                ],
            }
        }

        script2 = {
            "script": {
                "metadata": {
                    "title": "剧本2",
                    "original_novel": "小说2",
                    "author": "作者2",
                },
                "characters": [
                    {"id": "char_002", "name": "王芳", "role": "配角"}
                ],
                "scenes": [
                    {
                        "id": "scene_002",
                        "location": "操场",
                        "time": "午后",
                        "actions": [
                            {"type": "action", "content": "打篮球"}
                        ],
                    }
                ],
                "outline": [
                    {"chapter": 2, "title": "第二章", "summary": "概要2"}
                ],
            }
        }

        merged = merge_scripts([script1, script2])

        # 检查合并结果
        assert len(merged["script"]["characters"]) == 2
        assert len(merged["script"]["scenes"]) == 2
        assert len(merged["script"]["outline"]) == 2

        # 检查场景ID是否重新编号
        assert merged["script"]["scenes"][0]["id"] == "scene_001"
        assert merged["script"]["scenes"][1]["id"] == "scene_002"


class TestScriptGenerator:
    """剧本生成器测试"""

    def test_generator_initialization(self):
        """测试生成器初始化"""
        # 注意：这个测试需要配置文件存在
        config_path = Path("config.yaml")
        if config_path.exists():
            generator = ScriptGenerator()
            assert generator.ai_client is not None
        else:
            pytest.skip("配置文件不存在")

    def test_validate_yaml_file(self):
        """测试YAML文件验证"""
        # 创建一个测试YAML文件
        test_yaml_path = Path("tests/test_data/test_script.yaml")
        test_yaml_path.parent.mkdir(parents=True, exist_ok=True)

        test_yaml_content = """
script:
  metadata:
    title: "测试剧本"
    original_novel: "测试小说"
    author: "测试作者"
  characters:
    - id: "char_001"
      name: "李明"
      role: "主角"
  scenes:
    - id: "scene_001"
      location: "教室"
      time: "日"
      actions:
        - type: "dialogue"
          character_id: "char_001"
          content: "你好"
"""

        with open(test_yaml_path, "w", encoding="utf-8") as f:
            f.write(test_yaml_content)

        generator = ScriptGenerator()
        result = generator.validate_only(str(test_yaml_path))
        assert result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])