# ExamPilot 测试文档

本目录包含 ExamPilot 项目的测试文件和测试数据。

## 目录结构

```
tests/
├── README.md                # 本文档
├── fixtures/                # 测试数据文件
│   ├── test_markdown.md    # Markdown 格式测试文件
│   └── test_text.txt       # 纯文本测试文件
├── unit/                    # 单元测试
│   └── test_markdown_parser.py  # Markdown 解析功能测试
└── integration/             # 集成测试
    └── test_upload.py       # 文件上传功能端到端测试
```

## 测试说明

### 单元测试

#### 1. Markdown 解析测试 (`unit/test_markdown_parser.py`)

测试 Markdown 文件解析为纯文本的功能。

**运行方式：**
```bash
# 从项目根目录运行
.venv/bin/python tests/unit/test_markdown_parser.py
```

**测试内容：**
- Markdown 转纯文本解析
- 格式标记去除验证
- 文本内容保留验证
- 文本分块功能测试

**预期输出：**
- 显示原始 Markdown 和解析后的纯文本
- 统计信息（原始长度、解析后长度、压缩率）
- 8 项内容验证（全部应显示 ✓）
- 分块结果展示

### 集成测试

#### 2. 文件上传测试 (`integration/test_upload.py`)

测试知识库文件上传 API 的完整功能。

**运行方式：**
```bash
# 1. 首先启动后端服务
cd backend
uvicorn main:app --reload

# 2. 在另一个终端运行测试（从项目根目录）
.venv/bin/python tests/integration/test_upload.py
```

**测试内容：**
1. 上传 .md 文件（应成功）
2. 上传 .txt 文件（应成功）
3. 上传 .pdf 文件（应被拒绝，返回 400）
4. 上传超大文件（应被拒绝，返回 400）
5. 获取文档列表（应成功）

**预期结果：**
- 测试 1、2、5 应显示 ✓ 成功
- 测试 3、4 应显示 ✓ 正确拒绝

## 测试数据说明

### fixtures/test_markdown.md

包含各种 Markdown 格式的测试文档：
- 标题（多级）
- 列表（有序、无序）
- 文本格式（加粗、斜体、删除线、代码）
- 代码块
- 引用
- 表格
- 链接

用于验证 Markdown 解析功能是否能正确处理各种格式。

### fixtures/test_text.txt

简单的纯文本文件，用于验证基本的文本文件上传功能。

## 功能覆盖

### 已测试功能

✅ **Markdown 解析**
- Markdown 转纯文本
- 格式标记移除
- 内容完整性保留

✅ **文件验证**
- 文件格式验证（.txt, .md）
- 文件大小限制（10MB）
- UTF-8 编码验证

✅ **文档处理**
- 文档上传
- 文档分块
- 元数据记录

✅ **API 测试**
- 上传接口
- 列表查询接口
- 错误处理

### 未来扩展

⏸️ **待添加测试**
- 向量生成测试（需要 Embedding 服务）
- 搜索功能测试
- 文档删除测试
- 并发上传测试
- 性能测试

⏸️ **待支持格式**
- PDF 文件解析
- Word 文档解析
- HTML 文件解析

## 测试环境要求

### Python 依赖

确保已安装以下依赖（已包含在 requirements.txt 中）：
```
markdown==3.5.2
beautifulsoup4==4.12.3
httpx  # 用于集成测试
```

### 后端服务

集成测试需要后端服务运行在 `http://localhost:8000`

### 数据库

测试会在数据库中创建真实的文档记录，建议使用测试数据库。

## 故障排除

### 单元测试失败

**问题：** `ModuleNotFoundError: No module named 'backend'`

**解决：** 确保从项目根目录运行测试，或检查 Python 路径设置。

**问题：** `FileNotFoundError: test_markdown.md`

**解决：** 确保测试数据文件在 `tests/fixtures/` 目录下。

### 集成测试失败

**问题：** `Connection refused`

**解决：** 确保后端服务已启动并运行在 `http://localhost:8000`

**问题：** `未配置Embedding服务`

**解决：** 在 LLM 设置中添加并激活一个 Embedding 配置。

## 贡献指南

添加新测试时，请遵循以下规范：

1. **单元测试**：放在 `tests/unit/` 目录
2. **集成测试**：放在 `tests/integration/` 目录
3. **测试数据**：放在 `tests/fixtures/` 目录
4. **命名规范**：测试文件以 `test_` 开头
5. **文档更新**：在本 README 中记录新测试的说明

## 许可

与 ExamPilot 项目相同的许可协议。
