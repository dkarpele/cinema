import os

AUTH = {
        'HOST_AUTH': os.environ.get('HOST_AUTH', '127.0.0.1'),
        'PORT_AUTH': os.environ.get('PORT_AUTH', 80),
}
