"""
locust file for open discussions
This test the full usage flow of open discussion
"""

import random

from faker import Faker
from locust import HttpLocust, TaskSet, task
from open_discussions_api.client import OpenDiscussionsApi
from open_discussions_api.users.client import UsersApi
from open_discussions_api.channels.client import ChannelsApi

import settings
import utils


fake = Faker()


class UsersChannel(TaskSet):

    tasks = {}

    def on_start(self):
        """on_start is called before any task is scheduled """
        self.moderators = set()
        self.contributors = set()
        self.posts = []
        self.comments = []
        self.channel = random.choice(self.parent.discussion_channels)
        self.api = self.parent.api

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

    @task
    def stop(self):
        """Return to the parent task"""
        self.interrupt()

    @task
    def add_moderator(self):
        """Adds a moderator to the channel"""
        username = random.choice(self.parent.discussion_usernames)
        self.api.channels.add_moderator(self.channel, username)
        self.api.channels.add_subscriber(self.channel, username)
        self.moderators.add(username)

    @task(10)
    def add_contributor(self):
        """Adds a contributor to the channel"""
        username = random.choice(self.parent.discussion_usernames)
        self.api.channels.add_contributor(self.channel, username)
        self.api.channels.add_subscriber(self.channel, username)
        self.contributors.add(username)

    @task(6)
    def remove_contributor(self):
        """Removes a contributor from the channel"""
        try:
            username = random.choice(list(self.contributors))
        except IndexError:
            # no contributors
            return
        self.api.channels.remove_subscriber(self.channel, username)
        self.api.channels.remove_contributor(self.channel, username)
        self.contributors.remove(username)

    @task(20)
    def load_frontpage(self):
        """Hits the frontpage api"""
        try:
            username = random.choice(list(self.contributors))
        except IndexError:
            # this means that this started before creating contributors
            return
        client = self.get_client_for(username)
        client.get('/api/v0/frontpage/')

    @task(20)
    def load_channels(self):
        """Hits the channel api"""
        try:
            username = random.choice(list(self.contributors))
        except IndexError:
            # this means that this started before creating contributors
            return
        client = self.get_client_for(username)
        client.get('/api/v0/channels/')

    @task(20)
    def load_channel_posts(self):
        """Hits the channel posts api"""
        try:
            username = random.choice(list(self.contributors))
        except IndexError:
            # this means that this started before creating contributors
            return
        client = self.get_client_for(username)
        client.get(
            '/api/v0/channels/{}/posts/'.format(self.channel),
            name='/api/v0/channels/[channel_name]/posts/',
        )

    @task(20)
    def load_post_comments(self):
        """Loads the post comments"""
        try:
            username = random.choice(list(self.contributors))
            post_id = random.choice(self.posts)
        except IndexError:
            # this means that this started before creating contributors or posts
            return
        client = self.get_client_for(username)
        client.get(
            '/api/v0/posts/{}/comments/'.format(post_id),
            name='/api/v0/posts/[post_id]/comments/',
        )

    @task(6)
    def create_post(self):
        """
        creates a post for an user
        """
        try:
            username = random.choice(list(self.contributors))
        except IndexError:
            # this means that this started before creating contributors
            return
        client = self.get_client_for(username)
        res = client.post(
            '/api/v0/channels/{}/posts/'.format(self.channel),
            json={
                'title': ' '.join(fake.paragraph().split(' ')[:2]),
                'text': fake.paragraph(),
                'upvoted': False,
            },
            name='/api/v0/channels/[channel_name]/posts/'
        )
        self.posts.append(res.json()['id'])

    @task(10)
    def create_comment(self):
        """
        Creates a comment for a post
        """
        try:
            username = random.choice(list(self.contributors))
            post_id = random.choice(self.posts)
        except IndexError:
            # this means that this started before creating contributors or posts
            return
        client = self.get_client_for(username)
        res = client.post(
            '/api/v0/posts/{}/comments/'.format(post_id),
            json={"text": fake.paragraph()},
            name='/api/v0/posts/[post_id]/comments/'
        )
        self.comments.append(res.json()['id'])

    @task(20)
    def upvote_post(self):
        """
        Upvotes a post
        """
        try:
            username = random.choice(list(self.contributors))
            post_id = random.choice(self.posts)
        except IndexError:
            # this means that this started before creating contributors or posts
            return
        client = self.get_client_for(username)
        client.patch(
            '/api/v0/posts/{}/'.format(post_id),
            json={"upvoted": True},
            name='/api/v0/posts/[post_id]/'
        )

    @task(20)
    def upvote_comment(self):
        """
        Upvotes a comment
        """
        try:
            username = random.choice(list(self.contributors))
            comment_id = random.choice(self.comments)
        except IndexError:
            # this means that this started before creating contributors or posts
            return
        client = self.get_client_for(username)
        client.patch(
            '/api/v0/comments/{}/'.format(comment_id),
            json={"upvoted": True},
            name='/api/v0/comments/[comment_id]/'
        )

    @task(20)
    def downvote_comment(self):
        """
        Downvotes a comment
        """
        try:
            username = random.choice(list(self.contributors))
            comment_id = random.choice(self.comments)
        except IndexError:
            # this means that this started before creating contributors or posts
            return
        client = self.get_client_for(username)
        client.patch(
            '/api/v0/comments/{}/'.format(comment_id),
            json={"downvoted": True},
            name='/api/v0/comments/[comment_id]/'
        )


class UserBehavior(TaskSet):

    tasks = {UsersChannel: 10}

    discussion_usernames_number = 100
    username = None

    def on_start(self):
        """on_start is called before any task is scheduled """
        self.discussion_usernames = []
        self.discussion_channels = []

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
        for _ in range(2):
            self.create_user()
        # create a couple of channels
        for _ in range(1):
            self.create_channel()

    def create_user(self):
        """creates an user in the system"""
        # limit the number of users
        if len(self.discussion_usernames) >= self.discussion_usernames_number:
            return
        res = self.api.users.create(name=fake.name(), image=None, image_small=None, image_medium=None)
        if res.status_code != 201:
            return
        self.discussion_usernames.append(res.json()['username'])

    def create_channel(self):
        """Create a channel"""
        name = '_'.join(fake.paragraph().split(' ')[:2]).lower()
        res = self.api.channels.create(
            title=' '.join(fake.paragraph().split(' ')[:2]),
            name=name,
            public_description=fake.paragraph(),
            channel_type='private',
        )
        if res.status_code != 201:
            return
        self.discussion_channels.append(name)

    @task
    def create_additional_channel(self):
        """New channels are occational"""
        self.create_channel()

    @task
    def create_additional_user(self):
        """New users are occational"""
        self.create_user()

    @task(5)
    def update_user(self):
        """updates an user in the system"""
        self.api.users.update(
            username=random.choice(self.discussion_usernames),
            name=fake.name(),
            image=None,
            image_small=None,
            image_medium=None
        )

    @task(10)
    def index(self):
        """Load index page"""
        self.client.get("/")


class WebsiteUser(HttpLocust):
    host = settings.OPEN_DISCUSSIONS_BASE_URL
    task_set = UserBehavior
    min_wait = settings.LOCUST_TASK_MIN_WAIT
    max_wait = settings.LOCUST_TASK_MAX_WAIT
