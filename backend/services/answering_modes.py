"""答题模式管理"""
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from backend.models.question import Question
from backend.models.answer import Answer, AnswerStatus
from backend.core.logger import log
from backend.services.llm_service import LLMService
from backend.services.knowledge_base import KnowledgeBaseService
from sqlalchemy.ext.asyncio import AsyncSession


class AnsweringMode(str, Enum):
    """答题模式"""
    FULL_AUTO = "FULL_AUTO"
    USER_SELECT = "USER_SELECT"
    PRESET_ANSWERS = "PRESET_ANSWERS"
    
    @property
    def display_name(self) -> str:
        """显示名称（中文）"""
        names = {
            "FULL_AUTO": "全自动AI答题",
            "USER_SELECT": "用户勾选AI介入",
            "PRESET_ANSWERS": "预设答案自动填充",
        }
        return names.get(self.value, self.value)


class ModeHandler:
    """答题模式处理器"""
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        knowledge_service: Optional[KnowledgeBaseService] = None,
    ):
        self.llm_service = llm_service
        self.knowledge_service = knowledge_service
    
    async def handle_full_auto(
        self,
        questions: List[Question],
        session: AsyncSession,
        use_knowledge: bool = True,
        confidence_threshold: float = 0.7,
        callback: Optional[Callable] = None,
        timing_simulator = None,
        kb_document_ids: Optional[List[int]] = None,
        kb_top_k: int = 3,
        kb_score_threshold: float = 0.5,
    ) -> Dict[str, Answer]:
        """
        全自动AI答题模式
        
        Args:
            questions: 题目列表
            session: 数据库会话
            use_knowledge: 是否使用知识库
            confidence_threshold: 置信度阈值
            callback: 进度回调函数
            kb_document_ids: 知识库文档ID列表（None表示搜索所有文档）
            kb_top_k: 使用前N个知识块
            kb_score_threshold: 相似度阈值
            
        Returns:
            答案字典，key为题目ID
        """
        log.info(f"开始全自动AI答题，共 {len(questions)} 题")
        log.info(f"使用LLM: {self.llm_service.model} @ {self.llm_service.base_url}")
        answers = {}
        
        for idx, question in enumerate(questions, 1):
            try:
                # 记录题目信息
                log.info(f"")
                log.info(f"━━━ 题目 {idx}/{len(questions)} ━━━")
                log.info(f"ID: {question.id} | 类型: {question.type.value}")
                log.info(f"题目: {question.content[:100]}{'...' if len(question.content) > 100 else ''}")
                if question.options:
                    log.info(f"选项共 {len(question.options)} 个:")
                    for opt_idx, opt in enumerate(question.options):
                        log.info(f"  [{opt_idx}] {opt[:70]}{'...' if len(opt) > 70 else ''}")
                
                # 获取知识库上下文
                knowledge_context = None
                knowledge_references = None
                if use_knowledge and self.knowledge_service:
                    knowledge_context, knowledge_references = await self._get_knowledge_context(
                        session, question, kb_top_k, kb_score_threshold, kb_document_ids
                    )
                    if knowledge_context:
                        log.info(f"引用知识库: {len(knowledge_context)} 字符，共 {len(knowledge_references)} 个引用")
                
                # 使用LLM生成答案
                log.debug(f"调用 {self.llm_service.model}...")
                answer = await self.llm_service.answer_question(
                    question, knowledge_context
                )
                
                # 添加知识库引用信息
                if knowledge_references:
                    answer.knowledge_references = knowledge_references
                
                # 记录答案
                log.info(f"AI答案: {answer.content}")
                log.info(f"置信度: {answer.confidence:.2%}")
                log.info(f"推理: {answer.reasoning[:80]}{'...' if len(answer.reasoning) > 80 else ''}")
                
                # 模拟人类答题时间
                if timing_simulator:
                    await timing_simulator.wait_before_answer(idx, len(questions))
                
                # 检查置信度
                if answer.needs_confirmation(confidence_threshold):
                    log.warning(
                        f"⚠️  置信度较低 ({answer.confidence:.2%} < {confidence_threshold:.2%})，建议人工确认"
                    )
                else:
                    log.info(f"✓ 置信度正常 ({answer.confidence:.2%})")
                
                answers[question.id] = answer
                
                # 回调进度（即使失败也不影响答题）
                if callback:
                    try:
                        await callback({
                            "current": idx,
                            "total": len(questions),
                            "question_id": question.id,
                            "answer": answer.dict(),
                        })
                    except Exception as callback_error:
                        log.warning(f"进度回调失败: {callback_error}")
                
                log.info(f"✓ 完成题目 {idx}/{len(questions)}")
                log.info("─" * 60)
                
            except Exception as e:
                error_msg = str(e) if str(e) else repr(e)
                log.error(f"答题失败 {question.id}: {error_msg}", exc_info=True)
                answers[question.id] = Answer(
                    question_id=question.id,
                    content="",
                    status=AnswerStatus.FAILED,
                    reasoning=error_msg or "未知错误",
                )
        
        return answers
    
    async def handle_user_select(
        self,
        questions: List[Question],
        selected_question_ids: List[str],
        session: AsyncSession,
        use_knowledge: bool = True,
        callback: Optional[Callable] = None,
        kb_document_ids: Optional[List[int]] = None,
        kb_top_k: int = 3,
        kb_score_threshold: float = 0.5,
    ) -> Dict[str, Answer]:
        """
        用户勾选AI介入模式
        
        Args:
            questions: 题目列表
            selected_question_ids: 用户选择需要AI答题的题目ID列表
            session: 数据库会话
            use_knowledge: 是否使用知识库
            callback: 进度回调函数
            kb_document_ids: 知识库文档ID列表（None表示搜索所有文档）
            kb_top_k: 使用前N个知识块
            kb_score_threshold: 相似度阈值
            
        Returns:
            答案字典，仅包含选中的题目
        """
        log.info(
            f"用户勾选模式，共 {len(questions)} 题，"
            f"选中 {len(selected_question_ids)} 题"
        )
        
        # 过滤出用户选中的题目
        selected_questions = [
            q for q in questions if q.id in selected_question_ids
        ]
        
        # 对选中的题目使用全自动模式
        return await self.handle_full_auto(
            selected_questions, session, use_knowledge, 
            callback=callback,
            kb_document_ids=kb_document_ids,
            kb_top_k=kb_top_k,
            kb_score_threshold=kb_score_threshold
        )
    
    async def handle_preset_answers(
        self,
        questions: List[Question],
        preset_answers: List[Any],
        callback: Optional[Callable] = None,
    ) -> Dict[str, Answer]:
        """
        预设答案自动填充模式
        
        Args:
            questions: 题目列表
            preset_answers: 预设答案列表，按题目顺序
            callback: 进度回调函数
            
        Returns:
            答案字典
        """
        log.info(f"预设答案模式，共 {len(questions)} 题")
        answers = {}
        
        for idx, question in enumerate(questions):
            try:
                # 获取预设答案
                if idx < len(preset_answers):
                    answer_content = preset_answers[idx]
                else:
                    answer_content = ""
                    log.warning(f"题目 {question.id} 没有预设答案")

                # 验证答案格式
                is_valid, error_msg = question.validate_answer(answer_content)

                if not is_valid:
                    log.error(
                        f"❌ 题目 {idx+1}({question.id}) 的预设答案无效: {answer_content}\n"
                        f"   错误: {error_msg}\n"
                        f"   题目: {question.content[:50]}..."
                    )
                    # 创建失败状态的答案
                    answer = Answer(
                        question_id=question.id,
                        content="",
                        status=AnswerStatus.FAILED,
                        confidence=0.0,
                        reasoning=f"答案验证失败: {error_msg}",
                    )
                else:
                    # 验证通过,创建预设答案
                    answer = Answer(
                        question_id=question.id,
                        content=answer_content,
                        status=AnswerStatus.PRESET,
                        confidence=1.0,
                        reasoning="预设答案",
                    )
                    log.info(f"✓ 题目 {idx+1}({question.id}) 预设答案有效: {answer_content}")

                answers[question.id] = answer
                
                # 回调进度
                if callback:
                    await callback({
                        "current": idx + 1,
                        "total": len(questions),
                        "question_id": question.id,
                        "answer": answer.dict(),
                    })
                
            except Exception as e:
                log.error(f"填充预设答案失败 {question.id}: {e}")
                answers[question.id] = Answer(
                    question_id=question.id,
                    content="",
                    status=AnswerStatus.FAILED,
                    reasoning=str(e),
                )
        
        return answers
    
    async def _get_knowledge_context(
        self,
        session: AsyncSession,
        question: Question,
        top_k: int = 3,
        score_threshold: float = 0.5,
        document_ids: Optional[List[int]] = None,
    ) -> tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        获取知识库上下文
        
        Returns:
            tuple: (上下文字符串, 引用信息列表)
        """
        # 如果没有知识库服务，直接返回None
        if not self.knowledge_service:
            return None, None
            
        try:
            # 搜索相关知识
            results = await self.knowledge_service.search(
                session=session,
                query=question.content,
                top_k=top_k,
                score_threshold=score_threshold,
                document_ids=document_ids,
            )
            
            if not results:
                return None, None
            
            # 组合上下文
            context_parts = []
            references = []
            
            for idx, result in enumerate(results, 1):
                context_parts.append(
                    f"参考资料{idx}（来自《{result['document_title']}》，"
                    f"相似度：{result['similarity']:.2f}）：\n{result['content']}"
                )
                
                # 保存引用信息（用于前端展示）
                references.append({
                    "document_id": result['document_id'],
                    "document_title": result['document_title'],
                    "chunk_index": result['chunk_index'],
                    "content": result['content'],
                    "similarity": result['similarity'],
                })
            
            return "\n\n".join(context_parts), references
            
        except Exception as e:
            log.warning(f"获取知识库上下文失败: {e}")
            return None, None

