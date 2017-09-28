"""
Settings for the micromasters app
"""
import os


def get_var(name, default=None):
    """Return the settings in a the environment"""
    return os.environ.get(name, default)


# locust settings
LOCUST_TASK_MIN_WAIT = int(get_var('LOCUST_TASK_MIN_WAIT', 1000))
LOCUST_TASK_MAX_WAIT = int(get_var('LOCUST_TASK_MAX_WAIT', 3000))

OPEN_DISCUSSIONS_JWT_SECRET = get_var('OPEN_DISCUSSIONS_JWT_SECRET', 'terribly_unsafe_default_jwt_secret_key')
OPEN_DISCUSSIONS_BASE_URL = get_var('OPEN_DISCUSSIONS_BASE_URL', 'http://mit-open.mit.local:8063')
OPEN_DISCUSSIONS_API_USERNAME = get_var('OPEN_DISCUSSIONS_API_USERNAME', 'mitodl')
