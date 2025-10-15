#!/usr/bin/env python3
"""清理知识库数据库脏数据"""
import asyncio
from sqlalchemy import select, delete
from backend.core.database import async_session_maker
from backend.models.schema import KnowledgeDocument, KnowledgeChunk, VectorEmbedding
from backend.core.logger import log


async def clean_database():
    """清理数据库中的孤儿数据和重复数据"""
    print("=" * 60)
    print("开始清理知识库数据库")
    print("=" * 60)
    
    async with async_session_maker() as session:
        # 1. 查找并删除孤儿分块（document_id对应的文档不存在）
        print("\n1. 检查孤儿分块...")
        result = await session.execute(
            select(KnowledgeChunk)
        )
        all_chunks = result.scalars().all()
        
        orphan_chunks = []
        for chunk in all_chunks:
            doc_result = await session.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == chunk.document_id)
            )
            doc = doc_result.scalar_one_or_none()
            if not doc:
                orphan_chunks.append(chunk)
        
        if orphan_chunks:
            print(f"  发现 {len(orphan_chunks)} 个孤儿分块")
            for chunk in orphan_chunks:
                await session.delete(chunk)
            print(f"  ✓ 已删除孤儿分块")
        else:
            print("  ✓ 没有孤儿分块")
        
        # 2. 查找并删除孤儿向量（chunk_id对应的分块不存在）
        print("\n2. 检查孤儿向量...")
        result = await session.execute(
            select(VectorEmbedding)
        )
        all_vectors = result.scalars().all()
        
        orphan_vectors = []
        for vector in all_vectors:
            chunk_result = await session.execute(
                select(KnowledgeChunk).where(KnowledgeChunk.id == vector.chunk_id)
            )
            chunk = chunk_result.scalar_one_or_none()
            if not chunk:
                orphan_vectors.append(vector)
        
        if orphan_vectors:
            print(f"  发现 {len(orphan_vectors)} 个孤儿向量")
            for vector in orphan_vectors:
                await session.delete(vector)
            print(f"  ✓ 已删除孤儿向量")
        else:
            print("  ✓ 没有孤儿向量")
        
        # 3. 统计当前状态
        print("\n3. 当前数据库状态:")
        doc_result = await session.execute(select(KnowledgeDocument))
        docs = doc_result.scalars().all()
        print(f"  文档数量: {len(docs)}")
        
        for doc in docs:
            chunk_result = await session.execute(
                select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc.id)
            )
            chunks = chunk_result.scalars().all()
            print(f"    - {doc.title}: {len(chunks)} 个分块")
        
        # 提交更改
        await session.commit()
        print("\n" + "=" * 60)
        print("✓ 清理完成！")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(clean_database())
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n❌ 清理失败: {e}")
        import traceback
        print(traceback.format_exc())

