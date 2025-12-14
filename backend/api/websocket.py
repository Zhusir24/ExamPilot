"""WebSocket API - 答题实时通信"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional
import json
from datetime import datetime
from backend.core.database import async_session_maker
from backend.models.schema import (
    Questionnaire, 
    QuestionRecord, 
    AnsweringSession as AnsweringSessionDB,  # 重命名避免冲突
    AnswerRecord, 
    LLMConfig, 
    SystemSetting
)
from backend.models.question import Question, QuestionType
from backend.models.answer import Answer, AnswerStatus
from backend.services.platforms import get_platform
from backend.services.llm_service import LLMService, EmbeddingService, RerankService
from backend.services.knowledge_base import KnowledgeBaseService
from backend.services.answering_modes import AnsweringMode, ModeHandler
from backend.services.timing_simulator import TimingSimulator, TimingStrategy, TimingProfile
from backend.core.logger import log
from backend.api.settings import deserialize_value
from backend.core.encryption import encryption_service

router = APIRouter()


class AnsweringSession:
    """答题会话"""
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.questionnaire_id: Optional[int] = None
        self.session_id: Optional[int] = None  # 数据库会话ID
        self.mode: Optional[AnsweringMode] = None
        self.questions: list = []
        self.answers: Dict[str, Answer] = {}
    
    async def send_message(self, message_type: str, data: Any):
        """发送消息"""
        await self.websocket.send_json({
            "type": message_type,
            "data": data,
        })
    
    async def send_error(self, error: str):
        """发送错误消息"""
        await self.send_message("error", {"message": error})
    
    async def send_progress(self, current: int, total: int, question_id: str, answer: dict):
        """发送进度消息"""
        await self.send_message("progress", {
            "current": current,
            "total": total,
            "question_id": question_id,
            "answer": answer,
        })
    
    async def send_complete(self, results: dict):
        """发送完成消息"""
        await self.send_message("complete", results)


@router.websocket("/ws/answer")
async def websocket_answer_endpoint(websocket: WebSocket):
    """答题WebSocket端点"""
    await websocket.accept()
    session = AnsweringSession(websocket)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "start":
                # 开始答题
                await handle_start_answering(session, data)
            
            elif command == "confirm":
                # 确认低置信度答案
                await handle_confirm_answer(session, data)
            
            elif command == "submit":
                # 提交答案
                await handle_submit_answers(session, data)
            
            else:
                await session.send_error(f"未知命令: {command}")
    
    except WebSocketDisconnect:
        log.info("WebSocket连接断开")
    except Exception as e:
        log.error(f"WebSocket错误: {e}")
        await session.send_error(str(e))


async def handle_start_answering(session: AnsweringSession, data: dict):
    """处理开始答题"""
    try:
        questionnaire_id = data.get("questionnaire_id")
        mode = data.get("mode", "FULL_AUTO")
        selected_questions = data.get("selected_questions", [])
        preset_answers = data.get("preset_answers", [])
        knowledge_config = data.get("knowledge_config")  # 获取知识库配置
        
        async with async_session_maker() as db:
            # 获取问卷
            result = await db.execute(
                select(Questionnaire).where(Questionnaire.id == questionnaire_id)
            )
            questionnaire = result.scalar_one_or_none()
            
            if not questionnaire:
                await session.send_error("问卷不存在")
                return
            
            # 获取题目
            result = await db.execute(
                select(QuestionRecord)
                .where(QuestionRecord.questionnaire_id == questionnaire_id)
                .order_by(QuestionRecord.order)
            )
            question_records = result.scalars().all()
            
            # 转换为Question对象
            questions = [
                Question(
                    id=q.question_id,
                    type=QuestionType(q.question_type),
                    content=q.content,
                    options=q.options,
                    order=q.order,
                    required=q.required,
                    platform_data=q.platform_data,
                )
                for q in question_records
            ]
            
            session.questions = questions
            session.questionnaire_id = questionnaire_id
            # 转换mode为枚举对象
            mode_enum = AnsweringMode(mode)
            session.mode = mode_enum
            
            # 获取LLM配置
            llm_service = await get_active_llm_service(db)
            if not llm_service:
                await session.send_error("未配置LLM服务，请先在'LLM设置'中添加配置")
                return
            
            embedding_service = await get_active_embedding_service(db)
            rerank_service = await get_active_rerank_service(db)
            
            # 创建知识库服务（如果有embedding服务）
            kb_service = None
            if embedding_service:
                kb_service = KnowledgeBaseService(embedding_service, rerank_service)
            
            # 创建模式处理器
            mode_handler = ModeHandler(llm_service, kb_service)
            
            # 创建答题会话（mode是字符串）
            answering_session_db = AnsweringSessionDB(
                questionnaire_id=questionnaire_id,
                mode=mode,  # 直接使用字符串
                status="in_progress",
                total_questions=len(questions),
                answered_questions=0,
            )
            db.add(answering_session_db)
            await db.commit()
            await db.refresh(answering_session_db)
            
            session.session_id = answering_session_db.id
            log.info(f"创建答题会话: ID={answering_session_db.id}, 模式={mode}")
            
            # 获取系统设置
            settings = await get_system_settings(db)
            confidence_threshold = settings.get("confidence_threshold", 0.7)
            visual_mode = settings.get("visual_mode", False)  # 可视化模式

            # 可视化模式提示
            if visual_mode:
                log.info("=" * 60)
                log.info("🎬 可视化答题模式已启用")
                log.info("📺 浏览器窗口即将弹出，您可以实时观看答题过程")
                log.info("=" * 60)
            
            # 知识库配置：优先使用前端传递的配置，如果未启用则使用系统设置
            if knowledge_config and knowledge_config.get("enabled"):
                use_knowledge = True
                kb_document_ids = knowledge_config.get("document_ids", [])
                kb_top_k = knowledge_config.get("top_k", 3)
                kb_score_threshold = knowledge_config.get("score_threshold", 0.5)
                log.info(f"使用知识库配置: 文档={kb_document_ids}, top_k={kb_top_k}, 阈值={kb_score_threshold}")
            else:
                # 使用系统设置的默认值
                use_knowledge = settings.get("use_knowledge_base", False)
                kb_document_ids = None
                kb_top_k = 3
                kb_score_threshold = 0.5
            
            # 创建时间模拟器
            timing_simulator = await get_timing_simulator(db)
            
            # 进度回调（发送进度并实时保存到数据库）
            async def progress_callback(progress_data):
                try:
                    await session.send_progress(
                        progress_data["current"],
                        progress_data["total"],
                        progress_data["question_id"],
                        progress_data["answer"],
                    )
                except Exception as e:
                    # WebSocket断开不影响答题
                    log.warning(f"发送进度失败: {e}")

                # 实时保存答案和更新进度到数据库
                try:
                    # 1. 保存答案记录
                    answer_data = progress_data["answer"]
                    question_id = progress_data["question_id"]

                    # 检查是否已存在该题答案（避免重复保存）
                    existing_answer = await db.execute(
                        select(AnswerRecord).where(
                            AnswerRecord.session_id == answering_session_db.id,
                            AnswerRecord.question_id == question_id
                        )
                    )
                    existing = existing_answer.scalar_one_or_none()

                    if existing:
                        # 更新已有答案
                        existing.content = json.dumps(answer_data.get("content"), ensure_ascii=False)
                        existing.status = answer_data.get("status")
                        existing.confidence = answer_data.get("confidence")
                        existing.reasoning = answer_data.get("reasoning")
                        existing.knowledge_references = answer_data.get("knowledge_references")
                    else:
                        # 创建新答案记录
                        answer_record = AnswerRecord(
                            session_id=answering_session_db.id,
                            questionnaire_id=questionnaire_id,
                            question_id=question_id,
                            content=json.dumps(answer_data.get("content"), ensure_ascii=False),
                            status=answer_data.get("status"),
                            confidence=answer_data.get("confidence"),
                            reasoning=answer_data.get("reasoning"),
                            knowledge_references=answer_data.get("knowledge_references"),
                        )
                        db.add(answer_record)

                    # 2. 更新会话进度
                    answering_session_db.answered_questions = progress_data["current"]

                    # 3. 增量更新平均置信度
                    new_confidence = answer_data.get("confidence")
                    if new_confidence is not None:
                        current = progress_data["current"]
                        prev_avg = answering_session_db.avg_confidence or 0
                        prev_count = current - 1
                        answering_session_db.avg_confidence = (
                            (prev_avg * prev_count + new_confidence) / current
                        ) if current > 0 else new_confidence

                    await db.commit()
                    log.debug(f"实时保存答案: {question_id}, 进度: {progress_data['current']}/{progress_data['total']}")

                except Exception as db_error:
                    log.warning(f"实时保存答案失败: {db_error}")
                    await db.rollback()
                    # 不影响答题继续
            
            # 根据模式执行答题
            if session.mode == AnsweringMode.FULL_AUTO:
                answers = await mode_handler.handle_full_auto(
                    questions, db, use_knowledge, confidence_threshold, progress_callback, timing_simulator,
                    kb_document_ids, kb_top_k, kb_score_threshold
                )
            elif session.mode == AnsweringMode.USER_SELECT:
                answers = await mode_handler.handle_user_select(
                    questions, selected_questions, db, use_knowledge, progress_callback,
                    kb_document_ids, kb_top_k, kb_score_threshold
                )
            elif session.mode == AnsweringMode.PRESET_ANSWERS:
                answers = await mode_handler.handle_preset_answers(
                    questions, preset_answers, progress_callback
                )
            else:
                await session.send_error(f"不支持的答题模式: {mode}")
                return
            
            session.answers = answers

            # 答案已通过progress_callback实时保存，这里只需要更新会话状态为完成
            answering_session_db.status = "completed"
            answering_session_db.end_time = datetime.utcnow()
            if answering_session_db.start_time:
                duration = (answering_session_db.end_time - answering_session_db.start_time).total_seconds()
                answering_session_db.duration = int(duration)
            
            await db.commit()
            log.info(f"答题会话完成: ID={answering_session_db.id}, 已答={answering_session_db.answered_questions}/{answering_session_db.total_questions}, 平均置信度={answering_session_db.avg_confidence:.2%}")
            
            # 发送完成消息
            await session.send_complete({
                "total": len(answers),
                "answers": {k: v.model_dump() if hasattr(v, 'model_dump') else v.dict() for k, v in answers.items()},
            })
    
    except Exception as e:
        import traceback
        error_msg = str(e) if str(e) else "未知错误"
        error_traceback = traceback.format_exc()
        log.error(f"答题失败: {error_msg}\n{error_traceback}")

        # 尝试更新会话状态为失败并保存错误信息
        try:
            async with async_session_maker() as db:
                if hasattr(session, 'session_id') and session.session_id:
                    result = await db.execute(
                        select(AnsweringSessionDB).where(AnsweringSessionDB.id == session.session_id)
                    )
                    answering_session_db = result.scalar_one_or_none()
                    if answering_session_db:
                        answering_session_db.status = "failed"
                        answering_session_db.end_time = datetime.utcnow()
                        # 保存错误信息到submission_result字段
                        answering_session_db.submission_result = json.dumps({
                            "success": False,
                            "error": error_msg,
                            "traceback": error_traceback
                        }, ensure_ascii=False)
                        await db.commit()
                        log.info(f"答题会话标记为失败: ID={session.session_id}, 错误: {error_msg}")
        except Exception as update_error:
            log.error(f"更新会话状态失败: {update_error}")

        await session.send_error(error_msg)


async def handle_confirm_answer(session: AnsweringSession, data: dict):
    """处理确认答案"""
    question_id = data.get("question_id")
    confirmed_answer = data.get("answer")
    
    if question_id in session.answers:
        answer = session.answers[question_id]
        answer.content = confirmed_answer
        answer.status = AnswerStatus.USER_CONFIRMED
        answer.confidence = 1.0
        
        await session.send_message("answer_confirmed", {
            "question_id": question_id,
            "answer": answer.model_dump() if hasattr(answer, 'model_dump') else answer.dict(),
        })


async def handle_submit_answers(session: AnsweringSession, data: dict):
    """处理提交答案"""
    try:
        async with async_session_maker() as db:
            # 获取问卷
            result = await db.execute(
                select(Questionnaire).where(Questionnaire.id == session.questionnaire_id)
            )
            questionnaire = result.scalar_one_or_none()

            if not questionnaire:
                await session.send_error("问卷不存在")
                return

            # 获取系统设置
            settings = await get_system_settings(db)
            visual_mode = settings.get("visual_mode", False)

            # 获取平台适配器
            platform = get_platform(questionnaire.url)

            # 准备答案数据
            answers_to_submit = {}
            for question_id, answer in session.answers.items():
                answers_to_submit[question_id] = answer.content

            # 提交答案
            if visual_mode:
                await session.send_message("submitting", {
                    "message": "可视化模式：正在浏览器中填写答案，请查看浏览器窗口..."
                })
            else:
                await session.send_message("submitting", {"message": "正在提交答案..."})

            result = await platform.submit_answers(questionnaire.url, answers_to_submit, visual_mode=visual_mode)
            
            # 更新数据库
            if result.get("success"):
                update_result = await db.execute(
                    select(AnswerRecord).where(
                        AnswerRecord.questionnaire_id == session.questionnaire_id
                    )
                )
                answer_records = update_result.scalars().all()
                
                for record in answer_records:
                    record.submitted = True
                
                # 更新答题会话
                if hasattr(session, 'session_id') and session.session_id:
                    session_result = await db.execute(
                        select(AnsweringSessionDB).where(AnsweringSessionDB.id == session.session_id)
                    )
                    answering_session_db = session_result.scalar_one_or_none()
                    if answering_session_db:
                        answering_session_db.submitted = True
                        answering_session_db.submission_result = json.dumps(result, ensure_ascii=False)
                        log.info(f"答题会话已提交: ID={session.session_id}")
                
                await db.commit()
            
            # 发送结果
            await session.send_message("submit_result", result)
    
    except Exception as e:
        log.error(f"提交答案失败: {e}")
        await session.send_error(str(e))


async def get_active_llm_service(db: AsyncSession) -> Optional[LLMService]:
    """获取激活的LLM服务"""
    result = await db.execute(
        select(LLMConfig)
        .where(LLMConfig.config_type == "llm", LLMConfig.is_active == True)
        .limit(1)
    )
    config = result.scalar_one_or_none()

    if not config:
        log.warning("未找到激活的LLM配置")
        return None

    if not config.api_key:
        log.warning(f"LLM配置 {config.name} 缺少API密钥")
        return None

    # 解密API密钥（兼容明文）
    decrypted_api_key = encryption_service.decrypt(config.api_key)
    if not decrypted_api_key:
        log.error(f"LLM配置 {config.name} API密钥为空或处理失败")
        return None

    return LLMService(
        api_key=decrypted_api_key,
        base_url=config.base_url,
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


async def get_active_embedding_service(db: AsyncSession) -> Optional[EmbeddingService]:
    """获取激活的Embedding服务"""
    result = await db.execute(
        select(LLMConfig)
        .where(LLMConfig.config_type == "embedding", LLMConfig.is_active == True)
        .limit(1)
    )
    config = result.scalar_one_or_none()

    if not config:
        return None

    # 解密API密钥
    decrypted_api_key = ""
    if config.api_key:
        decrypted_api_key = encryption_service.decrypt(config.api_key) or ""

    return EmbeddingService(
        api_key=decrypted_api_key,
        base_url=config.base_url,
        model=config.model,
    )


async def get_active_rerank_service(db: AsyncSession) -> Optional[RerankService]:
    """获取激活的Rerank服务"""
    result = await db.execute(
        select(LLMConfig)
        .where(LLMConfig.config_type == "rerank", LLMConfig.is_active == True)
        .limit(1)
    )
    config = result.scalar_one_or_none()

    if not config:
        return None

    # 解密API密钥
    decrypted_api_key = ""
    if config.api_key:
        decrypted_api_key = encryption_service.decrypt(config.api_key) or ""

    return RerankService(
        api_key=decrypted_api_key,
        base_url=config.base_url,
        model=config.model,
    )


async def get_system_settings(db: AsyncSession) -> dict:
    """获取系统设置"""
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    
    return {
        s.key: deserialize_value(s.value, s.value_type)
        for s in settings
    }


async def get_timing_simulator(db: AsyncSession) -> TimingSimulator:
    """获取时间模拟器"""
    settings = await get_system_settings(db)

    strategy_str = settings.get("timing_strategy", "none")
    strategy_map = {
        "none": TimingStrategy.NONE,
        "uniform": TimingStrategy.UNIFORM,
        "normal": TimingStrategy.NORMAL,
        "segmented": TimingStrategy.SEGMENTED,
    }
    strategy = strategy_map.get(strategy_str, TimingStrategy.NORMAL)

    min_time = settings.get("timing_min_time", 2.0)
    max_time = settings.get("timing_max_time", 10.0)

    return TimingSimulator(
        strategy=strategy,
        min_time=min_time,
        max_time=max_time,
    )

