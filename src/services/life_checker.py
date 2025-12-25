import httpx


async def check_health_service(url: str) -> bool:
    if not url.startswith("http://") or not url.startswith("https://"):
        url = "http://" + url
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                return True
            else:
                return False
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        return False
