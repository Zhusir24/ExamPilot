#!/bin/bash
# ExamPilot 测试运行脚本

set -e  # 遇到错误立即退出

echo "======================================"
echo "  ExamPilot 测试套件"
echo "======================================"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 错误：未找到虚拟环境 .venv"
    echo "请先创建虚拟环境：python3 -m venv .venv"
    exit 1
fi

# 显示菜单
echo "请选择要运行的测试："
echo "  1) 单元测试 - Markdown 解析"
echo "  2) 集成测试 - 文件上传（需要后端运行）"
echo "  3) 运行所有单元测试"
echo "  q) 退出"
echo ""
read -p "请输入选项 [1-3/q]: " choice

case $choice in
    1)
        echo ""
        echo "======================================"
        echo "运行单元测试：Markdown 解析"
        echo "======================================"
        .venv/bin/python tests/unit/test_markdown_parser.py
        ;;
    2)
        echo ""
        echo "======================================"
        echo "运行集成测试：文件上传"
        echo "======================================"
        echo ""
        echo "⚠️  注意：此测试需要后端服务运行在 http://localhost:8000"
        echo ""
        read -p "后端服务是否已运行？(y/n): " backend_running
        if [ "$backend_running" = "y" ] || [ "$backend_running" = "Y" ]; then
            .venv/bin/python tests/integration/test_upload.py
        else
            echo ""
            echo "请先启动后端服务："
            echo "  cd backend"
            echo "  uvicorn main:app --reload"
            echo ""
            echo "然后重新运行此脚本。"
        fi
        ;;
    3)
        echo ""
        echo "======================================"
        echo "运行所有单元测试"
        echo "======================================"
        echo ""

        echo "→ 测试 1/1: Markdown 解析"
        .venv/bin/python tests/unit/test_markdown_parser.py

        echo ""
        echo "======================================"
        echo "✅ 所有单元测试完成！"
        echo "======================================"
        ;;
    q|Q)
        echo "退出测试。"
        exit 0
        ;;
    *)
        echo "❌ 无效选项：$choice"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "测试运行完成！"
echo "======================================"
