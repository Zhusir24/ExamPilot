"""
修复历史问卷标题

此脚本将：
1. 扫描所有标题为"未命名问卷"的记录
2. 重新访问问卷URL提取标题
3. 更新数据库
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from backend.core.database import async_session_maker
from backend.models.schema import Questionnaire
from backend.services.platforms import get_platform
from backend.core.logger import log


async def fix_questionnaire_titles():
    """修复所有未命名问卷的标题"""

    log.info("=" * 60)
    log.info("开始修复问卷标题")
    log.info("=" * 60)

    total_count = 0
    unnamed_count = 0
    fixed_count = 0
    failed_count = 0

    async with async_session_maker() as db:
        # 查询所有问卷
        result = await db.execute(select(Questionnaire))
        questionnaires = result.scalars().all()

        total_count = len(questionnaires)
        log.info(f"找到 {total_count} 个问卷记录")

        for q in questionnaires:
            if q.title == "未命名问卷" or not q.title:
                unnamed_count += 1
                log.info(f"\n处理问卷 ID={q.id}, URL={q.url}")

                try:
                    # 获取平台适配器
                    platform = get_platform(q.url)

                    # 重新提取标题
                    log.info(f"正在访问问卷页面提取标题...")
                    questions, metadata = await platform.extract_questions(q.url)

                    new_title = metadata.get("title", "未命名问卷")

                    if new_title and new_title != "未命名问卷":
                        # 更新标题
                        q.title = new_title

                        # 同时更新 meta_data
                        if q.meta_data:
                            q.meta_data["title"] = new_title
                        else:
                            q.meta_data = {"title": new_title}

                        await db.flush()
                        fixed_count += 1
                        log.info(f"✅ 成功更新标题: {new_title}")
                    else:
                        log.warning(f"⚠️ 仍然无法提取标题")
                        failed_count += 1

                except Exception as e:
                    log.error(f"❌ 处理失败: {e}")
                    failed_count += 1

        # 提交所有更改
        try:
            await db.commit()
            log.info("\n✓ 数据库更改已提交")
        except Exception as e:
            await db.rollback()
            log.error(f"❌ 数据库提交失败: {e}")
            return False

    # 显示统计信息
    log.info("\n" + "=" * 60)
    log.info("修复完成！统计信息：")
    log.info(f"  总问卷数: {total_count}")
    log.info(f"  未命名问卷: {unnamed_count}")
    log.info(f"  成功修复: {fixed_count}")
    log.info(f"  修复失败: {failed_count}")
    log.info("=" * 60)

    return failed_count == 0


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("问卷标题修复工具")
    print("=" * 60)
    print("\n此脚本将：")
    print("  1. 扫描所有标题为'未命名问卷'的记录")
    print("  2. 重新访问问卷URL提取标题")
    print("  3. 更新数据库")
    print("\n⚠️  注意：")
    print("  - 此过程会访问每个问卷URL，可能需要一些时间")
    print("  - 请确保网络连接正常")
    print()

    # 检查是否有命令行参数 --yes 来跳过确认
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    if not auto_confirm:
        # 询问用户确认
        try:
            confirm = input("是否继续？(yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("已取消修复")
                return
        except (KeyboardInterrupt, EOFError):
            print("\n已取消修复")
            return
    else:
        print("自动确认模式，开始修复...")
        print()

    # 执行修复
    success = await fix_questionnaire_titles()

    if success:
        print("\n" + "=" * 60)
        print("✅ 修复成功完成！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 修复过程中出现错误，请检查日志")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n修复已中断")
    except Exception as e:
        log.error(f"修复脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
