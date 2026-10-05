"""
api/routes/apps.py
FastAPI REST routes for App Builder subsystem.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from api.schemas.app_schema import (
    AppCreateRequest,
    AppBriefUpdateRequest,
    AppProjectResponse,
    AppStatusResponse,
    AppListResponse
)
from api.services.app_service import get_app_service, AppService

router = APIRouter(prefix="/api/apps", tags=["App Builder"])


@router.post("", summary="Create App Project")
async def create_app(
    request: AppCreateRequest,
    service: AppService = Depends(get_app_service)
):
    """
    Creates a new APP project.
    If an active app project exists, the new app enters the queue.
    """
    try:
        data = service.create_app(
            name=request.name or "",
            description=request.description or "",
            initial_prompt=request.initial_prompt or ""
        )
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create app project: {str(e)}"
        )


@router.post("/{app_id}/brief", summary="Update/Merge App Brief")
async def update_brief(
    app_id: str,
    request: AppBriefUpdateRequest,
    service: AppService = Depends(get_app_service)
):
    """
    Merges new information, requirements, features, or references into an existing APP project brief.
    """
    updated = service.update_brief(
        app_id=app_id,
        text=request.text or "",
        name=request.name,
        description=request.description,
        features=request.features,
        requirements=request.requirements,
        ui_ux=request.ui_ux,
        authentication=request.authentication,
        database=request.database,
        apis=request.apis,
        platforms=request.platforms,
        references=request.references,
        images=request.images,
        design_preferences=request.design_preferences
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App project with ID '{app_id}' not found."
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content=updated)


@router.get("", response_model=AppListResponse, summary="List App Projects")
async def list_apps(service: AppService = Depends(get_app_service)):
    """
    Lists active app project, queue, and historical app projects.
    """
    try:
        return service.list_apps()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list app projects: {str(e)}"
        )


@router.get("/{app_id}", summary="Get App Project Details")
async def get_app(app_id: str, service: AppService = Depends(get_app_service)):
    """
    Retrieves full details of a specific APP project.
    """
    app = service.get_app(app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App project with ID '{app_id}' not found."
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content=app)


@router.get("/{app_id}/status", summary="Get App Project Status")
async def get_status(app_id: str, service: AppService = Depends(get_app_service)):
    """
    Retrieves concise status and progress of a specific APP project.
    """
    st = service.get_status(app_id)
    if not st:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App project with ID '{app_id}' not found."
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content=st)


@router.post("/{app_id}/queue", summary="Queue App Project")
async def queue_app(app_id: str, service: AppService = Depends(get_app_service)):
    """
    Transitions target app project status to QUEUED.
    """
    app = service.queue_app(app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App project with ID '{app_id}' not found."
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content=app)


@router.post("/{app_id}/start", summary="Start App Development")
async def start_app(app_id: str, service: AppService = Depends(get_app_service)):
    """
    Triggers development pipeline start for target APP project.
    """
    app = service.start_app(app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App project with ID '{app_id}' not found."
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content=app)
