"""
AI客户端模块 - 统一接口封装多个AI提供商
"""

import os
import yaml
import json
import time
from typing import Dict, Optional, List, Any
from pathlib import Path


class AIClientError(Exception):
    """AI客户端错误"""
    pass


class BaseAIProvider:
    """AI提供商基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0)

    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        核心对话接口

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词（可选）

        Returns:
            AI回复文本
        """
        raise NotImplementedError("子类必须实现chat方法")

    def _get_api_key(self, key_field: str = "api_key") -> str:
        """
        获取API密钥（支持环境变量）

        Args:
            key_field: 配置字段名

        Returns:
            API密钥
        """
        key = self.config.get(key_field, "")
        if key.startswith("${") and key.endswith("}"):
            env_var = key[2:-1]
            key = os.getenv(env_var, "")
            if not key:
                raise AIClientError(f"环境变量 {env_var} 未设置")
        return key


class ClaudeProvider(BaseAIProvider):
    """Claude API提供商"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self._get_api_key())
            self.model = config.get("model", "claude-sonnet-4-6")
        except ImportError:
            raise AIClientError("请安装anthropic包: pip install anthropic")

    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用Claude API"""
        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages,
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)
            return response.content[0].text

        except Exception as e:
            raise AIClientError(f"Claude API调用失败: {str(e)}")


class OpenAIProvider(BaseAIProvider):
    """OpenAI API提供商"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import openai
            self.client = openai.OpenAI(api_key=self._get_api_key())
            self.model = config.get("model", "gpt-4")
        except ImportError:
            raise AIClientError("请安装openai包: pip install openai")

    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用OpenAI API"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            return response.choices[0].message.content

        except Exception as e:
            raise AIClientError(f"OpenAI API调用失败: {str(e)}")


class OllamaProvider(BaseAIProvider):
    """Ollama本地模型提供商"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import requests
            self.requests = requests
            self.base_url = config.get("base_url", "http://localhost:11434")
            self.model = config.get("model", "llama3")
        except ImportError:
            raise AIClientError("请安装requests包: pip install requests")

    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用Ollama API"""
        try:
            url = f"{self.base_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": self.max_tokens,
                    "temperature": self.temperature,
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = self.requests.post(url, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except Exception as e:
            raise AIClientError(f"Ollama API调用失败: {str(e)}")


class AIClient:
    """
    AI客户端统一接口

    使用方法:
        client = AIClient()
        response = client.chat("你的提示词")
    """

    PROVIDERS = {
        "claude": ClaudeProvider,
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化AI客户端

        Args:
            config_path: 配置文件路径（默认：config.yaml）
        """
        self.config = self._load_config(config_path)
        self.provider_name = self.config.get("ai_provider", "claude")
        self.provider = self._init_provider()

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """加载配置文件"""
        if not config_path:
            config_path = "config.yaml"

        path = Path(config_path)
        if not path.exists():
            raise AIClientError(f"配置文件不存在: {config_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise AIClientError(f"配置文件加载失败: {str(e)}")

    def _init_provider(self) -> BaseAIProvider:
        """初始化AI提供商"""
        provider_class = self.PROVIDERS.get(self.provider_name)
        if not provider_class:
            raise AIClientError(f"不支持的AI提供商: {self.provider_name}")

        provider_config = self.config.get("providers", {}).get(self.provider_name, {})
        return provider_class(provider_config)

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        retry_count: int = 3,
        retry_delay: int = 2,
    ) -> str:
        """
        发送对话请求（带重试机制）

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            retry_count: 重试次数
            retry_delay: 重试延迟（秒）

        Returns:
            AI回复文本
        """
        for attempt in range(retry_count):
            try:
                return self.provider.chat(prompt, system_prompt)
            except AIClientError as e:
                if attempt == retry_count - 1:
                    raise e
                time.sleep(retry_delay)

    def get_provider_name(self) -> str:
        """获取当前AI提供商名称"""
        return self.provider_name

    def get_model_name(self) -> str:
        """获取当前模型名称"""
        return self.provider.model


def test_connection():
    """测试AI连接"""
    client = AIClient()
    print(f"使用AI提供商: {client.get_provider_name()}")
    print(f"模型: {client.get_model_name()}")

    test_prompt = "你好，请回复'测试成功'"
    response = client.chat(test_prompt)
    print(f"AI回复: {response}")


if __name__ == "__main__":
    # 测试AI客户端
    test_connection()