import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from langchain.tools import tool

@tool
def requests_get_tool(url: str, headers: Optional[Dict] = None) -> str:
    """使用requests获取网页内容，支持重试机制。输入：url字符串和可选的headers字典。返回：网页HTML内容。如果失败，返回错误信息。"""
    import time
    
    # 更完整的浏览器headers，模拟真实浏览器访问
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    if headers:
        default_headers.update(headers)
    
    # 重试机制：最多尝试3次
    max_retries = 3
    retry_delay = 2  # 重试间隔（秒）
    
    for attempt in range(max_retries):
        try:
            # 增加超时时间到30秒
            response = requests.get(
                url, 
                headers=default_headers, 
                timeout=30,
                allow_redirects=True,
                verify=True  # 验证SSL证书
            )
            response.raise_for_status()
            
            # 尝试多种编码方式
            if response.encoding:
                response.encoding = response.apparent_encoding or response.encoding or 'utf-8'
            else:
                response.encoding = 'utf-8'
            
            # 检查内容长度，如果太短可能是错误页面
            content = response.text
            if len(content) < 100:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return f"警告：获取到的内容过短（{len(content)}字符），可能不是有效页面。URL: {url}"
            
            return content
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"⚠️ 请求超时，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            return f"错误：访问 {url} 超时（30秒）。可能是网络问题或网站响应慢。"
            
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                print(f"⚠️ 连接错误，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            return f"错误：无法连接到 {url}。连接被中断或拒绝。详细错误：{str(e)}"
            
        except requests.exceptions.HTTPError as e:
            status_code = response.status_code if 'response' in locals() else '未知'
            return f"错误：HTTP错误 {status_code} 访问 {url}。服务器返回：{str(e)}"
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ 请求失败，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            return f"错误：访问 {url} 时发生未知错误：{str(e)}"
    
    return f"错误：访问 {url} 失败，已重试 {max_retries} 次。"

@tool
def beautifulsoup_parse_tool(html: str, selector: str) -> str:
    """使用BeautifulSoup解析HTML并提取内容。输入：html字符串和CSS选择器。返回：提取的文本内容。"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        elements = soup.select(selector)
        return '\n'.join([elem.get_text(strip=True) for elem in elements if elem.get_text(strip=True)])
    except Exception as e:
        return f"Error parsing HTML: {str(e)}"

@tool
def check_url_accessible(url: str) -> bool:
    """检查URL是否可访问。输入：url字符串。返回：True如果可访问，False如果不可访问。"""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except:
        try:
            response = requests.get(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
