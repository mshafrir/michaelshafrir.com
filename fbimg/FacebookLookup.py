from google.appengine.ext import db
from google.appengine.api import users

from helper import *

import logging
logging.getLogger().setLevel(logging.DEBUG)


class FacebookLookup(db.Model):
    user = db.UserProperty(required=True, auto_current_user=True)
    image_url = db.LinkProperty(required=True)
    created = db.DateTimeProperty(required=True, auto_now=True)