from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from typing import Dict, List
from app.config import settings
from app.utils.llm_config import NativeDashScopeLLM
from app.agents.news_collector import NewsCollectorAgent
from app.agents.news_analyzer import NewsAnalyzerAgent

class MultiAgentCoordinator:
    def __init__(self):
        # 使用原生SDK包装类（虽然当前未使用，但保留以备将来扩展）
        self.llm = NativeDashScopeLLM(
            model=settings.LLM_MODEL,
            temperature=0.3,
            enable_search=True
        )
        
        # 初始化子Agent
        self.collector_agent = NewsCollectorAgent()
        self.analyzer_agent = NewsAnalyzerAgent()
        
        system_prompt = """你是一个多Agent协调器。你的任务是：
1. 接收用户的复杂请求
2. 将任务拆分为子任务
3. 协调各个Agent完成子任务
4. 汇总最终结果

可用的Agent：
- 采集Agent：负责新闻采集和清洗
- 分析Agent：负责新闻分析和报告生成
- 格式转换Agent：负责输出格式转换
- 推送Agent：负责结果推送

请根据任务需求，合理分配和协调这些Agent。"""
        
        self.system_prompt = system_prompt
    
    async def execute_task(self, task_description: str, news_sources: List[Dict] = None) -> Dict:
        """执行复杂任务"""
        # 任务分解
        subtasks = await self._decompose_task(task_description)
        
        results = {}
        
        # 执行子任务
        for subtask in subtasks:
            agent_type = subtask.get('agent')
            task = subtask.get('task')
            
            try:
                if agent_type == 'collector':
                    results['collection'] = await self.collector_agent.collect_news(news_sources)
                elif agent_type == 'analyzer':
                    news_list = task.get('news', results.get('collection', []))
                    analysis_type = task.get('analysis_type', 'daily')
                    results['analysis'] = await self.analyzer_agent.analyze_news(news_list, analysis_type)
            except Exception as e:
                print(f"执行{agent_type}任务时出错: {str(e)}")
                results[agent_type] = {"error": str(e)}
        
        # 汇总结果
        final_result = await self._aggregate_results(results)
        
        return final_result
    
    async def _decompose_task(self, task: str) -> List[Dict]:
        """分解任务为子任务"""
        # 简化版本：根据关键词判断任务类型
        task_lower = task.lower()
        
        subtasks = []
        
        # 如果需要采集新闻
        if any(keyword in task_lower for keyword in ['采集', '收集', '获取', '生成日报']):
            subtasks.append({
                "agent": "collector",
                "task": {"sources": []}
            })
        
        # 如果需要分析
        if any(keyword in task_lower for keyword in ['分析', '报告', '总结']):
            subtasks.append({
                "agent": "analyzer",
                "task": {"news": [], "analysis_type": "daily"}
            })
        
        # 如果都没有，默认执行采集和分析
        if not subtasks:
            subtasks = [
                {"agent": "collector", "task": {"sources": []}},
                {"agent": "analyzer", "task": {"news": [], "analysis_type": "daily"}}
            ]
        
        return subtasks
    
    async def _aggregate_results(self, results: Dict) -> Dict:
        """汇总结果"""
        return {
            "status": "success",
            "results": results,
            "summary": "任务执行完成"
        }
