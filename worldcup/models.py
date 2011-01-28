import logging, traceback
import os
import re
import cgi
import sys
import urllib
 
from google.appengine.api import users
from google.appengine.ext import db

class Venue(db.Model):
    city = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    coord = db.GeoPtProperty(required=False)
    capacity = db.IntegerProperty(required=True)

class Country(db.Model):
    group = db.StringProperty(required=True)
    seed = db.IntegerProperty(required=True)
    name = db.StringProperty(required=False)
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    date = db.DateTimeProperty(required=True, auto_now_add=True)
    order = db.IntegerProperty(default=sys.maxint)
    
class Match(db.Model):
    country1 = db.StringProperty(required=True)
    country2 = db.StringProperty(required=True)
    venue = db.ReferenceProperty(required=True, reference_class=Venue)
    date = db.DateTimeProperty(required=True)