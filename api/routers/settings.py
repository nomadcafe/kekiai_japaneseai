"""
設定関連のルート
"""
from fastapi import APIRouter
import os
from api.models.settings import ProviderConfig, TestKeyRequest, SettingsUpdate
from api.core.settings_manager import SettingsManager
from api.core.llm_provider import LLMFactory

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/providers")
async def get_providers():
    """利用可能なLLMプロバイダーの一覧と状態を取得"""
    settings_manager = SettingsManager()
    
    # 利用可能なプロバイダー
    available_providers = LLMFactory.get_available_providers()
    
    # APIキーの状態
    key_status = settings_manager.get_all_keys_status()
    
    # 現在の設定
    settings = settings_manager.get_settings()
    
    # 結果を統合
    providers = []
    for provider_info in available_providers:
        provider_id = provider_info["id"]
        status = key_status.get(provider_id.value, {})
        
        providers.append({
            "id": provider_id.value,
            "name": provider_info["name"],
            "models": provider_info["models"],
            "configured": status.get("configured", False),
            "masked_key": status.get("masked_key"),
            "key_source": status.get("source"),
            "requires_region": provider_info.get("requires_region", False)
        })
    
    return {
        "providers": providers,
        "default_provider": settings.get("default_provider"),
        "default_models": settings.get("default_model"),
        "temperature": settings.get("temperature"),
        "max_tokens": settings.get("max_tokens")
    }


@router.post("/provider")
async def save_provider_config(config: ProviderConfig):
    """プロバイダーの設定とAPIキーを保存"""
    settings_manager = SettingsManager()
    
    # APIキーを保存
    settings_manager.save_api_key(config.provider, config.api_key)
    
    # デフォルトプロバイダーとして設定
    settings = settings_manager.get_settings()
    settings["default_provider"] = config.provider
    if config.model:
        if "default_model" not in settings:
            settings["default_model"] = {}
        settings["default_model"][config.provider] = config.model
    settings_manager.save_settings(settings)
    
    return {"message": "プロバイダー設定を保存しました"}


@router.delete("/provider/{provider}")
async def delete_provider_config(provider: str):
    """プロバイダーの設定を削除"""
    settings_manager = SettingsManager()
    
    # APIキーを削除
    settings_manager.delete_api_key(provider)
    
    # デフォルトプロバイダーだった場合は変更
    settings = settings_manager.get_settings()
    if settings.get("default_provider") == provider:
        # 他の設定済みプロバイダーを探す
        key_status = settings_manager.get_all_keys_status()
        for other_provider, status in key_status.items():
            if other_provider != provider and status.get("configured"):
                settings["default_provider"] = other_provider
                break
        else:
            # 設定済みプロバイダーがない場合はOpenAIをデフォルトに
            settings["default_provider"] = "openai"
    
    settings_manager.save_settings(settings)
    
    return {"message": "プロバイダー設定を削除しました"}


@router.post("/test-key")
async def test_api_key(request: TestKeyRequest):
    """APIキーの有効性をテスト"""
    settings_manager = SettingsManager()
    
    try:
        result = await settings_manager.test_api_key(request.provider, request.api_key)
        return result
    except Exception as e:
        return {
            "valid": False,
            "message": f"APIキーのテストに失敗しました: {str(e)}"
        }


@router.put("")
async def update_settings(update: SettingsUpdate):
    """全般的な設定を更新"""
    settings_manager = SettingsManager()
    settings = settings_manager.get_settings()
    
    if update.default_provider is not None:
        settings["default_provider"] = update.default_provider
    if update.default_model is not None:
        settings["default_model"] = update.default_model
    if update.temperature is not None:
        settings["temperature"] = update.temperature
    if update.max_tokens is not None:
        settings["max_tokens"] = update.max_tokens
    
    settings_manager.save_settings(settings)
    
    return {"message": "設定を更新しました"}

