#!/bin/bash
# 打包项目源码，排除构建文件和依赖

echo "📦 开始打包 ExamPilot 源码..."

# 设置输出文件名（带时间戳）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="exampilot_source_${TIMESTAMP}.zip"

# 使用 zip 命令打包，排除不需要的文件
zip -r "$OUTPUT_FILE" . \
  -x ".venv/*" \
  -x "venv/*" \
  -x "env/*" \
  -x "frontend/node_modules/*" \
  -x "frontend/dist/*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*.pyo" \
  -x ".git/*" \
  -x ".gitignore" \
  -x ".vscode/*" \
  -x "*.log" \
  -x "data/database.db*" \
  -x "data/*.db-journal" \
  -x "debug_*.png" \
  -x "*.egg-info/*" \
  -x ".DS_Store" \
  -x "*.swp" \
  -x "*~" \
  -x "*.zip" \
  -x ".pytest_cache/*" \
  -x ".mypy_cache/*" \
  -x "*.bak"

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo "✅ 打包完成！"
    echo "📁 文件名: $OUTPUT_FILE"
    echo "📊 大小: $SIZE"
    echo ""
    echo "排除的目录/文件："
    echo "  - .venv/ (Python虚拟环境)"
    echo "  - frontend/node_modules/ (前端依赖)"
    echo "  - frontend/dist/ (前端构建)"
    echo "  - __pycache__/ (Python缓存)"
    echo "  - .git/ (Git仓库)"
    echo "  - .vscode/ (编辑器配置)"
    echo "  - data/database.db (数据库文件)"
    echo "  - *.log (日志文件)"
    echo "  - *.zip (旧的压缩包)"
else
    echo "❌ 打包失败"
    exit 1
fi
