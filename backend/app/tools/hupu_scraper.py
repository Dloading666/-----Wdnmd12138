"""
虎扑网站新闻采集工具
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import re
import time

class HupuScraper:
    """虎扑新闻采集器 - 支持API接口和网页爬取"""
    
    def __init__(self):
        self.base_url = "https://www.hupu.com"
        self.api_base_url = "https://bbs.hupu.com/v1"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.hupu.com/',
            'Origin': 'https://www.hupu.com'
        }
    
    def get_news_from_api(self, category: str = "nba", page: int = 1, limit: int = 20) -> Optional[List[Dict]]:
        """
        通过虎扑API接口获取新闻（优先使用）
        
        Args:
            category: 新闻类别 (nba, soccer, cba等)
            page: 页码
            limit: 每页数量
        
        Returns:
            新闻列表，如果API不可用返回None
        """
        try:
            # 虎扑API接口
            api_url = f"{self.api_base_url}/news/{category}"
            params = {
                'page': page,
                'limit': limit
            }
            
            print(f"📡 尝试使用虎扑API获取数据: {api_url}")
            
            response = requests.get(api_url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✓ 虎扑API返回数据: {type(data)}")
                    
                    # 解析API返回的数据结构
                    news_list = []
                    
                    # 尝试不同的数据结构
                    if isinstance(data, dict):
                        # 可能的结构: {"data": [...], "list": [...], "news": [...]}
                        items = data.get('data') or data.get('list') or data.get('news') or data.get('result', [])
                    elif isinstance(data, list):
                        items = data
                    else:
                        print(f"⚠️ 未知的API数据结构: {type(data)}")
                        return None
                    
                    if not items:
                        print(f"⚠️ API返回数据为空")
                        return None
                    
                    print(f"✓ 从API获取到 {len(items)} 条数据")
                    
                    # 解析每条新闻
                    for item in items[:limit]:
                        try:
                            # 处理不同的数据结构
                            if isinstance(item, dict):
                                news = {
                                    "title": item.get('title') or item.get('headline') or item.get('name', ''),
                                    "content": item.get('content') or item.get('summary') or item.get('description') or item.get('title', ''),
                                    "source": item.get('source') or item.get('author') or "虎扑",
                                    "url": item.get('url') or item.get('link') or item.get('href', ''),
                                    "category": self._map_category(category),
                                    "publish_time": self._parse_api_time(item.get('time') or item.get('publish_time') or item.get('date')),
                                    "metadata": {
                                        "source_site": "虎扑",
                                        "source_type": "API",
                                        "category_code": category,
                                        "api_data": item  # 保留原始API数据
                                    }
                                }
                                
                                # 智能识别类别
                                detected_category = self._detect_category_from_content(news['title'], news['content'])
                                if detected_category != '体育':
                                    news['category'] = detected_category
                                
                                if news['title']:
                                    news_list.append(news)
                        except Exception as e:
                            print(f"⚠️ 解析API新闻项失败: {str(e)}")
                            continue
                    
                    if news_list:
                        print(f"✓ 成功从虎扑API获取 {len(news_list)} 条新闻")
                        return news_list
                    else:
                        print(f"⚠️ API数据解析后为空")
                        return None
                        
                except ValueError as e:
                    # JSON解析错误
                    print(f"⚠️ API返回非JSON数据: {str(e)}")
                    print(f"   响应内容前100字符: {response.text[:100]}")
                    return None
            else:
                print(f"⚠️ 虎扑API请求失败，状态码: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⚠️ 虎扑API请求超时")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ 虎扑API连接失败: {str(e)}")
            return None
        except Exception as e:
            print(f"⚠️ 虎扑API调用失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_api_time(self, time_value) -> datetime:
        """解析API返回的时间"""
        if not time_value:
            return datetime.now()
        
        try:
            # 如果是时间戳
            if isinstance(time_value, (int, float)):
                return datetime.fromtimestamp(time_value)
            
            # 如果是字符串
            if isinstance(time_value, str):
                # 尝试多种时间格式
                time_formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d %H:%M',
                    '%Y/%m/%d %H:%M:%S',
                    '%Y/%m/%d %H:%M',
                ]
                
                for fmt in time_formats:
                    try:
                        return datetime.strptime(time_value, fmt)
                    except:
                        continue
                
                # 如果是时间戳字符串
                try:
                    return datetime.fromtimestamp(float(time_value))
                except:
                    pass
        except:
            pass
        
        return datetime.now()
    
    def get_news_list(self, category: str = "nba", limit: int = 10, use_api: bool = True) -> List[Dict]:
        """
        获取虎扑新闻列表（优先使用API，失败则使用网页爬取）
        
        Args:
            category: 新闻类别 (nba, soccer, cba, etc.)
            limit: 获取数量限制
            use_api: 是否优先使用API接口
        
        Returns:
            新闻列表
        """
        # 1. 优先尝试使用API接口
        if use_api:
            api_news = self.get_news_from_api(category, page=1, limit=limit)
            if api_news and len(api_news) > 0:
                return api_news[:limit]
            else:
                print("⚠️ 虎扑API不可用，降级到网页爬取")
        
        # 2. 备用方案：网页爬取
        try:
            # 虎扑新闻列表页URL
            url = f"{self.base_url}/{category}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                # 如果主站不可用，尝试移动端
                url = f"https://m.hupu.com/{category}"
                response = requests.get(url, headers=self.headers, timeout=10)
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            
            # 尝试多种选择器来匹配虎扑的新闻列表结构
            selectors = [
                'div.news-list-item',
                'div.list-item',
                'a.news-item',
                'div.news-item',
                'li.news-item',
                'div[class*="news"]',
                'a[href*="/news/"]',
                'a[href*="/article/"]'
            ]
            
            items = []
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    break
            
            # 如果找不到标准结构，尝试从链接中提取
            if not items:
                items = soup.find_all('a', href=re.compile(r'/(news|article|bbs)/'))
            
            for item in items[:limit]:
                try:
                    news = self._parse_news_item(item, category)
                    if news and news.get('title'):
                        news_list.append(news)
                except Exception as e:
                    print(f"解析新闻项失败: {str(e)}")
                    continue
            
            return news_list[:limit]
            
        except Exception as e:
            print(f"获取虎扑新闻列表失败: {str(e)}")
            return []
    
    def _parse_news_item(self, item, category: str) -> Optional[Dict]:
        """解析单个新闻项"""
        try:
            # 提取标题
            title_elem = item.find(['h3', 'h2', 'h1', 'a', 'span'], class_=re.compile(r'title|headline'))
            if not title_elem:
                title_elem = item.find('a')
            
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # 提取链接
            link_elem = item.find('a') if item.name != 'a' else item
            url = link_elem.get('href', '') if link_elem else ''
            if url and not url.startswith('http'):
                url = self.base_url + url
            
            # 提取摘要/内容
            content_elem = item.find(['p', 'div', 'span'], class_=re.compile(r'content|summary|desc|intro'))
            content = content_elem.get_text(strip=True) if content_elem else ""
            
            # 提取时间
            time_elem = item.find(['span', 'div', 'time'], class_=re.compile(r'time|date|publish'))
            publish_time = None
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                publish_time = self._parse_time(time_text)
            
            # 提取来源
            source_elem = item.find(['span', 'div'], class_=re.compile(r'source|author|from'))
            source = source_elem.get_text(strip=True) if source_elem else "虎扑"
            
            if not title:
                return None
            
            # 智能识别类别（基于内容而非URL路径）
            detected_category = self._detect_category_from_content(title, content or title)
            # 如果检测到的类别与URL类别不一致，使用检测到的类别
            mapped_category = self._map_category(category)
            # 优先使用智能检测的类别，如果检测不到才使用URL映射的类别
            final_category = detected_category if detected_category != '体育' else mapped_category
            
            return {
                "title": title,
                "content": content or title,  # 如果没有内容，使用标题
                "source": source,
                "url": url,
                "category": final_category,
                "publish_time": publish_time or datetime.now(),
                "metadata": {
                    "source_site": "虎扑",
                    "category_code": category,
                    "detected_category": detected_category,
                    "original_category": mapped_category
                }
            }
        except Exception as e:
            print(f"解析新闻项出错: {str(e)}")
            return None
    
    def _parse_time(self, time_text: str) -> Optional[datetime]:
        """解析时间文本"""
        try:
            # 处理相对时间（如"2小时前"）
            if '小时前' in time_text or '分钟前' in time_text or '天前' in time_text:
                return datetime.now()
            
            # 处理绝对时间
            time_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d %H:%M',
                '%m-%d %H:%M',
                '%m/%d %H:%M'
            ]
            
            for fmt in time_formats:
                try:
                    return datetime.strptime(time_text, fmt)
                except:
                    continue
            
            return datetime.now()
        except:
            return datetime.now()
    
    def _map_category(self, category_code: str) -> str:
        """映射类别代码到中文名称"""
        category_map = {
            'nba': 'NBA',
            'soccer': '足球',
            'cba': 'CBA',
            'bbs': '社区',
            'news': '综合',
            'basketball': '篮球',
            'football': '足球',
            'lol': '电竞',
            'esports': '电竞',
            'kog': '电竞'
        }
        return category_map.get(category_code, '体育')
    
    def _detect_category_from_content(self, title: str, content: str) -> str:
        """根据标题和内容智能识别新闻类别"""
        # 合并标题和内容，标题权重更高
        text = (title + " " + title + " " + content).lower()  # 标题重复一次增加权重
        
        # 电竞关键词（高优先级，避免误判）
        esports_keywords = [
            'lol', '英雄联盟', '王者荣耀', 'kpl', 'lpl', 'dota', 'csgo', 'pubg', 
            '和平精英', '穿越火线', 'cf', 'valorant', '无畏契约', 'apex', 
            'gala', 'tes', 'jdg', 'rng', 'edg', 'fpx', 'ig', 'we', 'omg', 'blg',
            '电竞', '职业联赛', 'moba', 'fps', 'rts', 'moba游戏', '女枪', 'bo3',
            '流言板', '一图流', 'jrs', '神评', 'wcba', 'wcba今日', 'wcba常规赛'
        ]
        
        # 足球关键词
        soccer_keywords = [
            '足球', '英超', '西甲', '意甲', '德甲', '法甲', '中超', '世界杯', 
            '欧洲杯', '欧冠', '亚冠', '国足', '男足', '女足', '梅西', 'c罗', 
            '内马尔', '姆巴佩', '哈兰德', '皇马', '巴萨', '曼联', '利物浦', 
            '切尔西', '曼城', '阿森纳', '拜仁', '多特', '尤文', 'ac米兰', 
            '国际米兰', '巴黎', '大巴黎', 'fifa', 'u23', 'u20', 'u17', '亚洲杯',
            '世预赛', '预选赛', '门将', '进球', '助攻', '点球', '任意球'
        ]
        
        # NBA关键词
        nba_keywords = [
            'nba', '湖人', '勇士', '凯尔特人', '热火', '篮网', '76人', 
            '雄鹿', '太阳', '独行侠', '快船', '掘金', '灰熊', '爵士', 
            '詹姆斯', '库里', '杜兰特', '字母哥', '东契奇', '约基奇', 
            '恩比德', '塔图姆', '布克', '莫兰特', '季后赛', '常规赛', 
            '总决赛', 'mvp', '得分王', '篮板王', '助攻王', '三分', '扣篮',
            'nba常规赛', 'nba季后赛', 'nba总决赛'
        ]
        
        # CBA关键词
        cba_keywords = [
            'cba', 'cba联赛', '中国男篮', '中国女篮', 'wcba', '易建联', 
            '郭艾伦', '周琦', '王哲林', '赵继伟', '广东宏远', '辽宁', 
            '北京首钢', '新疆', '广厦', '上海', '浙江', '深圳', '山东',
            'cba常规赛', 'cba季后赛', '杨珂菁', '准绝杀', '女篮'
        ]
        
        # 计算每个类别的匹配度（标题中的关键词权重更高）
        title_lower = title.lower()
        content_lower = (content or "").lower()
        
        def calculate_score(keywords, text, title_text):
            score = 0
            for keyword in keywords:
                # 标题中的关键词权重为2，内容中的权重为1
                if keyword in title_text:
                    score += 2
                if keyword in text:
                    score += 1
            return score
        
        esports_score = calculate_score(esports_keywords, content_lower, title_lower)
        soccer_score = calculate_score(soccer_keywords, content_lower, title_lower)
        nba_score = calculate_score(nba_keywords, content_lower, title_lower)
        cba_score = calculate_score(cba_keywords, content_lower, title_lower)
        
        # 返回得分最高的类别
        scores = {
            '电竞': esports_score,
            '足球': soccer_score,
            'NBA': nba_score,
            'CBA': cba_score
        }
        
        max_score = max(scores.values())
        if max_score >= 2:  # 至少需要2分（标题中有一个关键词）才认为匹配
            # 返回得分最高的类别
            for category, score in scores.items():
                if score == max_score:
                    return category
        
        # 如果没有匹配，返回默认类别
        return '体育'
    
    def get_hot_topics(self, category: str = "nba", limit: int = 10) -> List[Dict]:
        """
        获取虎扑热门话题/球迷热议
        
        Args:
            category: 类别
            limit: 数量限制
        
        Returns:
            热门话题列表
        """
        try:
            # 尝试使用API获取热门话题
            api_url = f"{self.api_base_url}/bbs/hot"
            params = {
                'category': category,
                'limit': limit
            }
            
            response = requests.get(api_url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    topics = []
                    
                    if isinstance(data, dict):
                        items = data.get('data') or data.get('list') or data.get('topics', [])
                    elif isinstance(data, list):
                        items = data
                    else:
                        items = []
                    
                    for item in items[:limit]:
                        if isinstance(item, dict):
                            topic = {
                                "title": item.get('title') or item.get('subject', ''),
                                "content": item.get('content') or item.get('summary', ''),
                                "source": "虎扑社区",
                                "url": item.get('url') or item.get('link', ''),
                                "category": self._map_category(category),
                                "publish_time": self._parse_api_time(item.get('time') or item.get('publish_time')),
                                "reply_count": item.get('reply_count', 0),
                                "view_count": item.get('view_count', 0),
                                "metadata": {
                                    "source_site": "虎扑",
                                    "source_type": "热门话题",
                                    "category_code": category
                                }
                            }
                            if topic['title']:
                                topics.append(topic)
                    
                    if topics:
                        print(f"✓ 从虎扑API获取 {len(topics)} 条热门话题")
                        return topics
                except:
                    pass
            
            # 如果API失败，返回空列表
            return []
        except Exception as e:
            print(f"⚠️ 获取热门话题失败: {str(e)}")
            return []
    
    def get_news_detail(self, url: str) -> Optional[Dict]:
        """获取新闻详情"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title_elem = soup.find(['h1', 'h2'], class_=re.compile(r'title|headline'))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # 提取正文内容
            content_selectors = [
                'div.article-content',
                'div.content',
                'div.post-content',
                'div[class*="content"]',
                'article'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 移除脚本和样式
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    content = content_elem.get_text(separator='\n', strip=True)
                    if content:
                        break
            
            return {
                "title": title,
                "content": content,
                "url": url
            }
        except Exception as e:
            print(f"获取新闻详情失败: {str(e)}")
            return None

def scrape_hupu_news(category: str = "nba", limit: int = 5, use_api: bool = True) -> List[Dict]:
    """
    采集虎扑新闻的便捷函数（优先使用API，失败则使用网页爬取）
    
    Args:
        category: 新闻类别
        limit: 获取数量
        use_api: 是否优先使用API接口
    
    Returns:
        新闻列表
    """
    scraper = HupuScraper()
    
    # 优先使用API获取指定类别
    if use_api:
        api_news = scraper.get_news_from_api(category, page=1, limit=limit)
        if api_news and len(api_news) >= limit * 0.6:  # 如果API获取到60%以上的数据，直接返回
            return api_news[:limit]
    
    # 如果API失败或数据不足，使用网页爬取
    # 尝试多个类别以确保获取足够的新闻
    categories = [category, "nba", "soccer", "cba", "news"]
    all_news = []
    
    for cat in categories:
        if len(all_news) >= limit:
            break
        
        news = scraper.get_news_list(cat, limit=limit, use_api=False)  # 网页爬取不使用API
        # 去重
        seen_titles = {item['title'] for item in all_news}
        for item in news:
            if item['title'] not in seen_titles:
                all_news.append(item)
                seen_titles.add(item['title'])
        
        time.sleep(0.5)  # 避免请求过快
    
    return all_news[:limit]
