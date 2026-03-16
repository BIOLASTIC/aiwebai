import importlib.metadata
from fastapi import APIRouter, Depends
from backend.app.auth.dependencies import get_current_admin
from backend.app.db.models import User

router = APIRouter(prefix="/admin/packages", tags=["admin-packages"])

@router.get("/")
async def list_packages(admin: User = Depends(get_current_admin)):
    packages = [
        "gemini-webapi",
        "gemini-web-mcp-cli",
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "pydantic",
        "fastmcp",
    ]
    
    results = []
    for pkg in packages:
        try:
            version = importlib.metadata.version(pkg)
            results.append({"name": pkg, "version": version, "status": "installed"})
        except importlib.metadata.PackageNotFoundError:
            results.append({"name": pkg, "version": "Not Found", "status": "missing"})
            
    return results
