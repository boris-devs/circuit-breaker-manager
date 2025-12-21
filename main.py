from fastapi import FastAPI
from views import service_monitoring_router

app = FastAPI()

api_version_prefix = "/api/v1"

app.include_router(service_monitoring_router, prefix=api_version_prefix, tags=["service_monitoring"])


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
