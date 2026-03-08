from fastapi import Request
from typing import Optional
import uuid


async def get_client_info(request: Request) -> dict:
    
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


async def get_request_id(request: Request) -> str:
    
    request_id = request.headers.get("X-Request-ID")
    
    if not request_id:
        request_id = str(uuid.uuid4())
    
    return request_id


async def get_user_agent_info(request: Request) -> dict:
    user_agent = request.headers.get("user-agent", "")
    
    info = {
        "user_agent": user_agent,
        "is_mobile": any(x in user_agent.lower() for x in ["mobile", "android", "iphone"]),
        "is_bot": any(x in user_agent.lower() for x in ["bot", "crawler", "spider"]),
        "browser": "unknown",
        "os": "unknown"
    }
    
    if "chrome" in user_agent.lower():
        info["browser"] = "Chrome"
    elif "firefox" in user_agent.lower():
        info["browser"] = "Firefox"
    elif "safari" in user_agent.lower():
        info["browser"] = "Safari"
    elif "edge" in user_agent.lower():
        info["browser"] = "Edge"
    
    if "windows" in user_agent.lower():
        info["os"] = "Windows"
    elif "mac" in user_agent.lower():
        info["os"] = "macOS"
    elif "linux" in user_agent.lower():
        info["os"] = "Linux"
    elif "android" in user_agent.lower():
        info["os"] = "Android"
    elif "ios" in user_agent.lower() or "iphone" in user_agent.lower():
        info["os"] = "iOS"
    
    return info


async def get_cors_origin(request: Request) -> Optional[str]:
    """
    Usage:
        @router.options("/api/something")
        def handle_preflight(origin: Optional[str] = Depends(get_cors_origin)):
            # Handle CORS preflight
    """
    
    return request.headers.get("origin")