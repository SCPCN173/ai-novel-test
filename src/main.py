"""
CLI入口模块 - 命令行界面
"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .novel_parser import NovelParser, NovelParserError, parse_from_file
from .script_generator import ScriptGenerator, ScriptGeneratorError, generate_script_from_file
from .utils import load_yaml, save_yaml, truncate_text


console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    AI小说转剧本工具

    将小说文本自动转换为结构化剧本（YAML格式）
    """
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), default='output/script.yaml',
              help='输出剧本文件路径（默认：output/script.yaml）')
@click.option('--config', type=click.Path(exists=True), default='config.yaml',
              help='配置文件路径（默认：config.yaml）')
@click.option('--verbose', '-v', is_flag=True,
              help='详细输出模式')
@click.option('--validate-only', is_flag=True,
              help='仅验证YAML格式，不生成')
@click.option('--min-chapters', type=int, default=3,
              help='最少章节数要求（默认：3）')
def convert(input_file, output, config, verbose, validate_only, min_chapters):
    """
    转换小说为剧本

    INPUT_FILE: 小说文本文件路径
    """
    try:
        # 验证模式
        if validate_only:
            _validate_yaml(input_file)
            return

        # 显示欢迎信息
        if verbose:
            _show_welcome()

        # 开始转换流程
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # 步骤1：解析小说
            task1 = progress.add_task("[cyan]解析小说文本...", total=None)

            try:
                parsed_novel = parse_from_file(input_file, min_chapters=min_chapters)
                progress.update(task1, description="[green]✓ 小说解析完成")

                # 显示解析结果摘要
                if verbose:
                    parser = NovelParser()
                    console.print(Panel(
                        parser.get_summary(parsed_novel),
                        title="小说解析结果",
                        border_style="blue"
                    ))

            except NovelParserError as e:
                progress.stop()
                console.print(f"[red]错误：{str(e)}[/red]")
                sys.exit(1)

            # 步骤2：生成剧本
            task2 = progress.add_task("[cyan]调用AI生成剧本...", total=None)

            try:
                generator = ScriptGenerator(config)
                script_data = generator.generate(parsed_novel, output, verbose)

                progress.update(task2, description="[green]✓ 剧本生成完成")

            except ScriptGeneratorError as e:
                progress.stop()
                console.print(f"[red]错误：{str(e)}[/red]")
                sys.exit(1)
            except Exception as e:
                progress.stop()
                console.print(f"[red]未知错误：{str(e)}[/red]")
                sys.exit(1)

        # 显示成功信息
        _show_success(script_data, output)

    except KeyboardInterrupt:
        console.print("\n[yellow]用户中断操作[/yellow]")
        sys.exit(0)


@cli.command()
@click.argument('novel_file', type=click.Path(exists=True))
@click.option('--min-chapters', type=int, default=3,
              help='最少章节数要求')
def parse(novel_file, min_chapters):
    """
    仅解析小说（不生成剧本）

    NOVEL_FILE: 小说文本文件路径
    """
    try:
        console.print("[cyan]解析小说文本...[/cyan]")

        parsed_novel = parse_from_file(novel_file, min_chapters=min_chapters)

        # 显示解析结果
        parser = NovelParser()
        console.print(Panel(
            parser.get_summary(parsed_novel),
            title="小说解析结果",
            border_style="blue"
        ))

        # 显示章节详情
        table = Table(title="章节详情")
        table.add_column("章节", style="cyan")
        table.add_column("标题", style="green")
        table.add_column("字数", justify="right")
        table.add_column("角色数", justify="right")

        for chapter in parsed_novel['chapters']:
            table.add_row(
                f"第{chapter['number']}章",
                chapter['title'],
                str(chapter['word_count']),
                str(len(chapter['characters']))
            )

        console.print(table)

    except NovelParserError as e:
        console.print(f"[red]错误：{str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('yaml_file', type=click.Path(exists=True))
def validate(yaml_file):
    """
    验证剧本YAML格式

    YAML_FILE: 剧本YAML文件路径
    """
    _validate_yaml(yaml_file)


@cli.command()
def info():
    """
    显示工具信息和配置
    """
    from .ai_client import AIClient

    try:
        client = AIClient()
        provider = client.get_provider_name()
        model = client.get_model_name()

        info_panel = Panel(
            f"""
[bold]AI小说转剧本工具[/bold]

版本：1.0.0
作者：暑训营项目

当前配置：
• AI提供商：[cyan]{provider}[/cyan]
• 模型：[cyan]{model}[/cyan]
• 配置文件：config.yaml

功能特点：
• 支持3个章节以上的小说转换
• 输出YAML格式剧本
• 可配置多种AI模型

使用方法：
• python -m src.main convert novel.txt -o script.yaml
• python -m src.main parse novel.txt
• python -m src.main validate script.yaml
            """,
            title="工具信息",
            border_style="green"
        )

        console.print(info_panel)

    except Exception as e:
        console.print(f"[red]配置加载失败：{str(e)}[/red]")
        console.print("[yellow]请检查config.yaml文件[/yellow]")


def _validate_yaml(yaml_file: str):
    """验证YAML文件"""
    from .yaml_schema import validate_script_yaml

    console.print(f"[cyan]验证YAML文件：{yaml_file}[/cyan]")

    try:
        yaml_data = load_yaml(yaml_file)
        script = validate_script_yaml(yaml_data)

        # 显示验证结果
        console.print("[green]✓ YAML格式验证通过[/green]")

        # 显示剧本统计
        table = Table(title="剧本统计")
        table.add_column("项目", style="cyan")
        table.add_column("数量", justify="right")

        table.add_row("角色数", str(len(script.characters)))
        table.add_row("场景数", str(len(script.scenes)))
        if script.outline:
            table.add_row("大纲章节数", str(len(script.outline)))

        console.print(table)

        # 显示基本信息
        console.print(f"\n[bold]剧本信息[/bold]")
        console.print(f"标题：{script.metadata.title}")
        console.print(f"原小说：{script.metadata.original_novel}")
        console.print(f"作者：{script.metadata.author}")
        console.print(f"创建日期：{script.metadata.created_date}")

    except Exception as e:
        console.print(f"[red]✗ YAML验证失败：{str(e)}[/red]")
        sys.exit(1)


def _show_welcome():
    """显示欢迎信息"""
    welcome_panel = Panel(
        """
[bold cyan]AI小说转剧本工具[/bold cyan]

欢迎使用AI辅助剧本创作工具！
本工具将自动将小说转换为结构化剧本。

功能特点：
• 智能识别角色和对话
• 自动分割场景
• 输出可编辑的YAML格式

按Ctrl+C可随时中断操作
        """,
        title="欢迎",
        border_style="cyan"
    )
    console.print(welcome_panel)


def _show_success(script_data: dict, output_path: str):
    """显示成功信息"""
    console.print("\n")

    success_panel = Panel(
        f"""
[green bold]✓ 剧本生成成功！[/green bold]

输出文件：[cyan]{output_path}[/cyan]

剧本统计：
• 总角色数：{len(script_data['script']['characters'])}
• 总场景数：{len(script_data['script']['scenes'])}
• 总章节数：{script_data['script']['metadata'].get('total_chapters', 0)}

下一步建议：
1. 打开YAML文件查看剧本内容
2. 根据需要修改角色描述和对话
3. 调整场景顺序和舞台指示
4. 使用 --validate 参数验证修改后的剧本
        """,
        title="完成",
        border_style="green"
    )
    console.print(success_panel)


def main():
    """主函数"""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]错误：{str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()