#!/bin/bash

# ExamPilot 启动脚本

echo "======================================"
echo "  ExamPilot - 智能自动答题系统"
echo "======================================"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 安装后端依赖
if [ ! -f ".venv/installed" ]; then
    echo "安装后端依赖..."
    pip install -r backend/requirements.txt
    
    echo "安装Playwright浏览器..."
    playwright install chromium
    
    # 检查系统依赖
    echo ""
    echo "检查Playwright系统依赖..."
    if ! dpkg -l | grep -q libnss3; then
        echo "警告: 缺少Playwright运行所需的系统依赖"
        echo "请运行以下命令安装（需要sudo权限）："
        echo ""
        echo "sudo apt-get update"
        echo "sudo apt-get install -y libnss3 libnspr4 libasound2t64 libatk1.0-0t64 \\"
        echo "    libatk-bridge2.0-0t64 libcups2t64 libdrm2 libxkbcommon0 \\"
        echo "    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \\"
        echo "    libpango-1.0-0 libcairo2 libxshmfence1 libxext6 libxfixes3 \\"
        echo "    libxrender1 libxcb1 libxcb-shm0 libx11-6 libx11-xcb1"
        echo ""
        read -p "是否现在安装? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt-get update
            sudo apt-get install -y libnss3 libnspr4 libasound2t64 libatk1.0-0t64 \
                libatk-bridge2.0-0t64 libcups2t64 libdrm2 libxkbcommon0 \
                libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
                libpango-1.0-0 libcairo2 libxshmfence1 libxext6 libxrender1 \
                libxcb1 libxcb-shm0 libx11-6 libx11-xcb1
        fi
    fi
    
    touch .venv/installed
fi

# 检查前端是否构建
if [ ! -d "frontend/dist" ]; then
    echo ""
    echo "警告: 前端未构建，将只启动后端服务"
    echo "如需使用前端，请运行:"
    echo "  cd frontend && npm install && npm run build"
    echo ""
fi

# 启动后端服务
echo "启动后端服务..."
python -m backend.main

