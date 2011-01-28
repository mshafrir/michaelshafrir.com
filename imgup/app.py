import os
import wsgiref.handlers
import cgi
import datetime
import simplejson
import urllib

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import urlfetch

from lib.BeautifulSoup import BeautifulSoup

from imgup.models import *
import imgup.helper as helper

import logging
logging.getLogger().setLevel(logging.DEBUG)


class ImgUpApp(webapp.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/imgup/upload')
        template_values = {'upload_url': upload_url}
        self.response.out.write(template.render(helper.get_template_path("home"),
                                                template_values))


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('image')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        self.redirect('/imgup/serve/%s' % blob_info.key())


class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)

    
def main():
    ROUTES = [
        ('/imgup', ImgUpApp),
        ('/imgup/upload', UploadHandler),
        ('/imgup/serve/([^/]+)?', ServeHandler),
    ]
    application = webapp.WSGIApplication(ROUTES, debug=True)
    run_wsgi_app(application)

    
if __name__ == "__main__":
    main()