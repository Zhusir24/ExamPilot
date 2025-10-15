"""平台适配器基类"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
from backend.models.question import Question, TemplateType


class PlatformType(str, Enum):
    """平台类型"""
    WENJUANXING = "问卷星"
    # 预留扩展
    TENCENT_SURVEY = "腾讯问卷"
    JINSHUJU = "金数据"


class BasePlatform(ABC):
    """平台适配器基类"""
    
    @property
    @abstractmethod
    def platform_name(self) -> PlatformType:
        """平台名称"""
        pass
    
    @abstractmethod
    async def parse_url(self, url: str) -> Dict[str, Any]:
        """
        解析问卷URL
        
        Args:
            url: 问卷URL
            
        Returns:
            包含问卷基本信息的字典
        """
        pass
    
    @abstractmethod
    async def extract_questions(self, url: str) -> tuple[List[Question], Dict[str, Any]]:
        """
        提取题目列表
        
        Args:
            url: 问卷URL
            
        Returns:
            (题目列表, 问卷元数据)
        """
        pass
    
    @abstractmethod
    async def submit_answers(self, url: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        提交答案
        
        Args:
            url: 问卷URL
            answers: 答案字典，key为题目ID，value为答案内容
            
        Returns:
            提交结果
        """
        pass
    
    @abstractmethod
    def detect_template_type(self, page_content: str) -> TemplateType:
        """
        检测模板类型
        
        Args:
            page_content: 页面内容
            
        Returns:
            模板类型
        """
        pass
    
    def normalize_question_id(self, raw_id: str) -> str:
        """
        规范化题目ID
        
        Args:
            raw_id: 原始题目ID
            
        Returns:
            规范化的题目ID
        """
        return raw_id.strip()
    
    async def validate_url(self, url: str) -> bool:
        """
        验证URL是否有效
        
        Args:
            url: 问卷URL
            
        Returns:
            是否有效
        """
        return bool(url and url.startswith(("http://", "https://")))

