import httpx


async def check_health_service(url: str) -> bool:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return True
            else:
                return False
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        return False
