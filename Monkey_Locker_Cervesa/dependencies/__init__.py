# dependencies/__init__.py
"""
Reusable dependencies for FastAPI routes
"""

from .auth import (
    get_current_user,
    get_current_active_user,
    require_face_enrolled,
    optional_current_user
)

from .validation import (
    get_user_or_404
)

from .pagination import PaginationParams

from .context import (
    get_client_info,
    get_request_id
)

__all__ = [
    # Auth
    "get_current_user",
    "get_current_active_user",
    "require_face_enrolled",
    "optional_current_user",
    
    # Validation
    "get_user_or_404",
    
    # Pagination
    "PaginationParams",
    
    # Context
    "get_client_info",
    "get_request_id"
]