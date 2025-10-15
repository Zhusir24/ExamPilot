#!/usr/bin/env python3
"""重置知识库数据库"""
import asyncio
from sqlalchemy import delete
from backend.core.database import async_session_maker
from backend.models.schema import KnowledgeDocument, KnowledgeChunk, VectorEmbedding
from backend.core.logger import log


async def reset_database():
    """删除所有知识库数据"""
    print("=" * 60)
    print("重置知识库数据库（删除所有数据）")
    print("=" * 60)
    
    confirm = input("\n⚠️  这将删除所有知识库文档、分块和向量数据！\n确认继续吗? (yes/no): ")
    if confirm.lower() != "yes":
        print("已取消")
        return
    
    async with async_session_maker() as session:
        # 删除所有向量
        print("\n1. 删除所有向量...")
        await session.execute(delete(VectorEmbedding))
        print("  ✓ 已删除")
        
        # 删除所有分块
        print("\n2. 删除所有分块...")
        await session.execute(delete(KnowledgeChunk))
        print("  ✓ 已删除")
        
        # 删除所有文档
        print("\n3. 删除所有文档...")
        await session.execute(delete(KnowledgeDocument))
        print("  ✓ 已删除")
        
        # 提交更改
        await session.commit()
        print("\n" + "=" * 60)
        print("✓ 数据库已重置！现在可以重新添加文档了。")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(reset_database())
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n❌ 重置失败: {e}")
        import traceback
        print(traceback.format_exc())

