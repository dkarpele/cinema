import aiohttp
from fastapi import HTTPException
from starlette import status as st


async def get_api_helper(url: str,
                         header: dict | None = None) -> dict:
    try:
        async with aiohttp.ClientSession(headers=header) as session:
            async with session.get(url=url) as response:
                detail = await response.json()
                status_code = response.status
                if   status_code != st.HTTP_200_OK:
                    raise HTTPException(
                        status_code=status_code,
                        detail=detail['detail'],
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return detail
    except aiohttp.ServerTimeoutError as err:
        raise HTTPException(status_code=st.HTTP_504_GATEWAY_TIMEOUT,
                            detail=err.strerror)
    except aiohttp.TooManyRedirects as err:
        raise HTTPException(status_code=st.HTTP_502_BAD_GATEWAY,
                            detail=err.strerror)
    except aiohttp.ClientError as err:
        raise HTTPException(status_code=st.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=err.strerror)
