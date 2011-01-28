import os
import wsgiref.handlers
import urllib

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue

from lib.BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import lib.simplejson as simplejson
from datetime import datetime, timedelta

import hnstats.helper as helper
from hnstats.models import *

import logging
logging.getLogger().setLevel(logging.DEBUG)


LAST_HNID_KEY = "LAST_HNID_KEY"
ITEMS_PER_GO = 7


class NewsItemPage():
    @staticmethod
    def get_score(soup=None):
        if soup:
            return int(soup.contents[0].split()[0])
            
        return None
    
    @staticmethod
    def get_author(soup=None):
        if soup:
            return soup.contents[0].strip()
        
        return None
    
    @staticmethod
    def get_posted(soup=None):
        if soup:
            value, unit = str(soup).split()[:2]
            
            logging.info("date: %s %s" % (value, unit))

            if unit.startswith("minute"):
                ago = timedelta(minutes=int(value))
            elif unit.startswith("hour"):
                ago = timedelta(hours=int(value))
            elif unit.startswith("day"):
                ago = timedelta(days=int(value))
            else:
                raise ValueError("Date must be specified in days, hours, or minutes.")

            return datetime.now() - ago
        
        return None
            
    def __init__(self, id):
        self.processed = False
        if id > 0:
            self.id = id
            
        else:
            raise ValueError("Id must be a positive integer.")
        
    def process(self):
        hn_url = "http://news.ycombinator.com/item?id=%d" % (self.id)
        yql_query = urllib.quote_plus("select * from html where url=\"%s\"" % hn_url) # and xpath='//table[1]'" % hn_url)
        yql_query_url = "http://query.yahooapis.com/v1/public/yql?q=%s&format=xml" % yql_query
        logging.info("yql query url: [%s]" % yql_query_url)
        
        try:
            hn_response = urlfetch.fetch(url=yql_query_url, deadline=10)
        except urlfetch.DownloadError, detail:
            logging.error("Download error while fetching %s: %s" % (hn_url, detail))
            hn_response = None
        
        if hn_response and hn_response.status_code == 200:
            hn_soup = BeautifulSoup(hn_response.content)
            
            if hn_soup:
                hn_soup_results = hn_soup.find('results')
                if not hn_soup_results or not hn_soup_results.contents:
                    raise IndexError("News item does not exist.")
                
                else:
                    page_content = hn_soup_results.find('body')
                    
                    if len(page_content.findAll('table')) <= 3 or not page_content.findAll('table')[1].contents:
                        self.error = "Empty post."
                        
                    else:
                        title_td = page_content.find('td', {'class': 'title'})
                        
                        # top post
                        if title_td:
                            logging.info("top post")
                            
                            item_link = title_td.find('a')
                            if item_link:
                                sub_text = page_content.find('td', {'class': 'subtext'})
                                
                                if not sub_text:
                                    self.error = "Job post."
                                
                                else:
                                    author_anchor = sub_text.find('a')
                                    
                                    if not author_anchor:
                                        self.error = "Job post."
                                    
                                    else:
                                        if item_link['href'].startswith('http'):
                                            self.url = item_link['href']
                                        else:
                                            self.url = "http://news.ycombinator.com/%s" % item_link['href']
                                            
                                        self.title = ' '.join(unicode(item_link.contents[0]).strip().split())
                                        self.score = NewsItemPage.get_score(sub_text.find('span'))
                                        self.author = NewsItemPage.get_author(author_anchor)
                                        self.posted = NewsItemPage.get_posted(author_anchor.nextSibling)
                                        self.parent_id = 0
                                        
                                        top_block_rows = page_content.findAll('table')[2].findAll('tr')
                                        if len(top_block_rows) == 6:
                                            self.comment = ' '.join(top_block_rows[3].findAll('td')[1].find('p').contents[0].strip().split())
                                        else:
                                            self.comment = None
                                        
                                        self.processed = True
                            else:
                                self.error = "Dead post."
                        
                        # comment post   
                        else:
                            logging.info("comment post")
                            
                            top_block = page_content.find('td', {'class': 'default'})
                            comment_info = top_block.find('span', {'class': 'comhead'})
                            comment_info_anchors = comment_info.findAll('a')
                            
                            if len(comment_info_anchors) <= 1:
                                self.error = "Dead post."
                                
                            else:
                                self.url = None
                                self.title = None
                                self.score = NewsItemPage.get_score(comment_info.find('span'))
                                self.author = NewsItemPage.get_author(comment_info_anchors[0])
                                self.posted = NewsItemPage.get_posted(comment_info_anchors[0].nextSibling)
                                self.parent_id = int(comment_info_anchors[2]['href'].split('=')[1])
                                self.comment = ' '.join(unicode(top_block.find('span', {'class': 'comment'}).find('font').contents[0]).strip().split())
                                
                                self.processed = True
                                


    def persist(self):
        if self.processed:
            news_item = NewsItem.get(self.id)
            if news_item:
                logging.info("existing item")
                
                news_item.author = self.author
                news_item.score = self.score
                news_item.url = self.url
                news_item.title = self.title
                news_item.comment = self.comment
                news_item.posted = self.posted
                
            else:
                logging.info("new item")
                news_item = NewsItem(id=self.id, author=self.author, score=self.score,\
                                     url=self.url, title=self.title, comment=self.comment,\
                                     parent_id=self.parent_id, posted=self.posted)
                
            news_item.put()
        
        else:
            logging.info("error item.  %s: %s" % (self.id, self.error))
            error_news_item = ErrorNewsItem(id=self.id, error=self.error)
            error_news_item.put()
                
    

class ProcessNewsItem(webapp.RequestHandler):
    def get(self):
        hn_id = int(self.request.get("id", default_value=0))
        self.response.headers['Content-Type'] = "text/plain"
        
        logging.info("news item %d" % hn_id)
        
        try:
            item_page = NewsItemPage(id=hn_id)
            item_page.process()
            
        except ValueError, detail:
            item_page = None
            logging.info("\t%s" % detail)
            self.response.out.write("%s" % detail)
            
        except IndexError, detail:
            item_page = None
            logging.info("\t%s" % detail)
            self.response.out.write("%s" % detail)
        
        if item_page:
            if item_page.processed:           
                logging.info("\turl: %s" % item_page.url)
                logging.info("\ttitle: %s" % item_page.title)
                logging.info("\tscore: %d" % item_page.score)
                logging.info("\tauthor: %s" % item_page.author)
                logging.info("\tposted: %s" % item_page.posted)
                logging.info("\tparent: %s" % item_page.parent_id)
                logging.info("\tcomment: %s" % item_page.comment)
                
                self.response.out.write("item: %d\n" % hn_id)
                self.response.out.write("url: %s\n" % item_page.url)
                self.response.out.write("title: %s\n" % item_page.title)
                self.response.out.write("score: %d\n" % item_page.score)
                self.response.out.write("author: %s\n" % item_page.author)
                self.response.out.write("posted: %s\n" % item_page.posted)
                self.response.out.write("parent: %s\n" % item_page.parent_id)
                self.response.out.write("comment: %s\n" % item_page.comment)
                
            item_page.persist()


class NewsSearch(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = "text/plain"
        
        query = self.request.get("q")
        if query:
            for item in NewsItem.all().search(query).order('id'):
                self.response.out.write("%d\n\ttitle: %s:\n\tcomment: %s\n\n" % (item.id, item.title, item.comment))


class NewsCron(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = "text/plain"
        
        start_id = int(self.request.get('start', default_value=0))
        if start_id <= 0:
            max_news_item = NewsItem.max()
            max_error_news_item = ErrorNewsItem.max()
            
            if max_news_item and max_error_news_item:
                start_id = max(max_news_item.id, max_error_news_item.id)
                
            else:
                start_id = 0
        
        for hn_id in xrange(start_id + 1, start_id + 1 + ITEMS_PER_GO):
            task_name = "item-%d" % hn_id
            task = taskqueue.Task(url='/yn/process', params={'id': hn_id}, name=task_name, method='GET')
            
            try:
                task.add("news-items")
                logging.info("Adding hn id [%d] to the queue." % hn_id)
                self.response.out.write("Adding hn id [%d] to the queue.\n" % hn_id)
                
            except Exception, detail:
                logging.warning("Task [%s] already exists." % task_name)
                self.response.out.write("Task [%s] already exists.\n" % task_name)
        
        

class NewsStats(webapp.RequestHandler):    
    def get(self):
        template_values = helper.init_template_values(user=None)
        template_values['max'] = NewsItem.max()
        template_values['items'] = NewsItem.all().order('-id').fetch(1000)
        self.response.out.write(template.render(helper.get_template_path("yn"), \
                                                template_values))
            


def main():
    ROUTES = [
        ('/yn/job', NewsCron),
        ('/yn/search', NewsSearch),
        ('/yn/process', ProcessNewsItem),
        ('/yn', NewsStats)
    ]
    application = webapp.WSGIApplication(ROUTES, debug=True)
    run_wsgi_app(application)

    
if __name__ == "__main__":
    main()