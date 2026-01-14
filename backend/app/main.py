from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import news, report, chat, dashboard, auth
from app.models import User, NewsArticle, AnalysisReport

# 创建数据库表
try:
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表创建成功")
    
    # 检查并修复users表结构
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        if 'users' in inspector.get_table_names():
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            
            # 修复hashed_password字段
            if 'hashed_password' not in column_names:
                print("⚠ 检测到users表缺少hashed_password字段，正在修复...")
                with engine.connect() as conn:
                    try:
                        conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255) NOT NULL DEFAULT ''"))
                        conn.commit()
                        print("✓ hashed_password字段已添加")
                    except Exception as e:
                        print(f"   添加hashed_password字段时: {str(e)}")
                        conn.rollback()
            
            # 修复is_active字段
            if 'is_active' not in column_names:
                print("⚠ 检测到users表缺少is_active字段，正在修复...")
                with engine.connect() as conn:
                    try:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                        conn.commit()
                        print("✓ is_active字段已添加")
                    except Exception as e:
                        print(f"   添加is_active字段时: {str(e)}")
                        conn.rollback()
            
            # 确保hashed_password不能为NULL
            if 'hashed_password' in column_names:
                with engine.connect() as conn:
                    try:
                        conn.execute(text("ALTER TABLE users MODIFY COLUMN hashed_password VARCHAR(255) NOT NULL"))
                        conn.commit()
                    except Exception as e:
                        pass  # 如果已经是NOT NULL，忽略错误
                        
            print("✓ users表结构检查完成")
        else:
            print("⚠ users表不存在，已自动创建")
    except Exception as e:
        print(f"⚠ 检查users表时出错: {str(e)}")
        print("   可以手动运行: python fix_users_table.py")
except Exception as e:
    print(f"✗ 数据库表创建失败: {str(e)}")
    import traceback
    traceback.print_exc()

app = FastAPI(
    title="体育日报智能分析平台",
    description="基于LangChain和FastAPI的体育新闻智能分析平台",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（认证路由不需要保护）
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(news.router)
app.include_router(report.router)
app.include_router(chat.router)

@app.get("/")
async def root():
    return {
        "message": "体育日报智能分析平台API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
