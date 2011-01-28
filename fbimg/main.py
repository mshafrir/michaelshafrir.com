import os
import wsgiref.handlers

import simplejson, urllib

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users

from google.appengine.api import urlfetch
from xml.dom import minidom
from xml.parsers.expat import ExpatError

from helper import *
from FacebookLookup import *

from time import gmtime, strftime

webapp.template.register_template_library('customfilters')


class Home(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        
        template_values = init_template_values(user=user)

        img_url = self.request.get("url")
        
        if img_url:
            img_url = img_url.strip()
            template_values['img_url'] = img_url
            
            template_values['searched'] = True
            
            logging.info("img_url: %s" % img_url)
            fb_img_url_parts = img_url.split('/')
            
            logging.info("url parts:")
            for p in fb_img_url_parts:
                logging.info("\tpart: %s" % p)
            
            img_info_parts = fb_img_url_parts[-1].split('_')
            logging.info("img info parts:")
            for i in img_info_parts:
                logging.info("\timg part: %s" % i)

            
            user_id = None
            
            try:
                user_id = int(img_info_parts[0][1:])
                logging.info("user_id: %d" % user_id)
                
            except (ValueError):
                template_values['error'] = 'Error processing URL.'

            
            if user_id:
                photo_id = None
                photo_album_url = None
                
                if not img_info_parts or len(img_info_parts) <= 1:
                    template_values['error'] = 'Error processing URL.'
                
                else:
                    if len(img_info_parts) > 2:
                        try:
                            photo_id = int(img_info_parts[1])
                            logging.info("photo_id: %d" % photo_id)
                            photo_album_url = "http://www.facebook.com/photo.php?pid=%d&amp;id=%d" % (photo_id, user_id)
                            template_values['photo_album_url'] = photo_album_url
                            
                        except (ValueError):
                            pass
                    
                
                    thumbnail_photo_url, small_photo_url, normal_photo_url = get_image_urls(fb_img_url=img_url)
                    template_values['thumbnail_photo_url'] = thumbnail_photo_url
                    template_values['small_photo_url'] = small_photo_url
                    template_values['normal_photo_url'] = normal_photo_url
                     
                    
                    user_name = get_user_name_from_id(user_id=user_id)
                    template_values['full_name'] = user_name


                if user:
                    logging.info("**** trying to add img to data store")
                    lookup_exists = False
                    if FacebookLookup.all().filter('user =', user).filter('image_url =', img_url).count(1):
                        lookup_exists = True
                        
                    if not lookup_exists:
                        facebook_lookup = FacebookLookup(image_url=img_url)
                        facebook_lookup.put()
        else:
            template_values['img_url'] = ""
            
            lookup_param = self.request.get('lookup')
            if lookup_param and lookup_param == 'True':
                template_values['error'] = "Enter a URL."


        if user:
            facebook_lookups = FacebookLookup.all().filter('user =', user).order('-created')
            template_values['facebook_lookups'] = facebook_lookups

        
        path = os.path.join(os.path.dirname(__file__), "templates/main.html")
        
        self.response.out.write(template.render(path, template_values))


def main():
    application = webapp.WSGIApplication([('/', Home)], debug=True)
    run_wsgi_app(application)

    
if __name__ == "__main__":
    main()