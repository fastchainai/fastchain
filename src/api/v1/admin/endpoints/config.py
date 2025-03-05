"""Admin configuration management endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from src.config.config import settings, reload_config

logger = logging.getLogger(__name__)
router = APIRouter()

# Define sensitive terms that should be protected
SENSITIVE_TERMS = ('secret', 'password', 'token', 'key', 'auth', 'credential')

class ConfigUpdateRequest(BaseModel):
    """Request model for configuration updates."""
    value: Any

def is_sensitive_setting(setting_key: str) -> bool:
    """Check if a setting key contains any sensitive terms."""
    return any(term in setting_key.lower() for term in SENSITIVE_TERMS)

@router.get("/", include_in_schema=True)
async def get_config_settings() -> Dict[str, Any]:
    """Get all configuration settings."""
    try:
        # Convert Dynaconf settings to dict, excluding sensitive data
        config_dict = {}
        settings_dict = settings.to_dict()
        for key in settings_dict:
            if not is_sensitive_setting(key):
                config_dict[key] = settings_dict[key]
        return {"settings": config_dict}
    except Exception as e:
        logger.error(f"Error retrieving configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration settings")

@router.post("/{setting_key}")
async def update_config_setting(setting_key: str, request: ConfigUpdateRequest) -> Dict[str, str]:
    """Update a specific configuration setting."""
    try:
        # Check for sensitive settings first
        if is_sensitive_setting(setting_key):
            raise HTTPException(status_code=400, detail="Cannot modify sensitive settings via API")

        # Check if setting exists
        if not settings.exists(setting_key):
            raise HTTPException(status_code=404, detail="Setting not found")

        # Update the setting
        settings.set(setting_key, request.value)
        reload_config()

        return {
            "status": "success",
            "message": f"Setting {setting_key} updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update setting: {str(e)}")

@router.get("/{setting_key}")
async def get_config_setting(setting_key: str) -> Dict[str, Any]:
    """Get a specific configuration setting."""
    try:
        # Check for sensitive settings first
        if is_sensitive_setting(setting_key):
            raise HTTPException(status_code=400, detail="Cannot retrieve sensitive settings")

        # Check if setting exists
        if not settings.exists(setting_key):
            raise HTTPException(status_code=404, detail="Setting not found")

        # Get the setting value
        value = settings.get(setting_key)
        return {"key": setting_key, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving setting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve setting: {str(e)}")