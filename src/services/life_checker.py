import httpx


async def check_availability(url: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                return True
            else:
                return False
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        return False
