from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket, WebSocketDisconnect

from database import get_db
from database.session_redis import get_redis_cache

from repository.monitoring_repository import create_service, get_service, circuit_breaker_trip
from schemas.monitoring import (CreateServiceMonitoringSchema, CreateServiceMonitoringResponseSchema,
                                HealthServiceMonitoringSchema)
from services.service_status_cache import IRedisServiceStatusCache
from services.websocket_manager import ws_manager

router = APIRouter()


@router.post("/register_service/", response_model=CreateServiceMonitoringResponseSchema)
async def register_service(new_service: CreateServiceMonitoringSchema, db: AsyncSession = Depends(get_db)):
    created_service = await create_service(new_service, db)
    return created_service


@router.get("/health/{service_id}/", response_model=HealthServiceMonitoringSchema)
async def health_service(
        service_id: int,
        db: AsyncSession = Depends(get_db),
        redis_cache: IRedisServiceStatusCache = Depends(get_redis_cache)
):
    cached_status = await redis_cache.get_service_status(service_id)
    if cached_status:
        return cached_status

    service = await get_service(service_id, db)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    await redis_cache.set_service_status(service_id=service_id, service_data=service)
    return service


@router.post("/circuit-breaker/{service_id}/trip/", response_model=HealthServiceMonitoringSchema)
async def trip_circuit_breaker(
        service_id: int,
        db: AsyncSession = Depends(get_db),
        redis_cache: IRedisServiceStatusCache = Depends(get_redis_cache)
):
    service = await get_service(service_id, db)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service_trip = await circuit_breaker_trip(service, db)
    await redis_cache.set_service_status(service_id=service_id, service_data=service_trip)
    return service_trip


@router.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    await websocket.send_text("Connected to websocket!")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
