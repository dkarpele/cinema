import http
import logging

import requests
from requests.exceptions import Timeout, TooManyRedirects, RequestException
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

from config.components.services import AUTH

User = get_user_model()


class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        django_login_roles = {'admin', 'manager'}
        url = f"http://{AUTH['HOST_AUTH']}:{AUTH['PORT_AUTH']}" \
              f"/api/v1/auth/login-sso"
        payload = {'username': username, 'password': password}

        try:
            response = requests.post(url, json=payload)
        except (TooManyRedirects, RequestException, Timeout):
            logging.error('Auth service doesn\'t reply. Check immediately!')
            return None

        if response.status_code != http.HTTPStatus.OK:
            return None

        data = response.json()

        user, created = User.objects.get_or_create(id=data['id'],)
        user.email = data.get('email')
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.is_admin = False
        for django_role in django_login_roles:
            for user_role in data.get('roles'):
                if django_role in user_role:
                    user.is_admin = True
                    break
            else:
                continue
            break

        user.is_active = not data.get('disabled')
        user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
