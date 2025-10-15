"""日志配置模块 - 使用 Loguru"""
import sys
from loguru import logger
from pathlib import Path
from backend.core.config import settings


def setup_logger():
    """配置日志系统"""
    
    # 移除默认的logger
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # 添加文件输出 - 所有日志
    logger.add(
        settings.log_dir / "exampilot_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="00:00",  # 每天午夜轮转
        retention=f"{settings.log_retention_days} days",  # 保留天数
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
    )
    
    # 添加错误日志文件
    logger.add(
        settings.log_dir / "error_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="00:00",
        retention=f"{settings.log_retention_days} days",
        compression="zip",
        encoding="utf-8",
    )
    
    logger.info("日志系统初始化完成")
    logger.info(f"日志目录: {settings.log_dir}")
    
    return logger


# 初始化日志
log = setup_logger()

