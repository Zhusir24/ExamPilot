# ExamPilot 题型支持指南

本文档说明了ExamPilot系统支持的所有题型及其答案格式。

## 更新日志

**版本 2.0** (2025-10-18)
- ✅ 新增简答题支持 (type="2")
- ✅ 新增矩阵填空题支持 (type="9")
- ✅ 新增多项简答题支持 (type="34")
- ✅ 新增下拉选择题支持 (type="7")
- ✅ 新增多项填空题支持 (gapfill="1")
- ✅ 新增级联下拉支持 (多级下拉)

**题型覆盖率**: 现已支持 **10种题型**

---

## 1. 基础题型

### 1.1 填空题 (FILL_BLANK)

**问卷星type值**: `type="1"`

**HTML特征**:
```html
<input type="text" name="q1" />
```

**答案格式**: 字符串
```python
answer = "这是填空题的答案"
```

**答案示例**:
```json
{
  "q1": "测试工号001"
}
```

---

### 1.2 单选题 (SINGLE_CHOICE)

**问卷星type值**: `type="3"`

**HTML特征**:
```html
<div class="ui-radio">
  <input type="radio" value="1" name="q4" />
  <div class="label">选项A</div>
</div>
```

**答案格式**: 整数索引（从0开始）
```python
answer = 0  # 选择第一个选项
```

**答案示例**:
```json
{
  "q4": 0,      // 选择"设计部"
  "q6": 1       // 选择第二个选项
}
```

---

### 1.3 多选题 (MULTIPLE_CHOICE)

**问卷星type值**: `type="4"`

**HTML特征**:
```html
<div class="ui-checkbox">
  <input type="checkbox" value="1" name="q8" />
  <div class="label">选项1</div>
</div>
```

**答案格式**: 整数索引数组（从0开始）
```python
answer = [0, 2]  # 选择第1和第3个选项
```

**答案示例**:
```json
{
  "q8": [0, 1],      // 选择"选项1"和"选项2"
  "q14": [0]         // 只选择第一个选项
}
```

---

### 1.4 判断题 (TRUE_FALSE)

**问卷星type值**: `type="3"` + `ispanduan="1"`

**HTML特征**:
```html
<div class="field" type="3" ispanduan="1">
  <input type="radio" value="1" name="q7" /> 对
  <input type="radio" value="2" name="q7" /> 错
</div>
```

**答案格式**: 整数索引（通常0=对，1=错）
```python
answer = 0  # 选择"对"
```

**答案示例**:
```json
{
  "q7": 0      // 选择"对"
}
```

---

## 2. 文本类题型

### 2.1 简答题 (ESSAY)

**问卷星type值**: `type="2"`

**HTML特征**:
```html
<textarea name="q11" rows="3"></textarea>
```

**答案格式**: 字符串（可以是长文本）
```python
answer = "这是一段详细的简答题回答。可以包含多行文字。"
```

**答案示例**:
```json
{
  "q11": "根据我的理解，答案是...\n这是第二段内容。"
}
```

---

### 2.2 多项简答题 (MULTIPLE_ESSAY)

**问卷星type值**: `type="34"`

**HTML特征**:
```html
<table class="matrix-rating">
  <tr>
    <td>问答1</td>
    <td><textarea name="q12_0"></textarea></td>
  </tr>
  <tr>
    <td>问答2</td>
    <td><textarea name="q12_1"></textarea></td>
  </tr>
</table>
```

**答案格式**: 字典，key为子项名称
```python
answer = {
    "q12_0": "第一个问答的答案",
    "q12_1": "第二个问答的答案"
}
```

**答案示例**:
```json
{
  "q12": {
    "q12_0": "对于问答1，我的回答是...",
    "q12_1": "对于问答2，我认为..."
  }
}
```

---

## 3. 复杂题型

### 3.1 矩阵填空题 (MATRIX_FILL)

**问卷星type值**: `type="9"`

**HTML特征**:
```html
<table class="matrix-rating scaletablewrap">
  <tr>
    <td>姓名：</td>
    <td><textarea name="q2_0"></textarea></td>
  </tr>
  <tr>
    <td>部门：</td>
    <td><textarea name="q2_1"></textarea></td>
  </tr>
</table>
```

**答案格式**: 字典，key为子项名称（如q2_0, q2_1）
```python
answer = {
    "q2_0": "张三",
    "q2_1": "技术部",
    "q2_2": "EMP001"
}
```

**答案示例**:
```json
{
  "q2": {
    "q2_0": "张三",
    "q2_1": "技术部",
    "q2_2": "EMP001"
  },
  "q16": {
    "q16_0": "外观精美，设计现代",
    "q16_1": "功能完善，性能稳定"
  }
}
```

---

### 3.2 多项填空题 (GAP_FILL)

**问卷星type值**: `type="9"` + `gapfill="1"`

**HTML特征**:
```html
<div class="topictext">
  问题1：<input type="text" name="q10_1" />
  问题2：<input type="text" name="q10_2" />
</div>
```

**答案格式**: 字典或列表
```python
# 方式1：字典
answer = {
    "q10_1": "第一空的答案",
    "q10_2": "第二空的答案"
}

# 方式2：列表（按顺序填入）
answer = ["第一空的答案", "第二空的答案"]
```

**答案示例**:
```json
{
  "q10": {
    "q10_1": "北京",
    "q10_2": "上海"
  }
}

// 或者
{
  "q10": ["北京", "上海"]
}
```

---

## 4. 选择类题型

### 4.1 下拉单选题 (DROPDOWN)

**问卷星type值**: `type="7"`

**HTML特征**:
```html
<select name="q17">
  <option value="-2">请选择</option>
  <option value="1">选项35</option>
  <option value="2">选项36</option>
</select>
```

**答案格式**: 整数索引（从0开始，不包括"请选择"）
```python
answer = 0  # 选择第一个有效选项（value="1"）
```

**答案示例**:
```json
{
  "q17": 0      // 选择"选项35"
}
```

**注意**:
- 索引不包括"请选择"等默认选项
- 问卷星使用Select2插件，系统会自动处理

---

### 4.2 级联下拉 (CASCADE_DROPDOWN)

**问卷星type值**: `type="1"` + `verify="多级下拉"`

**HTML特征**:
```html
<input type="text" name="q18" verify="多级下拉"
       onclick="openCityBox(this,5,event,18);" readonly />
```

**答案格式**: 字符串（完整路径或最终选择的值）
```python
answer = "北京市-朝阳区"
# 或者
answer = "朝阳区"
```

**答案示例**:
```json
{
  "q18": "北京市-朝阳区"
}
```

**注意**:
- 级联下拉的实现比较复杂，当前版本提供基础支持
- 某些复杂的级联选择器可能需要额外定制

---

## 5. API使用示例

### 5.1 完整答案格式

针对测试问卷 (https://ks.wjx.com/vm/rDTLYkN.aspx) 的完整答案示例：

```json
{
  "div1": "工号12345",
  "div2": {
    "q2_0": "张三",
    "q2_1": "技术部",
    "q2_2": "EMP001"
  },
  "div3": "13800138000",
  "div4": 0,
  "div5": "张三",
  "div6": 0,
  "div7": 0,
  "div8": [0, 1],
  "div9": "这是单项填空的答案",
  "div10": {
    "q10_1": "答案1",
    "q10_2": "答案2"
  },
  "div11": "这是简答题的详细回答。\n可以包含多段文字。",
  "div12": {
    "q12_0": "第一个问答的答案",
    "q12_1": "第二个问答的答案"
  },
  "div13": 0,
  "div14": [0],
  "div15": "填空题答案",
  "div16": {
    "q16_0": "外观评价",
    "q16_1": "功能评价"
  },
  "div17": 0,
  "div18": "北京市-朝阳区",
  "div19": 0,
  "div20": [0]
}
```

### 5.2 Python API调用示例

```python
import asyncio
from backend.services.platforms.wenjuanxing import WenjuanxingPlatform

async def main():
    platform = WenjuanxingPlatform()

    # 1. 解析问卷
    url = "https://ks.wjx.com/vm/rDTLYkN.aspx"
    questions, metadata = await platform.extract_questions(url)

    print(f"问卷标题: {metadata['title']}")
    print(f"题目总数: {len(questions)}")

    # 2. 准备答案
    answers = {
        "div1": "工号12345",
        "div2": {
            "q2_0": "张三",
            "q2_1": "技术部",
            "q2_2": "EMP001"
        },
        "div3": "13800138000",
        "div4": 0,
        "div5": "张三",
        "div6": 0,
        "div7": 0,
        "div8": [0, 1],
        "div9": "单项填空答案",
        "div10": ["答案1", "答案2"],
        "div11": "这是简答题的回答",
        "div12": {
            "q12_0": "问答1的回答",
            "q12_1": "问答2的回答"
        },
        "div13": 0,
        "div14": [0],
        "div15": "填空题答案",
        "div16": {
            "q16_0": "外观很好",
            "q16_1": "功能完善"
        },
        "div17": 0,
        "div18": "北京市-朝阳区",
        "div19": 0,
        "div20": [0]
    }

    # 3. 提交答案
    result = await platform.submit_answers(url, answers)
    print(f"提交结果: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. 题型识别规则

系统按以下优先级检测题型：

1. **多项填空** - 检查 `gapfill="1"` 属性
2. **多项简答** - 检查 `type="34"` + 表格结构
3. **矩阵填空** - 检查 `type="9"` + 表格结构
4. **简答题** - 检查 `type="2"` + textarea（非表格）
5. **下拉选择** - 检查 `type="7"` + select元素
6. **级联下拉** - 检查 `verify="多级下拉"` 属性
7. **判断题** - 检查 `ispanduan="1"` 或 两个选项包含"对/错"关键词
8. **单选题** - 检查 `.ui-radio` 元素
9. **多选题** - 检查 `.ui-checkbox` 元素
10. **填空题** - 默认类型

---

## 7. 常见问题

### Q1: 矩阵填空题的子项名称如何确定？

A: 查看HTML中的name属性，通常格式为 `q{题号}_{子项索引}`，例如：
- 题目2的第一个子项：`q2_0`
- 题目2的第二个子项：`q2_1`

### Q2: 下拉选择题的索引如何计算？

A: 索引从0开始，不包括"请选择"等默认选项（value="-2"）。第一个有效选项索引为0。

### Q3: 多项填空题可以只填部分空吗？

A: 可以，但如果题目标记为必填，建议填写所有空格。

### Q4: 级联下拉如何处理？为什么看不到选项内容？

A: **级联下拉的选项是动态加载的**，无法在静态HTML中解析。

**原因**：
- 级联下拉的选项通过JavaScript动态加载（如省市区联动）
- 选项内容取决于用户的前序选择
- 在不与页面交互的情况下，无法获取所有可能的选项

**使用方法**：
- 答案格式：字符串（填写最终选择的完整路径）
- 示例：`"北京市-朝阳区"` 或 `"广东省-深圳市-南山区"`
- 系统会尝试将答案填入输入框，但复杂的级联选择器可能需要手动处理

**显示说明**：
- 解析时，级联下拉题会显示 `(级联下拉 - 选项动态加载)` 作为提示
- 这是正常现象，不影响答题功能

### Q5: 如何判断我的问卷用了哪些题型？

A: 调用 `extract_questions()` 方法，返回的 Question 对象中包含 `type` 字段。

---

## 8. 答案验证

系统会自动验证答案格式：

```python
from backend.models.question import Question, QuestionType

question = Question(
    id="q6",
    type=QuestionType.SINGLE_CHOICE,
    content="选择题",
    options=["选项1", "选项2"],
    order=1
)

# 验证答案
valid, error = question.validate_answer(0)
if valid:
    print("答案有效")
else:
    print(f"答案无效: {error}")
```

---

## 9. 技术支持

如遇到不支持的题型或问题，请提供：
1. 问卷URL
2. 具体题目的HTML片段
3. 题目截图

项目地址: https://github.com/yourusername/exampilot
