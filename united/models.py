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

import united.helper as helper

class Account(db.Model):
    user = db.UserProperty()
    level = db.StringProperty(required=True)
    rdm = db.IntegerProperty(required=True, default=0)
    eqm = db.IntegerProperty(required=True, default=0)
    eqs = db.IntegerProperty(required=True, default=0)
    lifetime = db.IntegerProperty(required=True, default=0)
    expiration_date = db.DateProperty(required=False)
    
    @staticmethod
    def git(user=None):
        account = Account.all()
        if user:
            account.filter("user =", user)
        
        return account.get()
    
    def __str__(self):
        s = ""
        s += "Membership level: %s\n" % self.level
        s += "Current redeemable miles balance: %s\n" % self.rdm
        s += "YTD EQM: %s\n" % self.eqm
        s += "YTD EQS: %s\n" % self.eqs
        s += "Lifetime United flight miles: %s\n" % self.lifetime
        s += "Expiration date: %s\n\n\n" % self.expiration_date
        
        return s
    
    

class MileageEntry(db.Model):
    user = db.UserProperty()
    date = db.DateProperty(required=True)
    description = db.StringProperty(required=True)
    base_miles = db.IntegerProperty(required=True, default=0)
    elite_miles = db.IntegerProperty(required=True, default=0)
    fare_miles = db.IntegerProperty(required=True, default=0)
    total_miles = db.IntegerProperty(required=True, default=0)



class UpgradeMonth(db.Model):
    user = db.UserProperty()
    date = db.DateProperty(required=True)
    swu_count = db.IntegerProperty(required=True, default=0)
    cr1_count = db.IntegerProperty(required=True, default=0)
    e500_count = db.IntegerProperty(required=True, default=0)
    
    def __str__(self):
        return "%s: %d, %d, %d\n" % \
                (self.date, self.swu_count, self.cr1_count, self.e500_count)
    
    @staticmethod
    def git(user=None, date=None):
        upgrades = UpgradeMonth.all().order("date")
        if user:
            upgrades.filter("user =", user)
            
        if date:
            upgrades.filter("date =", date)
            return upgrades.get()
        
        return upgrades