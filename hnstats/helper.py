from __future__ import division

import os

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db

import logging
logging.getLogger().setLevel(logging.DEBUG)


def init_template_values(user=None):
    template_values = {}
    
    if user:
        template_values["user"] = user
        template_values["user_is_admin"] = users.is_current_user_admin()
        template_values["user_logout_url"] = users.create_logout_url("/").replace("&", "&amp;")

    else:
        template_values["user_login_url"] = users.create_login_url("/")
        
    return template_values


def get_template_path(template_name, extension=None):
    if not extension:
        extension = "html"

    return os.path.join(os.path.dirname(__file__), \
                        "templates/%s.%s" % (template_name, extension))