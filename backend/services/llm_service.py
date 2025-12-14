"""LLM服务模块"""
import json
from typing import Optional, Dict, Any, List
import httpx
from backend.models.question import Question, QuestionType
from backend.models.answer import Answer, AnswerStatus
from backend.core.logger import log


class LLMService:
    """LLM服务类"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def answer_question(
        self,
        question: Question,
        knowledge_context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Answer:
        """
        使用LLM回答问题
        
        Args:
            question: 题目对象
            knowledge_context: 知识库上下文
            system_prompt: 系统提示词
            
        Returns:
            答案对象
        """
        try:
            # 构建提示词
            messages = self._build_messages(question, knowledge_context, system_prompt)
            
            # 调用LLM
            response = await self._call_api(messages)
            
            # 解析响应
            answer = self._parse_response(question, response)
            
            return answer
            
        except Exception as e:
            log.error(f"LLM答题失败: {e}")
            return Answer(
                question_id=question.id,
                content="",
                status=AnswerStatus.FAILED,
                confidence=0.0,
                reasoning=f"错误: {str(e)}",
            )
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从文本中提取JSON对象（支持嵌套和代码块）

        Args:
            text: 可能包含JSON的文本

        Returns:
            提取的JSON对象，失败返回None
        """
        import re

        # 方法1: 直接解析整个文本
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # 方法2: 提取代码块中的JSON（```json ... ```）
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        code_match = re.search(code_block_pattern, text, re.DOTALL | re.IGNORECASE)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass

        # 方法3: 查找包含"answer"键的JSON对象（支持嵌套）
        # 使用栈来匹配大括号，确保找到完整的JSON对象
        answer_positions = [m.start() for m in re.finditer(r'"answer"', text)]

        for pos in answer_positions:
            # 向前查找最近的左大括号
            start = text.rfind('{', 0, pos)
            if start == -1:
                continue

            # 向后查找匹配的右大括号（使用栈）
            brace_count = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break

            if end == -1:
                continue

            # 尝试解析这段文本
            try:
                candidate = text[start:end]
                result = json.loads(candidate)
                if isinstance(result, dict) and "answer" in result:
                    return result
            except json.JSONDecodeError:
                continue

        # 方法4: 查找任何有效的JSON对象
        # 查找所有可能的JSON对象
        json_pattern = r'\{[^{}]*\}'
        for match in re.finditer(json_pattern, text):
            try:
                candidate = json.loads(match.group())
                if isinstance(candidate, dict) and "answer" in candidate:
                    return candidate
            except json.JSONDecodeError:
                continue

        return None

    def _build_messages(
        self,
        question: Question,
        knowledge_context: Optional[str],
        system_prompt: Optional[str],
    ) -> List[Dict[str, str]]:
        """构建对话消息"""
        messages = []
        
        # 系统提示词
        if not system_prompt:
            system_prompt = self._get_default_system_prompt(question.type)
        
        messages.append({
            "role": "system",
            "content": system_prompt,
        })
        
        # 用户消息
        user_content = self._build_user_prompt(question, knowledge_context)
        messages.append({
            "role": "user",
            "content": user_content,
        })
        
        return messages
    
    def _get_default_system_prompt(self, question_type: QuestionType) -> str:
        """获取默认系统提示词"""
        base_prompt = """你是一个专业的答题助手。请根据题目内容和提供的信息，给出准确答案。

【重要规则】
1. 你的回复必须且只能是一个有效的JSON对象，不要包含任何其他文字
2. 不要在JSON前后添加说明、思考过程或其他解释
3. 仔细分析题目，如果有参考资料优先使用
4. 评估答案的置信度（0-1之间）

【JSON格式】
{
    "answer": "你的答案",
    "reasoning": "50字以内的简要推理",
    "confidence": 0.95
}
"""
        
        if question_type == QuestionType.SINGLE_CHOICE:
            base_prompt += '\n【单选题】answer格式为"选项索引|选项内容"，例如："2|作为分解者，参与二氧化碳等物质循环"。'
        elif question_type == QuestionType.MULTIPLE_CHOICE:
            base_prompt += '\n【多选题】answer格式为选项索引数组，如"[0, 2]"表示选第1和第3个选项，然后加上完整内容。'
        elif question_type == QuestionType.TRUE_FALSE:
            base_prompt += '\n【判断题】answer格式为"选项索引|选项内容"，例如："0|正确"。'
        elif question_type == QuestionType.FILL_BLANK:
            base_prompt += '\n【填空题】answer直接填写答案文本即可。'
        
        return base_prompt
    
    def _build_user_prompt(self, question: Question, knowledge_context: Optional[str]) -> str:
        """构建用户提示词"""
        prompt_parts = [f"题目类型：{question.type.value}"]
        prompt_parts.append(f"题目内容：{question.content}")
        
        if question.options:
            prompt_parts.append("\n选项：")
            for idx, option in enumerate(question.options):
                prompt_parts.append(f"{idx}. {option}")
        
        if knowledge_context:
            prompt_parts.append(f"\n参考资料：\n{knowledge_context}")
        
        return "\n".join(prompt_parts)
    
    async def _call_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """调用OpenAI兼容的API"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            log.debug(f"→ 调用LLM API: {self.model}")
            log.debug(f"  URL: {url}")
            log.debug(f"  温度: {self.temperature}, 最大令牌: {self.max_tokens or '未限制'}")

            response = await self.client.post(url, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            result = response.json()

            # 记录token使用情况
            if "usage" in result:
                usage = result["usage"]
                log.debug(f"← Token使用: 输入={usage.get('prompt_tokens', 0)}, "
                         f"输出={usage.get('completion_tokens', 0)}, "
                         f"总计={usage.get('total_tokens', 0)}")

            return result

        except httpx.TimeoutException as e:
            log.error(f"❌ LLM API调用超时: {url}, 超时时间: 60秒")
            raise TimeoutError(f"LLM API调用超时: {str(e)}")

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_detail = "未知错误"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(error_data))
            except Exception:
                error_detail = e.response.text[:200]

            log.error(f"❌ LLM API返回错误状态码: {status_code}, 详情: {error_detail}")

            if status_code == 401:
                raise PermissionError(f"API密钥无效或未授权: {error_detail}")
            elif status_code == 429:
                raise ConnectionError(f"API速率限制: {error_detail}")
            elif status_code >= 500:
                raise ConnectionError(f"API服务器错误 ({status_code}): {error_detail}")
            else:
                raise ValueError(f"API请求失败 ({status_code}): {error_detail}")

        except httpx.ConnectError as e:
            log.error(f"❌ 无法连接到LLM API: {url}, 错误: {e}")
            raise ConnectionError(f"无法连接到API服务器: {str(e)}")

        except json.JSONDecodeError as e:
            log.error(f"❌ 解析LLM API响应失败: 无效的JSON格式")
            raise ValueError(f"API返回了无效的JSON响应: {str(e)}")

        except Exception as e:
            log.error(f"❌ LLM API调用发生未知错误: {type(e).__name__}: {e}")
            raise
    
    def _parse_response(self, question: Question, response: Dict[str, Any]) -> Answer:
        """解析LLM响应"""
        try:
            # 验证响应结构
            if not isinstance(response, dict):
                raise ValueError(f"响应不是字典类型: {type(response)}")

            if "choices" not in response:
                raise ValueError("响应中缺少 'choices' 字段")

            if not response["choices"] or len(response["choices"]) == 0:
                raise ValueError("响应中 'choices' 为空")

            # 提取回复内容
            try:
                content = response["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as e:
                raise ValueError(f"无法从响应中提取内容: {e}")

            if not content or not isinstance(content, str):
                raise ValueError(f"响应内容无效: {content}")

            # 尝试从内容中提取JSON（使用更健壮的方法）
            result = self._extract_json_from_text(content)

            if result and isinstance(result, dict) and "answer" in result:
                # 成功提取JSON格式
                try:
                    answer_raw = result.get("answer", "")
                    reasoning = str(result.get("reasoning", ""))[:200]  # 限制推理文本长度

                    # 验证并转换confidence
                    confidence_raw = result.get("confidence", 0.5)
                    try:
                        confidence = float(confidence_raw)
                        # 确保confidence在0-1之间
                        confidence = max(0.0, min(1.0, confidence))
                    except (ValueError, TypeError):
                        log.warning(f"无效的confidence值: {confidence_raw}, 使用默认值0.5")
                        confidence = 0.5

                    # 处理答案格式：如果是"索引|内容"格式，只保留内容部分用于显示
                    # 但实际提交时需要用索引
                    answer_content = str(answer_raw)

                    # 如果答案包含 | 分隔符，说明是"索引|内容"格式
                    if "|" in answer_content and question.type in [
                        QuestionType.SINGLE_CHOICE,
                        QuestionType.TRUE_FALSE
                    ]:
                        parts = answer_content.split("|", 1)
                        if len(parts) == 2:
                            # 保存完整格式，前端可以显示内容，提交时用索引
                            answer_content = answer_content  # 保持"索引|内容"格式

                except Exception as e:
                    log.warning(f"处理JSON结果时出错: {e}, 使用降级处理")
                    answer_content = str(result.get("answer", ""))
                    reasoning = "JSON解析成功但字段处理失败"
                    confidence = 0.3

            else:
                # 无法解析JSON，尝试智能提取答案
                log.warning(f"无法从响应中提取有效JSON，使用降级处理")
                # 移除多余的说明文字，只保留核心答案
                lines = content.strip().split('\n')
                # 找第一个看起来像答案的行
                answer_content = content.strip()[:100]  # 截断过长内容
                reasoning = "AI直接回答（未按格式）"
                confidence = 0.3  # 降低置信度

            return Answer(
                question_id=question.id,
                content=str(answer_content).strip(),
                status=AnswerStatus.AI_GENERATED,
                confidence=confidence,
                reasoning=reasoning,
            )

        except ValueError as e:
            log.error(f"解析LLM响应失败 (数据格式错误): {e}")
            return Answer(
                question_id=question.id,
                content="",
                status=AnswerStatus.FAILED,
                confidence=0.0,
                reasoning=f"数据格式错误: {str(e)}",
            )

        except Exception as e:
            log.error(f"解析LLM响应失败 (未知错误): {type(e).__name__}: {e}")
            return Answer(
                question_id=question.id,
                content="",
                status=AnswerStatus.FAILED,
                confidence=0.0,
                reasoning=f"解析错误: {str(e)}",
            )
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


class EmbeddingService:
    """Embedding服务类"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-embedding",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def embed_text(self, text: str) -> List[float]:
        """
        对文本进行embedding
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表
        """
        url = f"{self.base_url}/embeddings"
        
        payload = {
            "model": self.model,
            "input": text,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            log.debug(f"→ 调用Embedding API: {self.model}, 文本长度: {len(text)}")
            response = await self.client.post(url, json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()

            result = response.json()

            # 验证响应格式
            if not isinstance(result, dict) or "data" not in result:
                raise ValueError(f"Embedding API响应格式无效: {result}")

            if not result["data"] or len(result["data"]) == 0:
                raise ValueError("Embedding API返回空数据")

            embedding = result["data"][0].get("embedding")
            if not embedding or not isinstance(embedding, list):
                raise ValueError(f"无效的embedding数据: {embedding}")

            log.debug(f"← Embedding成功，维度: {len(embedding)}")
            return embedding

        except httpx.TimeoutException as e:
            log.error(f"❌ Embedding API调用超时: {url}")
            raise TimeoutError(f"Embedding API调用超时: {str(e)}")

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_detail = e.response.text[:200]
            log.error(f"❌ Embedding API返回错误状态码: {status_code}, 详情: {error_detail}")
            raise ConnectionError(f"Embedding API错误 ({status_code}): {error_detail}")

        except httpx.ConnectError as e:
            log.error(f"❌ 无法连接到Embedding API: {url}")
            raise ConnectionError(f"无法连接到Embedding服务器: {str(e)}")

        except ValueError as e:
            log.error(f"❌ Embedding响应数据格式错误: {e}")
            raise

        except Exception as e:
            log.error(f"❌ Embedding API调用失败: {type(e).__name__}: {e}")
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        批量embedding，自动分批处理
        
        Args:
            texts: 文本列表
            batch_size: 每批最多处理的文本数量（阿里云限制为10）
            
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        # 如果文本数量超过batch_size，分批处理
        if len(texts) > batch_size:
            log.info(f"→ 文本数量 {len(texts)} 超过批次限制 {batch_size}，将分批处理")
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                log.info(f"  处理第 {i//batch_size + 1} 批，共 {len(batch)} 个文本 ({i+1}-{i+len(batch)}/{len(texts)})")
                batch_embeddings = await self._embed_single_batch(batch)
                all_embeddings.extend(batch_embeddings)
            
            log.info(f"← 批量Embedding完成，共生成 {len(all_embeddings)} 个向量")
            return all_embeddings
        else:
            return await self._embed_single_batch(texts)
    
    async def _embed_single_batch(self, texts: List[str]) -> List[List[float]]:
        """
        处理单个批次的embedding
        
        Args:
            texts: 文本列表（不超过10个）
            
        Returns:
            向量列表
        """
        url = f"{self.base_url}/embeddings"
        
        payload = {
            "model": self.model,
            "input": texts,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            log.debug(f"→ 调用Embedding API: {self.model}, 文本数量: {len(texts)}")
            response = await self.client.post(url, json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()

            result = response.json()

            # 验证响应格式
            if not isinstance(result, dict) or "data" not in result:
                raise ValueError(f"批量Embedding响应格式无效")

            if not result["data"]:
                raise ValueError("批量Embedding返回空数据")

            # 提取embeddings
            embeddings = []
            for i, item in enumerate(result["data"]):
                if not isinstance(item, dict) or "embedding" not in item:
                    raise ValueError(f"第{i+1}个embedding数据格式无效")
                embedding = item["embedding"]
                if not isinstance(embedding, list):
                    raise ValueError(f"第{i+1}个embedding不是列表类型")
                embeddings.append(embedding)

            log.debug(f"← 批量Embedding成功，生成 {len(embeddings)} 个向量")
            return embeddings

        except httpx.TimeoutException as e:
            log.error(f"❌ 批量Embedding API调用超时")
            raise TimeoutError(f"批量Embedding超时: {str(e)}")

        except httpx.HTTPStatusError as e:
            log.error(f"❌ 批量Embedding API错误: {e.response.status_code}")
            raise ConnectionError(f"批量Embedding失败: HTTP {e.response.status_code}")

        except ValueError as e:
            log.error(f"❌ 批量Embedding数据格式错误: {e}")
            raise

        except Exception as e:
            log.error(f"❌ 批量Embedding失败: {type(e).__name__}: {e}")
            raise
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


class RerankService:
    """Rerank服务类"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-rerank",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前k个结果
            
        Returns:
            重排序后的结果列表，每项包含 index, score, document
        """
        # 注意：这里假设API支持rerank接口
        # 实际使用时可能需要根据具体供应商调整
        url = f"{self.base_url}/rerank"
        
        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
        }
        
        if top_k:
            payload["top_k"] = top_k
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            response = await self.client.post(url, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            result = response.json()

            # 验证响应格式
            if not isinstance(result, dict) or "results" not in result:
                log.warning(f"Rerank响应格式无效，返回原始顺序")
                return self._fallback_rerank(documents)

            return result.get("results", [])

        except httpx.TimeoutException as e:
            log.warning(f"Rerank超时，返回原始顺序: {e}")
            return self._fallback_rerank(documents)

        except httpx.HTTPStatusError as e:
            log.warning(f"Rerank API错误 ({e.response.status_code})，返回原始顺序")
            return self._fallback_rerank(documents)

        except Exception as e:
            log.warning(f"Rerank调用失败，返回原始顺序: {type(e).__name__}: {e}")
            return self._fallback_rerank(documents)

    def _fallback_rerank(self, documents: List[str]) -> List[Dict[str, Any]]:
        """Rerank失败时的降级处理"""
        return [
            {"index": i, "score": 1.0, "document": doc}
            for i, doc in enumerate(documents)
        ]
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

