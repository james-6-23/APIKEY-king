"""
Authentication service.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional

import os
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..database.database import db

# Constants
SECRET_KEY = os.getenv("APIKEY_KING_SECRET", "apikey-king-secret-key-change-in-production")
DEFAULT_PASSWORD = os.getenv("APIKEY_KING_DEFAULT_PASSWORD", "kyx200328")  # 仅用于首次启动
TOKEN_EXPIRE_HOURS = int(os.getenv("APIKEY_KING_TOKEN_EXPIRE_HOURS", "24"))

security = HTTPBearer()


class AuthService:
    """Authentication service."""
    
    def is_first_run(self) -> bool:
        """检查是否首次运行."""
        return db.is_first_run()
    
    def setup_password(self, password: str):
        """设置密码（首次运行）."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        db.save_system_setting("password_hash", password_hash)
    
    def verify_password(self, password: str) -> bool:
        """验证密码."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # 从数据库获取密码哈希
        stored_hash = db.get_system_setting("password_hash")
        
        # 如果数据库中没有，使用默认密码
        if stored_hash is None:
            # 首次运行，自动设置默认密码
            default_hash = hashlib.sha256(DEFAULT_PASSWORD.encode()).hexdigest()
            db.save_system_setting("password_hash", default_hash)
            return password_hash == default_hash
        
        return password_hash == stored_hash
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """修改密码."""
        if not self.verify_password(old_password):
            return False
        
        self.setup_password(new_password)
        return True
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


# Dependency for verifying tokens
def verify_token_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to verify JWT token."""
    auth_service = AuthService()
    return auth_service.verify_token(credentials.credentials)


