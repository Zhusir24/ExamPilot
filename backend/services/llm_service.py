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
        except Exception as e:
            log.error(f"❌ LLM API调用失败: {url}, 错误: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                log.error(f"响应内容: {e.response.text}")
            raise
    
    def _parse_response(self, question: Question, response: Dict[str, Any]) -> Answer:
        """解析LLM响应"""
        try:
            # 提取回复内容
            content = response["choices"][0]["message"]["content"]
            
            # 尝试从内容中提取JSON（可能混有其他文本）
            try:
                # 首先尝试直接解析
                result = json.loads(content)
            except json.JSONDecodeError:
                # 尝试从文本中提取JSON块
                import re
                json_match = re.search(r'\{[^{}]*"answer"[^{}]*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                    except:
                        result = None
                else:
                    result = None
            
            if result and isinstance(result, dict) and "answer" in result:
                # 成功提取JSON格式
                answer_raw = result.get("answer", "")
                reasoning = result.get("reasoning", "")[:200]  # 限制推理文本长度
                confidence = float(result.get("confidence", 0.5))
                
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
                
            else:
                # 无法解析JSON，尝试智能提取答案
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
            
        except Exception as e:
            log.error(f"解析LLM响应失败: {e}")
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
            log.debug(f"← Embedding成功，维度: {len(result['data'][0]['embedding'])}")
            return result["data"][0]["embedding"]
        except Exception as e:
            log.error(f"❌ Embedding API调用失败: {url}, 错误: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                log.error(f"响应内容: {e.response.text}")
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
            embeddings = [item["embedding"] for item in result["data"]]
            log.debug(f"← Embedding成功，生成 {len(embeddings)} 个向量")
            return embeddings
        except Exception as e:
            log.error(f"❌ Embedding API调用失败: {url}, 错误: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                log.error(f"响应内容: {e.response.text}")
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
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result.get("results", [])
        except Exception as e:
            log.warning(f"Rerank调用失败，返回原始顺序: {e}")
            # 如果rerank失败，返回原始顺序
            return [
                {"index": i, "score": 1.0, "document": doc}
                for i, doc in enumerate(documents)
            ]
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

