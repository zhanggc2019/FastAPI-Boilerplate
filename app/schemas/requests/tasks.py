from typing import Annotated
from pydantic import BaseModel, StringConstraints


class TaskCreate(BaseModel):
    title: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    description: Annotated[str, StringConstraints(min_length=1, max_length=1000)]