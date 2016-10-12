"""
Settings for the micromasters app
"""
import os


def get_var(name, default):
    """Return the settings in a the environment"""
    return os.environ.get(name, default)

EDXORG_BASE_URL = get_var('EDXORG_BASE_URL', 'http://192.168.33.10:8000')

MICROMASTERS_BASE_URL = get_var('MICROMASTERS_BASE_URL', 'http://192.168.99.100:8079')

MICROMASTERS_PROGRAM_ID = int(get_var('MICROMASTERS_PROGRAM_ID', 3))

USERNAMES_IN_EDX = ('zoe', 'emma')
