"""FastAPI主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
from backend.core.config import settings
from backend.core.logger import log
from backend.core.database import init_db, close_db
from backend.migrations.manager import migration_manager
from backend.api import questionnaire, llm, knowledge, settings as settings_api, websocket, history


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    log.info("=" * 60)
    log.info("ExamPilot 启动中...")
    log.info("=" * 60)
    
    try:
        # 执行数据库迁移
        log.info("执行数据库迁移...")
        await migration_manager.run_migrations()
        
        log.info("ExamPilot 启动完成")
        log.info(f"服务地址: http://{settings.host}:{settings.port}")
        log.info("=" * 60)
        
        yield
        
    finally:
        # 关闭时执行
        log.info("ExamPilot 关闭中...")
        await close_db()
        log.info("ExamPilot 已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="ExamPilot",
    description="智能自动答题系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(questionnaire.router)
app.include_router(llm.router)
app.include_router(knowledge.router)
app.include_router(settings_api.router)
app.include_router(history.router)
app.include_router(websocket.router)


# 静态文件服务（前端）
frontend_dist = settings.project_root / "frontend" / "dist"
if frontend_dist.exists():
    # 挂载静态资源
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    
    @app.get("/")
    async def serve_frontend():
        """服务前端页面"""
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "前端未构建，请先运行 cd frontend && npm run build"}
    
    @app.get("/{full_path:path}")
    async def serve_frontend_routes(full_path: str):
        """处理前端路由"""
        # 如果请求的是API路径，跳过
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            return {"error": "Not found"}
        
        # 检查是否是静态文件
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # 否则返回index.html（用于前端路由）
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        
        return {"error": "Not found"}


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "ExamPilot",
    }


@app.get("/api/info")
async def get_info():
    """获取系统信息"""
    return {
        "name": "ExamPilot",
        "version": "1.0.0",
        "description": "智能自动答题系统",
        "database": str(settings.db_path),
        "log_dir": str(settings.log_dir),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

