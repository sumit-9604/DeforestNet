from fastapi import APIRouter
from pydantic import BaseModel
from backend.config import state

router = APIRouter()

class SettingsUpdate(BaseModel):
    simulation_mode: bool

@router.get("/")
def get_settings():
    """Retrieve dynamic app settings"""
    return {
        "simulation_mode": state.simulation_mode
    }

@router.post("/")
def update_settings(payload: SettingsUpdate):
    """Update dynamic app settings at runtime"""
    state.simulation_mode = payload.simulation_mode
    return {
        "status": "success",
        "simulation_mode": state.simulation_mode
    }
