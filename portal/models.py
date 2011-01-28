import logging, traceback
import os
import re
import cgi
import sys
import urllib
 
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import memcache

import portal.helper as helper 



class PageTracker(db.Model):
    site = db.StringProperty(required=True)
    page = db.IntegerProperty(required=True, default=0)
    
    @staticmethod
    def get(site):
        return PageTracker.all().filter('site =', site).get()
    
    @staticmethod
    def reset(site):
        page_tracker = PageTracker.get(site)
        page_tracker.page = -1
        page_tracker.put()
    
    @staticmethod
    def site_page(site):
        page_tracker = PageTracker.get(site)
        if page_tracker:
            return page_tracker.page
        
        return 0
    
    @staticmethod
    def increment(site):
        page_tracker = PageTracker.get(site)
        if not page_tracker:
            page_tracker = PageTracker(site=site, page=0)
        
        page_tracker.page += 1
        page_tracker.put()


class PortalStats(db.Model):
    host_name = db.StringProperty(required=True)
    server_name = db.StringProperty()
    portal_version = db.StringProperty()
    total_request_time = db.IntegerProperty(default=-1)
    page_display_time = db.IntegerProperty(default=-1)
    control_time = db.IntegerProperty(default=-1)
    page_construction_time = db.IntegerProperty(default=-1)
    
    def props(self):
        return {'host_name': self.host_name, 'server_name': self.server_name, 'portal_version': self.portal_version, \
                'total_request_time': self.total_request_time, 'page_display_time': self.page_display_time, \
                'control_time': self.control_time, 'page_construction_time': self.page_construction_time}
        
    @staticmethod
    def csv_heading():
        return ['host_name', 'server_name', 'portal_version', 'total_request_time', \
                'page_display_time', 'control_time', 'page_construction_time']
    
    @staticmethod
    def get(host_name):
        return PortalStats.all().filter('host_name =', host_name).get()
    
    @staticmethod
    def make(host_name, stats):
        portal_stats = PortalStats.get(host_name)
        if not portal_stats:
            portal_stats = PortalStats(host_name=host_name)
            
        portal_stats.server_name = stats['server_name']
        portal_stats.portal_version = stats['portal_version']
        portal_stats.total_request_time = stats['total_request_time']
        portal_stats.page_construction_time = stats['page_construction_time']
        portal_stats.page_display_time = stats['page_display_time']
        portal_stats.control_time = stats['control_time']
        
        return portal_stats