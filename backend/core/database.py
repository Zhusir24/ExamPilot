"""数据库连接管理"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.core.config import settings
from backend.core.logger import log

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=False,  # 关闭SQL日志输出
    future=True,
)

# 创建会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 声明基类
Base = declarative_base()


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            log.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    log.info("数据库初始化完成")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    log.info("数据库连接已关闭")

