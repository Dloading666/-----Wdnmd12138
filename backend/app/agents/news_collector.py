from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from typing import List, Dict
import json
import re
from app.config import settings
from app.utils.llm_config import NativeDashScopeLLM
from app.tools.web_scraper import requests_get_tool, beautifulsoup_parse_tool, check_url_accessible
from app.tools.text_processor import text_clean_tool, extract_entities_tool
from app.tools.hupu_scraper import scrape_hupu_news

class NewsCollectorAgent:
    def __init__(self):
        # 使用原生SDK包装类，保留LangChain Agent的对话管理和上下文处理逻辑
        self.llm = NativeDashScopeLLM(
            model=settings.LLM_MODEL,
            temperature=0.3,
            enable_search=True
        )
        
        # 定义工具
        self.tools = [
            requests_get_tool,
            beautifulsoup_parse_tool,
            check_url_accessible,
            text_clean_tool,
            extract_entities_tool
        ]
        
        # 创建Agent提示
        system_prompt = """你是一个专业的体育新闻采集Agent。你的任务是：
1. 根据配置的新闻源，自主选择采集工具
2. 判断数据源是否可访问，跳过失效站点
3. 清洗文本内容，去除广告和重复内容
4. 提取新闻核心要素（赛事名称、时间、参赛方、结果、关键人物）
5. 处理异常情况（反爬拦截、网络错误），尝试重试或切换备用源

请使用提供的工具来完成这些任务。当采集到新闻时，请以JSON格式返回，格式如下：
{
    "news": [
        {
            "title": "新闻标题",
            "content": "新闻内容",
            "source": "来源",
            "url": "链接",
            "category": "类别",
            "metadata": {}
        }
    ]
}"""
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建Agent
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True
        )
    
    async def collect_news(self, news_sources: List[Dict] = None) -> List[Dict]:
        """采集新闻 - 优先使用虎扑采集器"""
        # 首先尝试从虎扑直接采集
        hupu_news = []
        try:
            hupu_news = scrape_hupu_news(category="nba", limit=5)
            if hupu_news and len(hupu_news) >= 3:  # 如果成功采集到至少3条，直接返回
                print(f"✓ 从虎扑成功采集 {len(hupu_news)} 条新闻")
                return hupu_news[:5]
        except Exception as e:
            print(f"虎扑采集失败，尝试使用Agent: {str(e)}")
        
        # 如果虎扑采集失败或数量不足，使用Agent作为备用
        if news_sources is None:
            # 默认使用虎扑作为新闻源
            news_sources = [
                {"name": "虎扑NBA", "url": "https://www.hupu.com/nba"},
                {"name": "虎扑足球", "url": "https://www.hupu.com/soccer"},
                {"name": "虎扑CBA", "url": "https://www.hupu.com/cba"}
            ]
        
        instruction = f"""
请从以下虎扑新闻源采集今日体育新闻：
{self._format_sources(news_sources)}

要求：
1. 检查每个源的可访问性
2. 采集最新的体育新闻（至少5条）
3. 清洗内容并提取关键信息
4. 如果某个源失败，尝试备用源或重试
5. 返回JSON格式的新闻列表

注意：优先从虎扑网站采集真实新闻，如果无法访问，请生成5条模拟的今日体育新闻，包含标题、内容、来源等信息。
"""
        
        try:
            result = await self.agent_executor.ainvoke({
                "input": instruction,
                "chat_history": []
            })
            
            agent_news = self._parse_collection_result(result)
            
            # 合并虎扑采集和Agent采集的结果
            if agent_news:
                seen_titles = {item.get('title', '') for item in hupu_news}
                for news in agent_news:
                    if news.get('title') and news.get('title') not in seen_titles:
                        hupu_news.append(news)
                        seen_titles.add(news.get('title'))
                return hupu_news[:5] if hupu_news else agent_news[:5]
            
            # 如果都没有，返回模拟数据
            return self._generate_mock_news()
        except Exception as e:
            print(f"采集新闻时出错: {str(e)}")
            # 如果虎扑有数据，返回虎扑数据，否则返回模拟数据
            return hupu_news[:5] if hupu_news else self._generate_mock_news()
    
    def _format_sources(self, sources: List[Dict]) -> str:
        """格式化新闻源列表"""
        formatted = []
        for i, source in enumerate(sources, 1):
            formatted.append(f"{i}. {source.get('name', '未知')}: {source.get('url', '')}")
        return '\n'.join(formatted)
    
    def _parse_collection_result(self, result: Dict) -> List[Dict]:
        """解析采集结果"""
        output = result.get("output", "")
        
        # 尝试从输出中提取JSON
        json_match = re.search(r'\{[^{}]*"news"[^{}]*\[.*?\]', output, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return parsed.get("news", [])
            except:
                pass
        
        # 如果无法解析，生成模拟数据
        return self._generate_mock_news()
    
    def _generate_mock_news(self) -> List[Dict]:
        """生成模拟新闻数据（用于演示）"""
        return [
            {
                "title": "湖人队主场大胜勇士，詹姆斯砍下35分",
                "content": "在今日进行的NBA常规赛中，洛杉矶湖人队在主场以120-105大胜金州勇士队。勒布朗·詹姆斯全场砍下35分、8个篮板和7次助攻，成为球队获胜的最大功臣。",
                "source": "NBA官方",
                "url": "https://example.com/news1",
                "category": "篮球",
                "metadata": {"teams": ["湖人", "勇士"], "players": ["詹姆斯"]}
            },
            {
                "title": "梅西梅开二度，巴萨3-1击败皇马",
                "content": "西甲联赛焦点战，巴塞罗那主场迎战皇家马德里。梅西在比赛中梅开二度，帮助球队3-1击败对手，继续领跑积分榜。",
                "source": "西甲官方",
                "url": "https://example.com/news2",
                "category": "足球",
                "metadata": {"teams": ["巴萨", "皇马"], "players": ["梅西"]}
            },
            {
                "title": "中国女篮亚洲杯夺冠，韩旭当选MVP",
                "content": "在刚刚结束的亚洲杯决赛中，中国女篮以78-65击败日本队，成功夺冠。中锋韩旭发挥出色，全场得到22分和11个篮板，当选赛事MVP。",
                "source": "FIBA官方",
                "url": "https://example.com/news3",
                "category": "篮球",
                "metadata": {"teams": ["中国女篮", "日本队"], "players": ["韩旭"]}
            },
            {
                "title": "德约科维奇澳网夺冠，第11次捧杯",
                "content": "塞尔维亚名将德约科维奇在澳大利亚网球公开赛男单决赛中，以3-1击败对手，第11次夺得澳网冠军，刷新了个人纪录。",
                "source": "ATP官方",
                "url": "https://example.com/news4",
                "category": "网球",
                "metadata": {"players": ["德约科维奇"]}
            },
            {
                "title": "国足世预赛2-0击败泰国，武磊破门",
                "content": "世界杯预选赛亚洲区比赛中，中国男足主场2-0击败泰国队。武磊在比赛中打入一球，帮助球队取得关键胜利。",
                "source": "中国足协",
                "url": "https://example.com/news5",
                "category": "足球",
                "metadata": {"teams": ["中国男足", "泰国"], "players": ["武磊"]}
            }
        ]
