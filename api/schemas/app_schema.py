"""
api/schemas/app_schema.py
Pydantic schemas for App Builder REST API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class AppCreateRequest(BaseModel):
    name: Optional[str] = Field(default="", description="Optional initial app name")
    description: Optional[str] = Field(default="", description="Optional app description")
    initial_prompt: Optional[str] = Field(default="", description="Optional natural language request prompt")
    technology: Optional[Dict[str, str]] = Field(
        default_factory=lambda: {"frontend": "Flutter", "backend": "Node.js"},
        description="Target tech stack"
    )


class AppBriefUpdateRequest(BaseModel):
    text: Optional[str] = Field(default="", description="Natural language text containing app requirements")
    name: Optional[str] = Field(default=None, description="App name")
    description: Optional[str] = Field(default=None, description="App description")
    features: Optional[List[str]] = Field(default=None, description="List of features")
    requirements: Optional[List[str]] = Field(default=None, description="Functional requirements")
    ui_ux: Optional[Dict[str, Any]] = Field(default=None, description="UI/UX preferences")
    authentication: Optional[str] = Field(default=None, description="Authentication mechanism")
    database: Optional[str] = Field(default=None, description="Database technology")
    apis: Optional[List[str]] = Field(default=None, description="External APIs")
    platforms: Optional[List[str]] = Field(default=None, description="Target platforms (e.g. Android)")
    references: Optional[List[Dict[str, Any]]] = Field(default=None, description="Reference metadata/links")
    images: Optional[List[str]] = Field(default=None, description="Image paths or URLs")
    design_preferences: Optional[List[str]] = Field(default=None, description="Design preferences")


class AppProjectResponse(BaseModel):
    success: bool = True
    app_id: str
    project_id: str
    type: str = "APP"
    name: str
    description: str
    status: str
    progress: int
    technology: Dict[str, str]
    brief: Dict[str, Any]
    created_at: str
    updated_at: str


class AppStatusResponse(BaseModel):
    success: bool = True
    app_id: str
    name: str
    status: str
    progress: int
    updated_at: str


class AppListResponse(BaseModel):
    success: bool = True
    total: int
    active_app: Optional[Dict[str, Any]] = None
    queue: List[Dict[str, Any]] = Field(default_factory=list)
    apps: List[Dict[str, Any]] = Field(default_factory=list)
