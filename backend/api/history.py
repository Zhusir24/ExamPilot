"""历史记录API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime
import json

from backend.core.database import get_db
from backend.models.schema import AnsweringSession, Questionnaire, QuestionRecord, AnswerRecord
from backend.core.logger import log

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/sessions")
async def get_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    questionnaire_id: Optional[int] = None,
    mode: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取答题会话列表
    
    Args:
        page: 页码
        page_size: 每页数量
        questionnaire_id: 问卷ID筛选
        mode: 答题模式筛选
        status: 状态筛选
        start_date: 起始日期
        end_date: 结束日期
    """
    try:
        # 构建查询
        query = select(AnsweringSession).join(
            Questionnaire, AnsweringSession.questionnaire_id == Questionnaire.id
        )
        
        # 添加筛选条件
        if questionnaire_id:
            query = query.where(AnsweringSession.questionnaire_id == questionnaire_id)
        if mode:
            query = query.where(AnsweringSession.mode == mode)
        if status:
            query = query.where(AnsweringSession.status == status)
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.where(AnsweringSession.start_time >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.where(AnsweringSession.start_time <= end_dt)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 排序和分页
        query = query.order_by(desc(AnsweringSession.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # 执行查询
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        # 构建响应
        items = []
        for session in sessions:
            # 获取问卷信息
            quest_result = await db.execute(
                select(Questionnaire).where(Questionnaire.id == session.questionnaire_id)
            )
            questionnaire = quest_result.scalar_one_or_none()
            
            # 模式显示名称
            mode_display = {
                "FULL_AUTO": "全自动AI答题",
                "USER_SELECT": "用户勾选AI介入",
                "PRESET_ANSWERS": "预设答案自动填充",
            }.get(session.mode, session.mode)
            
            items.append({
                "id": session.id,
                "questionnaire": {
                    "id": questionnaire.id if questionnaire else None,
                    "title": questionnaire.title if questionnaire else "未知问卷",
                    "url": questionnaire.url if questionnaire else "",
                } if questionnaire else None,
                "mode": session.mode,
                "mode_display": mode_display,
                "status": session.status,
                "total_questions": session.total_questions,
                "answered_questions": session.answered_questions,
                "correct_answers": session.correct_answers,
                "avg_confidence": session.avg_confidence,
                "duration": session.duration,
                "submitted": session.submitted,
                "submission_result": session.submission_result,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "created_at": session.created_at.isoformat() if session.created_at else None,
            })
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
        
    except Exception as e:
        log.error(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取答题会话详情"""
    try:
        # 获取会话
        result = await db.execute(
            select(AnsweringSession).where(AnsweringSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取问卷信息
        quest_result = await db.execute(
            select(Questionnaire).where(Questionnaire.id == session.questionnaire_id)
        )
        questionnaire = quest_result.scalar_one_or_none()
        
        # 获取问题列表
        questions_result = await db.execute(
            select(QuestionRecord)
            .where(QuestionRecord.questionnaire_id == session.questionnaire_id)
            .order_by(QuestionRecord.order)
        )
        questions = questions_result.scalars().all()
        
        # 获取答案列表
        answers_result = await db.execute(
            select(AnswerRecord)
            .where(AnswerRecord.session_id == session_id)
        )
        answers = answers_result.scalars().all()
        
        # 构建答案字典
        answers_dict = {answer.question_id: answer for answer in answers}
        
        # 构建详细答案列表
        detailed_answers = []
        for question in questions:
            answer = answers_dict.get(question.question_id)
            
            answer_content = None
            answer_display = None
            if answer:
                try:
                    answer_content = json.loads(answer.content) if answer.content else None
                    # 格式化显示
                    if isinstance(answer_content, str) and '|' in answer_content:
                        parts = answer_content.split('|', 1)
                        answer_display = parts[1] if len(parts) > 1 else answer_content
                    else:
                        answer_display = answer_content
                except:
                    answer_content = answer.content
                    answer_display = answer.content
            
            # 解析选项
            options = None
            if question.options:
                try:
                    options = json.loads(question.options) if isinstance(question.options, str) else question.options
                except:
                    options = question.options
            
            # 解析知识库引用
            knowledge_references = None
            if answer and answer.knowledge_references:
                try:
                    knowledge_references = json.loads(answer.knowledge_references) if isinstance(answer.knowledge_references, str) else answer.knowledge_references
                except:
                    knowledge_references = answer.knowledge_references

            detailed_answers.append({
                "question_id": question.question_id,
                "question": {
                    "order": question.order,
                    "type": question.question_type,
                    "content": question.content,
                    "options": options,
                    "required": question.required,
                },
                "answer": answer_content if answer else None,
                "answer_display": answer_display,
                "confidence": answer.confidence if answer else None,
                "reasoning": answer.reasoning if answer else None,
                "status": answer.status if answer else None,
                "knowledge_references": knowledge_references,
            })
        
        # 模式显示名称
        mode_display = {
            "FULL_AUTO": "全自动AI答题",
            "USER_SELECT": "用户勾选AI介入",
            "PRESET_ANSWERS": "预设答案自动填充",
        }.get(session.mode, session.mode)
        
        return {
            "session": {
                "id": session.id,
                "mode": session.mode,
                "mode_display": mode_display,
                "status": session.status,
                "total_questions": session.total_questions,
                "answered_questions": session.answered_questions,
                "correct_answers": session.correct_answers,
                "avg_confidence": session.avg_confidence,
                "duration": session.duration,
                "submitted": session.submitted,
                "submission_result": session.submission_result,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "end_time": session.end_time.isoformat() if session.end_time else None,
            },
            "questionnaire": {
                "id": questionnaire.id if questionnaire else None,
                "title": questionnaire.title if questionnaire else "未知问卷",
                "url": questionnaire.url if questionnaire else "",
                "description": questionnaire.description if questionnaire else "",
            } if questionnaire else None,
            "answers": detailed_answers,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"获取会话详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除答题会话"""
    try:
        # 检查会话是否存在
        result = await db.execute(
            select(AnsweringSession).where(AnsweringSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 删除关联的答案
        from sqlalchemy import delete
        await db.execute(
            delete(AnswerRecord).where(AnswerRecord.session_id == session_id)
        )
        
        # 删除会话
        await db.delete(session)
        await db.commit()
        
        log.info(f"删除答题会话: {session_id}")
        
        return {"success": True, "message": "删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"删除会话失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """获取统计信息"""
    try:
        # 总会话数
        total_result = await db.execute(
            select(func.count()).select_from(AnsweringSession)
        )
        total_sessions = total_result.scalar()
        
        # 总答题数
        questions_result = await db.execute(
            select(func.sum(AnsweringSession.answered_questions)).select_from(AnsweringSession)
        )
        total_questions_answered = questions_result.scalar() or 0
        
        # 平均置信度
        avg_result = await db.execute(
            select(func.avg(AnsweringSession.avg_confidence))
            .select_from(AnsweringSession)
            .where(AnsweringSession.avg_confidence.isnot(None))
        )
        avg_confidence = avg_result.scalar() or 0
        
        # 模式分布
        mode_result = await db.execute(
            select(AnsweringSession.mode, func.count())
            .group_by(AnsweringSession.mode)
        )
        mode_distribution = {row[0]: row[1] for row in mode_result.all()}
        
        # 最近5次会话
        recent_result = await db.execute(
            select(AnsweringSession)
            .order_by(desc(AnsweringSession.created_at))
            .limit(5)
        )
        recent_sessions = recent_result.scalars().all()
        
        recent_items = []
        for session in recent_sessions:
            quest_result = await db.execute(
                select(Questionnaire).where(Questionnaire.id == session.questionnaire_id)
            )
            questionnaire = quest_result.scalar_one_or_none()
            
            mode_display = {
                "FULL_AUTO": "全自动AI答题",
                "USER_SELECT": "用户勾选AI介入",
                "PRESET_ANSWERS": "预设答案自动填充",
            }.get(session.mode, session.mode)
            
            recent_items.append({
                "id": session.id,
                "questionnaire_title": questionnaire.title if questionnaire else "未知问卷",
                "mode_display": mode_display,
                "status": session.status,
                "answered_questions": session.answered_questions,
                "avg_confidence": session.avg_confidence,
                "created_at": session.created_at.isoformat() if session.created_at else None,
            })
        
        return {
            "total_sessions": total_sessions,
            "total_questions_answered": total_questions_answered,
            "avg_confidence": float(avg_confidence) if avg_confidence else 0,
            "mode_distribution": mode_distribution,
            "recent_sessions": recent_items,
        }
        
    except Exception as e:
        log.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/submit")
async def submit_session(
    session_id: int,
    answers: dict,  # {question_id: answer_content}
    db: AsyncSession = Depends(get_db),
):
    """提交答题会话（支持用户编辑后的答案）"""
    try:
        # 获取会话
        session_result = await db.execute(
            select(AnsweringSession).where(AnsweringSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 获取问卷
        quest_result = await db.execute(
            select(Questionnaire).where(Questionnaire.id == session.questionnaire_id)
        )
        questionnaire = quest_result.scalar_one_or_none()

        if not questionnaire:
            raise HTTPException(status_code=404, detail="问卷不存在")

        # 更新答案到数据库
        for question_id, answer_content in answers.items():
            answer_result = await db.execute(
                select(AnswerRecord).where(
                    AnswerRecord.session_id == session_id,
                    AnswerRecord.question_id == question_id
                )
            )
            answer_record = answer_result.scalar_one_or_none()

            if answer_record:
                # 更新已有答案
                answer_record.content = json.dumps(answer_content, ensure_ascii=False)
            else:
                # 创建新答案记录（防止遗漏）
                answer_record = AnswerRecord(
                    session_id=session_id,
                    questionnaire_id=session.questionnaire_id,
                    question_id=question_id,
                    content=json.dumps(answer_content, ensure_ascii=False),
                    status="user_edited",
                    confidence=1.0,
                    reasoning="用户手动编辑",
                )
                db.add(answer_record)

        await db.commit()

        # 使用平台适配器提交答案
        from backend.services.platforms import get_platform
        platform = get_platform(questionnaire.url)

        log.info(f"开始提交会话 {session_id} 的答案到问卷平台...")
        result = await platform.submit_answers(questionnaire.url, answers)

        # 更新会话状态
        if result.get("success"):
            session.submitted = True
            session.submission_result = json.dumps(result, ensure_ascii=False)
            session.status = "completed"  # 提交成功后标记为完成

            # 更新所有答案记录的submitted状态
            answers_result = await db.execute(
                select(AnswerRecord).where(AnswerRecord.session_id == session_id)
            )
            answer_records = answers_result.scalars().all()
            for record in answer_records:
                record.submitted = True

            log.info(f"会话 {session_id} 提交成功")
        else:
            session.submission_result = json.dumps(result, ensure_ascii=False)
            log.warning(f"会话 {session_id} 提交失败: {result.get('message')}")

        await db.commit()

        return {
            "success": result.get("success", False),
            "message": result.get("message", "提交完成"),
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"提交会话失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/export")
async def export_session(
    session_id: int,
    format: str = Query("json", regex="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
):
    """导出答题记录"""
    try:
        # 获取详情
        detail = await get_session_detail(session_id, db)

        if format == "json":
            return detail
        elif format == "csv":
            # TODO: 实现CSV导出
            raise HTTPException(status_code=501, detail="CSV导出功能待实现")

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"导出失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

