from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_hostname: str
    database_port: int
    database_password: str
    database_name: str
    database_username: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 60 * 24 * 7

    deepseek_api_key: str

    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # redis_url: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()