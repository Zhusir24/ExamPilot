#!/usr/bin/env python3
"""测试 Markdown 解析功能"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.services.knowledge_base import KnowledgeBaseService

def test_markdown_parser():
    """测试 markdown 解析功能"""

    # 创建服务实例（不需要 embedding_service，仅测试解析功能）
    service = KnowledgeBaseService(embedding_service=None)

    # 读取测试 markdown 文件（从 fixtures 目录）
    fixture_path = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'test_markdown.md')
    with open(fixture_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    print("=" * 60)
    print("原始 Markdown 内容：")
    print("=" * 60)
    print(markdown_content[:500])  # 显示前 500 个字符
    print(f"\n... (总共 {len(markdown_content)} 字符)\n")

    # 解析为纯文本
    parsed_text = service._parse_markdown_to_text(markdown_content)

    print("=" * 60)
    print("解析后的纯文本：")
    print("=" * 60)
    print(parsed_text)
    print()

    print("=" * 60)
    print("统计信息：")
    print("=" * 60)
    print(f"原始 Markdown 长度: {len(markdown_content)} 字符")
    print(f"解析后文本长度: {len(parsed_text)} 字符")
    print(f"压缩率: {(1 - len(parsed_text) / len(markdown_content)) * 100:.1f}%")
    print()

    # 验证关键内容是否保留
    print("=" * 60)
    print("内容验证：")
    print("=" * 60)

    checks = [
        ("包含标题文本", "测试 Markdown 文档" in parsed_text),
        ("包含列表内容", "有序列表项" in parsed_text),
        ("包含代码内容", "hello_world" in parsed_text),
        ("包含引用内容", "这是一段引用文本" in parsed_text),
        ("包含表格内容", "Markdown 解析" in parsed_text),
        ("移除了格式标记 #", "##" not in parsed_text),
        ("移除了格式标记 *", "**" not in parsed_text),
        ("移除了格式标记 `", "```" not in parsed_text),
    ]

    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")

    print()

    # 测试文本分块
    print("=" * 60)
    print("测试文本分块：")
    print("=" * 60)

    chunks = service._chunk_text(parsed_text, chunk_size=200, overlap=20)
    print(f"分块数量: {len(chunks)}")
    print(f"\n前 3 个分块内容：")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- 分块 {i+1} (长度: {len(chunk)} 字符) ---")
        print(chunk[:100] + "..." if len(chunk) > 100 else chunk)

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_markdown_parser()
