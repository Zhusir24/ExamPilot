# 🛠️ 迁移脚本使用指南

本文档介绍 ExamPilot 项目中的所有迁移和维护脚本。

---

## 📋 脚本列表

### 1. API密钥加密迁移脚本

**文件**：`backend/scripts/migrate_encrypt_api_keys.py`

**功能**：将数据库中所有明文存储的 API 密钥加密

#### 使用方法

```bash
# 交互式模式（会询问确认）
.venv/bin/python -m backend.scripts.migrate_encrypt_api_keys

# 自动确认模式（无需手动确认）
.venv/bin/python -m backend.scripts.migrate_encrypt_api_keys --yes
```

#### 执行过程

1. 扫描数据库中所有 LLM 配置
2. 检测哪些 API 密钥是明文
3. 使用 Fernet 加密明文密钥
4. 更新数据库
5. 验证加密是否成功

#### 输出示例

```
============================================================
API密钥加密迁移工具
============================================================

此脚本将：
  1. 扫描所有LLM配置
  2. 检测明文API密钥
  3. 加密并更新到数据库

⚠️  注意：请确保已备份数据库！

是否继续？(yes/no): yes

============================================================
开始API密钥加密迁移
============================================================
找到 3 个LLM配置
🔄 oneapi: 检测到明文API密钥，开始加密...
✅ oneapi: API密钥加密成功
✓ embedding_service: API密钥已加密，跳过
✓ rerank_service: API密钥已加密，跳过
✓ 数据库更改已提交

============================================================
迁移完成！统计信息：
  总配置数: 3
  已加密（跳过）: 2
  新加密: 1
  失败: 0
============================================================
```

#### 注意事项

- ⚠️ **运行前务必备份数据库**
- ⚠️ 确保 `data/.encryption_key` 文件存在
- ⚠️ 停止正在运行的服务
- ✅ 支持重复运行（已加密的会跳过）

---

### 2. 问卷标题修复脚本

**文件**：`backend/scripts/fix_questionnaire_titles.py`

**功能**：修复历史记录中标题为"未命名问卷"的记录

#### 使用方法

```bash
# 交互式模式
.venv/bin/python -m backend.scripts.fix_questionnaire_titles

# 自动确认模式
.venv/bin/python -m backend.scripts.fix_questionnaire_titles --yes
```

#### 执行过程

1. 扫描数据库中所有问卷
2. 找出标题为"未命名问卷"的记录
3. 重新访问问卷 URL
4. 使用增强的提取方法获取标题
5. 更新数据库

#### 输出示例

```
============================================================
问卷标题修复工具
============================================================

找到 3 个问卷记录

处理问卷 ID=1, URL=https://ks.wjx.com/vm/wZtNuC2.aspx
正在访问问卷页面提取标题...
成功提取问卷标题: 生物期中考试[复制] (使用选择器: h1)
✅ 成功更新标题: 生物期中考试[复制]

...

============================================================
修复完成！统计信息：
  总问卷数: 3
  未命名问卷: 3
  成功修复: 3
  修复失败: 0
============================================================
```

#### 注意事项

- 🌐 需要网络连接（会访问问卷 URL）
- ⏱️ 可能需要较长时间（每个问卷约2-3秒）
- ✅ 支持重复运行
- ⚠️ 运行前建议备份数据库

---

## 🔧 通用注意事项

### 运行环境

所有脚本必须使用项目虚拟环境：

```bash
# ✅ 正确
.venv/bin/python -m backend.scripts.xxx

# ❌ 错误
python backend/scripts/xxx.py
python3 -m backend.scripts.xxx
```

### 工作目录

必须在**项目根目录**执行：

```bash
# ✅ 正确
cd /path/to/exampilot
.venv/bin/python -m backend.scripts.xxx

# ❌ 错误
cd backend/scripts
python xxx.py
```

### 备份数据库

运行任何迁移脚本前，务必备份数据库：

```bash
# SQLite数据库备份
cp data/exampilot.db data/exampilot.db.backup_$(date +%Y%m%d_%H%M%S)

# 或使用专用备份工具
sqlite3 data/exampilot.db ".backup data/exampilot.db.backup"
```

### 停止服务

运行迁移脚本前，停止正在运行的服务：

```bash
# 查找进程
ps aux | grep "python.*backend.main"

# 停止进程
pkill -f "python.*backend.main"
```

---

## 📝 创建自定义脚本

### 脚本模板

```python
"""
脚本描述

使用方法：
    .venv/bin/python -m backend.scripts.your_script

功能：
    1. 功能描述1
    2. 功能描述2
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from backend.core.database import async_session_maker
from backend.core.logger import log


async def main_task():
    """主任务"""
    log.info("开始执行任务")

    async with async_session_maker() as db:
        # 你的逻辑
        pass

    log.info("任务执行完成")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("脚本标题")
    print("=" * 60)

    # 检查命令行参数
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    if not auto_confirm:
        try:
            confirm = input("是否继续？(yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("已取消")
                return
        except (KeyboardInterrupt, EOFError):
            print("\n已取消")
            return

    # 执行任务
    await main_task()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n已中断")
    except Exception as e:
        log.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
```

### 脚本位置

所有迁移脚本应放在：

```
backend/scripts/
├── __init__.py
├── migrate_encrypt_api_keys.py
├── fix_questionnaire_titles.py
└── your_custom_script.py
```

---

## 🐛 故障排除

### 问题1：ModuleNotFoundError: No module named 'backend'

**原因**：未在项目根目录执行

**解决**：
```bash
cd /path/to/exampilot
.venv/bin/python -m backend.scripts.xxx
```

---

### 问题2：数据库锁定错误

**错误**：`database is locked`

**原因**：服务正在运行

**解决**：
```bash
# 停止服务
pkill -f "python.*backend.main"

# 等待几秒后重试
sleep 3
.venv/bin/python -m backend.scripts.xxx
```

---

### 问题3：权限错误

**错误**：`Permission denied`

**解决**：
```bash
# 确保虚拟环境python有执行权限
chmod +x .venv/bin/python

# 确保脚本有读权限
chmod +r backend/scripts/*.py
```

---

## 📊 脚本对比

| 脚本 | 用途 | 运行时间 | 网络需求 | 数据库修改 |
|------|------|---------|---------|-----------|
| migrate_encrypt_api_keys | API密钥加密 | < 1秒 | 否 | ✅ 是 |
| fix_questionnaire_titles | 修复问卷标题 | 2-3秒/问卷 | ✅ 是 | ✅ 是 |

---

## 📞 获取帮助

如有问题，请：

1. **查看日志**：`data/logs/exampilot.log`
2. **检查脚本输出**：查看控制台详细信息
3. **提交Issue**：[GitHub Issues](https://github.com/your-repo/issues)

---

## 📝 相关文档

- [API密钥加密功能](../features/api_encryption.md)
- [故障排除](../troubleshooting/common_issues.md)

---

**最后更新**：2025-11-07
