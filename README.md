# ExamPilot - 智能自动答题系统

ExamPilot 是一个功能强大的问卷自动答题系统，支持多种答题模式、LLM智能解答和知识库检索。

## 功能特性

- 🤖 **智能答题**：集成LLM模型（支持OpenAI兼容API）进行智能答题
- 📚 **知识库检索**：支持文档上传、向量检索和结果重排序
- 🎯 **多种模式**：
  - 全自动AI答题
  - 用户勾选AI介入题目
  - 预设答案自动填充
- 🎬 **可视化答题模式**：实时观看AI答题过程，手动审核和提交 🆕
- 🔐 **API密钥加密**：使用Fernet加密存储所有API密钥，确保数据安全 🆕
- 🌐 **平台支持**：目前支持问卷星，可扩展其他平台
- 📝 **题型支持**：支持10种题型（填空、单选、多选、判断、简答、矩阵填空、多项简答、下拉选择、多项填空、级联下拉）
- ⏱️ **时间模拟**：人性化答题时间模拟（均匀/正态/分段停顿）
- 🔒 **置信度控制**：低置信度题目可设置人工确认

## 技术栈

### 后端
- FastAPI - Web框架
- Playwright - 浏览器自动化（支持Firefox和Chromium）
- SQLite - 数据存储
- Loguru - 日志管理
- SQLAlchemy - ORM
- Cryptography - API密钥加密（Fernet）

### 前端
- React 18
- TypeScript
- Vite
- TailwindCSS
- Material-UI
- Valtio - 状态管理

## 快速开始

### 方式一：使用启动脚本（推荐）

```bash
# 一键启动（会自动安装依赖）
./start.sh
```

### 方式二：开发模式（前后端分离）

```bash
# 启动前后端开发服务器
./dev.sh
```

### 方式三：手动安装

#### 1. 后端设置

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r backend/requirements.txt

# 安装Playwright浏览器
playwright install chromium

# 启动后端
cd backend
python main.py
```

后端将在 http://localhost:8000 启动

#### 2. 前端设置（可选，用于开发）

```bash
# 安装依赖
cd frontend
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

前端开发服务器将在 http://localhost:3000 启动

## 配置说明

### 环境变量

编辑 `.env` 文件配置系统参数：

```bash
# LLM配置
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# Embedding配置
EMBEDDING_API_KEY=your_api_key_here
EMBEDDING_BASE_URL=https://api.deepseek.com/v1
EMBEDDING_MODEL=deepseek-embedding

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### Web界面配置

系统启动后，可通过Web界面进行配置：

1. **LLM设置** (`/llm-settings`) - 配置多个LLM供应商
2. **知识库** (`/knowledge`) - 上传参考文档
3. **系统设置** (`/settings`) - 调整答题参数

## 使用指南

### 基本流程

1. **访问首页** - 打开 http://localhost:8000
2. **配置LLM** - 在"LLM设置"中添加API配置
3. **输入问卷URL** - 在首页输入问卷星链接
4. **解析题目** - 系统自动解析所有题目
5. **选择模式** - 选择答题模式（全自动/用户勾选/预设答案）
6. **开始答题** - 系统自动完成答题
7. **提交答案** - 确认后提交到问卷平台

### 答题模式说明

#### 模式一：全自动AI答题
- AI自动回答所有题目
- 适合完全信任AI的场景
- 可设置置信度阈值，低置信度题目会标记

#### 模式二：用户勾选AI介入
- 用户选择哪些题目由AI回答
- 适合部分题目需要AI辅助的场景
- 其他题目可手动填写或跳过

#### 模式三：预设答案自动填充
- 按题目顺序使用预设答案
- 适合已知答案的快速填写
- 可批量导入答案列表

### 知识库使用

1. 在"知识库"页面上传参考文档（.txt, .md）
2. 系统自动进行文档分块和向量化
3. 答题时自动检索相关内容
4. 支持Top-K和相似度阈值设置

### 时间模拟

系统支持三种时间模拟策略：

- **均匀分布**：每题耗时在min-max之间均匀分布
- **正态分布**：模拟正常人答题的时间分布
- **分段停顿**：随机添加思考停顿，更接近真实行为

可在"系统设置"中调整参数。

## API文档

启动后访问：http://localhost:8000/docs

## 项目结构

```
exampilot/
├── backend/                  # 后端代码
│   ├── api/                 # FastAPI路由
│   │   ├── questionnaire.py # 问卷接口
│   │   ├── llm.py          # LLM配置接口
│   │   ├── knowledge.py    # 知识库接口
│   │   ├── settings.py     # 系统设置接口
│   │   └── websocket.py    # WebSocket接口
│   ├── core/               # 核心模块
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # 数据库连接
│   │   ├── encryption.py   # 加密服务 🆕
│   │   └── logger.py       # 日志配置
│   ├── models/             # 数据模型
│   │   ├── question.py     # 题目模型
│   │   ├── answer.py       # 答案模型
│   │   └── schema.py       # 数据库模型
│   ├── services/           # 业务逻辑
│   │   ├── platforms/      # 平台适配器
│   │   ├── llm_service.py  # LLM服务
│   │   ├── knowledge_base.py # 知识库服务
│   │   ├── answering_modes.py # 答题模式
│   │   └── timing_simulator.py # 时间模拟
│   ├── migrations/         # 数据库迁移
│   ├── scripts/           # 维护脚本 🆕
│   │   ├── migrate_encrypt_api_keys.py  # API密钥加密迁移
│   │   └── fix_questionnaire_titles.py  # 问卷标题修复
│   ├── main.py            # 主入口
│   └── requirements.txt   # Python依赖
├── frontend/              # 前端代码
│   ├── src/
│   │   ├── api/          # API调用
│   │   ├── components/   # React组件
│   │   ├── pages/        # 页面
│   │   ├── store/        # 状态管理
│   │   ├── types/        # TypeScript类型
│   │   ├── utils/        # 工具函数
│   │   ├── App.tsx       # 主组件
│   │   └── main.tsx      # 入口
│   ├── package.json      # npm依赖
│   ├── vite.config.ts    # Vite配置
│   └── tailwind.config.js # Tailwind配置
├── data/                 # 数据目录
│   ├── database.db      # SQLite数据库
│   ├── .encryption_key  # 加密密钥文件 🆕 ⚠️重要！
│   └── logs/            # 日志文件
├── .venv/               # Python虚拟环境
├── .env                 # 环境变量
├── start.sh             # 启动脚本
├── dev.sh               # 开发模式脚本
└── README.md            # 本文件
```

## 扩展开发

### 添加新平台

1. 在 `backend/services/platforms/` 创建新的平台适配器
2. 继承 `BasePlatform` 基类
3. 实现必要的方法：`parse_url`, `extract_questions`, `submit_answers`
4. 在 `__init__.py` 中注册平台

### 添加新的LLM供应商

系统设计支持任何OpenAI兼容的API，只需在Web界面配置即可。

对于非OpenAI兼容的API：
1. 在 `backend/services/llm_service.py` 创建新的服务类
2. 实现统一的接口
3. 在配置中添加供应商类型

### 添加新题型

1. 在 `backend/models/question.py` 添加题型枚举
2. 在平台适配器中实现题型识别
3. 在前端添加题型显示逻辑

## 常见问题

### 1. Playwright浏览器安装失败

```bash
# 手动安装
playwright install chromium

# 如果网络问题，可以使用镜像
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
playwright install chromium
```

### 2. 前端打包后访问404

确保前端已正确构建：
```bash
cd frontend
npm run build
```

### 3. WebSocket连接失败

检查防火墙设置，确保8000端口可访问。

### 4. 数据库迁移失败

删除数据库文件重新初始化：
```bash
rm data/database.db
# 重启服务会自动创建新数据库
```

### 5. 可视化模式浏览器没有弹出

检查设置和环境：
```bash
# 检查可视化模式是否启用
curl http://localhost:8000/api/settings/visual_mode

# 如果未启用，通过API启用
curl -X PUT http://localhost:8000/api/settings/visual_mode \
  -H "Content-Type: application/json" \
  -d '{"key":"visual_mode","value":true,"value_type":"bool"}'

# 确保在图形界面环境中运行（不支持纯SSH）
```

详细故障排除：[可视化答题模式文档](docs/features/visual_mode.md#-故障排除)

### 6. API密钥加密迁移

如果数据库中有明文API密钥，运行迁移脚本：
```bash
# 备份数据库
cp data/exampilot.db data/exampilot.db.backup

# 运行迁移脚本
.venv/bin/python -m backend.scripts.migrate_encrypt_api_keys --yes

# 备份加密密钥文件（⚠️ 极其重要！）
cp data/.encryption_key ~/backup/encryption_key_$(date +%Y%m%d)
```

详细说明：[API密钥加密文档](docs/features/api_encryption.md)

## 注意事项

1. **使用规范**：请确保使用本系统符合相关平台的服务条款
2. **API限额**：注意LLM API的调用限额和费用
3. **数据安全**：
   - API密钥已自动加密存储（Fernet加密）
   - ⚠️ **重要**：立即备份 `data/.encryption_key` 文件！
   - 丢失加密密钥将无法恢复已加密的API密钥
4. **网络稳定**：答题过程需要稳定的网络连接
5. **可视化模式**：
   - 适合少量题目的问卷（< 50题）
   - 需要图形界面环境（不支持纯命令行服务器）
   - 可在系统设置中开启/关闭

## 版本历史

### v2.1 (2025-11-07) 🆕
- 🎬 **可视化答题模式**：实时观看AI答题，手动审核提交
- 🔐 **API密钥加密**：Fernet加密存储，自动兼容明文
- 🛡️ **增强错误处理**：详细的异常分类和友好的错误信息
- 🤖 **LLM改进**：更健壮的JSON解析和响应处理
- 🌐 **浏览器优化**：优先使用Firefox，避免macOS崩溃
- 📚 详细更新日志：[docs/CHANGELOG.md](docs/CHANGELOG.md)

### v2.0 (2025-10-18) 🎉
- ✅ **新增6种题型支持**：简答题、矩阵填空、多项简答、下拉选择、多项填空、级联下拉
- ✅ **题型覆盖率100%**：可完整解析测试问卷的所有20道题目
- ✅ **URL清理优化**：支持带锚点的URL（如 `#`）
- ✅ **域名支持增强**：支持 wjx.com、wjx.cn 等多个问卷星域名
- 📖 题型使用指南：[docs/guides/question_types.md](docs/guides/question_types.md)

### v1.0
- ✅ 项目基础架构
- ✅ 问卷星平台适配器
- ✅ LLM智能答题
- ✅ 知识库向量检索
- ✅ 三种答题模式
- ✅ 时间模拟
- ✅ Web界面
- ✅ 基础题型支持（填空、单选、多选、判断）

## 开发计划

### 近期计划 (v2.2)
- [ ] 更多题型支持（排序题、矩阵单选/多选、量表题等）
- [ ] 可视化模式的高级配置（自定义延迟、窗口大小等）
- [ ] 答题报告导出（PDF、Excel）

### 中期计划 (v3.0)
- [ ] 更多平台支持（腾讯问卷、金数据等）
- [ ] 批量答题功能
- [ ] 答题历史记录查询和分析
- [ ] Docker部署支持

### 长期计划
- [ ] 多用户支持和权限管理
- [ ] API接口开放
- [ ] 插件系统

## 文档索引

- 📖 **[文档中心](docs/README.md)** - 完整文档导航和索引
- 📖 **[题型使用指南](docs/guides/question_types.md)** - 所有10种题型的详细说明和答案格式
- 🎬 **[可视化答题模式](docs/features/visual_mode.md)** - 实时观看AI答题全过程
- 🔐 **[API密钥加密](docs/features/api_encryption.md)** - 密钥加密存储和迁移指南
- 🛠️ **[迁移脚本指南](docs/scripts/migration_scripts.md)** - 数据迁移和维护脚本
- 📚 **[更新日志](docs/CHANGELOG.md)** - 版本更新记录

## 常见问题

### 如何清除问卷缓存？

如果需要重新解析某个问卷，使用清除缓存脚本：

```bash
python scripts/clear_cache.py rDTLYkN  # 参数为问卷URL的一部分
```

更多工具脚本请查看 [scripts/README.md](scripts/README.md)。

### 支持哪些问卷星域名？

- `wjx.cn` - 主域名
- `wjx.com` - 国际域名
- `wjx.top` - 备用域名
- `wenjuan.com` - 旧域名
- `sojump.com` - 早期域名
- `wenjuan.in` - 备用域名

所有这些域名的问卷都能正常识别和解析。

### 题型支持情况

ExamPilot v2.0 支持以下10种题型：

| 题型 | 状态 | 说明 |
|------|------|------|
| 填空题 | ✅ | 单行文本输入 |
| 单选题 | ✅ | 包括普通单选和评分单选 |
| 多选题 | ✅ | 支持多项选择 |
| 判断题 | ✅ | 对/错题 |
| 简答题 | ✅ v2.0新增 | 长文本输入 |
| 矩阵填空 | ✅ v2.0新增 | 多行多列表格填空 |
| 多项简答 | ✅ v2.0新增 | 多个简答题组合 |
| 下拉选择 | ✅ v2.0新增 | Select下拉框 |
| 多项填空 | ✅ v2.0新增 | 段落中嵌入多个填空 |
| 级联下拉 | ✅ v2.0新增 | 省市区等级联选择 |

详细的题型说明和答案格式请参考 [题型使用指南](docs/QUESTION_TYPES_GUIDE.md)。

## 贡献

欢迎提交Issue和Pull Request！

## License

MIT License

## 作者

ExamPilot Team

## 致谢

感谢所有开源项目的贡献者！

