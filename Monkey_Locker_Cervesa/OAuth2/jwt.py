from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt


class JWTManager:
    
    def __init__(
        self, 
        secret_key: str, 
        algorithm: str = "HS256",
        expire_minutes: int = 1440
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes
    
    def create_token(
        self, 
        user_id: int,
        additional_claims: Optional[Dict] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError:
            return None
    
    def extract_user_id(self, token: str) -> Optional[int]:
        payload = self.verify_token(token)
        if payload:
            try:
                return int(payload.get("sub"))
            except (ValueError, TypeError):
                return None
        return None
    
    def is_expired(self, token: str) -> bool:
        payload = self.verify_token(token)
        if not payload:
            return True
        
        exp = payload.get("exp")
        if not exp:
            return True
        
        return datetime.utcnow() > datetime.fromtimestamp(exp)