"""
LLMプロバイダーの抽象化層
OpenAI, Claude, Gemini, DeepSeekをサポート
"""
from typing import Protocol, Dict, List, Optional, Any
from abc import ABC, abstractmethod
import os
import json
from dataclasses import dataclass
from enum import Enum

class LLMProvider(str, Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"

@dataclass
class LLMConfig:
    provider: LLMProvider
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000

class LLMInterface(ABC):
    """LLMプロバイダーの共通インターフェース"""
    
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None
    ) -> str:
        """テキスト生成"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """プロバイダーが利用可能かチェック"""
        pass

class OpenAIAdapter(LLMInterface):
    """OpenAI APIアダプター"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=config.api_key or os.getenv("OPENAI_API_KEY"))
            self.model = config.model_id or "gpt-5.2"
        except ImportError:
            self.client = None
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None
    ) -> str:
        if not self.client:
            raise Exception("OpenAI client not initialized")
        
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        return self.client is not None and (self.config.api_key or os.getenv("OPENAI_API_KEY"))

class ClaudeAdapter(LLMInterface):
    """Claude (Anthropic) APIアダプター"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=config.api_key or os.getenv("ANTHROPIC_API_KEY")
            )
            self.model = config.model_id or "claude-3-opus-20240229"
        except ImportError:
            self.client = None
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None
    ) -> str:
        if not self.client:
            raise Exception("Claude client not initialized")
        
        # Claudeは system と user を組み合わせる
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # response_formatがJSONの場合、プロンプトに指示を追加
        if response_format and response_format.get("type") == "json_object":
            combined_prompt += "\n\nPlease respond with valid JSON only."
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": combined_prompt}
            ]
        )
        
        return message.content[0].text
    
    def is_available(self) -> bool:
        return self.client is not None and (self.config.api_key or os.getenv("ANTHROPIC_API_KEY"))

class GeminiAdapter(LLMInterface):
    """Google Gemini APIアダプター"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        try:
            import google.generativeai as genai
            api_key = config.api_key or os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(
                    config.model_id or "gemini-2.0-flash-exp"
                )
            else:
                self.model = None
        except ImportError:
            self.model = None
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None
    ) -> str:
        if not self.model:
            raise Exception("Gemini model not initialized")
        
        # Geminiは system と user を組み合わせる
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # response_formatがJSONの場合、プロンプトに指示を追加
        if response_format and response_format.get("type") == "json_object":
            combined_prompt += "\n\nPlease respond with valid JSON only."
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        response = self.model.generate_content(
            combined_prompt,
            generation_config=generation_config
        )
        
        return response.text
    
    def is_available(self) -> bool:
        return self.model is not None

class DeepSeekAdapter(LLMInterface):
    """DeepSeek APIアダプター（OpenAI互換API）"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        try:
            from openai import OpenAI
            # DeepSeekはOpenAI互換のAPIを使用
            self.client = OpenAI(
                api_key=config.api_key or os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            )
            self.model = config.model_id or "deepseek-chat"
        except ImportError:
            self.client = None
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[Dict] = None
    ) -> str:
        if not self.client:
            raise Exception("DeepSeek client not initialized")
        
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        return self.client is not None and (self.config.api_key or os.getenv("DEEPSEEK_API_KEY"))

class LLMFactory:
    """LLMプロバイダーのファクトリー"""
    
    @staticmethod
    def create(config: LLMConfig) -> LLMInterface:
        """設定に基づいてLLMインスタンスを作成"""
        if config.provider == LLMProvider.OPENAI:
            return OpenAIAdapter(config)
        elif config.provider == LLMProvider.CLAUDE:
            return ClaudeAdapter(config)
        elif config.provider == LLMProvider.GEMINI:
            return GeminiAdapter(config)
        elif config.provider == LLMProvider.DEEPSEEK:
            return DeepSeekAdapter(config)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")
    
    @staticmethod
    def get_available_providers() -> List[Dict[str, Any]]:
        """利用可能なプロバイダーのリストを返す"""
        providers = []
        
        # OpenAI
        try:
            config = LLMConfig(provider=LLMProvider.OPENAI)
            adapter = OpenAIAdapter(config)
            providers.append({
                "id": LLMProvider.OPENAI,
                "name": "OpenAI",
                "models": [
                    "gpt-5.2",           # 最新モデル（2025年）
                    "gpt-5.1",           # GPT-5.1
                    "gpt-5",             # GPT-5
                    "gpt-4o"             # GPT-4o（2024年5月）
                ],
                "requires_key": True,
                "available": adapter.is_available()
            })
        except:
            pass
        
        # Claude
        try:
            config = LLMConfig(provider=LLMProvider.CLAUDE)
            adapter = ClaudeAdapter(config)
            providers.append({
                "id": LLMProvider.CLAUDE,
                "name": "Claude (Anthropic)",
                "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                "requires_key": True,
                "available": adapter.is_available()
            })
        except:
            pass
        
        # Gemini
        try:
            config = LLMConfig(provider=LLMProvider.GEMINI)
            adapter = GeminiAdapter(config)
            providers.append({
                "id": LLMProvider.GEMINI,
                "name": "Google Gemini",
                "models": [
                    "gemini-2.0-flash-exp",  # 最新モデル（2025年）
                    "gemini-1.5-pro"         # Gemini 1.5 Pro
                ],
                "requires_key": True,
                "available": adapter.is_available()
            })
        except:
            pass
        
        # DeepSeek
        try:
            config = LLMConfig(provider=LLMProvider.DEEPSEEK)
            adapter = DeepSeekAdapter(config)
            providers.append({
                "id": LLMProvider.DEEPSEEK,
                "name": "DeepSeek",
                "models": [
                    "deepseek-chat",      # DeepSeek Chat（最新）
                    "deepseek-coder"      # DeepSeek Coder（コード生成特化）
                ],
                "requires_key": True,
                "available": adapter.is_available()
            })
        except:
            pass
        
        return providers