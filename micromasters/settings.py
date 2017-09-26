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

MICROMASTERS_BASE_URL = get_var('MICROMASTERS_BASE_URL', 'http://192.168.99.100:8079')
MICROMASTERS_PROGRAM_ID = int(get_var('MICROMASTERS_PROGRAM_ID', 3))

EDXORG_BASE_URL = get_var('EDXORG_BASE_URL', 'http://192.168.33.10:8000')

usernames_in_edx_env = get_var('USERNAMES_IN_EDX')
USERNAMES_IN_EDX = []
# first try to load usernames from environment
if usernames_in_edx_env:
    USERNAMES_IN_EDX = [username.strip() for username in usernames_in_edx_env.split(',')]
# otherwise load from file
else:
    with open(os.path.join(os.path.dirname(__file__), 'usernames.txt')) as user_file:
        for username in user_file:
            USERNAMES_IN_EDX.append(username.strip())
