#!/bin/bash

# ExamPilot 开发模式启动脚本

echo "======================================"
echo "  ExamPilot - 开发模式"
echo "======================================"
echo ""

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "错误: 虚拟环境不存在，请先运行 ./start.sh"
    exit 1
fi

# 启动后端（后台运行）
echo "启动后端服务（端口8000）..."
python -m backend.main &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端开发服务器
echo "启动前端开发服务器（端口3000）..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

npm run dev

# 清理：关闭后端进程
kill $BACKEND_PID

