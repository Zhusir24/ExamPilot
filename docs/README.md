# 📚 ExamPilot 文档中心

欢迎来到 ExamPilot 的文档中心！这里包含了所有的使用指南、功能说明和开发文档。

---

## 🎯 快速导航

### 🚀 新手入门

- **[项目主页](../README.md)** - 项目简介和快速开始
- **[题型使用指南](./guides/question_types.md)** - 了解所有支持的题型和答案格式

### ✨ 功能特性

- **[🎬 可视化答题模式](./features/visual_mode.md)**
  - 实时观看 AI 答题过程
  - 慢动作播放，手动提交
  - 适合重要问卷和调试

- **[🔐 API密钥加密](./features/api_encryption.md)**
  - Fernet 对称加密
  - 自动密钥管理
  - 向后兼容明文密钥

### 🛠️ 脚本工具

- **[迁移脚本指南](./scripts/migration_scripts.md)**
  - API密钥加密迁移
  - 问卷标题修复
  - 自定义脚本开发

### 📖 开发文档

- **[更新日志](./CHANGELOG.md)** - 版本更新记录

---

## 📋 文档目录结构

```
docs/
├── README.md                          # 文档索引（本文件）
├── CHANGELOG.md                       # 更新日志
│
├── features/                          # 功能特性文档
│   ├── visual_mode.md                 # 可视化答题模式
│   └── api_encryption.md              # API密钥加密
│
├── guides/                            # 使用指南
│   └── question_types.md              # 题型使用指南
│
├── scripts/                           # 脚本文档
│   └── migration_scripts.md           # 迁移脚本使用指南
│
├── development/                       # 开发文档（预留）
│   └── (待添加)
│
└── troubleshooting/                   # 故障排除（预留）
    └── (待添加)
```

---

## 📖 题型快速参考

| 题型 | 答案格式 | 示例 |
|------|---------|------|
| 填空题 | 字符串 | `"答案内容"` |
| 单选题 | 整数索引 | `0` (第一个选项) |
| 多选题 | 整数数组 | `[0, 2]` |
| 判断题 | 整数索引 | `0` (对) 或 `1` (错) |
| 简答题 | 字符串 | `"详细回答..."` |
| 矩阵填空 | 字典 | `{"q2_0": "答案1", "q2_1": "答案2"}` |
| 多项简答 | 字典 | `{"q12_0": "回答1", "q12_1": "回答2"}` |
| 下拉选择 | 整数索引 | `0` |
| 多项填空 | 字典或列表 | `["答案1", "答案2"]` |
| 级联下拉 | 字符串 | `"北京市-朝阳区"` |

详细说明请查看 **[题型使用指南](./guides/question_types.md)**。

---

## 🎬 功能特性速览

### 可视化答题模式

**适用场景**：
- ✅ 第一次使用 ExamPilot
- ✅ 重要问卷需要人工审核
- ✅ 调试答题逻辑

**使用方法**：
```bash
# 1. 启用可视化模式（前端设置页面 或 API）
# 2. 开始答题
# 3. 浏览器窗口自动弹出，慢动作填写答案
# 4. 检查答案后手动提交
```

**详细文档**：[可视化答题模式](./features/visual_mode.md)

---

### API密钥加密

**功能**：
- 🔒 使用 Fernet 加密所有 API 密钥
- 🔄 自动兼容明文和密文
- 🔑 自动生成和管理加密密钥

**迁移方法**：
```bash
# 加密已有的明文API密钥
.venv/bin/python -m backend.scripts.migrate_encrypt_api_keys --yes
```

**详细文档**：[API密钥加密](./features/api_encryption.md)

---

## 🛠️ 常用脚本

### 1. API密钥加密迁移

```bash
# 将所有明文API密钥加密
.venv/bin/python -m backend.scripts.migrate_encrypt_api_keys --yes
```

### 2. 修复问卷标题

```bash
# 修复"未命名问卷"的标题
.venv/bin/python -m backend.scripts.fix_questionnaire_titles --yes
```

**详细文档**：[迁移脚本指南](./scripts/migration_scripts.md)

---

## 🔧 系统要求

### 运行环境

- **Python**: 3.10+
- **数据库**: SQLite / PostgreSQL
- **浏览器**: Firefox / Chromium（Playwright）
- **操作系统**: Windows / macOS / Linux

### 可视化模式要求

- ✅ **本地开发**：完全支持
- ⚠️ **云服务器**：需要 X11/VNC 或虚拟显示
- ❌ **无头环境**：不支持

---

## 📊 版本信息

- **当前版本**: v2.0
- **最新更新**: 2025-11-07
- **Python版本**: 3.10+
- **主要依赖**: FastAPI, Playwright, SQLAlchemy, Cryptography

查看完整更新日志：[CHANGELOG.md](./CHANGELOG.md)

---

## 🐛 故障排除

### 常见问题

#### 1. 可视化模式浏览器没有弹出

**解决方案**：
- 检查 `visual_mode` 设置是否为 `true`
- 确保在图形界面环境中运行
- 查看后端日志确认是否有错误

**详细文档**：[可视化答题模式 - 故障排除](./features/visual_mode.md#-故障排除)

---

#### 2. API密钥解密失败

**错误信息**：`Incorrect padding`

**解决方案**：
- 系统会自动降级为明文使用（临时方案）
- 运行迁移脚本加密所有密钥（永久方案）

**详细文档**：[API密钥加密 - 故障排除](./features/api_encryption.md#-故障排除)

---

#### 3. 问卷标题显示"未命名问卷"

**解决方案**：
```bash
.venv/bin/python -m backend.scripts.fix_questionnaire_titles --yes
```

**详细文档**：[迁移脚本指南](./scripts/migration_scripts.md#2-问卷标题修复脚本)

---

## 💡 最佳实践

### 安全建议

- ✅ 立即备份 `data/.encryption_key` 文件
- ✅ 定期备份数据库
- ✅ 使用迁移脚本加密明文 API 密钥
- ✅ 限制对服务器的访问权限

### 使用建议

- 💡 第一次使用时开启可视化模式，观察 AI 答题过程
- 💡 重要问卷使用可视化模式，人工审核答案
- 💡 批量答题时关闭可视化模式，提高速度
- 💡 定期查看日志文件，及时发现问题

---

## 📞 获取帮助

### 查看日志

```bash
# 后端日志
tail -f data/logs/exampilot.log

# 按时间查看
ls -lt data/logs/
```

### 报告问题

如果遇到问题，请：

1. **查看相关文档** - 检查是否有故障排除章节
2. **查看日志文件** - `data/logs/exampilot.log`
3. **提交 Issue** - [GitHub Issues](https://github.com/your-repo/issues)

提交 Issue 时请包含：
- 问题描述
- 错误信息
- 相关日志
- 复现步骤

---

## 💻 开发相关

### 贡献文档

欢迎改进文档！

1. Fork 项目仓库
2. 创建文档分支 (`git checkout -b docs/improve-xxx`)
3. 修改文档
4. 提交更改 (`git commit -m 'docs: 改进xxx文档'`)
5. 推送到分支 (`git push origin docs/improve-xxx`)
6. 创建 Pull Request

### 文档规范

- 使用 Markdown 格式
- 添加清晰的标题和目录
- 包含代码示例和输出示例
- 添加必要的警告和注意事项
- 更新"最后更新"日期

---

## 🔗 相关链接

- **[项目主页](../README.md)**
- **[GitHub 仓库](#)**
- **[问题反馈](#)**
- **[更新日志](./CHANGELOG.md)**

---

## 📅 文档更新记录

| 日期 | 更新内容 |
|------|---------|
| 2025-11-07 | 重组文档结构，添加可视化模式和API加密文档 |
| 2025-10-18 | v2.0版本发布，添加题型指南 |

---

**感谢使用 ExamPilot！** 🎉

如果文档有帮助，请给项目一个 ⭐️
