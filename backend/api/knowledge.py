"""知识库API"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from backend.core.database import get_db
from backend.services.knowledge_base import KnowledgeBaseService
from backend.services.llm_service import EmbeddingService, RerankService
from backend.models.schema import LLMConfig
from backend.core.logger import log
from backend.core.encryption import encryption_service

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


class AddDocumentRequest(BaseModel):
    """添加文档请求"""
    title: str
    content: str
    chunk_size: int = 500
    chunk_overlap: int = 50


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    title: str
    filename: Optional[str]
    file_type: Optional[str]
    file_size: Optional[int]
    total_chunks: int
    created_at: str


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    top_k: int = 5
    score_threshold: float = 0.0
    use_rerank: bool = True


class SearchResultItem(BaseModel):
    """搜索结果项"""
    content: str
    document_title: str
    chunk_index: int
    similarity: float
    document_id: int


class ChunkResponse(BaseModel):
    """分块响应"""
    id: int
    chunk_index: int
    content: str
    start_pos: int
    end_pos: int


async def get_knowledge_service(db: AsyncSession = Depends(get_db), require_embedding: bool = True):
    """
    获取知识库服务实例

    Args:
        db: 数据库会话
        require_embedding: 是否必须有Embedding配置(查看列表不需要,添加文档需要)
    """
    # 从数据库获取激活的embedding服务配置
    result = await db.execute(
        select(LLMConfig)
        .where(LLMConfig.config_type == "embedding", LLMConfig.is_active == True)
        .limit(1)
    )
    embedding_config = result.scalar_one_or_none()

    if not embedding_config and require_embedding:
        raise HTTPException(
            status_code=400,
            detail="未配置Embedding服务，请先在LLM设置中添加并激活Embedding配置"
        )

    # 创建embedding服务(如果有配置)
    embedding_service = None
    if embedding_config:
        # 解密API密钥
        decrypted_api_key = ""
        if embedding_config.api_key:
            decrypted_api_key = encryption_service.decrypt(embedding_config.api_key) or ""

        embedding_service = EmbeddingService(
            api_key=decrypted_api_key,
            base_url=embedding_config.base_url,
            model=embedding_config.model,
        )

    # 从数据库获取激活的rerank服务配置（可选）
    result = await db.execute(
        select(LLMConfig)
        .where(LLMConfig.config_type == "rerank", LLMConfig.is_active == True)
        .limit(1)
    )
    rerank_config = result.scalar_one_or_none()

    rerank_service = None
    if rerank_config:
        # 解密API密钥
        decrypted_rerank_key = ""
        if rerank_config.api_key:
            decrypted_rerank_key = encryption_service.decrypt(rerank_config.api_key) or ""

        rerank_service = RerankService(
            api_key=decrypted_rerank_key,
            base_url=rerank_config.base_url,
            model=rerank_config.model,
        )

    return KnowledgeBaseService(embedding_service, rerank_service)


@router.post("/documents", response_model=DocumentResponse)
async def add_document(
    request: AddDocumentRequest,
    db: AsyncSession = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    """添加文档到知识库"""
    try:
        document = await kb_service.add_document(
            session=db,
            title=request.title,
            content=request.content,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )

        return DocumentResponse(
            id=document.id,
            title=document.title,
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            total_chunks=document.total_chunks,
            created_at=document.created_at.isoformat(),
        )

    except ValueError as e:
        log.error(f"添加文档失败 (参数错误): {e}")
        raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")

    except ConnectionError as e:
        log.error(f"添加文档失败 (Embedding服务连接失败): {e}")
        raise HTTPException(status_code=503, detail=f"Embedding服务不可用: {str(e)}")

    except TimeoutError as e:
        log.error(f"添加文档失败 (Embedding服务超时): {e}")
        raise HTTPException(status_code=504, detail=f"Embedding服务超时: {str(e)}")

    except RuntimeError as e:
        log.error(f"添加文档失败 (运行时错误): {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

    except Exception as e:
        log.error(f"添加文档失败 (未知错误): {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    db: AsyncSession = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    """上传文档文件到知识库"""
    # 常量定义
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.txt', '.md'}

    try:
        # 1. 验证文件名
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        # 2. 验证文件扩展名
        import os
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # 3. 读取文件内容
        content = await file.read()

        # 4. 验证文件大小
        file_size = len(content)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超出限制。最大允许: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB，当前文件: {file_size / 1024 / 1024:.2f}MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="文件内容为空")

        # 5. 解码文件内容
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件编码错误，请使用UTF-8编码的文件")

        # 6. 添加到知识库
        document = await kb_service.add_document(
            session=db,
            title=file.filename,
            content=text_content,
            filename=file.filename,
            file_type=file.content_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        return DocumentResponse(
            id=document.id,
            title=document.title,
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            total_chunks=document.total_chunks,
            created_at=document.created_at.isoformat(),
        )

    except HTTPException:
        # 重新抛出已经格式化的HTTP异常
        raise

    except ValueError as e:
        log.error(f"上传文档失败 (参数错误): {e}")
        raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")

    except ConnectionError as e:
        log.error(f"上传文档失败 (Embedding服务连接失败): {e}")
        raise HTTPException(status_code=503, detail=f"Embedding服务不可用: {str(e)}")

    except TimeoutError as e:
        log.error(f"上传文档失败 (Embedding服务超时): {e}")
        raise HTTPException(status_code=504, detail=f"Embedding服务超时: {str(e)}")

    except RuntimeError as e:
        log.error(f"上传文档失败 (运行时错误): {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

    except Exception as e:
        log.error(f"上传文档失败 (未知错误): {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")


@router.get("/documents", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """获取文档列表(不需要Embedding配置)"""
    # 直接查询数据库,不需要通过KnowledgeBaseService
    from backend.models.schema import KnowledgeDocument as KnowledgeDocumentModel

    result = await db.execute(
        select(KnowledgeDocumentModel)
        .order_by(KnowledgeDocumentModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()

    return [
        DocumentResponse(
            id=doc.id,
            title=doc.title,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            total_chunks=doc.total_chunks,
            created_at=doc.created_at.isoformat(),
        )
        for doc in documents
    ]


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除文档(不需要Embedding配置)"""
    from backend.models.schema import KnowledgeDocument as KnowledgeDocumentModel

    try:
        # 获取文档
        result = await db.execute(
            select(KnowledgeDocumentModel).where(KnowledgeDocumentModel.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail=f"文档不存在: {document_id}")

        # 删除文档(级联删除会自动删除分块和向量)
        await db.delete(document)
        await db.commit()

        log.info(f"成功删除文档: {document_id}")
        return {"message": "删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/chunks", response_model=List[ChunkResponse])
async def get_document_chunks(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取文档的所有分块(不需要Embedding配置)"""
    from backend.models.schema import KnowledgeDocument as KnowledgeDocumentModel, KnowledgeChunk as KnowledgeChunkModel

    try:
        # 验证文档存在
        result = await db.execute(
            select(KnowledgeDocumentModel).where(KnowledgeDocumentModel.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail=f"文档不存在: {document_id}")

        # 获取所有分块
        result = await db.execute(
            select(KnowledgeChunkModel)
            .where(KnowledgeChunkModel.document_id == document_id)
            .order_by(KnowledgeChunkModel.chunk_index)
        )
        chunks = result.scalars().all()

        return [
            ChunkResponse(
                id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                start_pos=chunk.start_pos,
                end_pos=chunk.end_pos,
            )
            for chunk in chunks
        ]

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"获取文档分块失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[SearchResultItem])
async def search_knowledge(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    """搜索知识库"""
    try:
        results = await kb_service.search(
            session=db,
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            use_rerank=request.use_rerank,
        )

        return [
            SearchResultItem(**result)
            for result in results
        ]

    except ValueError as e:
        log.error(f"搜索知识库失败 (参数错误): {e}")
        raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")

    except ConnectionError as e:
        log.error(f"搜索知识库失败 (服务连接失败): {e}")
        raise HTTPException(status_code=503, detail=f"服务不可用: {str(e)}")

    except TimeoutError as e:
        log.error(f"搜索知识库失败 (服务超时): {e}")
        raise HTTPException(status_code=504, detail=f"服务超时: {str(e)}")

    except Exception as e:
        log.error(f"搜索知识库失败 (未知错误): {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

