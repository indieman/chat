__author__ = 'indieman'

import datetime

from schematics.models import Model
from schematics.types import StringType, DateTimeType


class Message(Model):
    nickname = StringType(required=True, max_length=12, min_length=1)
    body = StringType(required=True, max_length=140, min_length=1)
    date = DateTimeType(default=datetime.datetime.now)