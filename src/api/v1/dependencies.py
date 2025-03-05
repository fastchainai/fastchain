# src/api/v1/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from config.config import settings

# OAuth2 scheme with a token URL (endpoint to obtain a token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT configuration
SECRET_KEY = settings.get('FASTAPI_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("FASTAPI_SECRET_KEY must be set in configuration")
ALGORITHM = "HS256"

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # Optionally, fetch user details from your database using user_id
        return {"user_id": user_id, "roles": payload.get("roles", [])}
    except JWTError:
        raise credentials_exception