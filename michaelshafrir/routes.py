from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import michaelshafrir.helper as helper

import logging
logging.getLogger().setLevel(logging.DEBUG)

class SitePulseView(webapp.RequestHandler):
    def get(self):
        template_values = None
        self.response.out.write(template.render(helper.get_template_path('sitepulse'),
                                                template_values))

    def head(self):
        pass

class AboutMeView(webapp.RequestHandler):
    def get(self):
        template_values = None
        self.response.out.write(template.render(helper.get_template_path('home'),
                                                template_values))

    def head(self):
        pass


def main():
    ROUTES = [
        ('/sitepulse', SitePulseView),
        ('/', AboutMeView)
    ]
    application = webapp.WSGIApplication(ROUTES, debug=False)
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
