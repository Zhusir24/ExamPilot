"""系统设置API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Any
import json
from backend.core.database import get_db
from backend.models.schema import SystemSetting
from backend.core.logger import log

router = APIRouter(prefix="/api/settings", tags=["系统设置"])


class SettingRequest(BaseModel):
    """设置请求"""
    key: str
    value: Any
    value_type: str  # str/int/float/bool/json
    description: Optional[str] = None
    category: Optional[str] = None


class SettingResponse(BaseModel):
    """设置响应"""
    id: int
    key: str
    value: Any
    value_type: str
    description: Optional[str]
    category: Optional[str]
    created_at: str
    updated_at: str


def serialize_value(value: Any, value_type: str) -> str:
    """序列化值"""
    if value_type == "json":
        return json.dumps(value, ensure_ascii=False)
    else:
        return str(value)


def deserialize_value(value_str: str, value_type: str) -> Any:
    """反序列化值"""
    if value_type == "int":
        return int(value_str)
    elif value_type == "float":
        return float(value_str)
    elif value_type == "bool":
        return value_str.lower() in ("true", "1", "yes")
    elif value_type == "json":
        return json.loads(value_str)
    else:
        return value_str


@router.get("", response_model=List[SettingResponse])
async def get_all_settings(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取所有设置"""
    query = select(SystemSetting)
    
    if category:
        query = query.where(SystemSetting.category == category)
    
    result = await db.execute(query.order_by(SystemSetting.category, SystemSetting.key))
    settings = result.scalars().all()
    
    return [
        SettingResponse(
            id=s.id,
            key=s.key,
            value=deserialize_value(s.value, s.value_type),
            value_type=s.value_type,
            description=s.description,
            category=s.category,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in settings
    ]


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单个设置"""
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(status_code=404, detail="设置不存在")
    
    return SettingResponse(
        id=setting.id,
        key=setting.key,
        value=deserialize_value(setting.value, setting.value_type),
        value_type=setting.value_type,
        description=setting.description,
        category=setting.category,
        created_at=setting.created_at.isoformat(),
        updated_at=setting.updated_at.isoformat(),
    )


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    request: SettingRequest,
    db: AsyncSession = Depends(get_db),
):
    """更新设置"""
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        # 创建新设置
        setting = SystemSetting(
            key=key,
            value=serialize_value(request.value, request.value_type),
            value_type=request.value_type,
            description=request.description,
            category=request.category,
        )
        db.add(setting)
    else:
        # 更新现有设置
        setting.value = serialize_value(request.value, request.value_type)
        setting.value_type = request.value_type
        if request.description is not None:
            setting.description = request.description
        if request.category is not None:
            setting.category = request.category
    
    await db.commit()
    await db.refresh(setting)
    
    log.info(f"更新设置: {key}")
    
    return SettingResponse(
        id=setting.id,
        key=setting.key,
        value=deserialize_value(setting.value, setting.value_type),
        value_type=setting.value_type,
        description=setting.description,
        category=setting.category,
        created_at=setting.created_at.isoformat(),
        updated_at=setting.updated_at.isoformat(),
    )


@router.post("", response_model=SettingResponse)
async def create_setting(
    request: SettingRequest,
    db: AsyncSession = Depends(get_db),
):
    """创建设置"""
    # 检查是否已存在
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == request.key)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="设置已存在")
    
    setting = SystemSetting(
        key=request.key,
        value=serialize_value(request.value, request.value_type),
        value_type=request.value_type,
        description=request.description,
        category=request.category,
    )
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    
    log.info(f"创建设置: {request.key}")
    
    return SettingResponse(
        id=setting.id,
        key=setting.key,
        value=deserialize_value(setting.value, setting.value_type),
        value_type=setting.value_type,
        description=setting.description,
        category=setting.category,
        created_at=setting.created_at.isoformat(),
        updated_at=setting.updated_at.isoformat(),
    )


@router.delete("/{key}")
async def delete_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
):
    """删除设置"""
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(status_code=404, detail="设置不存在")
    
    await db.delete(setting)
    await db.commit()
    
    log.info(f"删除设置: {key}")
    
    return {"message": "删除成功"}


# 预定义的设置键
DEFAULT_SETTINGS = {
    "confidence_threshold": {
        "value": 0.7,
        "value_type": "float",
        "description": "低置信度阈值，低于此值需要人工确认",
        "category": "answering",
    },
    "timing_strategy": {
        "value": "none",
        "value_type": "str",
        "description": "时间模拟策略 (none/uniform/normal/segmented)",
        "category": "timing",
    },
    "timing_min_time": {
        "value": 2.0,
        "value_type": "float",
        "description": "最小答题时间（秒）",
        "category": "timing",
    },
    "timing_max_time": {
        "value": 10.0,
        "value_type": "float",
        "description": "最大答题时间（秒）",
        "category": "timing",
    },
    "use_knowledge_base": {
        "value": True,
        "value_type": "bool",
        "description": "是否使用知识库辅助答题",
        "category": "answering",
    },
    "visual_mode": {
        "value": False,
        "value_type": "bool",
        "description": "可视化答题模式（弹出浏览器窗口，用户可见全过程）",
        "category": "answering",
    },
}


@router.post("/init-defaults")
async def init_default_settings(db: AsyncSession = Depends(get_db)):
    """初始化默认设置"""
    created_count = 0
    
    for key, config in DEFAULT_SETTINGS.items():
        # 检查是否已存在
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            setting = SystemSetting(
                key=key,
                value=serialize_value(config["value"], config["value_type"]),
                value_type=config["value_type"],
                description=config["description"],
                category=config["category"],
            )
            db.add(setting)
            created_count += 1
    
    await db.commit()
    log.info(f"初始化了 {created_count} 个默认设置")
    
    return {"message": f"初始化了 {created_count} 个默认设置"}

