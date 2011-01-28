import os
import wsgiref.handlers

import simplejson, urllib

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import urlfetch

from lib.BeautifulSoup import BeautifulSoup

import newsy.helper as helper

import logging
logging.getLogger().setLevel(logging.DEBUG)

'''
(function loadNewsy(scriptURL) {
    var newsyScript = document.createElement('script');
    newsyScript.setAttribute('type', 'text/javascript');
    newsyScript.setAttribute('src', 'http://localhost:8090/newsy/newsy.js');
    document.body.appendChild(newsyScript);
})();
'''

class Newsy(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        

        

class NewsyScript(webapp.RequestHandler):
    def fnid(self):
        ynews_response = urlfetch.fetch(url="http://news.ycombinator.com/submitlink")
        if ynews_response and ynews_response.status_code == 200:
            ynews_soup = BeautifulSoup(ynews_response.content)
            
            logging.info(ynews_soup.prettify())
            
            ynews_soup = ynews_soup.find('input', attrs={'name': "fnid"})
            if ynews_soup:
                return ynews_soup['value']
            
        return None
    
    
    def get(self):
        self.response.headers['Content-Type'] = 'text/javascript'

        template_values = {'fnid': self.fnid()}
        self.response.out.write(template.render(helper.get_template_path("newsy", extension="js"),
                                                template_values))


def main():
    ROUTES = [
        ('/newsy/newsy.js', NewsyScript),
        ('/newsy', Newsy)
    ]
    application = webapp.WSGIApplication(ROUTES, debug=True)
    run_wsgi_app(application)

    
if __name__ == "__main__":
    main()