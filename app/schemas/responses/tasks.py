from pydantic import Field

from app.schemas.base import BaseUUIDResponse


class TaskResponse(BaseUUIDResponse):
    title: str = Field(..., description="Task name", examples=["Task 1"])
    description: str = Field(..., description="Task description", examples=["Task 1 description"])
    completed: bool = Field(alias="is_completed", description="Task completed status")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Task 1",
                    "description": "Task 1 description",
                    "is_completed": False,
                    "uuid": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                }
            ]
        },
    }
