"""数据库模型"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, LargeBinary
from sqlalchemy.sql import func
from datetime import datetime
from backend.core.database import Base


class Questionnaire(Base):
    """问卷表"""
    __tablename__ = "questionnaires"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), nullable=False, unique=True, comment="问卷URL")
    platform = Column(String(50), nullable=False, comment="平台名称")
    template_type = Column(String(50), nullable=False, comment="模板类型")
    title = Column(String(200), comment="问卷标题")
    description = Column(Text, comment="问卷描述")
    total_questions = Column(Integer, default=0, comment="题目总数")
    meta_data = Column(JSON, comment="元数据")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class QuestionRecord(Base):
    """题目记录表"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False, comment="问卷ID")
    question_id = Column(String(100), nullable=False, comment="题目ID")
    question_type = Column(String(50), nullable=False, comment="题目类型")
    content = Column(Text, nullable=False, comment="题目内容")
    options = Column(JSON, comment="选项列表")
    order = Column(Integer, nullable=False, comment="题目顺序")
    required = Column(Boolean, default=True, comment="是否必答")
    platform_data = Column(JSON, comment="平台特定数据")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class AnsweringSession(Base):
    """答题会话记录表"""
    __tablename__ = "answering_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False, comment="问卷ID")
    mode = Column(String(50), nullable=False, comment="答题模式")
    status = Column(String(50), nullable=False, default="in_progress", comment="状态")
    total_questions = Column(Integer, default=0, comment="总题目数")
    answered_questions = Column(Integer, default=0, comment="已答题目数")
    correct_answers = Column(Integer, comment="正确答案数")
    avg_confidence = Column(Float, comment="平均置信度")
    start_time = Column(DateTime, default=datetime.utcnow, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    duration = Column(Integer, comment="答题时长(秒)")
    submitted = Column(Boolean, default=False, comment="是否已提交")
    submission_result = Column(Text, comment="提交结果")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class AnswerRecord(Base):
    """答案记录表"""
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("answering_sessions.id"), comment="会话ID")
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False, comment="问卷ID")
    question_id = Column(String(100), nullable=False, comment="题目ID")
    content = Column(Text, nullable=False, comment="答案内容")
    status = Column(String(50), nullable=False, comment="答案状态")
    confidence = Column(Float, comment="置信度")
    reasoning = Column(Text, comment="推理过程")
    knowledge_references = Column(JSON, comment="知识库引用")
    submitted = Column(Boolean, default=False, comment="是否已提交")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    submitted_at = Column(DateTime, comment="提交时间")


class KnowledgeDocument(Base):
    """知识库文档表"""
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="文档标题")
    filename = Column(String(200), comment="文件名")
    content = Column(Text, nullable=False, comment="文档内容")
    file_type = Column(String(50), comment="文件类型")
    file_size = Column(Integer, comment="文件大小(字节)")
    total_chunks = Column(Integer, default=0, comment="分块总数")
    meta_data = Column(JSON, comment="元数据")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class KnowledgeChunk(Base):
    """知识库分块表"""
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, comment="文档ID")
    chunk_index = Column(Integer, nullable=False, comment="分块索引")
    content = Column(Text, nullable=False, comment="分块内容")
    start_pos = Column(Integer, comment="起始位置")
    end_pos = Column(Integer, comment="结束位置")
    meta_data = Column(JSON, comment="元数据")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class VectorEmbedding(Base):
    """向量嵌入表"""
    __tablename__ = "vector_embeddings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(Integer, ForeignKey("knowledge_chunks.id", ondelete="CASCADE"), nullable=False, unique=True, comment="分块ID")
    embedding = Column(LargeBinary, nullable=False, comment="向量数据")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    dimension = Column(Integer, nullable=False, comment="向量维度")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class LLMConfig(Base):
    """LLM配置表"""
    __tablename__ = "llm_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="配置名称")
    provider = Column(String(50), nullable=False, comment="供应商")
    api_key = Column(String(200), comment="API密钥")
    base_url = Column(String(200), nullable=False, comment="API地址")
    model = Column(String(100), nullable=False, comment="模型名称")
    temperature = Column(Float, default=0.7, comment="温度参数")
    max_tokens = Column(Integer, comment="最大令牌数")
    config_type = Column(String(50), nullable=False, comment="配置类型(llm/embedding/rerank)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    extra_params = Column(JSON, comment="额外参数")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class SystemSetting(Base):
    """系统设置表"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, comment="设置键")
    value = Column(Text, nullable=False, comment="设置值")
    value_type = Column(String(50), nullable=False, comment="值类型")
    description = Column(String(200), comment="描述")
    category = Column(String(50), comment="分类")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class MigrationHistory(Base):
    """迁移历史表"""
    __tablename__ = "migration_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), nullable=False, unique=True, comment="版本号")
    description = Column(String(200), comment="描述")
    executed_at = Column(DateTime, default=datetime.utcnow, comment="执行时间")

