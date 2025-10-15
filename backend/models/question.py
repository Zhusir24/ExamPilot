"""统一题目模型"""
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """题目类型"""
    FILL_BLANK = "填空"
    SINGLE_CHOICE = "单选"
    MULTIPLE_CHOICE = "多选"
    TRUE_FALSE = "判断"


class TemplateType(str, Enum):
    """模板类型"""
    EXAM = "考试"
    SURVEY = "测评"


class Question(BaseModel):
    """统一题目模型"""
    
    id: str = Field(..., description="题目ID")
    type: QuestionType = Field(..., description="题目类型")
    content: str = Field(..., description="题目内容")
    options: Optional[List[str]] = Field(None, description="选项列表（单选、多选、判断）")
    order: int = Field(..., description="题目顺序")
    required: bool = Field(True, description="是否必答")
    platform_data: Optional[dict] = Field(None, description="平台特定数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "q1",
                "type": "单选",
                "content": "Python是一种什么类型的编程语言？",
                "options": ["编译型", "解释型", "混合型", "汇编型"],
                "order": 1,
                "required": True,
            }
        }
    
    def is_choice_question(self) -> bool:
        """是否为选择题"""
        return self.type in [
            QuestionType.SINGLE_CHOICE,
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.TRUE_FALSE
        ]
    
    def is_fill_question(self) -> bool:
        """是否为填空题"""
        return self.type == QuestionType.FILL_BLANK
    
    def validate_answer(self, answer: Any) -> tuple[bool, Optional[str]]:
        """
        验证答案格式是否正确

        Returns:
            tuple: (是否有效, 错误信息)
        """
        if answer is None or answer == "":
            return False, "答案不能为空"

        if self.type == QuestionType.SINGLE_CHOICE:
            # 单选题: 必须是整数索引
            if not isinstance(answer, int):
                try:
                    answer = int(answer)
                except (ValueError, TypeError):
                    return False, f"单选题答案必须是整数索引(0-{len(self.options or [])-1}),当前值: {answer}"

            if not (0 <= answer < len(self.options or [])):
                return False, f"单选题索引超出范围,应该在0-{len(self.options or [])-1},当前值: {answer}"

            return True, None

        elif self.type == QuestionType.MULTIPLE_CHOICE:
            # 多选题: 必须是整数索引数组
            if not isinstance(answer, list):
                return False, f"多选题答案必须是数组,当前类型: {type(answer).__name__}"

            if len(answer) == 0:
                return False, "多选题至少要选择一个选项"

            for idx, item in enumerate(answer):
                if not isinstance(item, int):
                    try:
                        answer[idx] = int(item)
                    except (ValueError, TypeError):
                        return False, f"多选题选项必须是整数索引,第{idx}项无效: {item}"

                if not (0 <= answer[idx] < len(self.options or [])):
                    return False, f"多选题索引超出范围,第{idx}项={answer[idx]},应该在0-{len(self.options or [])-1}"

            return True, None

        elif self.type == QuestionType.TRUE_FALSE:
            # 判断题: 必须是整数索引(通常0或1)
            if not isinstance(answer, int):
                try:
                    answer = int(answer)
                except (ValueError, TypeError):
                    return False, f"判断题答案必须是整数索引,当前值: {answer}"

            if not (0 <= answer < len(self.options or [])):
                return False, f"判断题索引超出范围,应该在0-{len(self.options or [])-1},当前值: {answer}"

            return True, None

        elif self.type == QuestionType.FILL_BLANK:
            # 填空题: 必须是非空字符串
            if not isinstance(answer, str):
                return False, f"填空题答案必须是字符串,当前类型: {type(answer).__name__}"

            if not answer.strip():
                return False, "填空题答案不能为空字符串"

            return True, None

        return False, f"未知题型: {self.type}"

