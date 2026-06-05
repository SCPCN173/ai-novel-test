"""
YAML Schema定义模块 - 使用Pydantic定义剧本结构
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class Metadata(BaseModel):
    """剧本元数据"""

    title: str = Field(..., description="剧本标题")
    original_novel: str = Field(..., description="原小说名称")
    author: str = Field(..., description="作者")
    created_date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="创建日期"
    )
    version: Optional[str] = Field("1.0", description="版本号")
    total_chapters: Optional[int] = Field(None, description="总章节数")
    notes: Optional[str] = Field(None, description="备注")


class Character(BaseModel):
    """角色信息"""

    id: str = Field(..., description="角色唯一ID", regex=r"^char_\d{3}$")
    name: str = Field(..., description="角色名称")
    role: str = Field(..., description="角色类型")
    description: Optional[str] = Field(None, description="角色描述")
    first_appearance: Optional[str] = Field(None, description="首次出场场景ID")
    aliases: Optional[List[str]] = Field(None, description="别名列表")
    age: Optional[int] = Field(None, description="年龄")
    gender: Optional[str] = Field(None, description="性别")

    @validator("role")
    def validate_role(cls, v):
        """验证角色类型"""
        valid_roles = ["主角", "配角", "龙套", "客串"]
        if v not in valid_roles:
            raise ValueError(f"角色类型必须是: {valid_roles}")
        return v


class Action(BaseModel):
    """场景中的动作"""

    type: str = Field(..., description="动作类型")
    content: str = Field(..., description="动作内容")
    character_id: Optional[str] = Field(None, description="角色ID（对话时）")
    note: Optional[str] = Field(None, description="舞台指示")
    duration: Optional[str] = Field(None, description="持续时间")

    @validator("type")
    def validate_type(cls, v):
        """验证动作类型"""
        valid_types = ["dialogue", "action", "transition", "direction"]
        if v not in valid_types:
            raise ValueError(f"动作类型必须是: {valid_types}")
        return v

    @validator("character_id", always=True)
    def validate_character_id(cls, v, values):
        """对话类型必须包含角色ID"""
        if values.get("type") == "dialogue" and not v:
            raise ValueError("对话类型必须包含character_id")
        return v


class Scene(BaseModel):
    """场景"""

    id: str = Field(..., description="场景唯一ID", regex=r"^scene_\d{3}$")
    location: str = Field(..., description="场景地点")
    time: str = Field(..., description="场景时间")
    description: Optional[str] = Field(None, description="场景描述")
    chapter: Optional[int] = Field(None, description="所属章节")
    actions: List[Action] = Field(..., description="动作序列")

    @validator("time")
    def validate_time(cls, v):
        """验证时间类型"""
        valid_times = ["日", "夜", "黄昏", "清晨", "午后", "深夜", "不限"]
        if v not in valid_times:
            raise ValueError(f"时间必须是: {valid_times}")
        return v


class Outline(BaseModel):
    """剧情大纲"""

    chapter: int = Field(..., description="章节号")
    title: str = Field(..., description="章节标题")
    summary: str = Field(..., description="章节概要")
    key_events: Optional[List[str]] = Field(None, description="关键事件")
    scenes: Optional[List[str]] = Field(None, description="场景ID列表")


class Script(BaseModel):
    """完整剧本结构"""

    metadata: Metadata = Field(..., description="元数据")
    characters: List[Character] = Field(..., description="角色列表")
    scenes: List[Scene] = Field(..., description="场景列表")
    outline: Optional[List[Outline]] = Field(None, description="剧情大纲")


def validate_script_yaml(yaml_data: Dict[str, Any]) -> Script:
    """
    验证剧本YAML数据

    Args:
        yaml_data: YAML数据字典

    Returns:
        验证后的Script对象

    Raises:
        ValidationError: 验证失败
    """
    script = Script(**yaml_data.get("script", {}))
    return script


def create_empty_script(
    title: str,
    original_novel: str,
    author: str
) -> Dict[str, Any]:
    """
    创建空的剧本模板

    Args:
        title: 剧本标题
        original_novel: 原小说名称
        author: 作者

    Returns:
        空剧本YAML数据
    """
    return {
        "script": {
            "metadata": {
                "title": title,
                "original_novel": original_novel,
                "author": author,
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "version": "1.0",
            },
            "characters": [],
            "scenes": [],
            "outline": [],
        }
    }


def merge_scripts(scripts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    合并多个剧本（用于分章节生成后合并）

    Args:
        scripts: 剧本列表

    Returns:
        合并后的剧本
    """
    if not scripts:
        return create_empty_script("未命名剧本", "未知", "未知")

    # 使用第一个剧本的元数据
    merged = scripts[0]

    # 合并角色（去重）
    all_characters = {}
    for script in scripts:
        for char in script["script"]["characters"]:
            char_id = char["id"]
            if char_id not in all_characters:
                all_characters[char_id] = char

    merged["script"]["characters"] = list(all_characters.values())

    # 合并场景（按顺序）
    all_scenes = []
    scene_counter = 1
    for script in scripts:
        for scene in script["script"]["scenes"]:
            # 更新场景ID
            scene["id"] = f"scene_{str(scene_counter).zfill(3)}"
            all_scenes.append(scene)
            scene_counter += 1

    merged["script"]["scenes"] = all_scenes

    # 合并大纲
    merged["script"]["outline"] = []
    for script in scripts:
        for outline in script["script"]["outline"]:
            merged["script"]["outline"].append(outline)

    # 更新元数据
    merged["script"]["metadata"]["total_chapters"] = len(merged["script"]["outline"])

    return merged


if __name__ == "__main__":
    # 测试Schema验证
    test_yaml = {
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
                    "description": "高中生",
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
                            "note": "热情地",
                        }
                    ],
                }
            ],
        }
    }

    script = validate_script_yaml(test_yaml)
    print("Schema验证成功")
    print(f"角色数: {len(script.characters)}")
    print(f"场景数: {len(script.scenes)}")