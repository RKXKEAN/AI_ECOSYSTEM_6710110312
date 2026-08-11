from label_studio_sdk import Client
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

def get_ls_client() -> Client:
    """
    Helper to construct a Label Studio client.
    """
    return Client(url=settings.LABEL_STUDIO_URL, api_key=settings.LABEL_STUDIO_API_KEY)

def list_projects() -> list:
    """
    List all projects from Label Studio.
    """
    try:
        ls = get_ls_client()
        ls.check_connection()
        projects = ls.get_projects()
        
        result = []
        for p in projects:
            task_count = p.params.get("task_number", 0)
            result.append({
                "id": p.id,
                "title": p.title,
                "task_count": task_count
            })
            
        logger.info(f"Successfully retrieved {len(result)} projects from Label Studio")
        return result
    except Exception as e:
        logger.error(f"Failed to list projects from Label Studio: {str(e)}")
        raise e

def list_tasks(project_id: int) -> list:
    """
    List all tasks for a specific project from Label Studio.
    """
    try:
        ls = get_ls_client()
        ls.check_connection()
        
        project = ls.get_project(project_id)
        tasks = project.get_tasks()
        
        result = []
        for t in tasks:
            result.append({
                "id": t.get("id"),
                "data": t.get("data", {}),
                "is_labeled": t.get("is_labeled", False)
            })
            
        logger.info(f"Successfully retrieved {len(result)} tasks for project #{project_id} from Label Studio")
        return result
    except Exception as e:
        logger.error(f"Failed to list tasks for project #{project_id} from Label Studio: {str(e)}")
        raise e
