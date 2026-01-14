from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from typing import List, Dict, Optional
from app.config import settings
from app.utils.llm_config import NativeDashScopeLLM
from app.tools.text_processor import extract_entities_tool
from app.tools.data_fetcher import fetch_sports_data_api

class NewsAnalyzerAgent:
    def __init__(self):
        # 使用原生SDK包装类，保留LangChain Agent的对话管理和上下文处理逻辑
        self.llm = NativeDashScopeLLM(
            model=settings.LLM_MODEL,
            temperature=0.5,
            enable_search=True
        )
        
        self.tools = [
            extract_entities_tool,
            fetch_sports_data_api
        ]
        
        self.system_prompt = """你是一位资深的体育评论员和分析专家。你的核心任务是：
1. **提取每条新闻的关键内容**：从新闻中提炼出核心信息（事件、人物、数据、结果等）
2. **进行专业点评**：对每条新闻进行深度分析和专业点评，提供独到见解
3. **分析影响和意义**：解读新闻事件的影响、价值和未来趋势

请用专业、客观、有深度的语言，以Markdown格式生成分析报告。"""
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=True
        )
    
    async def analyze_news(self, news_articles: List[Dict], analysis_type: str = "daily", progress_callback=None) -> Dict:
        """分析新闻并生成报告
        
        Args:
            news_articles: 新闻列表
            analysis_type: 分析类型
            progress_callback: 进度回调函数，接收(progress: int, message: str)参数
        """
        if progress_callback:
            await progress_callback(30, "正在格式化新闻内容...")
        
        news_content = self._format_news(news_articles)
        
        instruction = f"""
请作为资深体育评论员，对以下今日体育新闻进行**关键内容提取**和**专业点评**。

{news_content}

请生成一份Markdown格式的体育新闻分析报告，要求：

## 报告结构

### 一、今日新闻概览

简要总结今日主要体育新闻事件（2-3句话）

### 二、新闻关键内容提取与点评

**对每条新闻，按以下格式进行提取和点评：**

#### 新闻1：[新闻标题]

**关键内容提取：**
- **核心事件：** （用一句话概括新闻的核心事件）
- **关键人物：** （列出涉及的重要人物）
- **重要数据：** （比赛比分、统计数据、时间等关键数字）
- **比赛结果/事件结果：** （如果是比赛新闻，说明结果；如果是其他事件，说明结果）

**专业点评：**
（对这条新闻进行深度分析，包括：
- 事件的意义和价值
- 对相关球队、球员、联赛的影响
- 背后的原因和背景
- 未来可能的发展趋势
- 你的专业见解和评价

要求有独到见解，不要只是复述新闻内容，要有分析和判断）

---

#### 新闻2：[新闻标题]

**关键内容提取：**
- **核心事件：**
- **关键人物：**
- **重要数据：**
- **比赛结果/事件结果：**

**专业点评：**
（同上格式）

---

（继续处理所有新闻，确保每条新闻都有详细的提取和点评）

### 三、综合分析

**热点话题：**
（总结今日体育领域的热点话题，分析其背后的原因和意义）

**趋势预测：**
（基于今日新闻，预测相关事件的发展趋势和可能的影响）

**整体评价：**
（对今日体育新闻的整体评价，判断整体舆论倾向：正面/负面/中性，并说明理由）

**要求：**
- 使用Markdown格式（标题用##、###，列表用-，强调用**粗体**等）
- **重点是对每条新闻进行关键内容提取和专业点评**
- 点评要有深度，不能只是简单复述新闻内容
- 语言专业、客观、有见解
- 字数控制在2000-4000字之间
- 确保每条新闻都有详细的提取和点评
"""
        
        try:
            if progress_callback:
                await progress_callback(40, "正在调用AI模型生成分析报告...")
            
            # 先尝试使用Agent执行
            try:
                if progress_callback:
                    await progress_callback(50, "AI模型正在分析新闻内容，请稍候...")
                
                result = await self.agent_executor.ainvoke({
                    "input": instruction,
                    "chat_history": []
                })
                output = result.get("output", "")
                
                if progress_callback:
                    await progress_callback(70, "AI分析完成，正在处理结果...")
            except Exception as agent_error:
                # 如果Agent执行失败，直接调用原生SDK生成内容
                print(f"Agent执行失败，直接调用原生SDK: {str(agent_error)}")
                if progress_callback:
                    await progress_callback(50, "生成分析报告中...")
                
                from langchain_core.messages import HumanMessage
                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=instruction)
                ]
                response = await self.llm.ainvoke(messages)
                output = response.content if hasattr(response, 'content') else str(response)
                
                if progress_callback:
                    await progress_callback(70, "分析完成，正在处理结果...")
            
            if not output or len(output.strip()) < 100:
                raise ValueError("LLM返回内容为空或过短")
            
            print(f"✓ LLM生成内容长度: {len(output)} 字符")
            
            if progress_callback:
                await progress_callback(75, "正在解析分析结果...")
            
            # 解析输出，提取摘要和详细内容
            parsed_result = self._parse_analysis_output(output, news_articles)
            
            if progress_callback:
                await progress_callback(80, "正在提取统计信息...")
            
            # 提取更详细的统计信息
            statistics = self._extract_statistics(news_articles)
            
            # 进行情感分析
            sentiment_analysis = parsed_result.get("sentiment_analysis", self._analyze_sentiment(output))
            
            if progress_callback:
                await progress_callback(90, "分析报告生成完成！")
            
            return {
                "summary": parsed_result.get("summary", self._extract_summary(output)),
                "content": parsed_result.get("content", output),
                "analysis_type": analysis_type,
                "news_count": len(news_articles),
                "statistics": statistics,
                "sentiment_analysis": sentiment_analysis
            }
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            error_msg = str(e)
            
            # 检查是否是API额度或认证问题
            if "AllocationQuota" in error_msg or "free tier" in error_msg.lower() or "quota" in error_msg.lower():
                error_msg = f"API免费额度已用完: {error_msg}"
            elif "403" in error_msg or "401" in error_msg:
                error_msg = f"API认证失败: {error_msg}"
            
            print(f"✗ 分析新闻时出错: {error_msg}")
            print(f"错误详情: {error_detail}")
            # 抛出异常，让上层处理，而不是返回默认消息
            raise Exception(f"生成分析报告失败: {error_msg}")
    
    def _format_news(self, articles: List[Dict]) -> str:
        """格式化新闻列表，提供给LLM进行点评"""
        formatted = []
        formatted.append(f"=== 今日体育新闻（共{len(articles)}条）===\n")
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', '')
            content = article.get('content', '')
            source = article.get('source', '未知')
            category = article.get('category', '体育')
            
            # 保留更多内容供分析（最多1000字）
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            formatted.append(f"""
【新闻{i}】
标题：{title}
来源：{source} | 类别：{category}
内容：
{content}
---
""")
        
        formatted.append("\n请对以上新闻进行专业点评和分析。")
        return '\n'.join(formatted)
    
    def _extract_statistics(self, articles: List[Dict]) -> Dict:
        """提取统计数据"""
        categories = {}
        teams = set()
        players = set()
        
        for article in articles:
            cat = article.get('category', '其他')
            categories[cat] = categories.get(cat, 0) + 1
            
            metadata = article.get('metadata', {})
            if isinstance(metadata, dict):
                teams.update(metadata.get('teams', []))
                players.update(metadata.get('players', []))
        
        return {
            "total_news": len(articles),
            "categories": categories,
            "teams_count": len(teams),
            "players_count": len(players),
            "teams": list(teams),
            "players": list(players)
        }
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """简单的情感分析"""
        positive_words = ['胜利', '夺冠', '出色', '优秀', '精彩', '成功', '突破', '创造', '刷新', '领先', '优势']
        negative_words = ['失败', '失利', '伤病', '争议', '问题', '落后', '失误', '遗憾', '困难', '挑战']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = "正面"
        elif negative_count > positive_count:
            sentiment = "负面"
        else:
            sentiment = "中性"
        
        return {
            "sentiment": sentiment,
            "positive_score": positive_count,
            "negative_score": negative_count
        }
    
    def _parse_analysis_output(self, output: str, articles: List[Dict]) -> Dict:
        """解析分析输出，提取结构化内容"""
        result = {
            "summary": "",
            "content": output,
            "sentiment_analysis": self._analyze_sentiment(output)
        }
        
        # 提取摘要：优先提取"今日新闻综述"部分，如果没有则提取前几段
        summary = self._extract_summary(output)
        result["summary"] = summary
        
        return result
    
    def _extract_summary(self, text: str) -> str:
        """从分析报告中提取摘要"""
        # 尝试提取"今日新闻综述"部分
        import re
        
        # 查找"今日新闻综述"或"综述"部分
        patterns = [
            r'今日新闻综述[：:]\s*(.*?)(?=\n\n|\n\d+\.|$)',
            r'综述[：:]\s*(.*?)(?=\n\n|\n\d+\.|$)',
            r'新闻综述[：:]\s*(.*?)(?=\n\n|\n\d+\.|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 100:  # 确保摘要有意义
                    return summary[:800] + "..." if len(summary) > 800 else summary
        
        # 如果没有找到特定部分，提取前3-5段作为摘要
        paragraphs = text.split('\n\n')
        summary_paragraphs = []
        total_length = 0
        
        for para in paragraphs[:5]:
            para = para.strip()
            if para and not para.startswith('#'):  # 跳过标题
                if total_length + len(para) < 800:
                    summary_paragraphs.append(para)
                    total_length += len(para)
                else:
                    break
        
        if summary_paragraphs:
            summary = '\n\n'.join(summary_paragraphs)
            return summary[:800] + "..." if len(summary) > 800 else summary
        
        # 最后备选：提取前500字
        return text[:500] + "..." if len(text) > 500 else text