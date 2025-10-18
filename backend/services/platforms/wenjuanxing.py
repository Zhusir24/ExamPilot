"""问卷星平台适配器"""
import re
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
from backend.models.question import Question, QuestionType, TemplateType
from backend.core.logger import log
from backend.services.platforms.base import BasePlatform, PlatformType


class WenjuanxingPlatform(BasePlatform):
    """问卷星平台适配器"""

    @property
    def platform_name(self) -> PlatformType:
        return PlatformType.WENJUANXING

    def _clean_url(self, url: str) -> str:
        """清理URL，移除锚点等无关内容"""
        # 移除 # 及其后面的内容
        clean_url = url.split('#')[0].strip()
        # 移除尾部空格
        return clean_url

    async def parse_url(self, url: str) -> Dict[str, Any]:
        """解析问卷URL"""
        url = self._clean_url(url)
        if not await self.validate_url(url):
            raise ValueError("无效的URL")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # 获取问卷标题
                title = await self._extract_title(page)
                
                # 获取问卷描述
                description = await self._extract_description(page)
                
                # 检测模板类型
                page_content = await page.content()
                template_type = self.detect_template_type(page_content)
                
                return {
                    "url": url,
                    "platform": self.platform_name.value,
                    "template_type": template_type.value,
                    "title": title,
                    "description": description,
                }
                
            finally:
                await browser.close()
    
    async def extract_questions(self, url: str) -> tuple[List[Question], Dict[str, Any]]:
        """提取题目列表"""
        url = self._clean_url(url)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # 等待题目加载
                await page.wait_for_selector(".field", timeout=10000)
                
                # 获取问卷元数据
                metadata = {
                    "title": await self._extract_title(page),
                    "description": await self._extract_description(page),
                }
                
                # 提取所有题目
                questions = await self._extract_all_questions(page)
                
                log.info(f"成功提取 {len(questions)} 道题目")
                
                return questions, metadata
                
            finally:
                await browser.close()
    
    async def submit_answers(self, url: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """提交答案"""
        url = self._clean_url(url)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # 等待页面加载
                await page.wait_for_selector(".field", timeout=10000)
                
                # 填写答案
                for question_id, answer_content in answers.items():
                    # 预处理答案内容
                    processed_answer = self._preprocess_answer(answer_content)
                    if processed_answer is not None:
                        await self._fill_answer(page, question_id, processed_answer)
                    else:
                        log.warning(f"跳过无效答案: {question_id} = {answer_content}")
                
                # 提交表单 - 问卷星使用div作为提交按钮
                submit_button = None
                possible_selectors = [
                    "#ctlNext",  # 问卷星的提交按钮ID
                    ".submitbtn",  # 问卷星的提交按钮class
                    "div.submitbtn",  # div形式的提交按钮
                    "#divSubmit .submitbtn",  # 提交区域内的按钮
                    "button[type='submit']",  # 标准submit按钮
                    "input[type='submit']",  # input类型的提交按钮
                    "button:has-text('提交')",  # 包含"提交"文字的按钮
                    "div:has-text('提交')",  # 包含"提交"文字的div
                ]
                
                for selector in possible_selectors:
                    locator = page.locator(selector)
                    if await locator.count() > 0:
                        submit_button = locator.first
                        log.info(f"找到提交按钮: {selector}")
                        break
                
                if submit_button:
                    # 滚动到提交按钮位置
                    try:
                        await submit_button.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)  # 等待滚动完成
                    except:
                        pass
                    
                    # 点击提交按钮
                    await submit_button.click(timeout=5000)
                    log.info("已点击提交按钮，等待响应...")
                    
                    # 等待提交完成（增加等待时间到10秒）
                    try:
                        await page.wait_for_url("**/complete**", timeout=10000)
                        result = {"success": True, "message": "提交成功"}
                        log.info("提交成功：URL已跳转到完成页")
                    except PlaywrightTimeout:
                        # 等待一下，让页面有时间处理
                        await page.wait_for_timeout(2000)
                        
                        # 检查是否有错误提示
                        error_msg = await self._extract_error_message(page)
                        if error_msg:
                            result = {"success": False, "message": f"提交失败: {error_msg}"}
                            log.warning(f"提交失败: {error_msg}")
                        else:
                            # 即使URL没有跳转，也检查是否有成功提示
                            success_msg = await self._check_success_message(page)
                            if success_msg:
                                result = {"success": True, "message": success_msg}
                                log.info(f"提交成功: {success_msg}")
                            else:
                                # 检查页面内容，可能已经成功但没有明显提示
                                page_content = await page.content()
                                if any(kw in page_content for kw in ["感谢", "完成", "成功"]):
                                    result = {"success": True, "message": "提交完成（推测）"}
                                    log.info("提交可能成功（页面包含成功关键词）")
                                else:
                                    result = {"success": False, "message": "提交超时或未找到成功确认"}
                                    log.warning("提交超时或未找到成功确认")
                else:
                    # 记录页面HTML用于调试
                    log.warning("未找到提交按钮，页面可能结构不同")
                    try:
                        # 尝试查找所有按钮
                        all_buttons = await page.locator("button, input[type='submit'], input[type='button']").all()
                        log.info(f"页面共有 {len(all_buttons)} 个按钮")
                    except:
                        pass
                    result = {"success": False, "message": "未找到提交按钮"}
                
                return result
                
            except Exception as e:
                log.error(f"提交答案失败: {e}")
                return {"success": False, "message": str(e)}
            finally:
                await browser.close()
    
    def detect_template_type(self, page_content: str) -> TemplateType:
        """检测模板类型"""
        # 简单检测：查找关键词
        exam_keywords = ["考试", "测试", "考核", "exam", "test"]
        survey_keywords = ["调查", "问卷", "survey", "questionnaire"]
        
        page_lower = page_content.lower()
        
        exam_score = sum(1 for kw in exam_keywords if kw in page_lower)
        survey_score = sum(1 for kw in survey_keywords if kw in page_lower)
        
        if exam_score > survey_score:
            return TemplateType.EXAM
        else:
            return TemplateType.SURVEY
    
    async def _extract_title(self, page: Page) -> str:
        """提取问卷标题"""
        try:
            title_elem = page.locator(".surveyhead h1, .survey-title, h1.title")
            if await title_elem.count() > 0:
                return await title_elem.first.inner_text()
        except:
            pass
        return "未命名问卷"
    
    async def _extract_description(self, page: Page) -> str:
        """提取问卷描述"""
        try:
            desc_elem = page.locator(".surveyhead .description, .survey-description")
            if await desc_elem.count() > 0:
                return await desc_elem.first.inner_text()
        except:
            pass
        return ""
    
    async def _extract_all_questions(self, page: Page) -> List[Question]:
        """提取所有题目"""
        questions = []
        
        # 查找所有题目容器
        field_elements = await page.locator(".field").all()
        
        for index, field_elem in enumerate(field_elements, start=1):
            try:
                question = await self._parse_question_element(field_elem, index)
                if question:
                    questions.append(question)
                    log.debug(f"成功解析第 {index} 题: {question.type.value} - {question.content[:30]}")
            except Exception as e:
                log.error(f"解析第 {index} 题失败: {e}")
                # 即使解析失败，也尝试创建一个基本的题目对象
                try:
                    question_id = await field_elem.get_attribute("id") or f"div{index}"
                    fallback_question = Question(
                        id=self.normalize_question_id(question_id),
                        type=QuestionType.FILL_BLANK,  # 默认为填空题
                        content=f"题目{index}（解析失败，请手动检查）",
                        options=None,
                        order=index,
                        required=True,
                        platform_data={"parse_error": str(e)},
                    )
                    questions.append(fallback_question)
                    log.warning(f"第 {index} 题使用降级方案")
                except:
                    log.error(f"第 {index} 题完全解析失败，跳过")
                    continue
        
        return questions
    
    async def _parse_question_element(self, field_elem, order: int) -> Question:
        """解析单个题目元素"""
        # 获取题目ID
        question_id = await field_elem.get_attribute("id") or f"q{order}"

        # 获取题目内容 - 优先使用 .field-label 下的 .topichtml
        try:
            # 方法1: 查找 .field-label > .topichtml（最精确）
            topic_html = field_elem.locator(".field-label > .topichtml").first
            if await topic_html.count() > 0:
                content = await topic_html.inner_text()
            else:
                # 方法2: 查找直接子元素 .field-label
                field_label = field_elem.locator("> .field-label").first
                if await field_label.count() > 0:
                    content = await field_label.inner_text()
                else:
                    # 方法3: 使用默认内容
                    content = f"题目{order}"
        except Exception as e:
            log.debug(f"提取题目内容失败: {e}, 使用默认值")
            content = f"题目{order}"

        # 清理题目内容（移除题号、星号等）
        content = re.sub(r'^\*+\s*', '', content).strip()  # 移除开头的星号
        content = re.sub(r'^\d+[\.\、\s]+', '', content).strip()
        content = re.sub(r'^\[\s*[必选单多判填]\s*\]\s*', '', content).strip()
        
        # 判断题目类型
        question_type, options = await self._detect_question_type(field_elem, content)
        
        # 判断是否必答
        required = "required" in (await field_elem.get_attribute("class") or "")
        
        # 获取平台特定数据
        platform_data = {
            "element_id": question_id,
            "field_type": await field_elem.get_attribute("data-type") or "",
        }
        
        return Question(
            id=self.normalize_question_id(question_id),
            type=question_type,
            content=content,
            options=options,
            order=order,
            required=required,
            platform_data=platform_data,
        )
    
    async def _detect_question_type(self, field_elem, content: str) -> tuple[QuestionType, list]:
        """检测题目类型和选项"""
        try:
            # 获取题目的 type 属性
            field_type = await field_elem.get_attribute("type") or ""

            log.debug(f"题目类型检测: type={field_type}, content={content[:30]}")

            # 检查特殊标记
            is_gapfill = await field_elem.get_attribute("gapfill") == "1"

            # 检查是否有选项容器
            ui_radio_elements = await field_elem.locator(".ui-radio").all()
            ui_checkbox_elements = await field_elem.locator(".ui-checkbox").all()

            # 检查是否有 textarea（简答题）
            textarea_elements = await field_elem.locator("textarea").all()

            # 检查是否有 select（下拉题）
            select_elements = await field_elem.locator("select").all()

            # 检查是否有表格结构（矩阵题）
            table_elements = await field_elem.locator("table.matrix-rating").all()

            # 1. 多项填空题 (gapfill="1")
            if is_gapfill:
                log.debug("识别为多项填空题")
                return QuestionType.GAP_FILL, None

            # 2. 多项简答题 (type="34")
            if field_type == "34" and table_elements:
                log.debug("识别为多项简答题")
                return QuestionType.MULTIPLE_ESSAY, None

            # 3. 矩阵填空题 (type="9" with table)
            if field_type == "9" and table_elements:
                log.debug("识别为矩阵填空题")
                return QuestionType.MATRIX_FILL, None
        except Exception as e:
            log.error(f"题型检测出错: {e}")
            raise

        # 4. 简答题 (type="2")
        if field_type == "2" and textarea_elements and not table_elements:
            return QuestionType.ESSAY, None

        # 5. 下拉选择题 (type="7")
        if field_type == "7" and select_elements:
            # 提取下拉选项
            options = []
            for select_elem in select_elements:
                option_elements = await select_elem.locator("option").all()
                for option_elem in option_elements:
                    value = await option_elem.get_attribute("value")
                    # 跳过"请选择"等默认选项
                    if value and value != "-2":
                        option_text = await option_elem.inner_text()
                        if option_text and option_text.strip():
                            options.append(option_text.strip())
            return QuestionType.DROPDOWN, options if options else None

        # 6. 级联下拉 (verify="多级下拉")
        input_elements = await field_elem.locator("input[verify='多级下拉']").all()
        if input_elements:
            # 级联下拉的选项是动态加载的，无法静态解析
            # 返回一个提示性的选项列表
            placeholder_options = ["(级联下拉 - 选项动态加载)"]
            log.debug("识别为级联下拉题，选项需动态加载")
            return QuestionType.CASCADE_DROPDOWN, placeholder_options

        # 7. 单选题/判断题/多选题（原有逻辑）
        if not ui_radio_elements and not ui_checkbox_elements:
            # 没有选项，检查是否是普通填空题
            text_input = await field_elem.locator("input[type='text'], textarea").all()
            if text_input:
                return QuestionType.FILL_BLANK, None
            # 其他情况也当作填空题
            return QuestionType.FILL_BLANK, None
        
        # 提取选项文本
        options = []
        
        # 处理单选题选项
        for ui_radio in ui_radio_elements:
            try:
                # 问卷星使用 div.label 存储选项文本
                label_elem = ui_radio.locator("div.label, .label")
                if await label_elem.count() > 0:
                    option_text = await label_elem.first.inner_text()
                    if option_text and option_text.strip():
                        # 清理选项文本（移除前缀字母/数字）
                        option_text = re.sub(r'^[A-Z][\.\、\s]+', '', option_text.strip())
                        option_text = re.sub(r'^\d+[\.\、\s]+', '', option_text.strip())
                        options.append(option_text.strip())
            except Exception as e:
                log.warning(f"提取单选项失败: {e}")
                continue
        
        # 处理多选题选项
        for ui_checkbox in ui_checkbox_elements:
            try:
                label_elem = ui_checkbox.locator("div.label, .label")
                if await label_elem.count() > 0:
                    option_text = await label_elem.first.inner_text()
                    if option_text and option_text.strip():
                        option_text = re.sub(r'^[A-Z][\.\、\s]+', '', option_text.strip())
                        option_text = re.sub(r'^\d+[\.\、\s]+', '', option_text.strip())
                        options.append(option_text.strip())
            except Exception as e:
                log.warning(f"提取多选项失败: {e}")
                continue
        
        log.debug(f"提取到 {len(options)} 个选项: {options}")
        
        # 判断题型
        if ui_radio_elements:
            # 单选题或判断题
            # 检查是否有 ispanduan 属性
            is_panduan = await field_elem.get_attribute("ispanduan") == "1"
            if is_panduan or (len(options) == 2 and any(
                kw in "".join(options).lower()
                for kw in ["正确", "错误", "对", "错", "是", "否", "true", "false", "yes", "no"]
            )):
                return QuestionType.TRUE_FALSE, options
            else:
                return QuestionType.SINGLE_CHOICE, options
        elif ui_checkbox_elements:
            return QuestionType.MULTIPLE_CHOICE, options

        return QuestionType.FILL_BLANK, None
    
    async def _fill_answer(self, page: Page, question_id: str, answer_content: Any):
        """填写单个题目的答案"""
        try:
            # 问卷星使用的是字段ID，如 div1, div2，但input的name是q1, q2
            # 需要转换ID格式
            input_name = question_id.replace("div", "q")

            # 获取field容器
            field = page.locator(f"#{question_id}").first
            if not await field.count():
                log.warning(f"未找到题目容器: {question_id}")
                return

            # 获取题目类型
            field_type = await field.get_attribute("type") or ""
            is_gapfill = await field.get_attribute("gapfill") == "1"

            # 根据题型调用不同的填写方法
            # 1. 多项填空题
            if is_gapfill:
                await self._fill_gap_fill(page, input_name, answer_content)

            # 2. 多项简答题 (type="34")
            elif field_type == "34":
                await self._fill_multiple_essay(page, input_name, answer_content)

            # 3. 矩阵填空题 (type="9")
            elif field_type == "9":
                await self._fill_matrix(page, input_name, answer_content)

            # 4. 简答题 (type="2")
            elif field_type == "2":
                await self._fill_essay(page, input_name, answer_content)

            # 5. 下拉选择 (type="7")
            elif field_type == "7":
                await self._fill_dropdown(page, input_name, answer_content)

            # 6. 级联下拉
            elif await field.locator("input[verify='多级下拉']").count() > 0:
                await self._fill_cascade(page, input_name, answer_content)

            # 7. 原有题型
            elif await field.locator("input[type='radio']").count() > 0:
                # 单选题/判断题
                await self._fill_radio(page, input_name, answer_content)
            elif await field.locator("input[type='checkbox']").count() > 0:
                # 多选题
                await self._fill_checkbox(page, input_name, answer_content)
            elif await field.locator("input[type='text'], textarea").count() > 0:
                # 填空题
                await self._fill_text(page, input_name, answer_content)
            else:
                log.warning(f"未知题型: {question_id}")

        except Exception as e:
            log.error(f"填写题目 {question_id} 失败: {e}")
    
    def _preprocess_answer(self, answer_content: Any) -> Any:
        """预处理答案内容，确保格式正确"""
        try:
            # 如果是None或空字符串，返回None
            if answer_content is None or (isinstance(answer_content, str) and not answer_content.strip()):
                return None
            
            # 如果是整数，直接返回
            if isinstance(answer_content, int):
                return answer_content
            
            # 如果是列表（多选题），递归处理每个元素
            if isinstance(answer_content, list):
                processed_list = []
                for item in answer_content:
                    processed_item = self._preprocess_answer(item)
                    if processed_item is not None:
                        processed_list.append(processed_item)
                return processed_list if processed_list else None
            
            # 处理字符串
            if isinstance(answer_content, str):
                answer_str = answer_content.strip()
                
                # 先尝试解析JSON数组格式 (如 "[0, 1, 2]" 或 "[0,1,2]")
                if answer_str.startswith('[') and answer_str.endswith(']'):
                    try:
                        import json
                        parsed = json.loads(answer_str)
                        if isinstance(parsed, list):
                            # 递归处理解析出的列表
                            return self._preprocess_answer(parsed)
                    except:
                        # JSON解析失败，继续尝试其他方法
                        pass
                
                # 检查是否是逗号分隔的多选答案（如 "0,1,2" 或 "0, 1, 2"）
                if ',' in answer_str and not answer_str.startswith('['):
                    # 分割并处理每个部分
                    parts = [p.strip() for p in answer_str.split(',') if p.strip()]
                    if all(p.isdigit() for p in parts):
                        # 所有部分都是数字，转换为整数列表
                        return [int(p) for p in parts]
                    else:
                        # 有非数字部分，保持为列表
                        return parts
            
            # 如果是字符串，尝试解析
            if isinstance(answer_content, str):
                answer_str = answer_content.strip()
                
                # 如果是JSON字符串，尝试解析
                if answer_str.startswith('"') and answer_str.endswith('"'):
                    try:
                        import json
                        answer_str = json.loads(answer_str)
                    except:
                        pass
                
                # 如果包含管道符，说明是"索引|内容"格式，直接返回（解析逻辑在_fill_radio中）
                if '|' in answer_str:
                    return answer_str
                
                # 如果是纯数字，返回
                if answer_str.isdigit():
                    return answer_str
                
                # 如果包含中文圈号数字，返回
                if any(c in answer_str for c in '①②③④⑤⑥⑦⑧⑨⑩'):
                    return answer_str
                
                # 如果以字母开头（A, B, C...），返回
                if len(answer_str) >= 1 and answer_str[0].upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    return answer_str
                
                # 其他文本内容（可能是填空题答案）
                return answer_str
            
            # 其他类型，转为字符串
            return str(answer_content)
            
        except Exception as e:
            log.warning(f"预处理答案失败: {answer_content}, 错误: {e}")
            return None
    
    async def _find_option_by_text(self, page: Page, input_name: str, answer_text: str) -> int:
        """通过选项文本查找选项索引"""
        try:
            # 获取该题目的所有选项
            radios = await page.locator(f"input[type='radio'][name='{input_name}']").all()
            
            # 清理答案文本，移除前缀字母和标点
            cleaned_answer = answer_text.strip()
            cleaned_answer = re.sub(r'^[A-Z][\.\、\s]+', '', cleaned_answer)
            cleaned_answer = re.sub(r'^\d+[\.\、\s]+', '', cleaned_answer)
            
            log.debug(f"清理后的答案文本: {cleaned_answer[:30]}")
            
            for i, radio in enumerate(radios):
                try:
                    # 获取选项的文本
                    parent = radio.locator("xpath=ancestor::div[contains(@class, 'ui-radio')]")
                    if await parent.count() > 0:
                        label = await parent.first.locator(".label, div.label").inner_text()
                        
                        # 清理选项文本
                        cleaned_label = label.strip()
                        cleaned_label = re.sub(r'^[A-Z][\.\、\s]+', '', cleaned_label)
                        cleaned_label = re.sub(r'^\d+[\.\、\s]+', '', cleaned_label)
                        
                        # 模糊匹配：检查答案是否在选项中，或选项是否在答案中
                        if (cleaned_answer in cleaned_label or 
                            cleaned_label in cleaned_answer or
                            cleaned_answer == cleaned_label):
                            log.info(f"✓ 通过文本匹配找到选项: 索引{i}, 文本: {cleaned_label[:40]}")
                            return i
                except Exception as e:
                    log.debug(f"检查选项{i}失败: {e}")
                    continue
            
            log.warning(f"未找到匹配的选项文本: {cleaned_answer[:50]}")
            return None
            
        except Exception as e:
            log.error(f"文本匹配失败: {e}")
            return None
    
    def _convert_chinese_number(self, text: str) -> int:
        """将中文圈号数字转换为阿拉伯数字"""
        chinese_numbers = {
            '①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5, 
            '⑥': 6, '⑦': 7, '⑧': 8, '⑨': 9, '⑩': 10,
            '⑪': 11, '⑫': 12, '⑬': 13, '⑭': 14, '⑮': 15,
            '⑯': 16, '⑰': 17, '⑱': 18, '⑲': 19, '⑳': 20,
        }
        
        # 如果整个字符串是单个中文数字
        if text in chinese_numbers:
            return chinese_numbers[text]
        
        # 如果字符串包含中文数字，尝试提取第一个
        for char in text:
            if char in chinese_numbers:
                return chinese_numbers[char]
        
        raise ValueError(f"无法转换中文数字: {text}")
    
    async def _fill_radio(self, page: Page, input_name: str, answer: Any):
        """填写单选题"""
        try:
            # 解析答案：提取索引（问卷星value从1开始，AI索引从0开始）
            answer_index = None
            answer_str = str(answer).strip() if answer is not None else ""
            
            if isinstance(answer, int):
                answer_index = answer
            elif isinstance(answer, str) and answer_str:
                # 尝试多种格式解析
                try:
                    if '|' in answer_str:
                        # 格式："索引|内容"，提取索引部分
                        parts = answer_str.split('|', 1)
                        index_part = parts[0].strip()
                        
                        # 尝试解析索引部分
                        if index_part.isdigit():
                            answer_index = int(index_part)
                        elif any(c in index_part for c in '①②③④⑤⑥⑦⑧⑨⑩'):
                            answer_index = self._convert_chinese_number(index_part) - 1
                        else:
                            if len(index_part) >= 1 and index_part[0].upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                                answer_index = ord(index_part[0].upper()) - ord('A')
                    
                    elif answer_str.isdigit():
                        # 纯数字字符串
                        answer_index = int(answer_str)
                    
                    elif any(c in answer_str for c in '①②③④⑤⑥⑦⑧⑨⑩'):
                        # 包含中文圈号数字（如③④①②ightarrow尝试提取第一个）
                        try:
                            answer_index = self._convert_chinese_number(answer_str) - 1
                        except ValueError:
                            # 如果是多个中文数字，尝试只取第一个字符
                            if len(answer_str) > 0 and answer_str[0] in '①②③④⑤⑥⑦⑧⑨⑩':
                                answer_index = self._convert_chinese_number(answer_str[0]) - 1
                    
                    elif len(answer_str) >= 1 and answer_str[0].upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                        # 以字母开头（A, B, C...）
                        answer_index = ord(answer_str[0].upper()) - ord('A')
                    
                except ValueError as ve:
                    log.debug(f"数字解析失败，尝试文本匹配: {answer_str}")
            
            # 如果无法解析为索引，尝试通过文本匹配选项
            if answer_index is None and answer_str:
                log.debug(f"尝试通过文本匹配选项: {answer_str[:50]}")
                answer_index = await self._find_option_by_text(page, input_name, answer_str)
            
            # 如果找到了索引，点击对应的选项
            if answer_index is not None:
                # 转换为问卷星的value（索引0 -> value 1）
                value = str(answer_index + 1)
                radio_input = page.locator(f"input[type='radio'][name='{input_name}'][value='{value}']")
                
                if await radio_input.count() > 0:
                    # 问卷星的radio input是隐藏的，需要点击外层的可见元素
                    # 找到外层的 ui-radio 容器或 label
                    parent = radio_input.locator("xpath=ancestor::div[contains(@class, 'ui-radio')]").first
                    
                    if await parent.count() > 0:
                        # 点击外层容器（可见的）
                        try:
                            await parent.click(timeout=3000)
                            
                            # 获取选项文本用于日志
                            option_text = ""
                            try:
                                label = parent.locator("div.label, .label").first
                                if await label.count() > 0:
                                    option_text = await label.inner_text()
                            except:
                                pass
                            
                            log.info(f"✓ 已选择单选项: {input_name} -> 选项{value} {option_text[:50]}")
                        except Exception as click_err:
                            # 如果点击容器失败，尝试点击label
                            try:
                                label = parent.locator("div.label, .label").first
                                if await label.count() > 0:
                                    await label.click(timeout=3000)
                                    log.info(f"✓ 已选择单选项(通过label): {input_name} -> 选项{value}")
                                else:
                                    raise click_err
                            except:
                                log.error(f"点击选项失败: {input_name} value={value}, 错误: {click_err}")
                    else:
                        # 如果找不到父容器，尝试强制点击input（最后的备选方案）
                        await radio_input.first.click(force=True, timeout=3000)
                        log.info(f"✓ 已选择单选项(强制): {input_name} -> 选项{value}")
                else:
                    log.warning(f"❌ 未找到单选项: {input_name} value={value}")
            else:
                log.warning(f"无法解析答案: {answer_str[:50]}")
        except Exception as e:
            log.error(f"填写单选题失败: {e}")
    
    async def _fill_checkbox(self, page: Page, input_name: str, answers: Any):
        """填写多选题"""
        try:
            if not isinstance(answers, list):
                answers = [answers]
            
            for answer in answers:
                answer_index = None
                
                if isinstance(answer, int):
                    answer_index = answer
                elif isinstance(answer, str):
                    answer_str = answer.strip()
                    
                    # 尝试多种格式解析
                    try:
                        if '|' in answer_str:
                            # 格式："索引|内容"，提取索引部分
                            parts = answer_str.split('|', 1)
                            index_part = parts[0].strip()
                            
                            # 尝试解析索引部分
                            if index_part.isdigit():
                                answer_index = int(index_part)
                            elif any(c in index_part for c in '①②③④⑤⑥⑦⑧⑨⑩'):
                                # 包含中文圈号数字
                                answer_index = self._convert_chinese_number(index_part) - 1
                            else:
                                # 尝试提取前导字母（A, B, C, D...）
                                if len(index_part) >= 1 and index_part[0].upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                                    answer_index = ord(index_part[0].upper()) - ord('A')
                        
                        elif answer_str.isdigit():
                            # 纯数字字符串
                            answer_index = int(answer_str)
                        
                        elif any(c in answer_str for c in '①②③④⑤⑥⑦⑧⑨⑩'):
                            # 包含中文圈号数字
                            answer_index = self._convert_chinese_number(answer_str) - 1
                        
                        elif len(answer_str) >= 1 and answer_str[0].upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                            # 以字母开头（A, B, C, D...）
                            answer_index = ord(answer_str[0].upper()) - ord('A')
                        
                    except ValueError as ve:
                        log.warning(f"解析答案索引失败: {answer_str}, 错误: {ve}")
                
                if answer_index is not None:
                    # 问卷星多选的value也是从1开始
                    value = str(answer_index + 1)
                    checkbox_input = page.locator(f"input[type='checkbox'][name='{input_name}'][value='{value}']")
                    
                    if await checkbox_input.count() > 0:
                        # 问卷星的checkbox input也是隐藏的，需要点击外层元素
                        parent = checkbox_input.locator("xpath=ancestor::div[contains(@class, 'ui-checkbox')]").first
                        
                        if await parent.count() > 0:
                            try:
                                await parent.click(timeout=3000)
                                
                                # 获取选项文本
                                option_text = ""
                                try:
                                    label = parent.locator("div.label, .label").first
                                    if await label.count() > 0:
                                        option_text = await label.inner_text()
                                except:
                                    pass
                                
                                log.info(f"✓ 已选择多选项: {input_name} -> 选项{value} {option_text[:50]}")
                            except Exception as click_err:
                                log.error(f"点击多选项失败: {input_name} value={value}, 错误: {click_err}")
                        else:
                            # 备选方案：强制点击checkbox
                            await checkbox_input.first.check(force=True, timeout=3000)
                            log.info(f"✓ 已选择多选项(强制): {input_name} -> 选项{value}")
                    else:
                        log.warning(f"❌ 未找到多选项: {input_name} value={value}")
                else:
                    log.warning(f"无法解析答案 (类型: {type(answer).__name__}): {repr(answer)[:100]}")
        except Exception as e:
            log.error(f"填写多选题失败: {e}")
    
    async def _fill_text(self, page: Page, input_name: str, answer: str):
        """填写填空题"""
        try:
            text_input = page.locator(f"input[name='{input_name}'][type='text'], textarea[name='{input_name}']").first
            if await text_input.count() > 0:
                await text_input.fill(str(answer), timeout=5000)
                log.info(f"✓ 已填写文本: {input_name} = \"{answer[:80]}{'...' if len(str(answer)) > 80 else ''}\"")
            else:
                log.warning(f"❌ 未找到文本输入框: {input_name}")
        except Exception as e:
            log.error(f"填写填空题失败: {e}")
    
    async def _extract_error_message(self, page: Page) -> str:
        """提取错误提示信息"""
        try:
            error_elem = page.locator(".error-message, .alert-danger, .tip-error, .error-tip")
            if await error_elem.count() > 0:
                return await error_elem.first.inner_text()
        except:
            pass
        return ""
    
    async def _check_success_message(self, page: Page) -> str:
        """检查成功提示信息"""
        try:
            success_elem = page.locator(".success-message, .alert-success, .tip-success, .success-tip")
            if await success_elem.count() > 0:
                return await success_elem.first.inner_text()

            # 检查页面标题是否包含"成功"、"完成"等字样
            page_text = await page.content()
            if any(kw in page_text for kw in ["提交成功", "已完成", "感谢您的参与"]):
                return "提交成功"
        except:
            pass
        return ""

    async def _fill_essay(self, page: Page, input_name: str, answer: str):
        """填写简答题"""
        try:
            textarea = page.locator(f"textarea[name='{input_name}']").first
            if await textarea.count() > 0:
                await textarea.fill(str(answer), timeout=5000)
                log.info(f"✓ 已填写简答题: {input_name} = \"{answer[:80]}{'...' if len(str(answer)) > 80 else ''}\"")
            else:
                log.warning(f"❌ 未找到简答题输入框: {input_name}")
        except Exception as e:
            log.error(f"填写简答题失败: {e}")

    async def _fill_matrix(self, page: Page, input_name: str, answer: Any):
        """填写矩阵填空题"""
        try:
            # 答案应该是字典格式: {"q2_0": "张三", "q2_1": "技术部"}
            if not isinstance(answer, dict):
                log.warning(f"矩阵填空题答案格式错误，应为字典: {type(answer).__name__}")
                return

            filled_count = 0
            for sub_name, sub_answer in answer.items():
                # sub_name 可能是 "q2_0", "q2_1" 等
                textarea = page.locator(f"textarea[name='{sub_name}'], input[name='{sub_name}']").first
                if await textarea.count() > 0:
                    await textarea.fill(str(sub_answer), timeout=5000)
                    filled_count += 1
                    log.info(f"✓ 已填写矩阵子项: {sub_name} = \"{str(sub_answer)[:50]}\"")
                else:
                    log.warning(f"❌ 未找到矩阵子项输入框: {sub_name}")

            log.info(f"✓ 矩阵填空题 {input_name} 共填写 {filled_count} 个子项")
        except Exception as e:
            log.error(f"填写矩阵填空题失败: {e}")

    async def _fill_multiple_essay(self, page: Page, input_name: str, answer: Any):
        """填写多项简答题"""
        try:
            # 复用矩阵填空的逻辑，因为结构类似
            await self._fill_matrix(page, input_name, answer)
        except Exception as e:
            log.error(f"填写多项简答题失败: {e}")

    async def _fill_dropdown(self, page: Page, input_name: str, answer: Any):
        """填写下拉选择题"""
        try:
            # 解析答案索引
            answer_index = None
            if isinstance(answer, int):
                answer_index = answer
            elif isinstance(answer, str) and answer.strip().isdigit():
                answer_index = int(answer.strip())

            if answer_index is None:
                log.warning(f"下拉选择题答案格式错误: {answer}")
                return

            # 问卷星的下拉框value从1开始（0通常是"请选择"）
            value = str(answer_index + 1)

            # 使用 select2 插件的选择方法
            select = page.locator(f"select[name='{input_name}']").first
            if await select.count() > 0:
                # 检查是否使用了 select2 插件
                select2_container = page.locator(f"select[name='{input_name}'] + .select2").first
                if await select2_container.count() > 0:
                    # 使用 select2 的方式选择
                    # 点击 select2 容器打开下拉框
                    await select2_container.click(timeout=3000)
                    await page.wait_for_timeout(300)
                    # 选择对应的选项
                    option = page.locator(f".select2-results__option[data-select2-id]").nth(answer_index)
                    if await option.count() > 0:
                        await option.click(timeout=3000)
                        log.info(f"✓ 已选择下拉选项(select2): {input_name} -> 选项{value}")
                    else:
                        # 备选方案：直接设置select的value
                        await select.select_option(value, timeout=3000)
                        log.info(f"✓ 已选择下拉选项(fallback): {input_name} -> 选项{value}")
                else:
                    # 原生 select
                    await select.select_option(value, timeout=3000)
                    log.info(f"✓ 已选择下拉选项: {input_name} -> 选项{value}")
            else:
                log.warning(f"❌ 未找到下拉选择框: {input_name}")
        except Exception as e:
            log.error(f"填写下拉选择题失败: {e}")

    async def _fill_gap_fill(self, page: Page, input_name: str, answer: Any):
        """填写多项填空题（段落中嵌入的多个填空）"""
        try:
            # 答案可以是字典 {"q10_1": "答案1", "q10_2": "答案2"}
            # 或列表 ["答案1", "答案2"]
            if isinstance(answer, dict):
                for sub_name, sub_answer in answer.items():
                    # 尝试找到对应的输入框
                    text_input = page.locator(f"input[name='{sub_name}']").first
                    if await text_input.count() > 0:
                        await text_input.fill(str(sub_answer), timeout=5000)
                        log.info(f"✓ 已填写多项填空子项: {sub_name} = \"{str(sub_answer)[:50]}\"")
                    else:
                        # 尝试 contenteditable 元素
                        label = page.locator(f"label.textEdit").nth(int(sub_name.split('_')[-1]) - 1)
                        if await label.count() > 0:
                            span = label.locator("span.textCont").first
                            if await span.count() > 0:
                                await span.click(timeout=3000)
                                await span.fill(str(sub_answer), timeout=5000)
                                log.info(f"✓ 已填写多项填空(contenteditable): {sub_name} = \"{str(sub_answer)[:50]}\"")
                        else:
                            log.warning(f"❌ 未找到多项填空子项: {sub_name}")

            elif isinstance(answer, list):
                for idx, sub_answer in enumerate(answer, start=1):
                    sub_name = f"{input_name}_{idx}"
                    text_input = page.locator(f"input[name='{sub_name}']").first
                    if await text_input.count() > 0:
                        await text_input.fill(str(sub_answer), timeout=5000)
                        log.info(f"✓ 已填写多项填空第{idx}空: \"{str(sub_answer)[:50]}\"")
                    else:
                        # 尝试 contenteditable
                        label = page.locator(f"label.textEdit").nth(idx - 1)
                        if await label.count() > 0:
                            span = label.locator("span.textCont").first
                            if await span.count() > 0:
                                await span.click(timeout=3000)
                                await span.fill(str(sub_answer), timeout=5000)
                                log.info(f"✓ 已填写多项填空(contenteditable)第{idx}空: \"{str(sub_answer)[:50]}\"")
                        else:
                            log.warning(f"❌ 未找到多项填空第{idx}空")
            else:
                log.warning(f"多项填空题答案格式错误: {type(answer).__name__}")

        except Exception as e:
            log.error(f"填写多项填空题失败: {e}")

    async def _fill_cascade(self, page: Page, input_name: str, answer: str):
        """填写级联下拉题"""
        try:
            # 级联下拉通常需要点击输入框，然后从弹出的选择器中选择
            # 这里提供基础实现，具体逻辑可能需要根据实际页面调整
            cascade_input = page.locator(f"input[name='{input_name}']").first
            if await cascade_input.count() > 0:
                # 点击输入框打开级联选择器
                await cascade_input.click(timeout=3000)
                await page.wait_for_timeout(500)

                # 级联下拉的选择逻辑比较复杂，这里只做简单处理
                # 将答案直接填入输入框（某些情况下可能有效）
                await cascade_input.fill(str(answer), timeout=5000)
                log.info(f"✓ 已填写级联下拉: {input_name} = \"{answer[:80]}\"")

                # 如果需要点击确认按钮
                confirm_btn = page.locator(".weui-picker__action:has-text('确定')").first
                if await confirm_btn.count() > 0:
                    await confirm_btn.click(timeout=3000)
            else:
                log.warning(f"❌ 未找到级联下拉输入框: {input_name}")
        except Exception as e:
            log.error(f"填写级联下拉题失败: {e}")

