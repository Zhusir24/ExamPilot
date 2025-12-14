"""知识库管理服务"""
import numpy as np
import markdown
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.schema import KnowledgeDocument, KnowledgeChunk, VectorEmbedding
from backend.core.logger import log
from backend.services.llm_service import EmbeddingService, RerankService


class KnowledgeBaseService:
    """知识库服务类"""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        rerank_service: Optional[RerankService] = None,
    ):
        self.embedding_service = embedding_service
        self.rerank_service = rerank_service

    def _parse_markdown_to_text(self, markdown_content: str) -> str:
        """
        将 Markdown 内容解析为纯文本

        Args:
            markdown_content: Markdown 格式的文本

        Returns:
            解析后的纯文本（去除所有格式标记）
        """
        try:
            # 1. 使用 markdown 库将 markdown 转换为 HTML
            html = markdown.markdown(
                markdown_content,
                extensions=['extra', 'codehilite', 'tables', 'fenced_code']
            )

            # 2. 使用 BeautifulSoup 从 HTML 中提取纯文本
            soup = BeautifulSoup(html, 'html.parser')

            # 提取文本，自动处理标签之间的空白
            text = soup.get_text(separator='\n', strip=True)

            # 3. 清理多余的空行
            lines = [line.strip() for line in text.split('\n')]
            # 保留非空行，并合并连续的空行为单个空行
            cleaned_lines = []
            prev_empty = False
            for line in lines:
                if line:
                    cleaned_lines.append(line)
                    prev_empty = False
                elif not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True

            return '\n'.join(cleaned_lines).strip()

        except Exception as e:
            log.warning(f"Markdown 解析失败，将使用原始内容: {e}")
            return markdown_content
    
    async def add_document(
        self,
        session: AsyncSession,
        title: str,
        content: str,
        filename: Optional[str] = None,
        file_type: Optional[str] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        meta_data: Optional[Dict] = None,
    ) -> KnowledgeDocument:
        """
        添加文档到知识库

        Args:
            session: 数据库会话
            title: 文档标题
            content: 文档内容
            filename: 文件名
            file_type: 文件类型
            chunk_size: 分块大小（字符数）
            chunk_overlap: 分块重叠大小
            meta_data: 元数据

        Returns:
            文档对象
        """
        log.info(f"========== 开始添加文档: {title} ==========")
        log.info(f"内容长度: {len(content)} 字符, 分块大小: {chunk_size}, 重叠: {chunk_overlap}")

        # 初始化元数据
        if meta_data is None:
            meta_data = {}

        # 检测文件类型并处理 Markdown
        processed_content = content
        original_format = "text"

        if filename:
            import os
            file_ext = os.path.splitext(filename)[1].lower()

            if file_ext == '.md':
                log.info("检测到 Markdown 文件，开始解析为纯文本...")
                processed_content = self._parse_markdown_to_text(content)
                original_format = "markdown"
                log.info(f"Markdown 解析完成，原始长度: {len(content)}, 解析后长度: {len(processed_content)}")

                # 在元数据中记录原始格式
                meta_data['original_format'] = 'markdown'
                meta_data['original_length'] = len(content)
                meta_data['parsed_length'] = len(processed_content)
            elif file_ext == '.txt':
                original_format = "text"
                meta_data['original_format'] = 'text'

        # 创建文档记录
        log.info("1/5: 创建文档记录...")
        document = KnowledgeDocument(
            title=title,
            filename=filename,
            content=processed_content,  # 使用处理后的内容
            file_type=file_type,
            file_size=len(processed_content.encode('utf-8')),
            meta_data=meta_data,
        )
        session.add(document)
        await session.flush()
        log.info(f"✓ 文档记录创建成功，ID: {document.id}")
        
        # 文档分块
        log.info("2/5: 文档分块...")
        chunks = self._chunk_text(processed_content, chunk_size, chunk_overlap)
        log.info(f"✓ 文档分成 {len(chunks)} 块")
        
        # 保存分块
        log.info("3/5: 保存分块记录到数据库...")
        chunk_records = []
        for idx, chunk_content in enumerate(chunks):
            chunk = KnowledgeChunk(
                document_id=document.id,
                chunk_index=idx,
                content=chunk_content,
                start_pos=idx * (chunk_size - chunk_overlap),
                end_pos=idx * (chunk_size - chunk_overlap) + len(chunk_content),
            )
            session.add(chunk)
            chunk_records.append(chunk)
        
        await session.flush()
        log.info(f"✓ 保存 {len(chunk_records)} 个分块记录成功")
        
        # 生成向量
        log.info("4/5: 生成向量...")
        await self._generate_embeddings(session, chunk_records)
        
        # 更新文档的分块总数
        log.info("5/5: 更新文档元数据并提交...")
        document.total_chunks = len(chunks)
        await session.commit()
        
        log.info(f"========== ✓ 成功添加文档: {title} ==========")
        return document
    
    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        智能文本分块算法（参考Dify的递归分割策略）
        
        特点：
        1. 多级分隔符优先级：段落 > 句子 > 空格
        2. 智能合并小片段，尽量接近chunk_size
        3. 递归分割超长片段
        4. 保持文本自然性和语义完整性
        
        Args:
            text: 原始文本
            chunk_size: 每块最大字符数
            overlap: 重叠字符数
            
        Returns:
            分块列表
        """
        # 如果文本很短，直接返回
        if len(text) <= chunk_size:
            return [text.strip()] if text.strip() else []
        
        # 定义分隔符优先级（从高到低）
        # 优先保持段落完整 > 句子完整 > 词语完整 > 字符分割
        separators = [
            "\n\n",      # 段落分隔
            "\n",        # 行分隔  
            "。",        # 中文句号
            "！",        # 中文感叹号
            "？",        # 中文问号
            ";",         # 分号
            ".",         # 英文句号
            "!",         # 英文感叹号
            "?",         # 英文问号
            " ",         # 空格
            "",          # 字符级分割（最后手段）
        ]
        
        # 调用递归分割
        return self._recursive_split(text, separators, chunk_size, overlap)
    
    def _recursive_split(
        self, 
        text: str, 
        separators: List[str], 
        chunk_size: int, 
        overlap: int
    ) -> List[str]:
        """
        递归分割文本
        
        Args:
            text: 待分割文本
            separators: 分隔符列表（按优先级排序）
            chunk_size: 最大分块大小
            overlap: 重叠大小
            
        Returns:
            分块列表
        """
        import re
        
        if not text.strip():
            return []
        
        # 如果文本已经足够小，直接返回
        if len(text) <= chunk_size:
            return [text.strip()]
        
        # 选择当前使用的分隔符
        separator = ""
        new_separators = []
        
        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                break
            # 检查分隔符是否在文本中
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]  # 下一级分隔符
                break
        
        # 如果没有找到任何分隔符，使用字符级分割
        if separator == "" and not new_separators:
            return self._character_split(text, chunk_size, overlap)
        
        # 使用当前分隔符分割文本（保留分隔符）
        if separator == "":
            splits = [text]
        else:
            # 分割并保留分隔符
            parts = text.split(separator)
            splits = []
            for i, part in enumerate(parts[:-1]):
                splits.append(part + separator)  # 将分隔符加回
            if parts[-1]:  # 最后一部分可能没有分隔符
                splits.append(parts[-1])
        
        # 处理分割后的片段
        good_splits = []  # 长度合适的片段
        final_chunks = []
        
        for split in splits:
            split_len = len(split)
            
            if split_len <= chunk_size:
                # 片段大小合适，加入good_splits
                good_splits.append(split)
            else:
                # 片段太大，需要进一步分割
                # 先处理之前积累的good_splits
                if good_splits:
                    merged = self._merge_splits(good_splits, chunk_size, overlap)
                    final_chunks.extend(merged)
                    good_splits = []
                
                # 递归分割这个超长片段
                if new_separators:
                    sub_chunks = self._recursive_split(split, new_separators, chunk_size, overlap)
                    final_chunks.extend(sub_chunks)
                else:
                    # 没有更细的分隔符了，强制字符分割
                    sub_chunks = self._character_split(split, chunk_size, overlap)
                    final_chunks.extend(sub_chunks)
        
        # 处理剩余的good_splits
        if good_splits:
            merged = self._merge_splits(good_splits, chunk_size, overlap)
            final_chunks.extend(merged)
        
        return [c for c in final_chunks if c.strip()]
    
    def _merge_splits(self, splits: List[str], chunk_size: int, overlap: int) -> List[str]:
        """
        智能合并小片段，尽量让每个chunk接近chunk_size
        
        Args:
            splits: 待合并的片段列表
            chunk_size: 最大分块大小
            overlap: 重叠大小
            
        Returns:
            合并后的分块列表
        """
        if not splits:
            return []
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_len = len(split)
            
            # 检查加入这个片段后是否会超过chunk_size
            if current_length + split_len > chunk_size and current_chunk:
                # 超过了，先保存当前chunk
                chunks.append("".join(current_chunk))
                
                # 创建重叠部分：保留当前chunk的尾部作为新chunk的开头
                overlap_text = self._create_overlap(current_chunk, overlap)
                if overlap_text:
                    current_chunk = [overlap_text]
                    current_length = len(overlap_text)
                else:
                    current_chunk = []
                    current_length = 0
            
            # 加入新片段
            current_chunk.append(split)
            current_length += split_len
        
        # 保存最后的chunk
        if current_chunk:
            chunks.append("".join(current_chunk))
        
        return chunks
    
    def _create_overlap(self, chunks: List[str], overlap: int) -> str:
        """
        从chunk列表的尾部创建重叠部分
        
        Args:
            chunks: 片段列表
            overlap: 期望的重叠长度
            
        Returns:
            重叠文本
        """
        if not chunks or overlap <= 0:
            return ""
        
        # 从尾部开始累积，直到达到overlap长度
        overlap_parts = []
        total_len = 0
        
        for chunk in reversed(chunks):
            overlap_parts.insert(0, chunk)
            total_len += len(chunk)
            if total_len >= overlap:
                break
        
        overlap_text = "".join(overlap_parts)
        
        # 如果重叠文本太长，截取尾部
        if len(overlap_text) > overlap:
            overlap_text = overlap_text[-overlap:]
        
        return overlap_text
    
    def _character_split(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        字符级强制分割（最后手段）
        
        Args:
            text: 文本
            chunk_size: 最大分块大小
            overlap: 重叠大小
            
        Returns:
            分块列表
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk = text[start:end]
            chunks.append(chunk)
            
            # 计算下一个起始位置
            start += chunk_size - overlap
            
            # 防止无限循环
            if start <= end - chunk_size and overlap >= chunk_size:
                start = end
        
        return [c.strip() for c in chunks if c.strip()]
    
    async def _generate_embeddings(self, session: AsyncSession, chunks: List[KnowledgeChunk]):
        """为分块生成向量"""
        if not chunks:
            log.info("没有分块需要生成向量")
            return

        log.info(f"开始为 {len(chunks)} 个分块生成向量...")

        # 验证输入
        if not self.embedding_service:
            raise ValueError("Embedding服务未初始化")

        # 提取文本
        try:
            texts = [chunk.content for chunk in chunks]
            if not texts:
                raise ValueError("分块列表为空")

            # 验证文本内容
            for i, text in enumerate(texts):
                if not text or not isinstance(text, str):
                    raise ValueError(f"第{i+1}个分块内容无效: {text}")

            log.debug(f"分块内容示例: {texts[0][:100]}..." if texts else "无内容")

        except Exception as e:
            log.error(f"❌ 提取分块文本失败: {e}")
            raise ValueError(f"分块数据格式错误: {e}")

        # 批量生成向量
        try:
            log.info(f"调用Embedding服务批量生成向量...")
            embeddings = await self.embedding_service.embed_batch(texts)

            # 验证返回的embeddings
            if not embeddings:
                raise ValueError("Embedding服务返回空结果")

            if len(embeddings) != len(chunks):
                raise ValueError(f"Embedding数量不匹配: 期望{len(chunks)}，实际{len(embeddings)}")

            log.info(f"Embedding服务返回 {len(embeddings)} 个向量")

        except (TimeoutError, ConnectionError) as e:
            log.error(f"❌ Embedding服务连接失败: {e}")
            raise ConnectionError(f"无法连接到Embedding服务: {e}")

        except ValueError as e:
            log.error(f"❌ Embedding数据验证失败: {e}")
            raise

        except Exception as e:
            log.error(f"❌ 生成向量失败: {type(e).__name__}: {e}")
            import traceback
            log.error(f"错误堆栈: {traceback.format_exc()}")
            raise RuntimeError(f"Embedding生成失败: {e}")

        # 保存向量到数据库
        try:
            log.info(f"开始保存向量到数据库...")
            saved_count = 0

            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                try:
                    # 验证embedding
                    if not embedding or not isinstance(embedding, list):
                        log.warning(f"第{idx+1}个embedding格式无效，跳过")
                        continue

                    # 转换为numpy数组并序列化
                    vector_array = np.array(embedding, dtype=np.float32)
                    vector_bytes = vector_array.tobytes()

                    vector_embedding = VectorEmbedding(
                        chunk_id=chunk.id,
                        embedding=vector_bytes,
                        model_name=self.embedding_service.model,
                        dimension=len(embedding),
                    )
                    session.add(vector_embedding)
                    saved_count += 1

                    if (saved_count) % 10 == 0:
                        log.debug(f"已保存 {saved_count}/{len(chunks)} 个向量")

                except Exception as item_error:
                    log.warning(f"保存第{idx+1}个向量失败: {item_error}, 继续处理下一个")
                    continue

            if saved_count == 0:
                raise ValueError("没有成功保存任何向量")

            log.info(f"向量保存完成，开始flush到数据库...")
            await session.flush()
            log.info(f"✓ 成功生成并保存 {saved_count}/{len(chunks)} 个向量")

            if saved_count < len(chunks):
                log.warning(f"⚠️ 有 {len(chunks) - saved_count} 个向量保存失败")

        except ValueError as e:
            log.error(f"❌ 向量保存验证失败: {e}")
            raise

        except Exception as e:
            log.error(f"❌ 保存向量到数据库失败: {type(e).__name__}: {e}")
            import traceback
            log.error(f"错误堆栈: {traceback.format_exc()}")
            raise RuntimeError(f"数据库保存失败: {e}")
    
    async def search(
        self,
        session: AsyncSession,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        use_rerank: bool = True,
        document_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索知识库
        
        Args:
            session: 数据库会话
            query: 查询文本
            top_k: 返回前k个结果
            score_threshold: 相似度阈值
            use_rerank: 是否使用rerank
            document_ids: 限制搜索的文档ID列表（None表示搜索所有文档）
            
        Returns:
            搜索结果列表
        """
        # 生成查询向量
        query_embedding = await self.embedding_service.embed_text(query)
        query_vector = np.array(query_embedding, dtype=np.float32)
        
        # 构建查询
        query_stmt = (
            select(VectorEmbedding, KnowledgeChunk, KnowledgeDocument)
            .join(KnowledgeChunk, VectorEmbedding.chunk_id == KnowledgeChunk.id)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        )
        
        # 如果指定了文档ID，添加过滤条件
        if document_ids is not None and len(document_ids) > 0:
            query_stmt = query_stmt.where(KnowledgeDocument.id.in_(document_ids))
            log.info(f"搜索范围限定为文档ID: {document_ids}")
        
        # 执行查询
        result = await session.execute(query_stmt)
        
        all_records = result.all()
        
        if not all_records:
            return []
        
        # 计算相似度
        similarities = []
        for embedding_record, chunk, document in all_records:
            # 反序列化向量
            stored_vector = np.frombuffer(embedding_record.embedding, dtype=np.float32)
            
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_vector, stored_vector)
            
            if similarity >= score_threshold:
                similarities.append({
                    "chunk": chunk,
                    "document": document,
                    "similarity": float(similarity),
                })
        
        # 排序
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        # 取前top_k个
        top_results = similarities[:top_k * 2]  # 取更多结果用于rerank
        
        # 如果启用rerank且有rerank服务
        if use_rerank and self.rerank_service and top_results:
            top_results = await self._rerank_results(query, top_results, top_k)
        else:
            top_results = top_results[:top_k]
        
        # 格式化结果
        return [
            {
                "content": result["chunk"].content,
                "document_title": result["document"].title,
                "chunk_index": result["chunk"].chunk_index,
                "similarity": result["similarity"],
                "document_id": result["document"].id,
            }
            for result in top_results
        ]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def _rerank_results(
        self,
        query: str,
        results: List[Dict],
        top_k: int,
    ) -> List[Dict]:
        """使用rerank模型重排序结果"""
        try:
            # 提取文档内容
            documents = [result["chunk"].content for result in results]
            
            # 调用rerank
            reranked = await self.rerank_service.rerank(query, documents, top_k)
            
            # 重新组织结果
            reranked_results = []
            for item in reranked:
                idx = item["index"]
                if idx < len(results):
                    result = results[idx].copy()
                    result["rerank_score"] = item["score"]
                    reranked_results.append(result)
            
            return reranked_results[:top_k]
            
        except Exception as e:
            log.error(f"Rerank失败: {e}")
            return results[:top_k]
    
    async def get_document_list(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> List[KnowledgeDocument]:
        """获取文档列表"""
        result = await session.execute(
            select(KnowledgeDocument)
            .order_by(KnowledgeDocument.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_document_chunks(
        self,
        session: AsyncSession,
        document_id: int,
    ) -> List[KnowledgeChunk]:
        """获取文档的所有分块"""
        # 验证文档存在
        result = await session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"文档不存在: {document_id}")
        
        # 获取所有分块，按chunk_index排序
        result = await session.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index)
        )
        return result.scalars().all()
    
    async def delete_document(self, session: AsyncSession, document_id: int):
        """删除文档"""
        # 获取文档
        result = await session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"文档不存在: {document_id}")
        
        # 删除相关的向量和分块（通过级联删除或手动删除）
        # 这里简单起见，假设数据库配置了级联删除
        await session.delete(document)
        await session.commit()
        
        log.info(f"成功删除文档: {document_id}")

