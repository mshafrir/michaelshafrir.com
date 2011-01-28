import os
import wsgiref.handlers

import simplejson, urllib

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users

import virmanikitchen.helper as helper

import logging
logging.getLogger().setLevel(logging.DEBUG)


class KitchenApp(webapp.RequestHandler):
    def get(self, page=None):
        page = "home"
        
        template_values = None
        self.response.out.write(template.render(helper.get_template_path(page),
                                                template_values))
        
    def head(self):
        pass


def main():
    ROUTES = [
        ('/kitchen/(.*)', KitchenApp)
    ]
    application = webapp.WSGIApplication(ROUTES, debug=True)
    run_wsgi_app(application)

    
if __name__ == "__main__":
    main()