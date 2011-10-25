from __future__ import division

import json
import urllib
import os

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import urlfetch

import logging
logging.getLogger().setLevel(logging.DEBUG)

URLFETCH_DEADLINE = 10
REQUIRED_COOKIES = ['UALUBESession', 'SecureUALUBESession', 'NSC_ufmxxx-80', 'UALEtcSession', 'ciToken', 'NSC_vb2hp-mc-80', 'NSC_Vojufe_HSQ']

class UnitedLogin():
    def __init__(self, username, password, return_to="mpsummary_us", follow_redirects=False):
        self.username = username
        self.password = password
        self.return_to = return_to
        self.follow_redirects = follow_redirects
        self.cookies = []
        self.content = None
        
    def do_it(self):
        login_form_fields = {'userId': self.username, 'password': self.password}
        login_url = "https://www.ua2go.com/ci/DoLogin.jsp?stamp=NEWCOOKY*itn/ord=NEWREC,itn/air/united&return_to=%s" \
                     % (self.return_to)
                     
        login_response = urlfetch.fetch(url=login_url, \
                                        follow_redirects=False, \
                                        method=urlfetch.POST, \
                                        payload=urllib.urlencode(login_form_fields))
        
        while login_response.status_code == 302:
            self.next_location = login_response.headers['location']
            self.update_cookies(login_response.headers)
            self.content = login_response.content
            login_response = urlfetch.fetch(url=self.next_location, \
                                             follow_redirects=self.follow_redirects, \
                                             method=urlfetch.GET, \
                                             headers=self.cookies_to_headers(), \
                                             deadline=URLFETCH_DEADLINE)
            
        
        self.update_cookies(login_response.headers)
        self.content = login_response.content
        
        
        return (login_response.status_code == 200)
    
    def update_cookies(self, new_headers):
        if 'set-cookie' in new_headers:
            self.cookies.extend(UnitedLogin.make_cookies(new_headers['set-cookie']).split(';'))
        
    @staticmethod       
    def make_cookies(cookie_response_header, filter=False):
        if filter:
            return ';'.join([c.split(';')[0].strip() for c in cookie_response_header.split(',')
                             if c.split(';')[0].strip().split('=')[0] in REQUIRED_COOKIES])
                             
        else:
            return ';'.join([c.split(';')[0].strip() for c in cookie_response_header.split(',')])
        
    def cookies_to_headers(self):
        return {'Cookie': ';'.join(self.cookies)}


def init_template_values(user=None):
    template_values = {}
    
    if user:
        template_values["user"] = user
        template_values["user_is_admin"] = users.is_current_user_admin()
        template_values["user_logout_url"] = users.create_logout_url("/").replace("&", "&amp;")

    else:
        template_values["user_login_url"] = users.create_login_url("/")
        
    return template_values


def get_template_path(template_name, extension=None):
    if not extension:
        extension = "html"

    return os.path.join(os.path.dirname(__file__), "templates/%s.%s" % (template_name, extension))