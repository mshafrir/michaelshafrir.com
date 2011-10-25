import datetime
import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch

from lib.BeautifulSoup import BeautifulSoup

from united.helper import UnitedLogin
from united.models import *

import logging
logging.getLogger().setLevel(logging.DEBUG)


def cell_to_int(cell):
    cell_value = cell.contents[0].strip()
    if cell_value and len(cell_value):
        try:
            return int(cell_value)
        except:
            pass
    
    return 0

class UnitedUpgrades(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        
        username = "mshafrir@gmail.com" #"03107262821"
        password = "Jordan23"
        
        united_login = UnitedLogin(username=username, password=password, return_to="eug_sum", follow_redirects=False)
        success = united_login.do_it()
        if success:
            splitter = "<div id=\"upgrade_summary\">"
            upgrade_page = "%s%s" % (splitter, united_login.content.split(splitter)[1].replace("&nbsp;", " ").replace("<br />", "").strip())
            upgrade_page = upgrade_page.replace("<p class=\"eugSumTableData\">", "").replace("</p>", "")
            upgrade_page = upgrade_page.replace("<span class=\"eugSumTableData\">", "").replace("</span>", "")
            upgrade_soup = BeautifulSoup(upgrade_page)
            for upgrade_row in upgrade_soup.findAll('table')[1].findAll('tr')[3:]:
                cells = upgrade_row.findAll('td')
                month, year = [int(d) for d in str(cells[0].contents[0].strip()).split('/')]
                date = datetime.date(year, month, 1)
                swu = cell_to_int(cells[1])
                cr1 = cell_to_int(cells[2])
                e500 = cell_to_int(cells[3]) + cell_to_int(cells[4])
                
                upgrade_month = UpgradeMonth.git(user=None, date=date)
                if not upgrade_month:
                    upgrade_month = UpgradeMonth(date=date, swu_count=swu, cr1_count=cr1, e500_count=e500)
                    
                else:
                    upgrade_month.swu_count = swu
                    upgrade_month.cr1_count = cr1
                    upgrade_month.e500_count = e500
                    
                upgrade_month.put()
            
            for upgrade_month in UpgradeMonth.git(user=None):
                self.response.out.write("%s" % upgrade_month)


class UnitedMileageSummary(webapp.RequestHandler):
    def get_mileage_summary(self, login_cookies):
        today = datetime.date.today()
        
        mileage_summary_headers = {'Cookie': ';'.join(login_cookies)}
        mileage_summary_form_fields = {'frommonth': 1, 'fromday': 1, 'fromyear': 2009, \
                                       'tomonth': today.month, 'today': today.day, 'toyear': today.year, \
                                       'united': 'on', 'starAlliance': 'on', 'allAirlines': 'on', \
                                       'hotel': 'on', 'car': 'on', 'awards': 'on'}
        return urlfetch.fetch(url="https://travel.united.com/ube/secure/mpDetail.do", \
                              method=urlfetch.POST, deadline=10, \
                              headers=mileage_summary_headers, \
                              payload=urllib.urlencode(mileage_summary_form_fields))
        
    def parse_mileage_summary_page(self, mileage_summary_response):
        splitter = "<div class=\"w\" id=\"MPContent\">"
        mileage_summary_content = ("%s%s" % (splitter, mileage_summary_response.content.split(splitter)[1])).split("<div class=\"w\">")[0].replace("&nbsp;", " ")
        mileage_summary_soup = BeautifulSoup(mileage_summary_content)
        account_summary_table, mileage_details_table, mileage_summary_table = mileage_summary_soup.findAll('table')[:3]
        return account_summary_table, mileage_details_table, mileage_summary_table
    
    def parse_mileage_details(self, mileage_details_table):
        def norm_miles(miles_str):
            miles_str = ''.join(miles_str.split(','))
            if miles_str.startswith('('):
                return 0 - int(miles_str[1:-1])
            
            return int(miles_str)
        
        def parse_flight_details(flight_cell):
            airline = flight_cell[0].contents[0]
            flight_number, flight_class = flight_cell[1].strip().split(' ')[0:2]
            from_airport = flight_cell[2].contents[0]
            to_airport = flight_cell[5].contents[0]
            
            return "%s%s %s-%s (%s class)" % (airline, flight_number, from_airport, to_airport, flight_class)


        entries = []
        for r in mileage_details_table.findAll('tr')[1:]:
            cells = r.findAll('td')
            if cells and len(cells) == 6:
                entry = {'date': str(cells[0].contents[0]).replace('&nbsp;', ' '), \
                         'base_miles': norm_miles(cells[2].contents[0]), \
                         'elite_bonus': norm_miles(cells[3].contents[0]), \
                         'fare_bonus': norm_miles(cells[4].contents[0]), \
                         'total_miles': norm_miles(cells[5].contents[0])}
                
                activity_cell_contents = cells[1].contents
                if len(activity_cell_contents) == 1:
                    entry['activity'] = str(activity_cell_contents[0])
                elif activity_cell_contents:
                    entry['activity'] = parse_flight_details(activity_cell_contents)
                
                entries.append(entry)
            
        return entries

    def parse_account_summary(self, account_summary_table):
        def row_val(row):
            return str(row.findAll('td')[1].contents[0]).strip()
        
        account_summary_rows = account_summary_table.findAll('tr')[1:]
        
        level = row_val(account_summary_rows[0])
        rdm = int(row_val(account_summary_rows[1]).replace(',', ''))
        eqm = int(row_val(account_summary_rows[2]).replace(',', ''))
        eqs = int(row_val(account_summary_rows[3]).replace(',', ''))
        lifetime_miles = int(row_val(account_summary_rows[4]).replace(',', ''))
        expiration_date = datetime.datetime.strptime(row_val(account_summary_rows[5]), "%b %d, %Y").date()
        
        return level, rdm, eqm, eqs, lifetime_miles, expiration_date

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        
        united_login = UnitedLogin(username="03107262821", password="Jordan23", follow_redirects=True)
        success = united_login.do_it()
        if success:
            mileage_summary_response = self.get_mileage_summary(united_login.cookies)
            if mileage_summary_response:
                
                account_summary_table, mileage_details_table, mileage_summary_table = self.parse_mileage_summary_page(mileage_summary_response)
                
                level, rdm, eqm, eqs, lifetime_miles, expiration_date = self.parse_account_summary(account_summary_table)
                account = Account.git(user=None)
                if not account:
                    account = Account(level=level, rdm=rdm, eqm=eqm, eqs=eqs, lifetime=lifetime_miles,
                                      expiration_date=expiration_date)
                else:
                    account.level = level
                    account.rdm = rdm
                    account.eqm = eqm
                    account.eqs = eqs
                    account.lifetime = lifetime_miles
                    account.expiration_date = expiration_date
                account.put()
                self.response.out.write("%s" % account)

                
                mileage_entries = self.parse_mileage_details(mileage_details_table)
                for mileage_entry in mileage_entries:
                    self.response.out.write("%d. %s\n" % (mileage_entries.index(mileage_entry) + 1, mileage_entry['activity']))
                    self.response.out.write("Date: %s\n" % mileage_entry['date'])
                    self.response.out.write("Base miles: %s\n" % mileage_entry['base_miles'])
                    self.response.out.write("Elite bonus: %s\n" % mileage_entry['elite_bonus'])
                    self.response.out.write("Fare bonus: %s\n" % mileage_entry['fare_bonus'])
                    self.response.out.write("Total miles: %s\n" % mileage_entry['total_miles'])
                    self.response.out.write("\n\n")
            
    def head(self):
        pass
    
    
class UnitedItineraries(webapp.RequestHandler):
    def get(self):
        pass
    
    
def main():
    ROUTES = [
        ('/united/mileage', UnitedMileageSummary),
        ('/united/itins', UnitedItineraries),
        ('/united/upgrades', UnitedUpgrades)
    ]
    application = webapp.WSGIApplication(ROUTES, debug=True)
    run_wsgi_app(application)

    
if __name__ == "__main__":
    main()