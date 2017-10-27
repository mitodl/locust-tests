"""
Locust tests for PRAW
"""
import random
import uuid

from faker import Faker
from locust import HttpLocust, TaskSet, task

import settings
import channel_api


fake = Faker()


def make_api_client(username):
    return channel_api.Api(channel_api.FakeUser(username))


def recurse_comments(comment_tree):
    comments = list(comment_tree)
    for comment in comments:
        recurse_comments(comment.replies)


class UsersChannel(TaskSet):
    """Tasks for a user interacting with a subreddit"""
    tasks = {}

    def on_start(self):
        """on_start is called before any task is scheduled """
        self.moderators = set()
        self.contributors = set()
        self.posts = []
        self.comments = []
        self.channel = random.choice(self.parent.discussion_channels)

    @task
    def stop(self):
        """Return to the parent task"""
        self.interrupt()

    @task
    def add_moderator(self):
        """Adds a moderator to the channel"""
        username = random.choice(self.parent.discussion_usernames)
        api = make_api_client(settings.OPEN_DISCUSSIONS_API_USERNAME)
        api.add_moderator(username, self.channel)
        api.add_subscriber(username, self.channel)

        self.moderators.add(username)

    @task(10)
    def add_contributor(self):
        """Adds a contributor to the channel"""
        username = random.choice(self.parent.discussion_usernames)
        api = make_api_client(settings.OPEN_DISCUSSIONS_API_USERNAME)
        api.add_contributor(username, self.channel)
        api.add_subscriber(username, self.channel)

        self.contributors.add(username)

    @task(6)
    def remove_contributor(self):
        """Removes a contributor from the channel"""
        try:
            username = random.choice(list(self.contributors))
        except IndexError:
            # no contributors
            return
        api = make_api_client(settings.OPEN_DISCUSSIONS_API_USERNAME)
        api.remove_subscriber(username, self.channel)
        api.remove_contributor(username, self.channel)
        self.contributors.remove(username)

    @task(20)
    def load_frontpage(self):
        """Hits the frontpage api"""
        try:
            username = random.choice(list(self.contributors))
        except IndexError:
            # this means that this started before creating contributors
            return
        api = make_api_client(username)
        api.front_page()

    @task(20)
    def load_channel_posts(self):
        """Hits the channel posts api"""
        try:
            username = random.choice(list(self.contributors))
        except IndexError:
            # this means that this started before creating contributors
            return
        api = make_api_client(username)
        api.list_posts(self.channel)

    @task(20)
    def load_post_comments(self):
        """Loads the post comments"""
        try:
            username = random.choice(list(self.contributors))
            post_id = random.choice(self.posts)
        except IndexError:
            # this means that this started before creating contributors or posts
            return
        api = make_api_client(username)

        # TODO: how to group comment requests by name?
        comment_tree = api.list_comments(post_id)
        comment_tree.replace_more(limit=0)
        recurse_comments(comment_tree)

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
        api = make_api_client(username)
        post = api.create_post(
            channel_name=self.channel,
            title=' '.join(fake.paragraph().split(' ')[:2]),
            text=fake.paragraph(),
        )
        # Force HTTP GET request
        with channel_api.request_name("/comments/[post_id]/?limit=2048&sort=best&raw_json=1"):
            _ = post.title
        self.posts.append(post.id)

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
        api = make_api_client(username)
        comment = api.create_comment(
            text=fake.paragraph(),
            post_id=post_id,
        )
        self.comments.append(comment.id)

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
        api = make_api_client(username)
        post = api.get_post(post_id)
        # Force HTTP GET request
        with channel_api.request_name("/comments/[post_id]/?limit=2048&sort=best&raw_json=1"):
            already_upvoted = post.likes is True

        if not already_upvoted:
            post.upvote()

        # Due to the way the DRF view works we actually fetch API client twice
        api = make_api_client(username)
        post = api.get_post(post_id)

        with channel_api.request_name("/comments/[post_id]/?limit=2048&sort=best&raw_json=1"):
            # Force HTTP get request
            _ = post.title

    @task(5)
    def clear_vote_post(self):
        """Clear the vote on a post"""
        try:
            username = random.choice(list(self.contributors))
            post_id = random.choice(self.posts)
        except IndexError:
            # this means that this started before creating contributors or posts
            return
        api = make_api_client(username)
        post = api.get_post(post_id)
        # Force HTTP GET request
        with channel_api.request_name("/comments/[post_id]/?limit=2048&sort=best&raw_json=1"):
            # Technically this should never be False, just True or None, but just in case
            not_already_upvoted = post.likes is not True

        if not not_already_upvoted:
            post.clear_vote()

        # Due to the way the DRF view works we actually fetch API client twice
        api = make_api_client(username)
        post = api.get_post(post_id)

        with channel_api.request_name("/comments/[post_id]/?limit=2048&sort=best&raw_json=1"):
            # Force HTTP get request
            _ = post.title

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

        api = make_api_client(username)
        comment = api.get_comment(comment_id)
        # Force HTTP GET request
        with channel_api.request_name("/api/info?id=[comment_id]&raw_json=1"):
            likes = comment.likes

        if likes is not True:
            comment.upvote()

        # Due to the way the DRF view works we actually fetch API client twice
        api = make_api_client(username)
        comment = api.get_comment(comment_id)

        with channel_api.request_name("/api/info?id=[comment_id]&raw_json=1"):
            # Force HTTP get request
            _ = comment.text

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

        api = make_api_client(username)
        comment = api.get_comment(comment_id)
        # Force HTTP GET request
        with channel_api.request_name("/api/info?id=[comment_id]&raw_json=1"):
            likes = comment.likes

        if likes is not False:
            comment.downvote()

        # Due to the way the DRF view works we actually fetch API client twice
        api = make_api_client(username)
        comment = api.get_comment(comment_id)

        with channel_api.request_name("/api/info?id=[comment_id]&raw_json=1"):
            # Force HTTP get request
            _ = comment.text

    @task(5)
    def clear_vote_comment(self):
        """Clear the vote of a comment"""
        try:
            username = random.choice(list(self.contributors))
            comment_id = random.choice(self.comments)
        except IndexError:
            # this means that this started before creating contributors or posts
            return

        api = make_api_client(username)
        comment = api.get_comment(comment_id)
        # Force HTTP GET request
        with channel_api.request_name("/api/info?id=[comment_id]&raw_json=1"):
            likes = comment.likes

        if likes is not None:
            comment.clear_vote()

        # Due to the way the DRF view works we actually fetch API client twice
        api = make_api_client(username)
        comment = api.get_comment(comment_id)

        with channel_api.request_name("/api/info?id=[comment_id]&raw_json=1"):
            # Force HTTP get request
            _ = comment.text


class UserBehavior(TaskSet):
    """Tasks for testing reddit PRAW client"""
    tasks = {UsersChannel: 10}

    discussion_usernames_number = 100

    def on_start(self):
        """on_start is called before any task is scheduled """
        self.discussion_usernames = []
        self.discussion_channels = []

        channel_api.LOCUST_SESSION = self.client

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

        username = uuid.uuid4().hex
        channel_api.get_or_create_user(username)
        self.discussion_usernames.append(username)

    def create_channel(self):
        """Create a channel"""
        api = make_api_client(settings.OPEN_DISCUSSIONS_API_USERNAME)

        name = '_'.join(fake.paragraph().split(' ')[:2]).lower()

        api.create_channel(
            title=' '.join(fake.paragraph().split(' ')[:2]),
            name=name,
            public_description=fake.paragraph(),
            channel_type='private',
        )
        # access title to force an HTTP request
        _ = api.get_channel(name).title
        self.discussion_channels.append(name)

    @task
    def create_additional_channel(self):
        """New channels are occasional"""
        self.create_channel()

    @task
    def create_additional_user(self):
        """New users are occasional"""
        self.create_user()

    @task(5)
    def update_user(self):
        """updates an user in the system"""
        channel_api.get_or_create_user(random.choice(self.discussion_usernames))


class WebsiteUser(HttpLocust):
    host = settings.OPEN_DISCUSSIONS_BASE_URL
    task_set = UserBehavior
    min_wait = settings.LOCUST_TASK_MIN_WAIT
    max_wait = settings.LOCUST_TASK_MAX_WAIT
