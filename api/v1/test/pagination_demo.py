"""
分页功能使用示例

演示如何使用项目中的分页组件实现标准的分页查询接口
"""

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.common.pagination import DependsPagination, PageData, create_links

# 创建分页演示路由
pagination_router = APIRouter()


# 模拟数据模型
class DemoItem(BaseModel):
    """演示数据模型"""
    
    id: int
    name: str
    description: str


# 响应模型
class DemoItemSchema(BaseModel):
    """演示项响应模型"""
    
    id: int
    name: str
    description: str


# 生成模拟数据
async def generate_demo_data() -> List[DemoItem]:
    """生成演示数据"""
    return [
        DemoItem(id=i, name=f"项目 {i}", description=f"这是第 {i} 个演示项目的描述")
        for i in range(1, 101)  # 生成100条测试数据
    ]


@pagination_router.get("/demo-pagination", summary="分页演示接口")
async def demo_pagination(
    pagination=DependsPagination,  # 自动注入分页参数
):
    """
    分页功能演示接口
    
    演示如何使用项目的分页组件实现标准的分页查询
    
    Args:
        pagination: 分页参数依赖注入
        
    Returns:
        包含分页数据的标准响应
    """
    # 生成模拟数据
    demo_items = await generate_demo_data()
    
    # 模拟数据库查询（实际项目中这里会是真实的数据库查询）
    # 这里使用简单的列表切片来模拟分页
    page = pagination.page
    size = pagination.size
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    
    # 获取当前页数据
    current_page_items = demo_items[start_idx:end_idx]
    
    # 转换为响应模型
    items = [
        DemoItemSchema(
            id=item.id,
            name=item.name,
            description=item.description
        )
        for item in current_page_items
    ]
    
    # 使用分页组件包装数据
    total_pages = (len(demo_items) + size - 1) // size
    links = create_links(
        first={"page": 1, "size": size},
        last={"page": total_pages, "size": size},
        next={"page": page + 1, "size": size} if page < total_pages else None,
        prev={"page": page - 1, "size": size} if page > 1 else None,
    ).model_dump()
    
    page_data = PageData(
        items=items,
        total=len(demo_items),
        page=page,
        size=size,
        total_pages=total_pages,
        links=links,
    )
    
    return {
        "code": 200,
        "msg": "分页查询成功",
        "data": page_data
    }


@pagination_router.get("/sqlalchemy-pagination", summary="SQLAlchemy 分页演示")
async def sqlalchemy_pagination_demo(
    pagination=DependsPagination,
):
    """
    SQLAlchemy 分页演示接口
    
    演示如何结合 SQLAlchemy 查询使用分页组件
    
    Args:
        pagination: 分页参数依赖注入
        
    Returns:
        包含分页数据的标准响应
    """
    # 在实际项目中，这里会是真实的 SQLAlchemy 查询
    # 例如：select_stmt = select(User).where(User.is_active == True)
    
    # 由于这是演示，我们使用模拟数据
    demo_items = await generate_demo_data()
    
    # 模拟 SQLAlchemy 查询结果
    # 在实际项目中，这里会使用 paginate 函数：
    # page_data = await paginate(db, select_stmt, params=pagination)
    
    # 模拟分页结果
    page = pagination.page
    size = pagination.size
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    
    current_page_items = demo_items[start_idx:end_idx]
    
    # 转换为响应模型
    items = [
        DemoItemSchema(
            id=item.id,
            name=item.name,
            description=item.description
        )
        for item in current_page_items
    ]
    
    # 手动构建分页数据（实际项目中会使用 paginate 函数自动处理）
    page_data = PageData(
        items=items,
        total=len(demo_items),
        page=page,
        size=size,
        total_pages=(len(demo_items) + size - 1) // size,
        links={
            "first": {"page": 1, "size": size},
            "last": {"page": (len(demo_items) + size - 1) // size, "size": size},
            "next": {"page": page + 1, "size": size} if page < (len(demo_items) + size - 1) // size else None,
            "prev": {"page": page - 1, "size": size} if page > 1 else None,
        }
    )
    
    return {
        "code": 200,
        "msg": "SQLAlchemy 分页查询成功",
        "data": page_data
    }


@pagination_router.get("/custom-pagination", summary="自定义分页参数演示")
async def custom_pagination_demo(
    page: int = 1,
    size: int = 10,
    search: str = None,
):
    """
    自定义分页参数演示接口
    
    演示如何手动处理分页参数，适用于需要额外过滤条件的场景
    
    Args:
        page: 页码（从1开始）
        size: 每页数量（1-200）
        search: 搜索关键词
        
    Returns:
        包含分页数据的标准响应
    """
    # 参数验证
    page = max(1, page)
    size = max(1, min(200, size))
    
    # 生成模拟数据
    demo_items = await generate_demo_data()
    
    # 如果有搜索条件，过滤数据
    if search:
        demo_items = [
            item for item in demo_items 
            if search.lower() in item.name.lower() or search.lower() in item.description.lower()
        ]
    
    # 计算分页
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    current_page_items = demo_items[start_idx:end_idx]
    
    # 转换为响应模型
    items = [
        DemoItemSchema(
            id=item.id,
            name=item.name,
            description=item.description
        )
        for item in current_page_items
    ]
    
    # 构建分页数据
    page_data = PageData(
        items=items,
        total=len(demo_items),
        page=page,
        size=size,
        total_pages=(len(demo_items) + size - 1) // size,
        links={
            "first": {"page": 1, "size": size},
            "last": {"page": (len(demo_items) + size - 1) // size, "size": size},
            "next": {"page": page + 1, "size": size} if page < (len(demo_items) + size - 1) // size else None,
            "prev": {"page": page - 1, "size": size} if page > 1 else None,
        }
    )
    
    return {
        "code": 200,
        "msg": f"自定义分页查询成功{'（含搜索）' if search else ''}",
        "data": page_data
    }