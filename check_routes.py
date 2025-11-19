from app.core.server import app

# 打印所有注册的路由
print("所有注册的路由:")
for route in app.routes:
    print(f"路径: {route.path}, 方法: {list(route.methods) if hasattr(route, 'methods') else 'N/A'}")