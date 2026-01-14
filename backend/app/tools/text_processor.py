from langchain.tools import tool
from typing import List, Dict
import re

@tool
def text_clean_tool(text: str) -> str:
    """清洗文本，去除广告、重复内容等。输入：原始文本。返回：清洗后的文本。"""
    if not text:
        return ""
    
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 去除常见广告关键词
    ad_keywords = ['广告', '推广', '点击查看', '立即购买', '立即下载', '免费领取']
    for keyword in ad_keywords:
        text = text.replace(keyword, '')
    
    # 去除HTML标签残留
    text = re.sub(r'<[^>]+>', '', text)
    
    # 去除特殊字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff，。！？：；、]', '', text)
    
    return text.strip()

@tool
def extract_entities_tool(text: str) -> Dict:
    """提取新闻核心要素（赛事名称、时间、参赛方、结果、关键人物）。输入：新闻文本。返回：包含实体信息的字典。"""
    if not text:
        return {"teams": [], "players": [], "dates": [], "scores": []}
    
    entities = {
        'teams': [],
        'players': [],
        'dates': [],
        'scores': []
    }
    
    # 提取日期
    date_patterns = [
        r'\d{4}年\d{1,2}月\d{1,2}日',
        r'\d{4}-\d{1,2}-\d{1,2}',
        r'\d{1,2}月\d{1,2}日'
    ]
    for pattern in date_patterns:
        dates = re.findall(pattern, text)
        entities['dates'].extend(dates)
    
    # 提取比分（简化版）
    score_pattern = r'(\d+)[:：](\d+)'
    scores = re.findall(score_pattern, text)
    entities['scores'] = [f"{s[0]}:{s[1]}" for s in scores]
    
    # 常见球队名称（简化版，实际应该使用NER模型）
    common_teams = ['湖人', '勇士', '凯尔特人', '热火', '篮网', '皇马', '巴萨', '曼联', '利物浦', '切尔西']
    for team in common_teams:
        if team in text:
            entities['teams'].append(team)
    
    # 常见球员名称（简化版）
    common_players = ['詹姆斯', '库里', '杜兰特', '梅西', 'C罗', '内马尔']
    for player in common_players:
        if player in text:
            entities['players'].append(player)
    
    # 去重
    entities['teams'] = list(set(entities['teams']))
    entities['players'] = list(set(entities['players']))
    entities['dates'] = list(set(entities['dates']))
    
    return entities
