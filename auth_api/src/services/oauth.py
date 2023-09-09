import aiohttp
import logging
import random
import string

from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse

from core.config import yandex_config, google_config, settings
from models.users import User
from schemas.users import UserSignUpOAuth
from services.users import register_oauth_user


class OAuth:
    """
    Класс для работы с OAuth.
    """

    def __init__(self, code: int | str = None):
        self.client_id: str = ''
        self.secret: str = ''
        self.code: int = code
        self.authorization_url: str = ''
        self.url_oauth: str = ''
        self.url_userdata: str = ''
        self.data_oauth: dict = {}
        password: str = ''.join(
            random.choice(string.ascii_lowercase) +
            random.choice(string.ascii_uppercase) +
            random.choice(string.digits) for _ in range(10))
        self.password: str = ''.join(random.sample(password, len(password)))

    def authorize(self):
        """
        Редирект на авторизацию в сервере авторизации.
        """
        response = RedirectResponse(url=self.authorization_url)
        return response

    async def get_tokens(self):
        """
        Получить токены от сервера авторизации по коду.
        :return: {"token_type": "bearer",
                  "access_token": "AQAAAACy1C6ZAAAAfa6vDLuItEy8pg-iIpnDxIs",
                  "expires_in": 124234123534,
                  "refresh_token": "1:GN686QVt0mmakDd9:A4pYuW9LG...",
                  "scope": "login:info login:email login:avatar"
                  }
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url_oauth,
                                    data=self.data_oauth) as response:
                try:
                    res = await response.json()
                    if res['error']:
                        logging.error('Fail to receive tokens.')
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"{res}",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                except KeyError:
                    return res

    async def get_user_info(self) -> dict[str, str]:
        """
        Получить информацию о юзере по токенам.
        :return: Данные юзера
        """
        tokens = await self.get_tokens()
        headers = {
                    'Authorization': f'OAuth {tokens["access_token"]}',
                  }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(self.url_userdata) as response:
                try:
                    res = await response.json()
                    return res
                except KeyError:
                    logging.error('Fetching user data failed')

    async def register(self, user_info: dict, db) -> User:
        pass


class GoogleOAuth(OAuth):
    """Класс для работы с авторизацией google."""

    def __init__(self, code):
        super().__init__(code)
        self.client_id = google_config.client_id
        self.secret = google_config.secret
        self.redirect_url = 'http://127.0.0.1:80/api/v1/oauth/redirect/google'
        self.scope = 'email profile'
        self.authorization_url = f'https://accounts.google.com/o/oauth2/auth' \
                                 f'?response_type=code' \
                                 f'&client_id={self.client_id}' \
                                 f'&redirect_uri={self.redirect_url}' \
                                 f'&scope={self.scope}' \
                                 f'&state=google' \
                                 f'&access_type=offline'

        self.url_oauth = 'https://oauth2.googleapis.com/token'
        self.url_userdata = 'https://www.googleapis.com/userinfo/v2/me'
        self.data_oauth = {'client_id': self.client_id,
                           'client_secret': self.secret,
                           'code': self.code,
                           'redirect_uri': self.redirect_url,
                           'grant_type': 'authorization_code'
                           }

    async def register(self, user_info: dict, db) -> User:
        user = await register_oauth_user(
            UserSignUpOAuth(email=user_info['email'],
                            first_name=user_info['given_name'],
                            last_name=user_info['family_name'],
                            password=self.password,
                            social_id=user_info['id'],
                            social_name='google'),
            db)
        return user


class YandexOAuth(OAuth):
    """Класс для работы с авторизацией яндекса."""

    def __init__(self, code):
        super().__init__(code)
        self.client_id = yandex_config.client_id
        self.secret = yandex_config.secret
        self.scope = 'login:email login:info'
        self.authorization_url = f'https://oauth.yandex.ru/authorize' \
                                 f'?response_type=code' \
                                 f'&client_id={self.client_id}' \
                                 f'&display=popup' \
                                 f'&scope={self.scope}' \
                                 f'&state=yandex'
        self.url_oauth = 'https://oauth.yandex.ru/token'
        self.url_userdata = 'https://login.yandex.ru/info?'
        self.data_oauth = {'grant_type': 'authorization_code',
                           'client_id': self.client_id,
                           'client_secret': self.secret,
                           'code': self.code}

    async def register(self, user_info: dict, db) -> User:
        user = await register_oauth_user(
            UserSignUpOAuth(email=user_info['default_email'],
                            first_name=user_info['first_name'],
                            last_name=user_info['last_name'],
                            password=self.password,
                            social_id=user_info['id'],
                            social_name='yandex'
                            ),
            db)
        return user


def get_service_instance(service_name: str, code: int | str = None):
    if service_name == 'yandex':
        return YandexOAuth(code)
    if service_name == 'google':
        return GoogleOAuth(code)
