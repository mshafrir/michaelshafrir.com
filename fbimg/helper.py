import os
import logging
import simplejson

from google.appengine.api import users
from google.appengine.api import urlfetch


logging.getLogger().setLevel(logging.DEBUG)


def init_template_values(user=None):
    template_values = {}
    
    if user:
        template_values["is_logged_in"] = True
        
        is_admin = users.is_current_user_admin()              
        template_values["is_admin"] = is_admin
        
        nickname = user.nickname()
        template_values["nickname"] = nickname
        
        logout_url = users.create_logout_url("/").replace("&", "&amp;")
        template_values["logout_url"] = logout_url
        
    else:
        login_url = users.create_login_url("/")
        template_values["login_url"] = login_url
        
    return template_values


def get_template_path(path="", suffix=""):
    if path:
        script_name = os.path.split(path)[-1]
        template_name = script_name.split(".")[0]
        
        if suffix:
            template_name = template_name + "-" + suffix
        
        template_path = os.path.join(os.path.dirname(path), "templates/%s.html" % template_name)
        
        return template_path
    
    
def construct_yahoo_search(user_id):
    yahoo_api_key = "kZuLGaPV34H862VltztBe9b3iP4WYtHnIsTKLIYHYa9KIcaFrUswGhpJjYvRCiIzP7o-"
    search_url = "http://boss.yahooapis.com/ysearch/web/v1/facebook+%d?appid=%s&format=xml" % (user_id, yahoo_api_key)
    
    logging.info("construct_yahoo_search: %s" % search_url)
    
    return search_url


def get_image_urls(fb_img_url=None):
    photo_urls = None, None, None
    
    if fb_img_url:
        # the image is the smallest version
        if fb_img_url.find('/q') != -1:
            photo_urls = (fb_img_url, fb_img_url.replace('/q', '/s'), fb_img_url.replace('/q', '/n'))
            
        # the image is the small version
        elif fb_img_url.find('/s') != -1:
            photo_urls = (fb_img_url.replace('/s', '/q'), fb_img_url, fb_img_url.replace('/s', '/n'))
        
        # the image is the normal version    
        elif fb_img_url.find('/n') != -1:
            photo_urls = (fb_img_url.replace('/n', '/q'), fb_img_url.replace('/n', '/s'), fb_img_url)
            
    return photo_urls


def get_user_name_from_id(user_id=None):
    user_name = None
    
    if user_id:
        try:
            google_search_url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=facebook+%d" % user_id
            google_search_response = urlfetch.fetch(url=google_search_url, method=urlfetch.GET)
            logging.info("google_search_response content: %s" % google_search_response.content)
            
            google_search_json = simplejson.loads(google_search_response.content)
            
            try:
                fb_person_url = google_search_json['responseData']['results'][0]['url']
                
            except (IndexError):
                logging.info("index out of range in google search json response")
            
            logging.info("fb_person_url: %s" % fb_person_url)
        except (urlfetch.DownloadError):
            logging.info("Timed out while requesting google search results.")
                            
        yahoo_search_response = None
        full_name = None
        
        facebook_people_base_url = 'http://www.facebook.com/people/'
		
        if fb_person_url and fb_person_url.find(facebook_people_base_url) != -1:
            fb_name = fb_person_url.replace(facebook_people_base_url, '').replace('/%d' % user_id, '')
            logging.info("fb_name: %s" % fb_name)
            
            if fb_name.find('_') != -1:
                full_name = ' '.join(fb_name.split('_'))
            else:
                full_name = ' '.join(fb_name.split('-'))
    
    return user_name