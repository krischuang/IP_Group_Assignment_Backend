from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str
    db_name: str = "ip_group"
    jwt_secret: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    root_path: str = ""
    turnstile_secret_key: str = "0x4AAAAAADGCsV6Af8Wbu2ajKe6FIDFDu4M"

    class Config:
        env_file = ".env"


settings = Settings()
