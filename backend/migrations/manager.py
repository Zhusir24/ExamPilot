"""数据库迁移管理器"""
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy import text
from backend.core.database import async_session_maker, init_db
from backend.core.logger import log


class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self):
        self.migrations_dir = Path(__file__).parent / "versions"
        self.migrations_dir.mkdir(exist_ok=True)
    
    async def get_executed_migrations(self) -> set:
        """获取已执行的迁移版本"""
        async with async_session_maker() as session:
            try:
                result = await session.execute(
                    text("SELECT version FROM migration_history ORDER BY executed_at")
                )
                return {row[0] for row in result.fetchall()}
            except Exception as e:
                log.warning(f"获取迁移历史失败，可能是首次运行: {e}")
                return set()
    
    async def record_migration(self, version: str, description: str = ""):
        """记录迁移执行"""
        async with async_session_maker() as session:
            await session.execute(
                text(
                    "INSERT INTO migration_history (version, description, executed_at) "
                    "VALUES (:version, :description, :executed_at)"
                ),
                {
                    "version": version,
                    "description": description,
                    "executed_at": datetime.utcnow()
                }
            )
            await session.commit()
    
    async def get_pending_migrations(self) -> list:
        """获取待执行的迁移"""
        executed = await self.get_executed_migrations()
        all_migrations = []
        
        # 扫描迁移目录
        for file in sorted(self.migrations_dir.glob("*.sql")):
            version = file.stem
            if version not in executed:
                all_migrations.append((version, file))
        
        return all_migrations
    
    async def execute_migration(self, version: str, file_path: Path):
        """执行单个迁移"""
        log.info(f"执行迁移: {version}")
        
        try:
            # 读取SQL文件
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 执行SQL
            async with async_session_maker() as session:
                # 分割多个SQL语句
                statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                
                for statement in statements:
                    if statement:
                        await session.execute(text(statement))
                
                await session.commit()
            
            # 记录迁移
            await self.record_migration(version, f"Migration from {file_path.name}")
            log.info(f"迁移 {version} 执行成功")
            
        except Exception as e:
            log.error(f"迁移 {version} 执行失败: {e}")
            raise
    
    async def run_migrations(self):
        """执行所有待执行的迁移"""
        # 首先初始化数据库表结构
        await init_db()
        
        # 执行迁移脚本
        pending = await self.get_pending_migrations()
        
        if not pending:
            log.info("没有待执行的迁移")
            return
        
        log.info(f"发现 {len(pending)} 个待执行的迁移")
        
        for version, file_path in pending:
            await self.execute_migration(version, file_path)
        
        log.info("所有迁移执行完成")
    
    def create_migration(self, name: str) -> Path:
        """创建新的迁移文件"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        version = f"{timestamp}_{name}"
        file_path = self.migrations_dir / f"{version}.sql"
        
        # 创建迁移文件模板
        template = f"""-- Migration: {name}
-- Created at: {datetime.now().isoformat()}

-- Write your migration SQL here

"""
        file_path.write_text(template, encoding='utf-8')
        log.info(f"创建迁移文件: {file_path}")
        
        return file_path


# 全局迁移管理器实例
migration_manager = MigrationManager()

