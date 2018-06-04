"""
"""
import os
import json


def get_var(name, default=None):
    """Return the settings in a the environment"""
    return os.environ.get(name, default)


# locust settings
LOCUST_TASK_MIN_WAIT = int(get_var('LOCUST_TASK_MIN_WAIT', 1000))
LOCUST_TASK_MAX_WAIT = int(get_var('LOCUST_TASK_MAX_WAIT', 3000))

LMS_BASE_URL = get_var('LMS_BASE_URL', 'http://localhost:18000')
EDX_API_KEY = get_var('EDX_API_KEY', None)
EDX_TEST_USER_PW = 'edx'

usernames_in_edx_env = get_var('USERNAMES_IN_EDX')
USERNAMES_IN_EDX = set()
# first try to load usernames from environment
if usernames_in_edx_env:
    USERNAMES_IN_EDX = set([username.strip() for username in usernames_in_edx_env.split(',')])
# otherwise load from file
else:
    with open(os.path.join(os.path.dirname(__file__), 'usernames.txt')) as user_file:
        for username in user_file:
            USERNAMES_IN_EDX.add(username.strip())

course_data_env = get_var('RAPID_RESPONSE_COURSE_DATA')
RAPID_RESPONSE_COURSE_DATA = []
# first try to load course data JSON from environment
if course_data_env:
    RAPID_RESPONSE_COURSE_DATA = json.loads(course_data_env.strip())
else:
    with open(os.path.join(os.path.dirname(__file__), 'course_data.json')) as course_data_file:
        RAPID_RESPONSE_COURSE_DATA = json.load(course_data_file)
