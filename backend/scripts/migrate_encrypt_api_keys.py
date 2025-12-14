"""
数据迁移脚本：加密所有明文API密钥

使用方法：
    python -m backend.scripts.migrate_encrypt_api_keys

功能：
    1. 扫描数据库中所有LLM配置
    2. 检查API密钥是否已加密
    3. 如果是明文，进行加密并更新
    4. 显示迁移统计信息
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from backend.core.database import async_session_maker
from backend.models.schema import LLMConfig
from backend.core.encryption import encryption_service
from backend.core.logger import log


async def migrate_api_keys():
    """迁移所有API密钥到加密存储"""

    log.info("=" * 60)
    log.info("开始API密钥加密迁移")
    log.info("=" * 60)

    total_count = 0
    encrypted_count = 0
    already_encrypted_count = 0
    failed_count = 0

    async with async_session_maker() as db:
        # 查询所有LLM配置
        result = await db.execute(select(LLMConfig))
        configs = result.scalars().all()

        total_count = len(configs)
        log.info(f"找到 {total_count} 个LLM配置")

        for config in configs:
            if not config.api_key:
                log.info(f"⏭️  跳过 {config.name}: 没有API密钥")
                continue

            # 检查是否已加密
            if encryption_service.is_encrypted(config.api_key):
                log.info(f"✓ {config.name}: API密钥已加密，跳过")
                already_encrypted_count += 1
                continue

            # 尝试加密
            log.info(f"🔄 {config.name}: 检测到明文API密钥，开始加密...")

            try:
                # 加密API密钥
                encrypted_key = encryption_service.encrypt(config.api_key)

                if encrypted_key:
                    # 更新数据库
                    config.api_key = encrypted_key
                    await db.flush()

                    encrypted_count += 1
                    log.info(f"✅ {config.name}: API密钥加密成功")
                else:
                    failed_count += 1
                    log.error(f"❌ {config.name}: 加密失败（加密服务返回None）")

            except Exception as e:
                failed_count += 1
                log.error(f"❌ {config.name}: 加密失败 - {e}")

        # 提交所有更改
        try:
            await db.commit()
            log.info("✓ 数据库更改已提交")
        except Exception as e:
            await db.rollback()
            log.error(f"❌ 数据库提交失败: {e}")
            return False

    # 显示统计信息
    log.info("=" * 60)
    log.info("迁移完成！统计信息：")
    log.info(f"  总配置数: {total_count}")
    log.info(f"  已加密（跳过）: {already_encrypted_count}")
    log.info(f"  新加密: {encrypted_count}")
    log.info(f"  失败: {failed_count}")
    log.info("=" * 60)

    if failed_count > 0:
        log.warning(f"⚠️  有 {failed_count} 个配置加密失败，请检查日志")
        return False
    else:
        log.info("✅ 所有API密钥已成功加密！")
        return True


async def verify_encryption():
    """验证加密是否正确（测试解密）"""

    log.info("=" * 60)
    log.info("验证加密数据...")
    log.info("=" * 60)

    async with async_session_maker() as db:
        result = await db.execute(select(LLMConfig))
        configs = result.scalars().all()

        for config in configs:
            if not config.api_key:
                continue

            # 尝试解密
            decrypted = encryption_service.decrypt(config.api_key)

            if decrypted:
                log.info(f"✓ {config.name}: 解密测试成功")
            else:
                log.error(f"❌ {config.name}: 解密测试失败")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("API密钥加密迁移工具")
    print("=" * 60)
    print("\n此脚本将：")
    print("  1. 扫描所有LLM配置")
    print("  2. 检测明文API密钥")
    print("  3. 加密并更新到数据库")
    print("\n⚠️  注意：请确保已备份数据库！\n")

    # 询问用户确认
    try:
        confirm = input("是否继续？(yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("已取消迁移")
            return
    except KeyboardInterrupt:
        print("\n已取消迁移")
        return

    # 执行迁移
    success = await migrate_api_keys()

    if success:
        # 验证加密
        print("\n开始验证加密数据...")
        await verify_encryption()

        print("\n" + "=" * 60)
        print("✅ 迁移成功完成！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 迁移过程中出现错误，请检查日志")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n迁移已中断")
    except Exception as e:
        log.error(f"迁移脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
