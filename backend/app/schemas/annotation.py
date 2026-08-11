from pydantic import BaseModel
from typing import Dict, Any, List

class ProjectInfo(BaseModel):
    id: int
    title: str
    task_count: int

class ProjectListResponse(BaseModel):
    projects: List[ProjectInfo]

class TaskInfo(BaseModel):
    id: int
    data: Dict[str, Any]
    is_labeled: bool

class TaskListResponse(BaseModel):
    project_id: int
    tasks: List[TaskInfo]
