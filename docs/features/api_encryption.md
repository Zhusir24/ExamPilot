# 🔐 API密钥加密功能

## 📖 功能介绍

ExamPilot 使用 Fernet 对称加密技术对所有 API 密钥进行加密存储，确保数据库泄露时密钥安全。

### ✨ 主要特性

- 🔒 **Fernet 对称加密**：使用业界标准加密算法
- 🔑 **自动密钥管理**：首次启动自动生成加密密钥
- 🔄 **向后兼容**：自动处理明文和密文API密钥
- 📦 **透明加密**：对用户完全透明，无需额外操作
- 🛡️ **安全权限**：加密密钥文件权限设置为 0o600

---

## 🚀 工作原理

### 加密流程

```
┌─────────────────────────────────────────────────────────┐
│ 1. 用户输入API密钥                                      │
│    sk-xxxxxxxxxxxx                                      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. 加密服务加密                                         │
│    encryption_service.encrypt(api_key)                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. 存储加密后的密钥                                     │
│    gAAAAABl... (Base64编码的密文)                       │
└─────────────────────────────────────────────────────────┘
```

### 解密流程

```
┌─────────────────────────────────────────────────────────┐
│ 1. 从数据库读取                                         │
│    encrypted_key = config.api_key                       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. 加密服务解密                                         │
│    decrypted = encryption_service.decrypt(encrypted_key)│
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. 使用明文密钥                                         │
│    llm_service = LLMService(api_key=decrypted)          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 技术实现

### 加密服务

**文件位置**：`backend/core/encryption.py`

```python
from cryptography.fernet import Fernet
import os

class EncryptionService:
    def __init__(self):
        # 自动生成或加载加密密钥
        key_file = "data/.encryption_key"
        if not os.path.exists(key_file):
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # 设置严格权限

        with open(key_file, 'rb') as f:
            self._cipher = Fernet(f.read())

    def encrypt(self, text: str) -> str:
        """加密文本"""
        encrypted = self._cipher.encrypt(text.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_text: str) -> str:
        """解密文本，自动兼容明文"""
        try:
            decrypted = self._cipher.decrypt(encrypted_text)
            return decrypted.decode()
        except InvalidToken:
            # 解密失败，可能是明文，直接返回
            log.warning("解密失败，作为明文使用")
            return encrypted_text
```

### 向后兼容性

系统自动处理两种情况：

1. **新数据（已加密）**：正常解密使用
2. **旧数据（明文）**：直接使用，但建议迁移

---

## 🔄 迁移明文密钥

如果数据库中已有明文存储的 API 密钥，请使用迁移脚本进行加密。

### 运行迁移脚本

```bash
# 在项目根目录执行
.venv/bin/python -m backend.scripts.migrate_encrypt_api_keys

# 或自动确认模式
.venv/bin/python -m backend.scripts.migrate_encrypt_api_keys --yes
```

### 迁移过程

```bash
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

开始验证加密数据...
✓ oneapi: 解密测试成功
✓ embedding_service: 解密测试成功
✓ rerank_service: 解密测试成功

============================================================
✅ 迁移成功完成！
============================================================
```

---

## ⚠️ 重要事项

### 🔑 加密密钥文件

**位置**：`data/.encryption_key`

**重要性**：⚠️ **极其重要！丢失无法恢复数据！**

### 必须备份

```bash
# 备份加密密钥
cp data/.encryption_key data/.encryption_key.backup

# 或保存到安全位置
cp data/.encryption_key ~/safe-backup/exampilot_encryption_key_$(date +%Y%m%d)
```

### 权限设置

加密密钥文件自动设置为 `0o600`（只有所有者可读写）：

```bash
$ ls -l data/.encryption_key
-rw-------  1 user  staff  44 Nov  7 10:00 data/.encryption_key
```

---

## 🐛 故障排除

### 问题1：解密失败 "Incorrect padding"

**错误日志**：
```
ERROR | backend.core.encryption:decrypt:108 - 解密失败: Incorrect padding
ERROR | backend.api.websocket:get_active_llm_service:454 - LLM配置 oneapi API密钥解密失败
```

**原因**：数据库中有明文存储的 API 密钥

**解决方案**：

1. **临时方案**：系统自动降级为明文使用（会显示警告）
2. **永久方案**：运行迁移脚本加密所有密钥

```bash
.venv/bin/python -m backend.scripts.migrate_encrypt_api_keys --yes
```

---

### 问题2：加密密钥文件丢失

**后果**：无法解密已加密的 API 密钥

**解决方案**：

#### 方案A：恢复备份
```bash
# 从备份恢复
cp data/.encryption_key.backup data/.encryption_key
```

#### 方案B：重新配置（如果没有备份）
```bash
# 1. 删除旧的加密密钥（如果存在）
rm data/.encryption_key

# 2. 重启服务（会生成新密钥）
.venv/bin/python -m backend.main

# 3. 重新配置所有 API 密钥
# 访问前端 -> LLM设置 -> 重新输入所有 API 密钥
```

---

### 问题3：迁移脚本报错

**错误**：`No module named 'backend'`

**原因**：未在项目根目录执行

**解决**：
```bash
cd /path/to/exampilot
.venv/bin/python -m backend.scripts.migrate_encrypt_api_keys
```

---

## 📊 安全对比

| 特性 | 明文存储 | 加密存储 |
|------|---------|---------|
| 数据库泄露风险 | ⚠️ 高 | ✅ 低 |
| 密钥可读性 | 👁️ 直接可见 | 🔒 无法直接读取 |
| 备份要求 | 📦 数据库 | 📦 数据库 + 🔑 加密密钥 |
| 性能影响 | 无 | 极小（<1ms） |
| 实现复杂度 | 简单 | 中等 |
| 符合安全规范 | ❌ 否 | ✅ 是 |

---

## 💡 最佳实践

### 1. 立即备份加密密钥

```bash
# 第一次启动后立即备份
cp data/.encryption_key ~/backup/

# 定期备份（推荐）
crontab -e
# 添加：每天备份
0 2 * * * cp /path/to/exampilot/data/.encryption_key /backup/encryption_key_$(date +\%Y\%m\%d)
```

### 2. 使用密码管理器

将 `data/.encryption_key` 的内容保存到密码管理器（如 1Password、LastPass）。

### 3. 多地备份

- ✅ 本地备份
- ✅ 云存储（加密后）
- ✅ 密码管理器
- ✅ 移动硬盘

### 4. 权限控制

```bash
# 确保只有所有者可访问
chmod 600 data/.encryption_key

# 检查权限
ls -l data/.encryption_key
```

### 5. 迁移检查清单

- [ ] 备份数据库
- [ ] 停止正在运行的服务
- [ ] 确认加密密钥文件存在
- [ ] 运行迁移脚本
- [ ] 验证加密成功
- [ ] 备份加密密钥文件
- [ ] 测试功能是否正常

---

## 🔐 安全建议

### DO ✅

- ✅ 立即备份 `.encryption_key` 文件
- ✅ 定期检查文件权限（应为 600）
- ✅ 使用迁移脚本加密明文密钥
- ✅ 将密钥文件添加到备份计划
- ✅ 使用密码管理器保存密钥
- ✅ 限制对服务器的访问权限

### DON'T ❌

- ❌ 将 `.encryption_key` 提交到 Git
- ❌ 通过不安全渠道传输密钥
- ❌ 给密钥文件设置777权限
- ❌ 在公共场所显示密钥内容
- ❌ 忽略备份的重要性
- ❌ 在生产环境使用明文存储

---

## 📁 相关文件

### 核心文件

- `backend/core/encryption.py` - 加密服务实现
- `data/.encryption_key` - 加密密钥文件（⚠️ 重要！）
- `backend/scripts/migrate_encrypt_api_keys.py` - 迁移脚本

### 使用位置

- `backend/api/llm.py` - 创建/更新LLM配置时加密
- `backend/api/websocket.py` - 使用LLM时解密
- `backend/models/schema.py` - LLMConfig 模型

---

## 📞 获取帮助

如有问题，请：

1. **查看日志**：`data/logs/exampilot.log`
2. **检查配置**：`GET /api/llm/configs`
3. **验证加密**：查看数据库中 `api_key` 字段是否以 `gAAAAA` 开头
4. **提交Issue**：[GitHub Issues](https://github.com/your-repo/issues)

---

## 📝 相关文档

- [可视化答题模式](./visual_mode.md)
- [脚本使用指南](../scripts/migration_scripts.md)
- [故障排除](../troubleshooting/common_issues.md)

---

**最后更新**：2025-11-07

**保护好您的密钥，确保系统安全！🔐**
