"""
locust file for open discussions
This test focuses on the reads
"""

import random
import time
import uuid

from faker import Faker
from locust import HttpLocust, TaskSet, task
from open_discussions_api.client import OpenDiscussionsApi
from open_discussions_api.users.client import UsersApi
from open_discussions_api.channels.client import ChannelsApi

import settings
import utils

fake = Faker()


class UserBehavior(TaskSet):

    username = None

    def on_start(self):
        """on_start is called before any task is scheduled """
        self.usernames = []
        self.channels = []
        self.posts = []

        # monkey patch the library client
        OpenDiscussionsApi._get_session = utils.patch_get_session(self.client)
        UsersApi.update = utils.patched_user_update
        ChannelsApi.add_contributor = utils.patched_add_contributor
        ChannelsApi.remove_contributor = utils.patched_remove_contributor
        ChannelsApi.add_moderator = utils.patched_add_moderator
        ChannelsApi.remove_moderator = utils.patched_remove_moderator
        ChannelsApi.add_subscriber = utils.patched_add_subscriber
        ChannelsApi.remove_subscriber = utils.patched_remove_subscriber

        self.api = OpenDiscussionsApi(
            settings.OPEN_DISCUSSIONS_JWT_SECRET,
            settings.OPEN_DISCUSSIONS_BASE_URL,
            settings.OPEN_DISCUSSIONS_API_USERNAME,
            roles=['staff']
        )

        # create a some users to play with
        self.create_users()
        # create some channels
        self.create_channels()
        # add contributors
        self.add_contributors()
        self.add_posts()
        self.add_comments()
        time.sleep(settings.WAIT_BEFORE_LOAD_TEST_SECONDS)

    def get_client_for(self, username):
        """
        Creates an autenticated client
        """
        api = OpenDiscussionsApi(
            settings.OPEN_DISCUSSIONS_JWT_SECRET,
            settings.OPEN_DISCUSSIONS_BASE_URL,
            username,
        )
        return api._get_authenticated_session()

    def create_users(self):
        """creates users in the system"""
        for _ in range(settings.USERS_TO_CREATE):
            res = self.api.users.create(name=fake.name(), image=None, image_small=None, image_medium=None)
            time.sleep(settings.POST_WAIT_SECONDS)
            if res.status_code != 201:
                return
            self.usernames.append(res.json()['username'])

    def create_channels(self):
        """Create channels"""
        for _ in range(settings.CHANNELS_TO_CREATE):
            name = '_'.join(fake.paragraph().split(' ')[:2]).lower()
            res = self.api.channels.create(
                title=' '.join(fake.paragraph().split(' ')[:2]),
                name=name,
                public_description=fake.paragraph(),
                channel_type='private',
            )
            time.sleep(settings.POST_WAIT_SECONDS)
            if res.status_code != 201:
                return
            self.channels.append(name)
        # let's let reddit digest the posts
        time.sleep(5)

    def add_contributors(self):
        """Adds a contributor to the channel"""
        for channel in self.channels:
            for username in self.usernames:
                self.api.channels.add_contributor(channel, username)
                self.api.channels.add_subscriber(channel, username)
                time.sleep(settings.POST_WAIT_SECONDS)
        # let's let reddit digest the posts
        time.sleep(5)

    def add_posts(self):
        """
        creates posts
        """
        for channel in self.channels:
            for _ in range(settings.POSTS_PER_CHANNEL):
                try:
                    username = random.choice(list(self.usernames))
                except IndexError:
                    # this means that this started before creating contributors
                    return
                client = self.get_client_for(username)
                res = client.post(
                    '/api/v0/channels/{}/posts/'.format(channel),
                    json={
                        'title': ' '.join(fake.paragraph().split(' ')[:2]),
                        'text': fake.paragraph(),
                        'upvoted': False,
                    },
                    name='/api/v0/channels/[channel_name]/posts/'
                )
                self.posts.append(res.json()['id'])
                time.sleep(settings.POST_WAIT_SECONDS)
        # let's let reddit digest the posts
        time.sleep(5)

    def add_comments(self):
        """
        Creates comments for posts
        """
        for post_id in self.posts:
            for _ in range(settings.COMMENTS_PER_POST):
                try:
                    username = random.choice(list(self.usernames))
                except IndexError:
                    # this means that this started before creating contributors or posts
                    return
                client = self.get_client_for(username)
                client.post(
                    '/api/v0/posts/{}/comments/'.format(post_id),
                    json={"text": fake.paragraph()},
                    name='/api/v0/posts/[post_id]/comments/'
                )
                time.sleep(settings.POST_WAIT_SECONDS)
        # let's let reddit digest the posts
        time.sleep(5)

    @task
    def index(self):
        """Load index page"""
        self.client.get("/")

    @task
    def load_frontpage(self):
        """Hits the frontpage api"""
        try:
            username = random.choice(list(self.usernames))
        except IndexError:
            # this means that this started before creating contributors
            return
        client = self.get_client_for(username)
        client.get('/api/v0/frontpage/')

    @task
    def load_channels(self):
        """Hits the channel api"""
        try:
            username = random.choice(list(self.usernames))
        except IndexError:
            # this means that this started before creating contributors
            return
        client = self.get_client_for(username)
        client.get('/api/v0/channels/')

    @task
    def load_channel_posts(self):
        """Hits the channel posts api"""
        try:
            username = random.choice(list(self.usernames))
        except IndexError:
            # this means that this started before creating contributors
            return
        client = self.get_client_for(username)
        client.get(
            '/api/v0/channels/{}/posts/'.format(random.choice(list(self.channels))),
            name='/api/v0/channels/[channel_name]/posts/',
        )

    @task
    def load_post_comments(self):
        """Loads the post comments"""
        try:
            username = random.choice(list(self.usernames))
            post_id = random.choice(self.posts)
        except IndexError:
            # this means that this started before creating contributors or posts
            return
        client = self.get_client_for(username)
        client.get(
            '/api/v0/posts/{}/comments/'.format(post_id),
            name='/api/v0/posts/[post_id]/comments/',
        )


class WebsiteUser(HttpLocust):
    host = settings.OPEN_DISCUSSIONS_BASE_URL
    task_set = UserBehavior
    min_wait = settings.LOCUST_TASK_MIN_WAIT
    max_wait = settings.LOCUST_TASK_MAX_WAIT
