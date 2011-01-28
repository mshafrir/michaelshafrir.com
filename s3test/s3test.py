import os
import wsgiref.handlers
import mimetypes
import simplejson, urllib
import time
import sys

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import urlfetch

import s3test.helper as helper

import logging
logging.getLogger().setLevel(logging.DEBUG)

import s3test.S3 as S3


class S3Uploader(webapp.RequestHandler):
    CONTENT_TYPES = {'mp3': 'audio/mpeg',
                     'avi': 'video/avi'
                    }
    @staticmethod
    def content_type(extension=None):
        if extension and extension in S3Uploader.CONTENT_TYPES:
            return S3Uploader.CONTENT_TYPES[extension]
        
        return None
    
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        
        AWS_ACCESS_KEY_ID = '0NCWPNH62S64A93TFDG2'
        AWS_SECRET_ACCESS_KEY = 'wDFcygTpmK/S0theUTzmAjQLo89xktLMarJagPtK'
        BUCKET_NAME = "%s-test-bucket" % AWS_ACCESS_KEY_ID.lower();
        s3_conn = S3.AWSAuthConnection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

        template_values = { 'bucket_entries': s3_conn.list_bucket(BUCKET_NAME).entries,
                            'bucket_base_url': "https://%s.s3.amazonaws.com" % BUCKET_NAME
                           }
        
        self.response.out.write(template.render(helper.get_template_path("s3up", extension="html"),
                                                template_values))
    
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        
        uploaded_file = self.request.get("uploaded_file")
        uploaded_filename = self.request.get("uploaded_filename", default_value="")
        
        if uploaded_file and uploaded_filename:
            uploaded_filename_arr = uploaded_filename.split('.')
            
            if uploaded_filename_arr and len(uploaded_filename_arr) > 1:
                extension = uploaded_filename_arr[-1].lower()
                content_type = S3Uploader.content_type(extension)
                self.response.out.write("extension: %s\n" % extension)
                self.response.out.write("content type: %s\n" % content_type)
            
                AWS_ACCESS_KEY_ID = '0NCWPNH62S64A93TFDG2'
                AWS_SECRET_ACCESS_KEY = 'wDFcygTpmK/S0theUTzmAjQLo89xktLMarJagPtK'
                BUCKET_NAME = "%s-test-bucket" % AWS_ACCESS_KEY_ID.lower();
                KEY_NAME = 'test-key'

                s3_conn = S3.AWSAuthConnection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
                s3_conn.put(BUCKET_NAME, uploaded_filename, S3.S3Object(uploaded_file), \
                            {'x-amz-acl': 'public-read', 'Content-Type': content_type})
                    
        


def main():
    ROUTES = [
        ('/s3test', S3Uploader)
    ]
    application = webapp.WSGIApplication(ROUTES, debug=True)
    run_wsgi_app(application)

    
if __name__ == "__main__":
    main()