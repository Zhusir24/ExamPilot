#!/bin/bash

# 安装Playwright系统依赖的独立脚本

echo "======================================"
echo "  安装Playwright系统依赖"
echo "======================================"
echo ""

echo "此脚本将安装Playwright运行所需的系统库"
echo "需要sudo权限"
echo ""

# 更新包列表
echo "更新包列表..."
sudo apt-get update

# 安装依赖
echo ""
echo "安装系统依赖..."
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libasound2t64 \
    libatk1.0-0t64 \
    libatk-bridge2.0-0t64 \
    libcups2t64 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libxshmfence1 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libxcb-shm0 \
    libx11-6 \
    libx11-xcb1

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 系统依赖安装成功！"
    echo ""
    echo "现在可以运行 ./start.sh 启动系统"
else
    echo ""
    echo "✗ 安装失败，请检查错误信息"
    exit 1
fi

