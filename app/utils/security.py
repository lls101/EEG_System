import jwt
from passlib import pwd
from passlib.context import CryptContext

from app.schemas.login import JWTPayload
from app.settings import APP_SETTINGS

# 推荐使用 bcrypt 作为加密方式
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ALGORITHM = "HS256"


def create_access_token(*, data: JWTPayload):
    payload = data.model_dump().copy()
    encoded_jwt = jwt.encode(payload, APP_SETTINGS.SECRET_KEY, algorithm=APP_SETTINGS.JWT_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_password() -> str:
    return pwd.genword()
