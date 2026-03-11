from dataclasses import dataclass
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth_service import auth_service
from app.services.supabase_client import supabase_client

bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user_id: str
    user: Dict[str, Any]
    trip_id: Optional[str] = None
    trip_context: Optional[Dict[str, Any]] = None


async def get_auth_context(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    x_trip_id: Optional[str] = Header(default=None, alias="X-Trip-ID"),
) -> AuthContext:
    user = None
    user_id = None

    if credentials and credentials.scheme.lower() == "bearer":
        try:
            payload = auth_service.validate_token(credentials.credentials)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sem 'sub'")

        user = supabase_client.get_user_by_id(user_id)

    elif x_api_key:
        user = supabase_client.get_user_by_api_key(x_api_key)
        user_id = user.get("id") if user else None

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Envie Authorization: Bearer <token> ou X-API-Key",
        )

    if not user or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")

    trip_context = None
    if x_trip_id:
        trip_context = supabase_client.get_trip_context(x_trip_id, user_id)
        if not trip_context:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso à viagem")

    return AuthContext(user_id=user_id, user=user, trip_id=x_trip_id, trip_context=trip_context)
