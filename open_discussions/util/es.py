"""Elasticsearch utils"""
from collections import namedtuple
from enum import Enum

AGGREGATIONS = {
    "availability": {
        "aggs": {
            "runs": {
                "aggs": {
                    "courses": {
                        "reverse_nested": {}
                    }
                },
                "date_range": {
                    "field":   "runs.best_start_date",
                    "keyed":   False,
                    "missing": "1970-01-01T00:00:00Z",
                    "ranges":  [
                        {
                            "key": "availableNow",
                            "to":  "now"
                        },
                        {
                            "from": "now",
                            "key":  "nextWeek",
                            "to":   "now+7d"
                        },
                        {
                            "from": "now",
                            "key":  "nextMonth",
                            "to":   "now+1M"
                        },
                        {
                            "from": "now",
                            "key":  "next3Months",
                            "to":   "now+3M"
                        },
                        {
                            "from": "now",
                            "key":  "next6Months",
                            "to":   "now+6M"
                        },
                        {
                            "from": "now",
                            "key":  "nextYear",
                            "to":   "now+12M"
                        }
                    ]
                }
            }
        },
        "nested": {
            "path": "runs"
        }
    },
    "cost": {
        "aggs": {
            "prices": {
                "aggs": {
                    "courses": {
                        "reverse_nested": {}
                    }
                },
                "range": {
                    "field":   "runs.prices.price",
                    "keyed":   False,
                    "missing": 0,
                    "ranges":  [
                        {
                            "key": "free",
                            "to":  0.01
                        },
                        {
                            "from": 0.01,
                            "key":  "paid"
                        }
                    ]
                }
            }
        },
        "nested": {
            "path": "runs.prices"
        }
    },
    "offered_by": {
        "terms": {
            "field": "offered_by",
            "size":  10000
        }
    },
    "topics": {
        "terms": {
            "field": "topics",
            "size":  10000
        }
    },
    "type": {
        "terms": {
            "field": "object_type.keyword",
            "size":  10000
        }
    }
}

QueryParams = namedtuple("QueryParams", [
    "text",
    "types",
    "offered_by",
    "price"
])


class ResourceType(Enum):
    COURSE = "course"
    BOOTCAMP = "bootcamp"
    PROGRAM = "program"
    VIDEO = "video"
    USERLIST = "userlist"
    LEARNING_PATH = "learningpath"


class OfferedByType(Enum):
    MITX = "MITx"
    OCW = "OCW"
    XPRO = "xPro"
    BOOTCAMPS = "Bootcamps"
    MICROMASTERS = "MicroMasters"


class PriceType(Enum):
    FREE = "free"
    PAID = "paid"


# these field definitions are copy/paste from static/js/lib/search.js in the discussions project
COURSE_QUERY_FIELDS = [
  "title.english^3",
  "short_description.english^2",
  "full_description.english",
  "topics",
  "platform",
  "course_id",
  "coursenum^5",
  "offered_by"
]

PROGRAM_QUERY_FIELDS = [
  "title.english^3",
  "short_description.english^2",
  "topics",
  "platform",
]

VIDEO_QUERY_FIELDS = [
  "title.english^3",
  "short_description.english^2",
  "full_description.english",
  "transcript.english^2",
  "topics",
  "platform",
  "video_id",
  "offered_by"
]

BOOTCAMP_QUERY_FIELDS = [
  "title.english^3",
  "short_description.english^2",
  "full_description.english",
  "course_id",
  "coursenum^5",
  "offered_by"
]

RESOURCE_QUERY_NESTED_FIELDS = [
  "runs.year",
  "runs.semester",
  "runs.level",
  "runs.instructors^5"
]

LIST_QUERY_FIELDS = [
  "title.english",
  "short_description.english",
  "topics"
]

FIELDS_BY_TYPE = {
    ResourceType.COURSE: COURSE_QUERY_FIELDS,
    ResourceType.PROGRAM: PROGRAM_QUERY_FIELDS,
    ResourceType.BOOTCAMP: BOOTCAMP_QUERY_FIELDS,
    ResourceType.USERLIST: LIST_QUERY_FIELDS,
    ResourceType.LEARNING_PATH: LIST_QUERY_FIELDS,
    ResourceType.VIDEO: VIDEO_QUERY_FIELDS,
}

RUN_TYPES = [ResourceType.COURSE, ResourceType.BOOTCAMP, ResourceType.PROGRAM]

RESOURCE_QUERY_NESTED_FIELDS = [
  "runs.year",
  "runs.semester",
  "runs.level",
  "runs.instructors^5"
]

def generate_type_query(params, resource_type):
    q_type = "query_string" if "\"" in params.text else "multi_match"

    text_query = [{
          q_type: {
            "query":  params.text,
            "fields": FIELDS_BY_TYPE[resource_type]
          }
        },
    ]

    # these types have runs
    if resource_type in RUN_TYPES:
        text_query.append({
          "nested": {
            "path":  "runs",
            "query": {
              q_type: {
                "query": params.text,
                "fields": RESOURCE_QUERY_NESTED_FIELDS
              }
            }
          }
        })

    must = [{
      "term": {
        "object_type": resource_type.value
      }
    }, {
        "bool": {
          "should": text_query
        }
    }]

    if params.price and resource_type in RUN_TYPES:
        must.append({
            "bool": {
                "should": [{
                    "nested": {
                        "path": "runs.prices",
                        "query": {
                            "range": {
                                "runs.prices.price": {
                                    "from": 0.01
                                } if params.price == PriceType.PAID else {
                                    "to": 0.01
                                }
                            }
                        }
                    }
                }]
            }
        })

    if params.offered_by:
        must.append({
            "bool": {
                "should": [{
                    "term": {
                        "offered_by": offered_by.value
                    }
                } for offered_by in params.offered_by]
            }
        })


    return {
        "bool": {
            "filter": {
                "bool": {
                    "must": must
                }
            },
            "should": text_query
        }
    }


def generate_learn_query(params, offset, limit):
    return {
        "aggs": AGGREGATIONS,
        "query": {
            "bool": {
                "should": [generate_type_query(params, resource_type) for resource_type in params.types]
            }
        },
        "from": offset,
        "size": limit,
    }
