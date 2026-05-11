from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str
    db_name: str = "ip_group"
    jwt_secret: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    root_path: str = ""
    turnstile_secret_key: str
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    reset_token_expire_minutes: int = 15
    openrouter_api_key: str = ""
    openrouter_timeout: float = 60.0

    class Config:
        env_file = ".env"


settings = Settings()
