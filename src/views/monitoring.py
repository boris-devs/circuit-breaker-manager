from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from repository.monitoring_repository import create_service_monitoring, get_service, check_health_service
from schemas.monitoring import CreateServiceMonitoringSchema, CreateServiceMonitoringResponseSchema

router = APIRouter()


@router.post("/service_monitoring/", response_model=CreateServiceMonitoringResponseSchema)
async def register_service_monitoring(new_service: CreateServiceMonitoringSchema, db: AsyncSession = Depends(get_db)):
    created_service = await create_service_monitoring(new_service, db)
    return created_service

@router.get("/health/{service_id}")
async def get_state_service(service_id: int, db: AsyncSession = Depends(get_db)):
    service = await get_service(service_id, db)
    if not service:
        return {"message": "Service not found"}
    healthy =  await check_health_service(service, db)
    return {"message": healthy}