from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "apna_bhagalpur"
    
    app_name: str = "Apna Bhagalpur"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = ""
    
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    frontend_url: str = "http://localhost:5500"
    
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 1440
    
    class Config:
        env_file = ".env"
    
    @property
    def database_url(self) -> str:
        encoded_password = quote_plus(self.db_password)
        return f"mysql+pymysql://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"


@lru_cache()
def get_settings():
    return Settings()