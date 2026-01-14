# 体育日报智能分析平台

基于LangChain和FastAPI的体育新闻智能分析平台，使用MySQL 8.0作为数据库。

## 功能模块

1. **首页（仪表板）** - 显示统计数据
2. **体育日报生成界面** - 生成5条今日体育新闻
3. **分析报告界面** - 对今日体育新闻进行分析并生成报告
4. **智能助手对话模块** - 与AI助手进行体育相关对话

## 技术栈

### 后端
- FastAPI
- LangChain
- SQLAlchemy
- MySQL 8.0
- DashScope (通义千问)

### 前端
- React
- Ant Design
- Vite
- Axios

## 前置要求

1. Python 3.8+
2. Node.js 16+
3. MySQL 8.0
4. 网络连接（用于访问DashScope API）

## 快速开始

### 1. 环境准备

**如果项目路径包含中文字符（如 `D:\体育日报智能分析平台`），建议使用 Conda 来避免编码问题：**

```bash
# 创建conda环境
conda create -n sports_analysis python=3.10 -y

# 激活环境
conda activate sports_analysis

# 使用conda安装numpy（避免编码问题）
conda install numpy -y

# 安装其他依赖
cd backend
pip install -r requirements.txt
```

### 2. 数据库设置

#### 2.1 创建数据库

```bash
# 登录MySQL
mysql -u root -p

# 执行以下SQL创建数据库
CREATE DATABASE sports_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

#### 2.2 初始化数据库表

```bash
cd backend
conda activate sports_analysis  # 或你的conda环境
python init_tables.py
```

这个脚本会：
- 检查数据库连接
- 创建/更新所有表
- 验证表结构

### 3. 后端设置

#### 3.1 配置环境变量

在 `backend` 目录创建 `.env` 文件（可选，如果使用默认配置可以跳过）：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=sports_analysis
LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-79e462e4f6f04d37a10688706f0b5eae
LLM_MODEL=qwen3-max
```

#### 3.2 启动后端

```bash
conda activate sports_analysis
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 `http://localhost:8000` 启动

### 4. 前端设置

```bash
conda activate sports_analysis
cd frontend
npm install
npm run dev
```

前端将在 `http://localhost:3000` 启动

## 使用说明

### 1. 访问应用

打开浏览器访问 `http://localhost:3000`

### 2. 生成体育日报

1. 点击左侧菜单"体育日报"
2. 点击"生成今日日报"按钮
3. 系统将生成5条今日体育新闻

### 3. 生成分析报告

1. 点击左侧菜单"分析报告"
2. 点击"分析今日新闻"按钮
3. 系统将对今日新闻进行分析并生成报告（带进度条显示）

### 4. 使用智能助手

1. 点击左侧菜单"智能助手"
2. 在输入框中输入问题
3. 点击"发送"或按Enter键

## 数据库管理

### 初始化表结构

```bash
cd backend
python init_tables.py
```

### 验证表结构

在MySQL中执行：

```sql
USE sports_analysis;
DESCRIBE users;
DESCRIBE news_articles;
DESCRIBE analysis_reports;
DESCRIBE chat_records;
```

## Agent说明

### 1. 新闻采集与处理Agent (NewsCollectorAgent)
- 多源采集决策
- 智能内容清洗
- 异常处理和重试

### 2. 新闻分析与总结Agent (NewsAnalyzerAgent)
- 多维度总结
- 赛事数据挖掘
- 舆情分析

### 3. 用户交互Agent (ChatAgent)
- 自然语言指令执行
- 体育知识问答
- 个性化推荐

### 4. 多Agent协作系统 (MultiAgentCoordinator)
- 任务分解
- Agent协调
- 结果汇总

## API文档

运行后端后，访问 `http://localhost:8000/docs` 查看Swagger API文档。

## 常见问题

### 1. 数据库连接失败

- 检查MySQL服务是否启动
- 检查数据库用户名和密码是否正确
- 检查数据库是否已创建
- 运行 `python init_tables.py` 初始化表结构

### 2. API调用失败

- 检查网络连接
- 检查DashScope API Key是否正确
- 查看后端日志了解详细错误信息

### 3. 前端无法连接后端

- 检查后端是否正常运行
- 检查端口8000是否被占用
- 检查vite.config.js中的代理配置

### 4. 注册失败（500错误）

可能是数据库表结构不完整导致的：

1. 运行 `python init_tables.py` 初始化表
2. 检查users表是否有 `hashed_password` 和 `is_active` 字段
3. 查看后端日志了解详细错误信息

### 5. 数据库表结构错误

如果表结构完全错误，可以删除重建：

```sql
USE sports_analysis;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS news_articles;
DROP TABLE IF EXISTS analysis_reports;
DROP TABLE IF EXISTS chat_records;
```

然后重新运行 `python init_tables.py`

## 开发说明

### 修改新闻源

编辑 `backend/app/routers/news.py` 中的新闻源配置

### 修改Agent提示词

编辑对应的Agent文件：
- `backend/app/agents/news_collector.py` - 采集Agent
- `backend/app/agents/news_analyzer.py` - 分析Agent
- `backend/app/agents/chat_agent.py` - 对话Agent

### 添加新功能

1. 在后端 `backend/app/routers/` 添加新路由
2. 在前端 `frontend/src/pages/` 添加新页面
3. 在 `frontend/src/components/Sidebar.jsx` 添加菜单项

## 注意事项

1. 确保MySQL服务已启动
2. 确保网络可以访问DashScope API
3. 生产环境请修改CORS配置和安全密钥
4. 项目路径包含中文时建议使用Conda环境
