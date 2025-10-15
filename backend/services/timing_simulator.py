"""时间模拟器 - 模拟人类答题时间"""
import asyncio
import random
from enum import Enum
from typing import Optional, List
import numpy as np
from backend.core.logger import log


class TimingStrategy(str, Enum):
    """时间策略"""
    NONE = "无停顿"
    UNIFORM = "均匀分布"
    NORMAL = "正态分布"
    SEGMENTED = "分段停顿"


class TimingSimulator:
    """时间模拟器"""
    
    def __init__(
        self,
        strategy: TimingStrategy = TimingStrategy.NORMAL,
        min_time: float = 2.0,
        max_time: float = 10.0,
        mean_time: Optional[float] = None,
        std_time: Optional[float] = None,
        pause_probability: float = 0.2,
        pause_duration: tuple = (3.0, 8.0),
    ):
        """
        初始化时间模拟器
        
        Args:
            strategy: 时间策略
            min_time: 最小答题时间（秒）
            max_time: 最大答题时间（秒）
            mean_time: 平均答题时间（正态分布）
            std_time: 标准差（正态分布）
            pause_probability: 停顿概率（分段停顿）
            pause_duration: 停顿时长范围（分段停顿）
        """
        self.strategy = strategy
        self.min_time = min_time
        self.max_time = max_time
        self.mean_time = mean_time or (min_time + max_time) / 2
        self.std_time = std_time or (max_time - min_time) / 6
        self.pause_probability = pause_probability
        self.pause_duration = pause_duration
    
    async def wait_before_answer(self, question_index: int, total_questions: int):
        """
        在答题前等待
        
        Args:
            question_index: 题目索引（从0开始）
            total_questions: 题目总数
        """
        wait_time = self.calculate_wait_time(question_index, total_questions)
        log.debug(f"等待 {wait_time:.2f} 秒后回答第 {question_index + 1} 题")
        await asyncio.sleep(wait_time)
    
    def calculate_wait_time(self, question_index: int, total_questions: int) -> float:
        """
        计算等待时间

        Args:
            question_index: 题目索引
            total_questions: 题目总数

        Returns:
            等待时间（秒）
        """
        if self.strategy == TimingStrategy.NONE:
            return 0.0
        elif self.strategy == TimingStrategy.UNIFORM:
            return self._uniform_time()
        elif self.strategy == TimingStrategy.NORMAL:
            return self._normal_time()
        elif self.strategy == TimingStrategy.SEGMENTED:
            return self._segmented_time(question_index, total_questions)
        else:
            return self._normal_time()
    
    def _uniform_time(self) -> float:
        """均匀分布时间"""
        return random.uniform(self.min_time, self.max_time)
    
    def _normal_time(self) -> float:
        """正态分布时间"""
        time = np.random.normal(self.mean_time, self.std_time)
        # 限制在min和max之间
        return max(self.min_time, min(self.max_time, time))
    
    def _segmented_time(self, question_index: int, total_questions: int) -> float:
        """分段停顿时间"""
        # 基础时间（正态分布）
        base_time = self._normal_time()
        
        # 随机决定是否停顿
        if random.random() < self.pause_probability:
            pause = random.uniform(*self.pause_duration)
            log.debug(f"第 {question_index + 1} 题加入停顿: {pause:.2f} 秒")
            return base_time + pause
        
        return base_time
    
    async def simulate_reading_time(self, content_length: int) -> float:
        """
        根据内容长度模拟阅读时间
        
        Args:
            content_length: 内容长度（字符数）
            
        Returns:
            阅读时间（秒）
        """
        # 假设阅读速度：每分钟300字（中文），每秒5字
        reading_speed = 5  # 字/秒
        base_time = content_length / reading_speed
        
        # 添加随机波动（±30%）
        variation = base_time * random.uniform(-0.3, 0.3)
        total_time = max(1.0, base_time + variation)
        
        return total_time
    
    async def simulate_typing_time(self, text: str) -> float:
        """
        模拟打字时间
        
        Args:
            text: 要输入的文本
            
        Returns:
            打字时间（秒）
        """
        # 假设打字速度：每分钟60字（中文），每秒1字
        typing_speed = 1  # 字/秒
        base_time = len(text) / typing_speed
        
        # 添加随机波动
        variation = base_time * random.uniform(-0.2, 0.4)
        total_time = max(0.5, base_time + variation)
        
        return total_time
    
    async def simulate_thinking_time(self, difficulty: str = "medium") -> float:
        """
        模拟思考时间
        
        Args:
            difficulty: 难度（easy/medium/hard）
            
        Returns:
            思考时间（秒）
        """
        difficulty_map = {
            "easy": (1.0, 3.0),
            "medium": (2.0, 6.0),
            "hard": (4.0, 10.0),
        }
        
        min_t, max_t = difficulty_map.get(difficulty, (2.0, 6.0))
        return random.uniform(min_t, max_t)


class TimingProfile:
    """时间配置模板"""
    
    @staticmethod
    def get_fast_profile() -> TimingSimulator:
        """快速答题模式"""
        return TimingSimulator(
            strategy=TimingStrategy.UNIFORM,
            min_time=1.0,
            max_time=3.0,
        )
    
    @staticmethod
    def get_normal_profile() -> TimingSimulator:
        """正常答题模式"""
        return TimingSimulator(
            strategy=TimingStrategy.NORMAL,
            min_time=2.0,
            max_time=10.0,
            mean_time=5.0,
            std_time=2.0,
        )
    
    @staticmethod
    def get_careful_profile() -> TimingSimulator:
        """仔细答题模式"""
        return TimingSimulator(
            strategy=TimingStrategy.SEGMENTED,
            min_time=3.0,
            max_time=15.0,
            mean_time=8.0,
            std_time=3.0,
            pause_probability=0.3,
            pause_duration=(5.0, 12.0),
        )
    
    @staticmethod
    def get_custom_profile(config: dict) -> TimingSimulator:
        """自定义配置"""
        return TimingSimulator(**config)

