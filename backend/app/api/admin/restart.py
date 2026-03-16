import subprocess
import os
import sys
import signal
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.db.engine import get_db
from backend.app.db.models import User
from backend.app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin-restart"])


def restart_backend():
    """
    Restart the backend server gracefully.
    This function will:
    1. Kill the current backend process
    2. Restart it using the same command
    """
    try:
        # Get the current backend process PID
        backend_pid = os.getenv("BACKEND_PID")
        if backend_pid:
            # Send SIGTERM to gracefully shutdown
            try:
                os.kill(int(backend_pid), signal.SIGTERM)
            except ProcessLookupError:
                pass

            # Wait for process to terminate
            time.sleep(2)

        # Restart the backend
        # In development, use uvicorn command
        cmd = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "6400"]

        # In production, you might want to use gunicorn or other servers
        # This is development setup

        # Start backend in the background
        # For production, you'd use supervisor, systemd, etc.
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Save the new PID
        os.environ["BACKEND_PID"] = str(proc.pid)

        return {"status": "success", "message": "Backend restarting...", "new_pid": proc.pid}

    except Exception as e:
        return {"status": "error", "message": f"Failed to restart backend: {str(e)}"}


async def restart_frontend():
    """
    Restart the frontend server gracefully.
    """
    try:
        # Kill existing frontend process
        frontend_cmd = "pm2 restart gemini-frontend" if os.path.exists("/usr/local/bin/pm2") else None

        if frontend_cmd:
            subprocess.run(frontend_cmd, shell=True, capture_output=True)

        return {"status": "success", "message": "Frontend restarting..."}

    except Exception as e:
        return {"status": "error", "message": f"Failed to restart frontend: {str(e)}"}


@router.post("/restart")
async def restart_system(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    Restart the entire system (both frontend and backend).
    This endpoint will gracefully shutdown both services and restart them.
    """
    try:
        # Get current admin user
        result = await db.execute(select(User).where(User.email == admin.email))
        current_admin = result.scalar_one()

        # Restart backend
        backend_result = restart_backend()

        # Restart frontend
        frontend_result = restart_frontend()

        # Return combined results
        return {
            "status": "success",
            "message": "System restart initiated",
            "backend": backend_result,
            "frontend": frontend_result,
            "admin": current_admin.email,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to restart system: {str(e)}"
        )


@router.post("/restart/backend")
async def restart_backend_only(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    Restart only the backend server.
    """
    try:
        result = await db.execute(select(User).where(User.email == admin.email))
        current_admin = result.scalar_one()

        backend_result = restart_backend()

        return {
            "status": "success",
            "message": "Backend restarting...",
            "backend": backend_result,
            "admin": current_admin.email,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to restart backend: {str(e)}"
        )


@router.post("/restart/frontend")
async def restart_frontend_only(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    Restart only the frontend server.
    """
    try:
        result = await db.execute(select(User).where(User.email == admin.email))
        current_admin = result.scalar_one()

        frontend_result = restart_frontend()

        return {
            "status": "success",
            "message": "Frontend restarting...",
            "frontend": frontend_result,
            "admin": current_admin.email,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to restart frontend: {str(e)}"
        )
