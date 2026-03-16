import os
import psutil
import platform
from fastapi import APIRouter, Depends
from backend.app.auth.dependencies import get_current_admin
from backend.app.db.models import User
from datetime import datetime

router = APIRouter(prefix="/admin/health", tags=["admin-health"])

@router.get("/")
async def get_system_health(admin: User = Depends(get_current_admin)):
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy",
        "system": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        },
        "resources": {
            "cpu_usage_pct": cpu_usage,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_usage_pct": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_usage_pct": disk.percent,
        },
        "timestamp": datetime.utcnow().isoformat()
    }
