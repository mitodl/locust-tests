"""Tests for discussions learn search"""
import random

from locust import HttpLocust, TaskSet, task, between

from open_discussions.util.es import generate_learn_query, ResourceType, OfferedByType, QueryParams, PriceType

TEXTS = [
    "",  # no text, search all items
    "\"Quantum Mechanics\"",
    "\"Machine Learning\"",
    "Albedo",
    "Kinetic"
]

LIMIT = 6
SEARCH_URL = "/api/v0/search/"


class SearchPage(TaskSet):
    """
    TaskSet for interacting with the search page

    This operates by generating random tasks for a new search and subsequent
    search pages at a 1-to-10 ratio. If the pages are exhausted we initiate a new search.

    Search criteria (text and resource type) are randomly selected at the start of a new search.
    """

    def on_start(self):
        """Start the task"""
        # search() task must be the first one
        self.schedule_task(self.new_search)

    def _execute_search(self):
        """Execute a search request"""
        offset = self.page * LIMIT
        query = generate_learn_query(
            self.params,
            offset=offset,
            limit=LIMIT
        )
        # for now we ignore the response
        results = self.client.post(
            SEARCH_URL,
            json=query,
            name=(
                f"{SEARCH_URL}"
                f"?q={self.params.text}"
                f"&type={','.join([rt.value for rt in self.params.types])}"
                f"&o={','.join([o.value for o in self.params.offered_by])}"
                f"&p={self.page}"
            )
        ).json()
        # if we've run out of pages, queue a new search next
        if len(results["hits"]["hits"]) < LIMIT:
            self.schedule_task(self.new_search, first=True)

    @task(1)
    def new_search(self):
        """Start a new search"""
        self.page = 0
        # NOTE: sometimes the permutation generated here will return zero results
        #       because the facet combinations don't make sense
        #       that's a bit too complicated to codify so we don't worry about it for now
        self.params = QueryParams(
            # text search
            random.choice(TEXTS),
            # learning resource types 1..n
            random.sample(
                list(ResourceType),
                random.randint(1, len(ResourceType))
            ),
            # offered by 0..n
            random.sample(
                list(OfferedByType),
                random.randint(0, len(OfferedByType))
            ),
            # price 0..1
            random.sample(
                list(PriceType),
                random.randint(0, 1)
            )
        )
        self._execute_search()

    # generally this will be run 10x as often as a new search
    @task(10)
    def next_page(self):
        """Load the next page of search results"""
        self.page += 1
        self._execute_search()


class AnonymousUser(HttpLocust):
    task_set = SearchPage
    wait_time = between(1, 10)
