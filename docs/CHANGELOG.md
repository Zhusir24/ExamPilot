# ExamPilot 更新日志

---

## v2.1 (2025-11-07) 🆕

### 版本信息
- **版本号**: v2.1
- **发布日期**: 2025-11-07
- **重大更新**: 可视化答题模式、API密钥加密

---

### 🎉 主要更新

#### 1. 🎬 可视化答题模式（新功能）

**功能介绍**：
- 实时观看AI答题的全过程
- 浏览器窗口自动弹出（Firefox优先）
- 慢动作播放（800ms延迟）
- 答题完成后手动审核和提交
- 浏览器保持打开10分钟

**适用场景**：
- 第一次使用ExamPilot
- 重要问卷需要人工审核
- 调试答题逻辑
- 演示和教学

**文档**：[可视化答题模式](./features/visual_mode.md)

---

#### 2. 🔐 API密钥加密（新功能）

**功能介绍**：
- 使用Fernet对称加密所有API密钥
- 自动生成和管理加密密钥文件
- 向后兼容明文密钥（自动降级）
- 提供迁移脚本加密现有明文密钥

**安全特性**：
- 加密密钥文件权限设置为600
- 数据库泄露时密钥无法直接读取
- 符合安全规范和最佳实践

**文档**：[API密钥加密](./features/api_encryption.md)

---

#### 3. 🛡️ 增强错误处理

**改进内容**：
- 详细的异常分类（ValueError、ConnectionError、TimeoutError、RuntimeError）
- 友好的错误信息和建议
- LLM API调用的详细错误日志
- Embedding服务的超时和连接错误处理

**涉及文件**：
- `backend/api/knowledge.py` - 知识库API错误处理
- `backend/services/llm_service.py` - LLM服务错误处理
- `backend/services/knowledge_base.py` - 向量生成错误处理

---

#### 4. 🤖 LLM服务改进

**新增功能**：
- `_extract_json_from_text()` 方法：支持从各种格式中提取JSON
  - 代码块中的JSON（\`\`\`json ... \`\`\`）
  - 嵌套JSON对象
  - 使用栈匹配大括号，确保完整性

**改进内容**：
- 更健壮的响应验证
- 更好的降级处理
- 详细的错误日志

---

#### 5. 🌐 问卷星平台优化

**标题提取改进**：
- 支持8种不同的CSS选择器
- 从页面title标签降级提取
- 更智能的标题识别和清理

**浏览器引擎优化**：
- 优先使用Firefox（避免macOS上Chromium崩溃）
- Chromium回退时使用更稳定的启动参数
- 可视化模式下的窗口大小和位置优化

---

### 📝 新增文件

#### 核心功能
- `backend/core/encryption.py` - 加密服务实现
- `data/.encryption_key` - 加密密钥文件（自动生成，⚠️重要！）

#### 迁移脚本
- `backend/scripts/__init__.py` - 脚本模块初始化
- `backend/scripts/migrate_encrypt_api_keys.py` - API密钥加密迁移
- `backend/scripts/fix_questionnaire_titles.py` - 问卷标题修复

#### 文档
- `docs/features/visual_mode.md` - 可视化答题模式完整文档
- `docs/features/api_encryption.md` - API密钥加密完整文档
- `docs/scripts/migration_scripts.md` - 迁移脚本使用指南
- `docs/guides/question_types.md` - 题型指南（从根目录移动）

---

### 🔄 修改的文件

#### 后端API
- `backend/api/llm.py` - 添加API密钥加密逻辑
- `backend/api/knowledge.py` - 添加API密钥解密和错误处理
- `backend/api/websocket.py` - 添加可视化模式支持和API密钥解密
- `backend/api/settings.py` - 新增 `visual_mode` 配置项

#### 服务层
- `backend/services/llm_service.py` - 改进JSON解析和错误处理
- `backend/services/knowledge_base.py` - 增强向量生成验证和错误处理
- `backend/services/platforms/wenjuanxing.py` - 添加可视化模式和标题提取改进

#### 前端
- `frontend/src/pages/AnsweringProgressPage.tsx` - 添加可视化模式UI提示
- `frontend/src/pages/SystemSettingsPage.tsx` - 添加可视化模式开关

#### 依赖
- `backend/requirements.txt` - 新增 `cryptography==42.0.0`

#### 文档
- `docs/README.md` - 重组文档结构，添加快速导航
- `README.md` - 更新功能特性和版本历史

---

### ⚠️ 重要提醒

#### API密钥加密迁移

如果您的数据库中已有明文API密钥，请运行迁移脚本：

```bash
.venv/bin/python -m backend.scripts.migrate_encrypt_api_keys --yes
```

#### 备份加密密钥

**极其重要**：立即备份 `data/.encryption_key` 文件！

```bash
cp data/.encryption_key ~/backup/encryption_key_$(date +%Y%m%d)
```

丢失此文件将无法解密已加密的API密钥！

---

### 🔧 兼容性

#### 向后兼容
- ✅ 完全兼容v2.0的所有功能
- ✅ 自动兼容明文和密文API密钥
- ✅ 可视化模式为可选功能，默认关闭

#### 数据库
- ❌ 不需要数据库结构迁移
- ✅ 建议运行API密钥加密迁移脚本

---

### 📊 性能影响

- 加密/解密开销：< 1ms（可忽略）
- 可视化模式：慢动作播放，适合少量题目
- 非可视化模式：性能无影响

---

### 🐛 已知问题

#### macOS Chromium崩溃
- **状态**：已修复
- **解决方案**：优先使用Firefox

#### 云服务器可视化模式
- **限制**：需要GUI环境
- **解决方案**：使用xvfb虚拟显示

---

### 📖 文档更新

#### 新增文档
1. **可视化答题模式** - 完整使用指南和故障排除
2. **API密钥加密** - 安全原理和迁移步骤
3. **迁移脚本指南** - 所有脚本的使用说明

#### 更新文档
1. **主README** - 添加新功能介绍
2. **文档中心** - 重组结构，添加快速导航

---

## v2.0 (2025-10-18) 🎉

### 版本信息
- **版本号**: v2.0
- **发布日期**: 2025-10-18
- **重大更新**: 新增6种题型支持

---

### 🎉 主要更新

### 新增题型支持

本次更新大幅提升了ExamPilot对问卷星平台的题型支持，**从原来的4种题型扩展到10种题型**，题型覆盖率提升**150%**！

#### 新增题型列表：

1. **简答题** (ESSAY)
   - 问卷星type: `type="2"`
   - 支持长文本输入
   - 使用 `<textarea>` 元素

2. **矩阵填空题** (MATRIX_FILL)
   - 问卷星type: `type="9"`
   - 支持多行多列的表格填空
   - 答案格式：字典 `{"q2_0": "答案1", "q2_1": "答案2"}`

3. **多项简答题** (MULTIPLE_ESSAY)
   - 问卷星type: `type="34"`
   - 支持多个简答题组合
   - 类似矩阵填空，但用于长文本

4. **下拉单选题** (DROPDOWN)
   - 问卷星type: `type="7"`
   - 支持 `<select>` 下拉框
   - 兼容 Select2 插件

5. **多项填空题** (GAP_FILL)
   - 问卷星标记: `gapfill="1"`
   - 支持段落中嵌入多个填空
   - 支持 contenteditable 元素

6. **级联下拉** (CASCADE_DROPDOWN)
   - 问卷星标记: `verify="多级下拉"`
   - 支持省市区等级联选择
   - 提供基础实现

---

## 📊 题型支持对比

### v1.0 vs v2.0

| 题型 | v1.0 | v2.0 | 备注 |
|------|------|------|------|
| 填空题 | ✅ | ✅ | 单行文本输入 |
| 单选题 | ✅ | ✅ | 包括普通单选和评分单选 |
| 多选题 | ✅ | ✅ | 支持多项选择 |
| 判断题 | ✅ | ✅ | 对/错题 |
| **简答题** | ❌ | ✅ | **新增** |
| **矩阵填空** | ❌ | ✅ | **新增** |
| **多项简答** | ❌ | ✅ | **新增** |
| **下拉选择** | ❌ | ✅ | **新增** |
| **多项填空** | ❌ | ✅ | **新增** |
| **级联下拉** | ❌ | ✅ | **新增** |

### 测试问卷支持率

针对测试问卷 (https://ks.wjx.com/vm/rDTLYkN.aspx)：
- **v1.0**: 10/20 题目 (50%)
- **v2.0**: 20/20 题目 (100%) ✨

---

## 🔧 技术改进

### 1. 题型检测增强

**文件**: `backend/services/platforms/wenjuanxing.py`

增强了 `_detect_question_type` 方法，现在可以识别：
- `type` 属性值（2, 7, 9, 34等）
- 特殊标记（`gapfill`, `ispanduan`等）
- HTML结构特征（table, select, textarea等）
- 验证属性（`verify="多级下拉"`等）

### 2. 题型枚举扩展

**文件**: `backend/models/question.py`

```python
class QuestionType(str, Enum):
    FILL_BLANK = "填空"
    SINGLE_CHOICE = "单选"
    MULTIPLE_CHOICE = "多选"
    TRUE_FALSE = "判断"
    ESSAY = "简答"              # 新增
    MATRIX_FILL = "矩阵填空"     # 新增
    MULTIPLE_ESSAY = "多项简答"   # 新增
    DROPDOWN = "下拉选择"        # 新增
    GAP_FILL = "多项填空"        # 新增
    CASCADE_DROPDOWN = "级联下拉" # 新增
```

### 3. 答案填写方法

新增6个填写方法：
- `_fill_essay()` - 简答题填写
- `_fill_matrix()` - 矩阵填空题填写
- `_fill_multiple_essay()` - 多项简答题填写
- `_fill_dropdown()` - 下拉选择题填写
- `_fill_gap_fill()` - 多项填空题填写
- `_fill_cascade()` - 级联下拉填写

### 4. 答案验证

增强了 `Question.validate_answer()` 方法，支持所有新题型的答案格式验证。

---

## 📝 代码变更

### 修改的文件

1. **backend/models/question.py**
   - 新增6种题型枚举
   - 扩展答案验证逻辑（+83行）

2. **backend/services/platforms/wenjuanxing.py**
   - 增强题型检测逻辑（+60行）
   - 重构 `_fill_answer` 方法（+25行）
   - 新增6个填写方法（+167行）
   - 总计新增：~250行代码

### 新增的文件

1. **QUESTION_TYPES_GUIDE.md**
   - 详细的题型使用指南
   - 包含所有题型的答案格式说明
   - API使用示例

2. **CHANGELOG_v2.0.md**
   - 本更新日志

---

## 🚀 使用示例

### 矩阵填空题

```python
# 题目2: 基本信息测试（矩阵填空）
answers = {
    "div2": {
        "q2_0": "张三",      # 姓名
        "q2_1": "技术部",    # 部门
        "q2_2": "EMP001"    # 员工编号
    }
}
```

### 多项填空题

```python
# 题目10: 多项填空测试
# 方式1：字典格式
answers = {
    "div10": {
        "q10_1": "北京",
        "q10_2": "上海"
    }
}

# 方式2：列表格式
answers = {
    "div10": ["北京", "上海"]
}
```

### 简答题

```python
# 题目11: 简答题测试
answers = {
    "div11": "这是一段详细的简答题回答。\n可以包含多行文字。"
}
```

### 下拉选择题

```python
# 题目17: 下拉单选测试
answers = {
    "div17": 0  # 选择第一个选项（不包括"请选择"）
}
```

---

## ⚠️ 兼容性说明

### 向后兼容

- ✅ 完全兼容v1.0的答案格式
- ✅ 原有的4种题型功能不受影响
- ✅ API接口保持不变

### 数据库迁移

- ❌ 不需要数据库迁移
- ✅ 新题型使用现有的数据结构
- ✅ 矩阵题等复杂题型的答案存储为JSON格式

---

## 🐛 已知限制

### 级联下拉

- 当前版本提供基础支持
- 复杂的动态加载级联选择器可能需要额外定制
- 建议优先使用简单的级联下拉

### 多项填空（contenteditable）

- 某些复杂的contenteditable元素可能需要特殊处理
- 建议先测试具体问卷的兼容性

---

## 📖 文档更新

### 新增文档

1. **QUESTION_TYPES_GUIDE.md** - 题型支持详细指南
   - 所有10种题型的说明
   - 答案格式规范
   - 常见问题解答

### 更新文档

1. **README.md** - 建议更新"题型支持"部分，从4种改为10种

---

## 🧪 测试建议

### 测试用例

建议针对以下场景进行测试：

1. **基础题型组合**
   ```
   填空 + 单选 + 多选 + 判断
   ```

2. **新题型组合**
   ```
   简答 + 矩阵填空 + 多项简答
   ```

3. **复杂题型**
   ```
   下拉选择 + 多项填空 + 级联下拉
   ```

4. **混合场景**
   ```
   测试问卷全部20题
   ```

### 测试脚本

```python
# tests/test_new_question_types.py
import pytest
from backend.models.question import Question, QuestionType

def test_essay_validation():
    q = Question(
        id="q11",
        type=QuestionType.ESSAY,
        content="简答题",
        order=1
    )
    valid, error = q.validate_answer("这是答案")
    assert valid is True

def test_matrix_fill_validation():
    q = Question(
        id="q2",
        type=QuestionType.MATRIX_FILL,
        content="矩阵填空",
        order=2
    )
    valid, error = q.validate_answer({
        "q2_0": "张三",
        "q2_1": "技术部"
    })
    assert valid is True
```

---

## 🔜 未来计划

### v2.1 计划

- [ ] 排序题支持
- [ ] 矩阵单选/多选题支持
- [ ] 量表题支持
- [ ] 图片上传题支持

### v3.0 计划

- [ ] 更多平台支持（腾讯问卷、金数据）
- [ ] 批量答题功能
- [ ] 答题历史记录查询

---

## 💡 贡献者

感谢以下贡献者：
- @zhusir - 主要开发
- Claude - AI辅助开发

---

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues: https://github.com/yourusername/exampilot/issues
- Email: your.email@example.com

---

**Happy Coding! 🎉**
