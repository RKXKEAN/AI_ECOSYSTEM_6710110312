from fastapi import APIRouter, HTTPException
from app.services.annotation_service import list_projects, list_tasks
from app.schemas.annotation import ProjectListResponse, TaskListResponse, ProjectInfo, TaskInfo

router = APIRouter(prefix="/annotation", tags=["Annotation"])

@router.get("/projects", response_model=ProjectListResponse)
def get_projects():
    try:
        projects = list_projects()
        project_list = [ProjectInfo(**p) for p in projects]
        return ProjectListResponse(projects=project_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve projects: {str(e)}")

@router.get("/projects/{project_id}/tasks", response_model=TaskListResponse)
def get_project_tasks(project_id: int):
    try:
        tasks = list_tasks(project_id)
        task_list = [TaskInfo(**t) for t in tasks]
        return TaskListResponse(project_id=project_id, tasks=task_list)
    except Exception as e:
        if "404" in str(e) or "Not Found" in str(e) or "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Project #{project_id} not found")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks for project #{project_id}: {str(e)}")
