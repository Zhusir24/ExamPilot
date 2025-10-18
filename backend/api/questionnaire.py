"""问卷相关API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from backend.core.database import get_db
from backend.models.schema import Questionnaire, QuestionRecord
from backend.models.question import Question
from backend.services.platforms import get_platform
from backend.core.logger import log

router = APIRouter(prefix="/api/questionnaire", tags=["问卷"])


class ParseUrlRequest(BaseModel):
    """解析URL请求"""
    url: str


class ParseUrlResponse(BaseModel):
    """解析URL响应"""
    questionnaire_id: int
    url: str
    platform: str
    template_type: str
    title: str
    description: Optional[str]
    total_questions: int
    questions: List[Dict[str, Any]]


class QuestionnaireResponse(BaseModel):
    """问卷响应"""
    id: int
    url: str
    platform: str
    template_type: str
    title: str
    description: Optional[str]
    total_questions: int
    created_at: str


@router.post("/parse", response_model=ParseUrlResponse)
async def parse_questionnaire(
    request: ParseUrlRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    解析问卷URL

    1. 检测平台
    2. 提取题目
    3. 保存到数据库
    """
    try:
        # 清理URL：移除锚点等无关内容
        clean_url = request.url.split('#')[0].strip()

        # 检查是否已经解析过
        result = await db.execute(
            select(Questionnaire).where(Questionnaire.url == clean_url)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # 获取题目
            result = await db.execute(
                select(QuestionRecord)
                .where(QuestionRecord.questionnaire_id == existing.id)
                .order_by(QuestionRecord.order)
            )
            question_records = result.scalars().all()
            
            questions = [
                {
                    "id": q.question_id,
                    "type": q.question_type,
                    "content": q.content,
                    "options": q.options,
                    "order": q.order,
                    "required": q.required,
                }
                for q in question_records
            ]
            
            log.info(f"返回已解析的问卷: {existing.id}")
            return ParseUrlResponse(
                questionnaire_id=existing.id,
                url=existing.url,
                platform=existing.platform,
                template_type=existing.template_type,
                title=existing.title,
                description=existing.description,
                total_questions=existing.total_questions,
                questions=questions,
            )
        
        # 获取平台适配器
        platform = get_platform(clean_url)

        # 提取题目
        log.info(f"开始解析问卷: {clean_url}")
        questions, metadata = await platform.extract_questions(clean_url)
        
        # 检测模板类型
        template_type = metadata.get("template_type", "测评")
        
        # 保存问卷
        questionnaire = Questionnaire(
            url=clean_url,
            platform=platform.platform_name.value,
            template_type=template_type,
            title=metadata.get("title", "未命名问卷"),
            description=metadata.get("description"),
            total_questions=len(questions),
            meta_data=metadata,
        )
        db.add(questionnaire)
        await db.flush()
        
        # 保存题目
        for question in questions:
            question_record = QuestionRecord(
                questionnaire_id=questionnaire.id,
                question_id=question.id,
                question_type=question.type.value,
                content=question.content,
                options=question.options,
                order=question.order,
                required=question.required,
                platform_data=question.platform_data,
            )
            db.add(question_record)
        
        await db.commit()
        
        log.info(f"成功解析问卷: {questionnaire.id}，共 {len(questions)} 题")
        
        return ParseUrlResponse(
            questionnaire_id=questionnaire.id,
            url=questionnaire.url,
            platform=questionnaire.platform,
            template_type=questionnaire.template_type,
            title=questionnaire.title,
            description=questionnaire.description,
            total_questions=questionnaire.total_questions,
            questions=[q.dict() for q in questions],
        )
        
    except Exception as e:
        log.error(f"解析问卷失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{questionnaire_id}", response_model=QuestionnaireResponse)
async def get_questionnaire(
    questionnaire_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取问卷详情"""
    result = await db.execute(
        select(Questionnaire).where(Questionnaire.id == questionnaire_id)
    )
    questionnaire = result.scalar_one_or_none()
    
    if not questionnaire:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    return QuestionnaireResponse(
        id=questionnaire.id,
        url=questionnaire.url,
        platform=questionnaire.platform,
        template_type=questionnaire.template_type,
        title=questionnaire.title,
        description=questionnaire.description,
        total_questions=questionnaire.total_questions,
        created_at=questionnaire.created_at.isoformat(),
    )


@router.get("/{questionnaire_id}/questions")
async def get_questions(
    questionnaire_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取问卷的所有题目"""
    result = await db.execute(
        select(QuestionRecord)
        .where(QuestionRecord.questionnaire_id == questionnaire_id)
        .order_by(QuestionRecord.order)
    )
    questions = result.scalars().all()
    
    return [
        {
            "id": q.question_id,
            "type": q.question_type,
            "content": q.content,
            "options": q.options,
            "order": q.order,
            "required": q.required,
        }
        for q in questions
    ]

