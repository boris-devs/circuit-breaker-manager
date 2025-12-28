from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from repository.monitoring_repository import create_service, get_service
from schemas.monitoring import CreateServiceMonitoringSchema, CreateServiceMonitoringResponseSchema, \
    HealthServiceMonitoringSchema

router = APIRouter()


@router.post("/register_service/", response_model=CreateServiceMonitoringResponseSchema)
async def register_service(new_service: CreateServiceMonitoringSchema, db: AsyncSession = Depends(get_db)):
    created_service = await create_service(new_service, db)
    return created_service


@router.get("/health/{service_id}/", response_model=HealthServiceMonitoringSchema)
async def health_service(service_id: int, db: AsyncSession = Depends(get_db)):
    service = await get_service(service_id, db)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

