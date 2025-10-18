#!/usr/bin/env python3
"""测试文件上传功能的简单脚本"""

import asyncio
import httpx
import os

BASE_URL = "http://localhost:8000"

# 获取 fixtures 目录路径
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')

async def test_file_validation():
    """测试文件验证功能"""
    print("=" * 60)
    print("测试文件验证功能")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 测试 1: 上传 markdown 文件
        print("\n1. 测试上传 .md 文件...")
        try:
            md_file_path = os.path.join(FIXTURES_DIR, 'test_markdown.md')
            with open(md_file_path, 'rb') as f:
                files = {'file': ('test_markdown.md', f, 'text/markdown')}
                response = await client.post(
                    f"{BASE_URL}/api/knowledge/documents/upload",
                    files=files,
                    timeout=30.0
                )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ 上传成功！文档 ID: {data['id']}, 分块数: {data['total_chunks']}")
            else:
                print(f"   ✗ 上传失败: {response.status_code}")
                print(f"   错误信息: {response.json()}")
        except Exception as e:
            print(f"   ✗ 请求失败: {e}")

        # 测试 2: 上传 txt 文件
        print("\n2. 测试上传 .txt 文件...")
        try:
            txt_file_path = os.path.join(FIXTURES_DIR, 'test_text.txt')
            with open(txt_file_path, 'rb') as f:
                files = {'file': ('test_text.txt', f, 'text/plain')}
                response = await client.post(
                    f"{BASE_URL}/api/knowledge/documents/upload",
                    files=files,
                    timeout=30.0
                )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ 上传成功！文档 ID: {data['id']}, 分块数: {data['total_chunks']}")
            else:
                print(f"   ✗ 上传失败: {response.status_code}")
                print(f"   错误信息: {response.json()}")
        except Exception as e:
            print(f"   ✗ 请求失败: {e}")

        # 测试 3: 尝试上传不支持的文件格式（创建一个临时 .pdf 文件名）
        print("\n3. 测试上传不支持的文件格式 (.pdf)...")
        try:
            content = b"Fake PDF content"
            files = {'file': ('test.pdf', content, 'application/pdf')}
            response = await client.post(
                f"{BASE_URL}/api/knowledge/documents/upload",
                files=files,
                timeout=30.0
            )

            if response.status_code == 400:
                print(f"   ✓ 正确拒绝了不支持的格式")
                print(f"   错误信息: {response.json()['detail']}")
            else:
                print(f"   ✗ 应该返回 400 错误，实际: {response.status_code}")
        except Exception as e:
            print(f"   ✗ 请求失败: {e}")

        # 测试 4: 测试文件大小限制（创建一个超过 10MB 的文件）
        print("\n4. 测试文件大小限制...")
        try:
            # 创建一个 11MB 的内容
            large_content = "A" * (11 * 1024 * 1024)
            files = {'file': ('large.txt', large_content.encode(), 'text/plain')}
            response = await client.post(
                f"{BASE_URL}/api/knowledge/documents/upload",
                files=files,
                timeout=30.0
            )

            if response.status_code == 400:
                print(f"   ✓ 正确拒绝了超大文件")
                print(f"   错误信息: {response.json()['detail']}")
            else:
                print(f"   ✗ 应该返回 400 错误，实际: {response.status_code}")
        except Exception as e:
            print(f"   ✗ 请求失败: {e}")

        # 测试 5: 获取文档列表
        print("\n5. 测试获取文档列表...")
        try:
            response = await client.get(f"{BASE_URL}/api/knowledge/documents")

            if response.status_code == 200:
                documents = response.json()
                print(f"   ✓ 获取成功！共 {len(documents)} 个文档")
                for doc in documents[:3]:  # 显示前 3 个
                    print(f"      - {doc['title']} ({doc['total_chunks']} 分块)")
            else:
                print(f"   ✗ 获取失败: {response.status_code}")
        except Exception as e:
            print(f"   ✗ 请求失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    print("\n注意：此脚本需要后端服务在 http://localhost:8000 运行")
    print("如果后端未运行，请先启动后端服务：")
    print("  cd backend && uvicorn main:app --reload\n")

    try:
        asyncio.run(test_file_validation())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试失败: {e}")
