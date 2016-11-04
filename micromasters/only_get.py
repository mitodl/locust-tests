"""
locust file for micromasters
This tests does only gets requests (other than the post to login)
"""
import random
from urlparse import urljoin, urlparse

from locust import HttpLocust, TaskSet, task

import settings


class UserDashboardRefresh(TaskSet):
    """Dashboard refresh"""
    def on_start(self):
        """on_start is called before any task is scheduled """
        self.username = self.parent.username
        self.mm_csrftoken = self.parent.mm_csrftoken

    @task(1)
    def stop(self):
        """Return to the parent task"""
        self.interrupt()

    @task(10)
    def dashboard_reload(self):
        """
        Loads dashboard page and the backends
        """
        if not self.mm_csrftoken:
            self.interrupt()
        # load the page
        self.client.get('/dashboard/')
        self.client.get(
            '/api/v0/profiles/{}/'.format(self.username),
            name="'/api/v0/profiles/[username]/"
        )
        self.client.get('/api/v0/dashboard/')
        self.client.get('/api/v0/course_prices/')
        self.client.get('/api/v0/programs/')


class LearnerProfile(TaskSet):
    """
    User Profile view (/learners/<username>)
    """
    def on_start(self):
        """on_start is called before any task is scheduled """
        self.username = self.parent.username
        self.mm_csrftoken = self.parent.mm_csrftoken

    @task(1)
    def stop(self):
        """Return to the parent task"""
        self.interrupt()

    @task(10)
    def learner_profile(self):
        """
        Loads learner profile page and the backends
        """
        if not self.mm_csrftoken:
            self.interrupt()
        # load the page
        self.client.get('/learner/{}'.format(self.username),
                        name='/learner/[username]')
        self.client.get(
            '/api/v0/profiles/{}/'.format(self.username),
            name="'/api/v0/profiles/[username]/"
        )
        self.client.get('/api/v0/course_prices/')
        self.client.get('/api/v0/dashboard/')
        self.client.get('/api/v0/programs/')


class UserLogIn(TaskSet):
    """
    Section for login
    """
    tasks = {UserDashboardRefresh: 10, LearnerProfile: 10}

    def on_start(self):
        """on_start is called before any task is scheduled """
        self.username = self.parent.username
        self.mm_csrftoken = self.parent.mm_csrftoken

    @task
    def stop(self):
        """Return to the parent task"""
        self.interrupt()

    @task(5)
    def login(self):
        """
        Function to login an user on MicroMasters assuming she has an account on edX
        """
        # load the login form to get the token
        login_form = self.client.get(
            urljoin(settings.EDXORG_BASE_URL, '/login'),
            name='/login[edx login page]',
        )
        cookies = login_form.cookies.get_dict()
        # login edx
        self.client.post(
            urljoin(settings.EDXORG_BASE_URL, '/user_api/v1/account/login_session/'),
            data={
                "email": "{}@example.com".format(self.username),
                "password": "test",
                'remember': 'false'
            },
            headers={'Referer': urljoin(settings.EDXORG_BASE_URL, '/login'),
                     'X-CSRFToken': cookies.get('csrftoken')},
            name='/user_api/v1/account/login_session/[edx login form]'
        )
        # login micromasters
        self.client.get(
            '/login/edxorg/',
            name='/login/edxorg/[micromasters]'
        )
        # get the csrftoken
        parsed_url = urlparse(settings.MICROMASTERS_BASE_URL)
        domain = parsed_url.netloc
        if ':' in domain:
            domain = domain.split(':')[0]
        self.mm_csrftoken = self.client.cookies.get('csrftoken', domain=domain)

    @task
    def logout(self):
        """
        Logout from edx and micromasters
        """
        # logout edX
        self.client.get(
            urljoin(settings.EDXORG_BASE_URL, '/logout'),
            name='/logout[edx]'
        )
        # logout micromasters
        self.client.get(
            '/logout',
            name='/logout[micromasters]'
        )
        self.mm_csrftoken = None


class UserBehaviorGet(TaskSet):

    tasks = {UserLogIn: 10}
    username = None
    mm_csrftoken = None

    def on_start(self):
        """on_start is called before any task is scheduled """
        self.username = random.choice(settings.USERNAMES_IN_EDX)

    @task(2)
    def index_no_login(self):
        """Load index page without being logged in"""
        self.client.get("/")


class WebsiteUser(HttpLocust):
    host = settings.MICROMASTERS_BASE_URL
    task_set = UserBehaviorGet
    min_wait = settings.LOCUST_TASK_MIN_WAIT
    max_wait = settings.LOCUST_TASK_MAX_WAIT
