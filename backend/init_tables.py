"""
初始化数据库表结构
如果表已存在但结构不同，需要先删除旧表（谨慎使用）
注意：metadata是SQLAlchemy保留字，已改为article_metadata
"""
from app.database import engine, Base
from app.models import User, NewsArticle, AnalysisReport, ChatRecord
import traceback

def init_tables():
    """初始化数据库表"""
    try:
        print("=" * 50)
        print("开始初始化数据库表...")
        print("=" * 50)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("\n✓ 数据库表创建成功！")
        
        # 验证表是否存在
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n当前数据库中的表: {len(tables)} 个")
        for table in tables:
            print(f"  - {table}")
        
        # 检查users表结构
        if 'users' in tables:
            print("\n✓ users表已存在")
            columns = inspector.get_columns('users')
            print("users表字段:")
            required_fields = ['id', 'username', 'email', 'hashed_password', 'is_active', 'created_at']
            for col in columns:
                field_name = col['name']
                field_type = str(col['type'])
                is_required = field_name in required_fields
                status = "✓" if is_required else " "
                print(f"  {status} {field_name}: {field_type}")
            
            # 检查是否有hashed_password字段
            column_names = [col['name'] for col in columns]
            if 'hashed_password' not in column_names:
                print("\n⚠ 警告: users表缺少hashed_password字段！")
                print("   需要更新表结构。可以运行以下SQL:")
                print("   ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255) NOT NULL;")
                print("   ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;")
            else:
                print("\n✓ users表结构完整")
        else:
            print("\n✗ users表不存在，将创建...")
            Base.metadata.create_all(bind=engine)
            print("✓ users表创建完成")
        
        print("\n" + "=" * 50)
        print("数据库初始化完成！")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    init_tables()
