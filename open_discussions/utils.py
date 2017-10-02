"""
Utility functions
"""
from open_discussions_api.users.client import SUPPORTED_USER_ATTRIBUTES, quote


def patch_get_session(client):
    """
    Monkey patch the get session of OpenDiscussionApi to use the locust client
    """
    def patched_func(self):
        return client
    return patched_func


def patched_user_update(self, username, **profile):
    """
    Monkey patch the user update
    """
    if not profile:
        raise AttributeError("No fields provided to update")

    for key in profile:
        if key not in SUPPORTED_USER_ATTRIBUTES:
            raise AttributeError("Argument {} is not supported".format(key))

    return self.session.patch(
        self.get_url("/users/{}/".format(quote(username))),
        json=dict(profile=profile),
        name="/api/v0/users/[username]/",
    )


def patched_add_contributor(self, channel_name, username):
    """
    Monkey patch Add a contributor to a channel
    """

    return self.session.post(
        self.get_url("/channels/{channel_name}/contributors/".format(
            channel_name=quote(channel_name),
        )),
        json={"contributor_name": username},
        name="/api/v0/channels/[channel_name]/contributors/"
    )


def patched_remove_contributor(self, channel_name, username):
    """
    Monkey patch Remove a contributor from a channel
    """

    return self.session.delete(
        self.get_url("/channels/{channel_name}/contributors/{username}/".format(
            channel_name=quote(channel_name),
            username=quote(username),
        )),
        name="/api/v0/channels/[channel_name]/contributors/[username]/"
    )


def patched_add_moderator(self, channel_name, username):
    """
    Monkey patch Add a moderator to a channel
    """
    return self.session.post(
        self.get_url("/channels/{channel_name}/moderators/".format(
            channel_name=quote(channel_name)
        )),
        json={"moderator_name": username},
        name="/api/v0/channels/[channel_name]/moderators/"
    )


def patched_remove_moderator(self, channel_name, username):
    """
    Monkey patch Remove a moderator from a channel
    """
    return self.session.delete(
        self.get_url("/channels/{channel_name}/moderators/{username}/".format(
            channel_name=quote(channel_name),
            username=quote(username),
        )),
        name="/api/v0/channels/[channel_name]/moderators/[username]/"
    )


def patched_add_subscriber(self, channel_name, username):
    """
    Monkey patch Add a subscriber to a channel
    """
    return self.session.post(
        self.get_url("/channels/{channel_name}/subscribers/".format(
            channel_name=quote(channel_name),
        )),
        json={"subscriber_name": username},
        name="/api/v0/channels/[channel_name]/subscribers/"
    )


def patched_remove_subscriber(self, channel_name, username):
    """
    Monkey patch Remove a subscriber from a channel
    """
    return self.session.delete(
        self.get_url("/channels/{channel_name}/subscribers/{username}/".format(
            channel_name=quote(channel_name),
            username=quote(username),
        )),
        name="/api/v0/channels/[channel_name]/subscribers/[username]/"
    )
