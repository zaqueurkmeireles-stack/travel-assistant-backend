import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt


class AuthService:
    def __init__(self) -> None:
        self.secret_key = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PROD")
        self.algorithm = os.getenv("JWT_ALG", "HS256")

    def create_token(self, user_id: str, expires_hours: int = 24) -> str:
        exp = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        payload = {"sub": user_id, "exp": exp}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str) -> Dict[str, Any]:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])


auth_service = AuthService()
