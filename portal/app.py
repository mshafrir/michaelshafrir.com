import urllib
import urlparse
import csv
import StringIO
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import DownloadError
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from lib.BeautifulSoup import BeautifulSoup
import json

import portal.helper as helper
from portal.models import PageTracker
from portal.models import PortalStats

import logging
logging.getLogger().setLevel(logging.DEBUG)


BING_API_KEY = "A16D1EB6B28863355885D7765A99C8829D5DE9BD"
GOOGLE_SEARCH_API_KEY = "ABQIAAAAbS93tJ_uidHDZWvF7euCFBTZmOKYYemR0pO6WncbFXP3MJAR_hSr_l7ddwxqLDz-PZiHyU8HcukfGw"
PAGE_RANK_KEY = 'url_page_rank'
SEARCH_RESULTS_KEY = 'search_results'
MEMCACHE_TIME = 60 * 30

SEARCH_TERM = "portal server.pt"
PORTAL_URI = '/portal/server.pt'
START_STATS_TOKEN = '<!--Hostname:'


def parse_stats(content=None):
    stats = {}

    if content:
        found = False

        logging.debug('\n'.join(content))

        for i in xrange(len(content)):
            if content[i].find(START_STATS_TOKEN) != -1:
                logging.debug(content[i])
                s = content[i].split(START_STATS_TOKEN)[1]
                stats['server_name'], s = [p.strip() for p in s.split('--><!--', 1)]
                logging.debug('\n\n\n#### %s ####\n\n\n' % s)
                stats['total_request_time'] = int(s.split('Total Request Time:')[1].strip())
                found = True
                break

        if found:
            stats['control_time'] = int(content[i + 1].split(':')[1].strip())
            stats['page_construction_time'] = int(content[i + 2].split(':')[1].strip())
            stats['page_display_time'] = int(content[i + 3].split(':')[1].strip())
            stats['portal_version'] = content[i + 4].split('Portal Version:')[1].split(',')[0].strip()

            for key in stats.keys():
                logging.debug("\t\t%s => %s" % (key, stats[key]))

            return stats

    return None


def get_refresh_url(page_content):
    try:
        page_soup = BeautifulSoup(page_content)
        for meta_tag in page_soup.findAll('meta'):
            if meta_tag['http-equiv'].lower() == 'refresh':
                refresh_url = meta_tag['content'].split('URL=')[1]
                return refresh_url
    except:
        pass

    return None


def to_hostname(url=None):
    if url:
        return urlparse.urlparse(url).netloc

    return None


def normalize_url(url):
    new_url = "%s://%s%s" % urlparse.urlparse(url)[:3]
    if new_url.endswith('/'):
        new_url = new_url[:-1]

    return new_url


def mod_portal_url(url=None):
    if url:
        url = normalize_url(url)

        if url.find(PORTAL_URI) != -1:
            url = "%s%s" % (url.split(PORTAL_URI)[0], PORTAL_URI)

        else:
            url = "%s%s" % (url, PORTAL_URI)

        return "%s?space=Login" % normalize_url(url)

    return None


def yahoo_boss_lookup(count, page):
    if page == 0:
        offset = 0
    else:
        offset = count * page

    if offset + count >= 1000:
        return None

    else:
        portal_search_url = "http://boss.yahooapis.com/ysearch/web/v1/%s?appid=%s&format=json&count=%d&start=%d" \
                                % (urllib.quote(SEARCH_TERM), YAHOO_BOSS_API_KEY, count, offset)
        portal_search_response = urlfetch.fetch(url=portal_search_url, deadline=10)

        portal_urls = []
        if portal_search_response and portal_search_response.status_code == 200:
            boss_json = json.loads(portal_search_response.content)
            portal_urls = [str(result['url']) for result in boss_json['ysearchresponse']['resultset_web']]

        return portal_urls


def google_lookup(count, page):
    portal_search_url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s&start=%s" \
                            % (urllib.quote(SEARCH_TERM), page * count)
    portal_search_response = urlfetch.fetch(url=portal_search_url, deadline=10)

    portal_urls = []
    if portal_search_response and portal_search_response.status_code == 200:
        google_json = json.loads(portal_search_response.content)
        if google_json['responseStatus'] != 200:
            return None

        else:
            if google_json['responseData'] and 'results' in google_json['responseData']:
                for search_result in google_json['responseData']['results']:
                    url = str(search_result['unescapedUrl'])

                    portal_urls.append(url)

    return portal_urls


def bing_lookup(count, page):
    if page == 0:
        offset = 0
    else:
        offset = count * page + 1

    portal_search_url = "http://api.search.live.net/json.aspx?Appid=%s&query=%s&sources=web&web.count=%d&web.offset=%d" \
                            % (BING_API_KEY, urllib.quote(SEARCH_TERM), count, offset)
    portal_search_response = urlfetch.fetch(url=portal_search_url, deadline=10)

    portal_urls = []
    if portal_search_response and portal_search_response.status_code == 200:

        bing_json = json.loads(portal_search_response.content)
        if bing_json and 'SearchResponse' in bing_json:

            bing_search_response_json = bing_json['SearchResponse']

            # Errors found in response
            if 'Errors' in bing_search_response_json and len(bing_search_response_json['Errors']):
                return None

            # No errors found in response
            if bing_search_response_json and 'Web' in bing_search_response_json:
                bing_web_json = bing_search_response_json['Web']
                if bing_web_json and 'Results' in bing_web_json:
                    for result in bing_web_json['Results']:
                        portal_urls.append(result['Url'])

    return portal_urls


def versions():
    version_count = {}
    for portal_stats in PortalStats.all():
        if portal_stats.portal_version:
            version_count[portal_stats.portal_version] = \
                version_count.get(portal_stats.portal_version, 0) + 1

    versions = [(value, key) for key, value in version_count.iteritems()]
    versions.sort()
    versions.reverse()

    return versions


class PageTrackerReset(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        for page_tracker in PageTracker.all():
            page_tracker.page = 0
            page_tracker.put()
            self.response.out.write("reset %s\n" % page_tracker.site)


class PortalPage(webapp.RequestHandler):
    def get(self):
        portal_url = mod_portal_url(self.request.get('url'))

        if portal_url:
            logging.debug("[%s]" % portal_url)

            try:
                portal_page_response = urlfetch.fetch(url=portal_url, deadline=10, follow_redirects=True)
            except DownloadError:
                portal_page_response = None

            if portal_page_response and portal_page_response.status_code == 200:
                #get_refresh_url(portal_page_response.content)

                try:
                    parsed_stats = parse_stats(portal_page_response.content.split('\n')[-10:])
                except Exception, detail:
                    parsed_stats = None
                    logging.error("Exception while parsing stats. %s" % detail)

                if parsed_stats:
                    portal_stats = PortalStats.make(host_name=to_hostname(portal_url),\
                                                    stats=parsed_stats)
                    portal_stats.put()
                    logging.debug("Put stats for %s." % portal_url)


class PortalSearch(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'

        site = self.request.get('site', default_value='google')
        count = int(self.request.get('count', default_value=4))
        page = int(self.request.get('page', default_value=PageTracker.site_page(site)))

        if page != -1:
            self.response.out.write("site: %s\n" % site)
            self.response.out.write("count: %s\n" % count)
            self.response.out.write("page: %s\n" % page)

            if site == 'bing':
                portal_urls = bing_lookup(count, page)
            elif site == 'google':
                portal_urls = google_lookup(count, page)
            elif site == 'yahoo_boss':
                portal_urls = yahoo_boss_lookup(count, page)
            else:
                portal_urls = None

            if portal_urls is None:
                PageTracker.reset(site)
                self.response.out.write("\ndisabled site: %s\n" % site)

            else:
                for portal_url in [mod_portal_url(portal_url) for portal_url in portal_urls]:
                    task_name = "portal-%s-%s" % (to_hostname(portal_url).split(':')[0].replace('.', '-'), datetime.now().strftime('%s'))
                    task = taskqueue.Task(url='/portal/process', params={'url': portal_url}, name=task_name, method='GET')

                    try:
                        self.response.out.write("\ntask name: %s\n" % task_name)
                        task.add("portal-pages")

                    except Exception:
                        logging.warning("Task [%s] already exists." % task_name)
                        self.response.out.write("Task [%s] already exists.\n" % task_name)

                PageTracker.increment(site)


class Report(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'

        portals = PortalStats.all()

        version = self.request.get('v')
        if version:
            portals.filter('portal_version =', version)

        template_values = helper.init_template_values(user=None)
        template_values['stats'] = portals.fetch(1000)
        template_values['versions'] = versions()
        self.response.out.write(template.render(helper.get_template_path("report"), \
                                                template_values))


class DataDump(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(json.dumps([portal.props() for portal in PortalStats.all()]))


class DataLoad(webapp.RequestHandler):
    def get(self):
        data_dump_url = "http://www.michaelshafrir.com/portal/dump"

        try:
            data_dump_response = urlfetch.fetch(url=data_dump_url, deadline=10)
        except:
            data_dump_response = None

        if data_dump_response and data_dump_response.status_code == 200:
            for portal in json.loads(data_dump_response.content):
                PortalStats.make(portal['host_name'], portal).put()

        self.redirect('/portal/dump')


class ReportCSV(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/csv'

        csv_file = StringIO.StringIO()
        csv_writer = csv.DictWriter(csv_file, PortalStats.csv_heading(), dialect='excel')

        csv_writer.writerow({'host_name': 'Host Name', 'server_name': 'Server Name', 'portal_version': 'Portal Version', \
                            'total_request_time': 'Total Request Time', 'page_display_time': 'Page Display Time', \
                            'control_time': 'Control Time', 'page_construction_time': 'Page Construction Time'})

        for site in PortalStats.all():
            csv_writer.writerow(site.props())

        self.response.out.write("%s" % csv_file.getvalue())

        csv_file.close()


def main():
    ROUTES = [
        ('/portal/load', DataLoad),
        ('/portal/dump', DataDump),
        ('/portal.csv', ReportCSV),
        ('/portal/search', PortalSearch),
        ('/portal/process', PortalPage),
        ('/portal/reset', PageTrackerReset),
        ('/portal', Report)
    ]
    application = webapp.WSGIApplication(ROUTES, debug=False)
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
