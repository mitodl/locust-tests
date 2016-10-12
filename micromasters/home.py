"""
locust file for micromasters
"""
from urlparse import urljoin, urlparse

from locust import HttpLocust, TaskSet, task

import settings


class UserLoginAndProfile(TaskSet):

    username = "zoe"
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

    def index_no_login(self):
        """Load index page without being logged in"""
        self.client.get("/")

    def profile_tabs(self):
        """
        Profile tabs
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
            'email_optin': False,
            'filled_out': False,
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

        # education
        # add the high school
        profile['education'].append(
            {
                "degree_name": "hs",
                "graduation_date": "1998-02-01",
                "field_of_study": None,
                "online_degree": False,
                "school_name": "School User",
                "school_city": "Lexington",
                "school_state_or_territory": "US-MA",
                "school_country": "US"
            }
        )
        self.client.patch(
            '/api/v0/profiles/{}/'.format(self.username),
            json=profile,
            headers={'X-CSRFToken': self.mm_csrftoken},
        )
        # add college
        profile['education'].append(
            {
                "degree_name": "m",
                "graduation_date": "2008-12-01",
                "field_of_study": "14.0903",
                "online_degree": False,
                "school_name": "University of Here",
                "school_city": "Bologna",
                "school_state_or_territory": "IT-BO",
                "school_country": "IT",
                "graduation_date_edit": {"year": "2008", "month": "12"}
            }
        )
        self.client.patch(
            '/api/v0/profiles/{}/'.format(self.username),
            json=profile,
            headers={'X-CSRFToken': self.mm_csrftoken},
        )

        # professional
        profile['work_history'].append(
            {
                "position": "Senior Software Engineer",
                "industry": "Computer Software",
                "company_name": "MIT",
                "start_date": "2000-01-01",
                "end_date": None,
                "city": "Cambridge",
                "country": "US",
                "state_or_territory": "US-MA",
                "start_date_edit": {"year": "2000", "month": "1"}
            }
        )
        self.client.patch(
            '/api/v0/profiles/{}/'.format(self.username),
            json=profile,
            headers={'X-CSRFToken': self.mm_csrftoken},
        )

        # I am done!
        profile.update({
            'email_optin': True,
            'filled_out': True,
        })

    @task
    def login_and_profile(self):
        """
        The actual task with the different operations in the right sequence to be run by locust
        """
        self.index_no_login()

        self.login()

        self.profile_tabs()

        self.logout()


class WebsiteUser(HttpLocust):
    host = settings.MICROMASTERS_BASE_URL
    task_set = UserLoginAndProfile
    min_wait = 1000
    max_wait = 3000
