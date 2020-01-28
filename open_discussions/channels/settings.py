"""
Settings for the open_discussions locust tests
"""
import os


def get_var(name, default=None):
    """Return the settings in a the environment"""
    value = os.environ.get(name, default)
    if value is None:
        raise Exception("Missing value for {}".format(name))
    return value


# locust settings
LOCUST_TASK_MIN_WAIT = int(get_var('LOCUST_TASK_MIN_WAIT', 500))
LOCUST_TASK_MAX_WAIT = int(get_var('LOCUST_TASK_MAX_WAIT', 1500))

OPEN_DISCUSSIONS_JWT_SECRET = get_var('OPEN_DISCUSSIONS_JWT_SECRET', 'terribly_unsafe_default_jwt_secret_key')
OPEN_DISCUSSIONS_BASE_URL = get_var('OPEN_DISCUSSIONS_BASE_URL', 'http://mit-open.mit.local:8063')
OPEN_DISCUSSIONS_API_USERNAME = get_var('OPEN_DISCUSSIONS_API_USERNAME', 'mitodl')

POST_WAIT_SECONDS = int(get_var('OPEN_DISCUSSIONS_POST_WAIT_SECONDS', 0.5))
WAIT_BEFORE_LOAD_TEST_SECONDS = int(get_var('OPEN_DISCUSSIONS_WAIT_BEFORE_LOAD_TEST_SECONDS', 10))
USERS_TO_CREATE = int(get_var('OPEN_DISCUSSIONS_USERS_TO_CREATE', 15))
CHANNELS_TO_CREATE = int(get_var('OPEN_DISCUSSIONS_CHANNELS_TO_CREATE', 4))
POSTS_PER_CHANNEL = int(get_var('OPEN_DISCUSSIONS_POSTS_PER_CHANNEL', 10))
COMMENTS_PER_POST = int(get_var('OPEN_DISCUSSIONS_POSTS_PER_CHANNEL', 20))

OPEN_DISCUSSIONS_REDDIT_CLIENT_ID = get_var('OPEN_DISCUSSIONS_REDDIT_CLIENT_ID')
OPEN_DISCUSSIONS_REDDIT_SECRET = get_var('OPEN_DISCUSSIONS_REDDIT_SECRET')
OPEN_DISCUSSIONS_REDDIT_ACCESS_TOKEN = get_var('OPEN_DISCUSSIONS_REDDIT_ACCESS_TOKEN')
OPEN_DISCUSSIONS_REDDIT_URL = get_var('OPEN_DISCUSSIONS_REDDIT_URL')

OPEN_DISCUSSIONS_CHANNEL_POST_LIMIT = int(get_var('OPEN_DISCUSSIONS_CHANNEL_POST_LIMIT', 25))


# base settings to start a base django app
SECRET_KEY = 'fake'
VERSION = '9.9.99'
