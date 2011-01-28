from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import users

from django.template.defaultfilters import stringfilter

from time import gmtime, strftime


import logging
logging.getLogger().setLevel(logging.DEBUG)
 
register = webapp.template.create_template_register()


@register.filter
@stringfilter 
def format_date(_time):
    return _time