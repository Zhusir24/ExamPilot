"""LLM配置API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from backend.core.database import get_db
from backend.models.schema import LLMConfig
from backend.core.logger import log
from backend.core.encryption import encryption_service

router = APIRouter(prefix="/api/llm", tags=["LLM配置"])


class LLMConfigRequest(BaseModel):
    """LLM配置请求"""
    name: str
    provider: str
    api_key: Optional[str] = None
    base_url: str
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    config_type: str  # llm/embedding/rerank
    is_active: bool = True
    extra_params: Optional[dict] = None


class LLMConfigResponse(BaseModel):
    """LLM配置响应"""
    id: int
    name: str
    provider: str
    base_url: str
    model: str
    temperature: float
    max_tokens: Optional[int]
    config_type: str
    is_active: bool
    extra_params: Optional[dict]
    created_at: str
    updated_at: str


@router.get("/configs", response_model=List[LLMConfigResponse])
async def get_llm_configs(
    config_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取LLM配置列表"""
    query = select(LLMConfig)
    
    if config_type:
        query = query.where(LLMConfig.config_type == config_type)
    
    result = await db.execute(query.order_by(LLMConfig.created_at.desc()))
    configs = result.scalars().all()
    
    return [
        LLMConfigResponse(
            id=c.id,
            name=c.name,
            provider=c.provider,
            base_url=c.base_url,
            model=c.model,
            temperature=c.temperature,
            max_tokens=c.max_tokens,
            config_type=c.config_type,
            is_active=c.is_active,
            extra_params=c.extra_params,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in configs
    ]


@router.post("/configs", response_model=LLMConfigResponse)
async def create_llm_config(
    request: LLMConfigRequest,
    db: AsyncSession = Depends(get_db),
):
    """创建LLM配置"""
    try:
        # 检查名称是否已存在
        result = await db.execute(
            select(LLMConfig).where(LLMConfig.name == request.name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="配置名称已存在")

        # 检查该类型是否已有激活的配置
        if request.is_active:
            result = await db.execute(
                select(LLMConfig).where(
                    LLMConfig.config_type == request.config_type,
                    LLMConfig.is_active == True
                )
            )
            existing_active = result.scalar_one_or_none()

            if existing_active:
                raise HTTPException(
                    status_code=400,
                    detail=f"{request.config_type}类型已存在激活的配置: {existing_active.name}。每种类型只能有一个激活配置,请先停用现有配置或将此配置设为未激活状态。"
                )

        # 加密API密钥
        encrypted_api_key = None
        if request.api_key:
            encrypted_api_key = encryption_service.encrypt(request.api_key)
            if encrypted_api_key is None:
                raise HTTPException(status_code=500, detail="API密钥加密失败")
            log.info(f"API密钥已加密存储")

        # 创建配置
        config = LLMConfig(
            name=request.name,
            provider=request.provider,
            api_key=encrypted_api_key,  # 存储加密后的密钥
            base_url=request.base_url,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            config_type=request.config_type,
            is_active=request.is_active,
            extra_params=request.extra_params,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)

        log.info(f"创建LLM配置: {config.name} (类型: {config.config_type}, 激活: {config.is_active})")

        return LLMConfigResponse(
            id=config.id,
            name=config.name,
            provider=config.provider,
            base_url=config.base_url,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            config_type=config.config_type,
            is_active=config.is_active,
            extra_params=config.extra_params,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"创建LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/configs/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    config_id: int,
    request: LLMConfigRequest,
    db: AsyncSession = Depends(get_db),
):
    """更新LLM配置"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 检查该类型是否已有激活的配置(排除当前配置自己)
    if request.is_active:
        result = await db.execute(
            select(LLMConfig).where(
                LLMConfig.config_type == request.config_type,
                LLMConfig.is_active == True,
                LLMConfig.id != config_id
            )
        )
        existing_active = result.scalar_one_or_none()

        if existing_active:
            raise HTTPException(
                status_code=400,
                detail=f"{request.config_type}类型已存在激活的配置: {existing_active.name}。每种类型只能有一个激活配置,请先停用现有配置或将此配置设为未激活状态。"
            )

    # 更新字段
    config.name = request.name
    config.provider = request.provider

    # 如果提供了新的API密钥，加密后更新
    if request.api_key:
        encrypted_api_key = encryption_service.encrypt(request.api_key)
        if encrypted_api_key is None:
            raise HTTPException(status_code=500, detail="API密钥加密失败")
        config.api_key = encrypted_api_key
        log.info(f"API密钥已更新并加密")

    config.base_url = request.base_url
    config.model = request.model
    config.temperature = request.temperature
    config.max_tokens = request.max_tokens
    config.config_type = request.config_type
    config.is_active = request.is_active
    config.extra_params = request.extra_params

    await db.commit()
    await db.refresh(config)

    log.info(f"更新LLM配置: {config.name} (类型: {config.config_type}, 激活: {config.is_active})")

    return LLMConfigResponse(
        id=config.id,
        name=config.name,
        provider=config.provider,
        base_url=config.base_url,
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        config_type=config.config_type,
        is_active=config.is_active,
        extra_params=config.extra_params,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.delete("/configs/{config_id}")
async def delete_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除LLM配置"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    await db.delete(config)
    await db.commit()
    
    log.info(f"删除LLM配置: {config.name}")
    
    return {"message": "删除成功"}


@router.get("/configs/{config_id}", response_model=LLMConfigResponse)
async def get_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取单个LLM配置"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    return LLMConfigResponse(
        id=config.id,
        name=config.name,
        provider=config.provider,
        base_url=config.base_url,
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        config_type=config.config_type,
        is_active=config.is_active,
        extra_params=config.extra_params,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.post("/configs/validate")
async def validate_llm_config(request: LLMConfigRequest):
    """
    验证LLM配置是否有效
    测试API连接并返回验证结果
    """
    import httpx

    try:
        log.info(f"开始验证配置: {request.name} ({request.config_type})")

        # 根据配置类型进行不同的测试
        if request.config_type == "llm":
            # 测试LLM API
            url = f"{request.base_url.rstrip('/')}/chat/completions"
            payload = {
                "model": request.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5,
            }
        elif request.config_type == "embedding":
            # 测试Embedding API
            url = f"{request.base_url.rstrip('/')}/embeddings"
            payload = {
                "model": request.model,
                "input": "test",
            }
        elif request.config_type == "rerank":
            # 测试Rerank API
            url = f"{request.base_url.rstrip('/')}/rerank"
            payload = {
                "model": request.model,
                "query": "test",
                "documents": ["test document"],
            }
        else:
            raise HTTPException(status_code=400, detail=f"不支持的配置类型: {request.config_type}")

        headers = {
            "Content-Type": "application/json",
        }

        if request.api_key:
            headers["Authorization"] = f"Bearer {request.api_key}"

        # 发送测试请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                log.info(f"✓ 配置验证成功: {request.name}")
                return {
                    "valid": True,
                    "message": "配置验证成功,API连接正常",
                    "details": {
                        "status_code": response.status_code,
                        "config_type": request.config_type,
                    }
                }
            else:
                error_msg = f"API返回错误状态码: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f", 详情: {error_detail}"
                except:
                    error_msg += f", 响应: {response.text[:200]}"

                log.warning(f"配置验证失败: {request.name} - {error_msg}")
                return {
                    "valid": False,
                    "message": error_msg,
                    "details": {
                        "status_code": response.status_code,
                        "config_type": request.config_type,
                    }
                }

    except httpx.TimeoutException:
        error_msg = "连接超时,请检查API地址是否正确"
        log.error(f"配置验证超时: {request.name}")
        return {
            "valid": False,
            "message": error_msg,
            "details": {"error": "timeout"}
        }
    except httpx.ConnectError as e:
        error_msg = f"无法连接到API服务器: {str(e)}"
        log.error(f"配置验证连接失败: {request.name} - {error_msg}")
        return {
            "valid": False,
            "message": error_msg,
            "details": {"error": "connection_error"}
        }
    except Exception as e:
        error_msg = f"验证过程出错: {str(e)}"
        log.error(f"配置验证异常: {request.name} - {error_msg}")
        return {
            "valid": False,
            "message": error_msg,
            "details": {"error": str(e)}
        }

