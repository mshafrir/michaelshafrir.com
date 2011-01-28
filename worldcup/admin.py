import os
import wsgiref.handlers

import simplejson, urllib

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext.db import djangoforms
from google.appengine.api import memcache

import vbb.helper as helper
from vbb.models import *

import lib.S3 as S3

import logging
logging.getLogger().setLevel(logging.DEBUG)

MEMCACHE_ADMIN_SECTION_KEY = ("ADMIN", "SECTION")


class AdminCountry(webapp.RequestHandler):
    def get(self, code):
        pass
    
    def post(self, code):
        pass
    
class AdminCountries(webapp.RequestHandler):
    def get(self):
        pass
    
    def post(self):
        pass

class AdminMatch(webapp.RequestHandler):
    def get(self, code):
        pass
    
    def post(self, code):
        pass
    
class AdminMatches(webapp.RequestHandler):
    def get(self):
        pass
    
    def post(self):
        pass
    
class AdminVenue(webapp.RequestHandler):
    def get(self, code):
        pass
    
    def post(self, code):
        pass
    
class AdminVenues(webapp.RequestHandler):
    def get(self):
        pass
    
    def post(self):
        pass
    

class Admin(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render(helper.get_template_path("admin"),
                                                helper.init_template_values(user=users.get_current_user())))



def main():
    ROUTES = [
        ('/worldcup/admin/countries/(.*)', AdminCountry),
        ('/worldcup/admin/countries', AdminCountries),
        ('/worldcup/admin/venues/(.*)', AdminVenue),
        ('/worldcup/admin/venues', AdminVenues),
        ('/worldcup/admin/match', AdminMatch),
        ('/worldcup/admin/matches', AdminMatches),
        ('/worldcup/admin', Admin)
    ]
    application = webapp.WSGIApplication(ROUTES, debug=True)
    run_wsgi_app(application)

    
if __name__ == "__main__":
    main()