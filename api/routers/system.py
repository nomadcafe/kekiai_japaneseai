"""
システム関連のルート
"""
from fastapi import APIRouter
from api.routers.jobs import jobs_db
from api.core.async_worker import async_worker

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/system/status")
async def get_system_status():
    """システム状態を取得"""
    running_tasks = async_worker.get_running_tasks()
    return {
        "running_tasks": running_tasks,
        "active_jobs": len([job for job in jobs_db.values() if job.status == "processing"]),
        "total_jobs": len(jobs_db),
        "worker_capacity": async_worker.max_workers
    }

