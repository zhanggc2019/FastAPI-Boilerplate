from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field
from sqlalchemy import String, func
from sqlalchemy.dialects.mysql import JSON, LONGTEXT
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.orm import Mapped, mapped_column

from core.common.enums import StatusType
from core.common.model import TimeZone, id_key
from core.common.schema import SchemaBase
from core.common.timezone import timezone
from core.database import Base


class OperaLogSchemaBase(SchemaBase):
    """操作日志基础模型"""

    trace_id: str = Field(description='追踪 ID')
    username: str | None = Field(None, description='用户名')
    method: str = Field(description='请求方法')
    title: str = Field(description='操作标题')
    path: str = Field(description='请求路径')
    ip: str = Field(description='IP 地址')
    user_agent: str = Field(description='用户代理')
    os: str | None = Field(None, description='操作系统')
    browser: str | None = Field(None, description='浏览器')
    device: str | None = Field(None, description='设备')
    args: dict[str, Any] | None = Field(None, description='请求参数')
    status: StatusType = Field(description='状态')
    code: str = Field(description='状态码')
    msg: str | None = Field(None, description='消息')
    cost_time: float = Field(description='耗时')
    opera_time: datetime = Field(description='操作时间')


class CreateOperaLogParam(OperaLogSchemaBase):
    """创建操作日志参数"""


class UpdateOperaLogParam(OperaLogSchemaBase):
    """更新操作日志参数"""


class DeleteOperaLogParam(SchemaBase):
    """删除操作日志参数"""

    pks: list[int] = Field(description='操作日志 ID 列表')


class GetOperaLogDetail(OperaLogSchemaBase):
    """操作日志详情"""
    # from_attributes=True（在 Pydantic V1 中叫做 orm_mode=True）：
    # 这个配置允许 Pydantic 模型从任意的类实例（比如 SQLAlchemy 模型）
    # 中读取数据，而不仅仅是从字典中读取。这使得在 API 中可以很容易地将数据库模型转换为 Pydantic 模型。

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='日志 ID')
    created_time: datetime = Field(description='创建时间')


class OperaLog(Base):
    """操作日志表"""

    __tablename__ = 'opera_log'

    id: Mapped[id_key] = mapped_column()
    trace_id: Mapped[str] = mapped_column(String(32), comment='请求跟踪 ID')
    username: Mapped[str | None] = mapped_column(String(20), comment='用户名')
    method: Mapped[str] = mapped_column(String(20), comment='请求类型')
    title: Mapped[str] = mapped_column(String(255), comment='操作模块')
    path: Mapped[str] = mapped_column(String(500), comment='请求路径')
    ip: Mapped[str] = mapped_column(String(50), comment='IP地址')
    country: Mapped[str | None] = mapped_column(String(50), comment='国家')
    region: Mapped[str | None] = mapped_column(String(50), comment='地区')
    city: Mapped[str | None] = mapped_column(String(50), comment='城市')
    user_agent: Mapped[str] = mapped_column(LONGTEXT().with_variant(TEXT, 'postgresql'), comment='请求头')
    os: Mapped[str | None] = mapped_column(String(50), comment='操作系统')
    browser: Mapped[str | None] = mapped_column(String(50), comment='浏览器')
    device: Mapped[str | None] = mapped_column(String(50), comment='设备')
    args: Mapped[str | None] = mapped_column(JSON(), comment='请求参数')
    status: Mapped[int] = mapped_column(comment='操作状态（0异常 1正常）')
    code: Mapped[str] = mapped_column(String(20), insert_default='200', comment='操作状态码')
    msg: Mapped[str | None] = mapped_column(LONGTEXT().with_variant(TEXT, 'postgresql'), comment='提示消息')
    cost_time: Mapped[float] = mapped_column(insert_default=0.0, comment='请求耗时（ms）')
    opera_time: Mapped[datetime] = mapped_column(TimeZone, comment='操作时间')
    created_time: Mapped[datetime] = mapped_column(
        TimeZone,
        default=func.now(),
        comment='创建时间',
    )