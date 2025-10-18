# 工具脚本说明

本目录包含ExamPilot的维护和管理工具脚本。

## 📝 脚本列表

### 1. clear_cache.py - 清除问卷缓存

**用途**：清除指定问卷的解析缓存，强制重新解析。

**使用场景**：
- 问卷内容更新后，需要重新解析
- 解析结果不正确，需要强制刷新
- 测试新的解析逻辑

**用法**：
```bash
python scripts/clear_cache.py rDTLYkN
```

**参数**：
- `url_part`：问卷URL的一部分（如问卷ID）

**示例**：
```bash
# 清除特定问卷
python scripts/clear_cache.py rDTLYkN

# 清除包含特定关键词的所有问卷
python scripts/clear_cache.py test
```

---

### 2. clean_knowledge_db.py - 清理知识库脏数据

**用途**：清理知识库中的孤儿数据（孤儿分块和孤儿向量）。

**使用场景**：
- 删除文档后，清理残留的分块和向量数据
- 数据库维护，解决数据不一致问题
- 释放数据库空间

**用法**：
```bash
python scripts/clean_knowledge_db.py
```

**功能**：
1. 查找并删除孤儿分块（文档已删除但分块还在）
2. 查找并删除孤儿向量（分块已删除但向量还在）
3. 显示清理后的数据库状态

**注意**：此操作不可逆，但通常是安全的（只删除无效数据）。

---

### 3. reset_knowledge_db.py - 重置知识库

**用途**：完全清空知识库，删除所有文档、分块和向量数据。

**使用场景**：
- 重新开始构建知识库
- 清除所有测试数据
- 解决严重的数据问题

**用法**：
```bash
python scripts/reset_knowledge_db.py
```

**流程**：
1. 脚本会要求输入 `yes` 确认
2. 删除所有向量数据
3. 删除所有分块数据
4. 删除所有文档数据

**警告**：⚠️ 此操作不可逆！会删除所有知识库数据！

---

## 🔧 常见用例

### 场景1：重新解析某个问卷

```bash
# 1. 清除缓存
python scripts/clear_cache.py rDTLYkN

# 2. 在Web界面重新输入问卷URL进行解析
```

### 场景2：清理知识库

```bash
# 1. 先清理孤儿数据
python scripts/clean_knowledge_db.py

# 2. 如果还有问题，考虑完全重置
python scripts/reset_knowledge_db.py
```

### 场景3：开发测试

```bash
# 开发新功能前，清除测试数据
python scripts/clear_cache.py test
python scripts/reset_knowledge_db.py
```

---

## 📋 数据库表说明

### 问卷相关表
- `questionnaires` - 问卷基本信息
- `questions` - 题目记录
- `answering_sessions` - 答题会话
- `answers` - 答案记录

### 知识库相关表
- `knowledge_documents` - 知识库文档
- `knowledge_chunks` - 文档分块
- `vector_embeddings` - 向量嵌入

---

## ⚠️ 注意事项

1. **备份数据**：在使用重置脚本前，建议备份 `data/database.db`
2. **确认操作**：重置脚本需要输入 `yes` 确认
3. **停止服务**：运行脚本前，建议停止后端服务
4. **检查结果**：脚本执行后会显示操作结果，请仔细查看

---

## 🐛 故障排查

### 脚本运行失败

1. 检查Python环境是否激活：
   ```bash
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. 检查数据库文件是否存在：
   ```bash
   ls -lh data/database.db
   ```

3. 检查依赖是否安装：
   ```bash
   pip install -r backend/requirements.txt
   ```

### 数据未删除

- 确保后端服务已停止
- 检查数据库文件权限
- 查看脚本输出的错误信息

---

**最后更新**: 2025-10-18
