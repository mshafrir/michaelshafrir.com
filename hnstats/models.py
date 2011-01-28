import logging, traceback
import os
import re
import cgi
import sys
import urllib
 
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import search

class ErrorNewsItem(db.Model):
    id = db.IntegerProperty(required=True, default=0)
    error = db.StringProperty(required=False)
    
    @staticmethod
    def max():
        return ErrorNewsItem.all().order('-id').get()
    

class NewsItem(search.SearchableModel):
    id = db.IntegerProperty(required=True, default=0)
    author = db.StringProperty(required=True)
    score = db.IntegerProperty(required=True, default=0)
    url = db.LinkProperty(required=False)
    title = db.StringProperty(required=False)
    comment = db.TextProperty(required=False)
    parent_id = db.IntegerProperty(required=True, default=0)
    parent_item = db.SelfReferenceProperty()
    posted = db.DateTimeProperty(required=True)
    error = db.BooleanProperty(required=False, default=False)
    
    @staticmethod
    def get(id=None):
        if id:
            return NewsItem.all().filter('id =', id).get()
        
        return None
    
    @staticmethod
    def max():
        return NewsItem.all().order('-id').get()