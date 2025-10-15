"""配置管理模块"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """系统配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./data/database.db"
    
    # LLM配置
    llm_api_key: Optional[str] = None
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    
    # Embedding配置
    embedding_api_key: Optional[str] = None
    embedding_base_url: str = "https://api.deepseek.com/v1"
    embedding_model: str = "deepseek-embedding"
    
    # Rerank配置
    rerank_api_key: Optional[str] = None
    rerank_base_url: str = "https://api.deepseek.com/v1"
    rerank_model: str = "deepseek-rerank"
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # 日志配置
    log_level: str = "INFO"
    log_retention_days: int = 30
    
    # 路径配置
    @property
    def project_root(self) -> Path:
        """项目根目录"""
        return Path(__file__).parent.parent.parent
    
    @property
    def data_dir(self) -> Path:
        """数据目录"""
        path = self.project_root / "data"
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def log_dir(self) -> Path:
        """日志目录"""
        path = self.data_dir / "logs"
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def db_path(self) -> Path:
        """数据库文件路径"""
        return self.data_dir / "database.db"


# 全局配置实例
settings = Settings()

