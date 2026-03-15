"""
Incident 的 Pydantic Schemas（数据校验与对外返回结构）
MVP-1 目标：
- 创建 incident
- 查询自己的 incident 列表/详情

注意：
- reporter_id 不由前端传入（由后端根据当前用户写入）
- status 先作为字符串对外返回即可（"OPEN"/"TRIAGED"/"CLOSED"）
"""
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IncidentCreateRequest(BaseModel):
    """创建 incident 的请求体（客户端能传的字段）"""
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None


class IncidentPublic(BaseModel):
    """对外返回的 incident 字段（MVP-1 先返回这些）"""
    id: uuid.UUID
    title: str
    description: str | None
    status: str
    reporter_id: uuid.UUID
    assignee_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)


class IncidentAssignRequest(BaseModel):
    """管理员指派 incident 用的请求体"""
    assignee_id: uuid.UUID


IncidentStatusLiteral = Literal["OPEN", "TRIAGED", "CLOSED"]


class IncidentStatusUpdateRequest(BaseModel):
    """更新状态的请求体（Step 7 只做这个）"""
    status: IncidentStatusLiteral