"""
locust file for micromasters
"""
from urlparse import urljoin, urlparse

from locust import HttpLocust, TaskSet, task

import settings


class UserNavigation(TaskSet):

    username = "gio"
    mm_csrftoken = None

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        pass

    def login(self):
        """
        Function to login an user on MicroMasters assuming she has an account on edX
        """
        # load the login form to get the token
        login_form = self.client.get(urljoin(settings.EDXORG_BASE_URL, 'login'))
        cookies = login_form.cookies.get_dict()
        # login edx
        self.client.post(
            urljoin(settings.EDXORG_BASE_URL, '/user_api/v1/account/login_session/'),
            data={"email": "{}@example.com".format(self.username), "password": "test", 'remember': 'false'},
            headers={'X-CSRFToken': cookies.get('csrftoken')},
        )
        # login micromasters
        self.client.get('/login/edxorg/')
        # get the csrftoken
        parsed_url = urlparse(settings.MICROMASTERS_BASE_URL)
        domain = parsed_url.netloc
        if ':' in domain:
            domain = domain.split(':')[0]
        self.mm_csrftoken = self.client.cookies.get('csrftoken', domain=domain)

    def logout(self):
        """
        Logout from edx and micromasters
        """
        # logout edX
        self.client.get(urljoin(settings.EDXORG_BASE_URL, 'logout'))
        # logout micromasters
        self.client.get('/logout')

    @task
    def index_no_login(self):
        """Load index page without being logged in"""
        self.client.get("/")

    @task
    def perform_login(self):
        """Load index page after being logged in"""
        self.login()

    @task
    def profile_tab_personal(self):
        """
        Profile personal tab
        """
        # loading part
        self.client.get('/profile/')
        resp_profile = self.client.get('/api/v0/profiles/{}/'.format(self.username))
        profile = resp_profile.json()
        self.client.get('/api/v0/dashboard/')
        self.client.get('/api/v0/course_prices/')
        self.client.get('/api/v0/enrolledprograms/')
        # submission part
        profile.update({
            'agreed_to_terms_of_service': True,
            'birth_country': 'IT',
            'city': 'Los Angeles',
            'country': 'US',
            'date_of_birth': '2000-01-12',
            'first_name': '{}'.format(self.username),
            'gender': 'f',
            'last_name': 'Example',
            'nationality': 'IT',
            'preferred_language': 'en',
            'preferred_name': '{} Preferred'.format(self.username),
            'state_or_territory': 'US-CA',
        })
        self.client.patch(
            '/api/v0/profiles/{}/'.format(self.username),
            json=profile,
            headers={'X-CSRFToken': self.mm_csrftoken},
        )
        self.client.post(
            '/api/v0/enrolledprograms/',
            json={'program_id': settings.MICROMASTERS_PROGRAM_ID},
            headers={'X-CSRFToken': self.mm_csrftoken},
        )
        self.client.get('/api/v0/dashboard/')
        self.client.get('/api/v0/course_prices/')

    @task
    def finish(self):
        """Just end the navigation"""
        self.logout()

    # @task(2)
    # def dashboard(self):
    #    self.client.get("/api/v0/dashboard/", headers=self.headers)


class WebsiteUser(HttpLocust):
    host = settings.MICROMASTERS_BASE_URL
    task_set = UserNavigation
    min_wait = 5000
    max_wait = 9000
