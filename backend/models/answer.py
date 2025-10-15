"""答案模型"""
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AnswerStatus(str, Enum):
    """答案状态"""
    PENDING = "待答题"
    AI_GENERATED = "AI生成"
    USER_CONFIRMED = "用户确认"
    PRESET = "预设答案"
    SUBMITTED = "已提交"
    FAILED = "提交失败"


class Answer(BaseModel):
    """答案模型"""
    
    question_id: str = Field(..., description="题目ID")
    content: Any = Field(..., description="答案内容")
    status: AnswerStatus = Field(AnswerStatus.PENDING, description="答案状态")
    confidence: Optional[float] = Field(None, description="置信度（0-1）")
    reasoning: Optional[str] = Field(None, description="推理过程")
    knowledge_references: Optional[list] = Field(None, description="知识库引用")
    generated_at: Optional[datetime] = Field(None, description="生成时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q1",
                "content": "解释型",
                "status": "AI生成",
                "confidence": 0.95,
                "reasoning": "Python是一种解释型语言...",
            }
        }
    
    def needs_confirmation(self, threshold: float = 0.7) -> bool:
        """是否需要人工确认"""
        if self.confidence is None:
            return True
        return self.confidence < threshold

