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

import lib.simplejson as simplejson
import rank.helper as helper
from rank.pagerank import *

import logging
logging.getLogger().setLevel(logging.DEBUG)



GOOGLE_SEARCH_API_KEY = "ABQIAAAAbS93tJ_uidHDZWvF7euCFBTZmOKYYemR0pO6WncbFXP3MJAR_hSr_l7ddwxqLDz-PZiHyU8HcukfGw"
PAGE_RANK_KEY = 'url_page_rank'
SEARCH_RESULTS_KEY = 'search_results'
MEMCACHE_TIME = 60 * 30



class UrlSearchRank(webapp.RequestHandler):
    def get(self):
        pass
    


class RankLookup(webapp.RequestHandler):
    def get(self):
        template_values = {'query': self.request.get('q')}
        self.response.out.write(template.render(helper.get_template_path("rank_lookup"), \
                                                template_values))


class RankUrl(webapp.RequestHandler):
    def get(self):
        template_values = helper.init_template_values(user=None)
        
        page_rank = 0
        error = False
        
        url = self.request.get('url')
        if url:
            logging.debug("url: [%s]" % url)
            
            memcache_page_rank = memcache.get((PAGE_RANK_KEY, url))
            if memcache_page_rank:
                page_rank = memcache_page_rank
                
            else:
                page_rank_url = 'http://www.google.com/search?client=navclient-auto&features=Rank:&q=info:%s&ch=%s' % (url, checkHash(hashUrl(url)))
                page_rank_response = urlfetch.fetch(url=page_rank_url, deadline=10)
                
                logging.debug("status code: [%s]" % page_rank_response.status_code)
                
                if page_rank_response:
                    if page_rank_response.status_code == 403:
                        error = True
                        
                    elif len(page_rank_response.content) > 0:
                        page_rank_content = page_rank_response.content.strip()
                        page_rank = page_rank_content.split(':')[-1]
                        
                        logging.debug("content: [%s] => page rank: [%s]" % (page_rank_content, page_rank))
                
                memcache.set(PAGE_RANK_KEY, url, MEMCACHE_TIME)

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(simplejson.dumps({'page_rank': max(page_rank, 0), 'error': error}))


class SearchResults(webapp.RequestHandler):    
    def get(self):
        result_urls = []
        
        query = self.request.get('q')
        if query:
            logging.debug("QUERY: [%s]" % query)
            
            memcache_search_results = memcache.get((SEARCH_RESULTS_KEY, query))
            if memcache_search_results and len(memcache_search_results) > 0:
                result_urls = memcache_search_results
                
            else:
                for page in xrange(0, 7):
                    search_url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s&start=%s" % (urllib.quote(query), page * 4)
                    search_response = urlfetch.fetch(url=search_url, deadline=10)
                    
                    logging.debug("PAGE: %s => status code = %s" % (page, search_response.status_code))
                    
                    if search_response and search_response.status_code == 200:
                        search_response_json = simplejson.loads(search_response.content)
                        for search_result in search_response_json['responseData']['results']:
                            result_urls.append(str(search_result['unescapedUrl']))
                            
                memcache.set(SEARCH_RESULTS_KEY, result_urls, MEMCACHE_TIME)
                

        if "html" == self.request.get("view"):
            self.response.headers['Content-Type'] = 'text/html'
            template_values = {'result_urls': result_urls}
            self.response.out.write(template.render(helper.get_template_path("search_results"), \
                                                    template_values))

        else:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(simplejson.dumps({'urls': result_urls}))


def main():
    ROUTES = [
        ('/urlrank', UrlRank),
        ('/rank', RankLookup),
        ('/rank/u', RankUrl),
        ('/rank/s', SearchResults)
    ]
    application = webapp.WSGIApplication(ROUTES, debug=True)
    run_wsgi_app(application)

    
if __name__ == "__main__":
    main()