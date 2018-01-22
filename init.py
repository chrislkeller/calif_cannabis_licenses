#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.utils.text import slugify
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import datetime
import string
import urlparse
import csvkit
import re
import logging

logger = logging.getLogger("root")
logging.basicConfig(
    format = "\033[1;36m%(levelname)s: %(filename)s (def %(funcName)s %(lineno)s): \033[1;37m %(message)s",
    level=logging.INFO
)

class BeginCommand(object):

    help = "Begin request to pull cannabis licenses"

    def __init__(self):
        self.url_prefix = 'https://aca5.accela.com'
        self.url = 'https://aca5.accela.com/bcc/Cap/CapHome.aspx?module=Licenses&ShowMyPermitList=N'
        self.driver = webdriver.Chrome('/Users/user/_programming/_lat/_projects/2018_01_18_state_cannabis_licenses/chromedriver')
        self.driver.set_window_size(1200, 960)
        self.start_date = None
        self.end_date = None
        self.list_of_permits = []
        self.csv_filename = "cannabis_licenses.csv"
        self.csv_headers = [
            'date_added',
            'details_link',
            'permit_id',
            'permit_type',
            'legal_business_name',
            'expires_on',
            'status',
            'status_date',
            'license_address',
            'first_name',
            'last_name',
            'biz_name',
            'biz_name_extra',
            'biz_country',
            'biz_phone',
            'biz_email',
            'org_structure',
            'app_info_list',
            'notes',
        ]

    def clear_loading_time(self, seconds, element):
        wait = WebDriverWait(self.driver, seconds)
        wait.until(lambda driver: driver.find_element_by_id(element).is_displayed() == False)

    def process_table_data(self ,soup):
        try:
            table = soup.find('table', class_='ACA_GridView ACA_Grid_Caption')
            rows = table.find_all('tr', class_=['ACA_TabRow_Odd ACA_TabRow_Odd_FontSize', 'ACA_TabRow_Even ACA_TabRow_Even_FontSize'])
            for row in rows:
                tds = row.find_all("td")
                data_dict = {}
                data_dict['details_link'] = "%s%s" % (self.url_prefix, tds[1].find('a').get('href'))
                data_dict['permit_id'] = tds[1].get_text(strip=True)
                data_dict['permit_type'] = tds[2].get_text(strip=True)
                data_dict['legal_business_name'] = tds[3].get_text(strip=True)
                data_dict['expires_on'] = tds[4].get_text(strip=True)
                data_dict['status'] = tds[5].get_text(strip=True)
                data_dict['status_date'] = tds[6].get_text(strip=True)
                self.list_of_permits.append(data_dict)
        except Exception, exception:
            error_output = "%s" % (exception)
            return False

    def scrape(self):
        '''
        scrape all of the licenses for a given type
        '''
        self.driver.get(self.url);
        self.driver.find_element_by_id('ctl00_PlaceHolderMain_btnNewSearch').click()
        self.clear_loading_time(30, 'divGlobalLoading')
        s = BeautifulSoup(self.driver.page_source, 'html5lib')
        self.process_table_data(s)
        proceed = True
        while proceed == True:
            try:
                next_page_elem = self.driver.find_element_by_xpath("//a[text()='Next >']")
                logger.info(next_page_elem)
                next_page_elem.click()
                self.clear_loading_time(30, 'divGlobalLoading')
                s = BeautifulSoup(self.driver.page_source, 'html5lib')
                self.process_table_data(s)
            except NoSuchElementException, exception:
                error_output = "%s" % (exception)
                logger.info(error_output)
                proceed = False
        logger.info(len(self.list_of_permits))
        with open(self.csv_filename, "wb") as csv_file:
            csv_output = csvkit.writer(csv_file, delimiter=",", encoding="utf-8")
            csv_output.writerow(self.csv_headers)
            print self.list_of_permits
            for permit in self.list_of_permits:
                permit['notes'] = None
                self.driver.get(permit['details_link']);
                try:
                    self.driver.find_element_by_id('lnkMoreDetail').click()
                    self.driver.find_element_by_id('lnkRc').click()
                    self.driver.find_element_by_id('lnkASITableList').click()
                except NoSuchElementException, exception:
                    permit['notes'] = exception
                    pass
                time.sleep(15)
                s = BeautifulSoup(self.driver.page_source, 'html5lib')
                try:
                    target_address = s.find('div', class_='div_parent_detail').find('tbody').find_all('td')
                    permit['license_address'] = target_address[0].get_text(separator=u' ', strip=True)
                except NoSuchElementException, exception:
                    permit['notes'] = exception
                    pass
                try:
                    r = s.find_all('td', class_='MoreDetail_BlockContent')
                except NoSuchElementException, exception:
                    r = None
                    permit['notes'] = exception
                    pass
                if r:
                    # business information
                    try:
                        permit['first_name'] = r[0].find('span', class_='contactinfo_firstname').get_text(strip=True)
                    except Exception, exception:
                        logger.info(exception)
                        permit['first_name'] = None
                    try:
                        permit['last_name'] = r[0].find('span', class_='contactinfo_lastname').get_text(strip=True)
                    except Exception, exception:
                        logger.info(exception)
                        permit['last_name'] = None
                    try:
                        permit['biz_name'] = r[0].find('span', class_='contactinfo_businessname').get_text(strip=True)
                    except Exception, exception:
                        logger.info(exception)
                        permit['biz_name'] = None
                    try:
                        permit['biz_name_extra'] = r[0].find('span', class_='contactinfo_businessname2').get_text(strip=True)
                    except Exception, exception:
                        logger.info(exception)
                        permit['biz_name_extra'] = None
                    try:
                        permit['biz_country'] = r[0].find('span', class_='contactinfo_country').get_text(strip=True)
                    except Exception, exception:
                        logger.info(exception)
                        permit['biz_country'] = None
                    try:
                        permit['biz_phone'] = r[0].find('div', class_='ACA_PhoneNumberLTR').get_text(strip=True)
                    except Exception, exception:
                        logger.info(exception)
                        permit['biz_phone'] = None
                    try:
                        permit['biz_email'] = r[0].find('span', class_='contactinfo_email').get_text(strip=True).replace('E-mail:', '')
                    except Exception, exception:
                        logger.info(exception)
                        permit['biz_email'] = None
                    # business org structure
                    try:
                        org_structure_data = r[0].find('div', class_='ACA_TabRow').find('ul').find('p')
                        org_structure_data = org_structure_data.get_text(strip=True).split(':')
                        permit['org_structure'] = org_structure_data[1].strip()
                    except NoSuchElementException, exception:
                        logger.info(exception)
                        raise
                    # application information lists
                    try:
                        span_list = []
                        spans = r[-1].find_all('span', class_='ACA_SmLabel ACA_SmLabel_FontSize')
                        for s in spans:
                            proper_text = s.get_text(strip=True)
                            span_list.append(proper_text)
                        permit['app_info_list'] = " ".join(span_list)
                    except Exception, exception:
                        logger.info(exception)
                        raise
                else:
                    permit['org_structure'] = None
                    permit['app_info_list'] = None
                permit['date_added'] = datetime.datetime.now()
                logger.info(permit)
                csv_row_data = [
                    permit['date_added'],
                    permit['details_link'],
                    permit['permit_id'],
                    permit['permit_type'],
                    permit['legal_business_name'],
                    permit['expires_on'],
                    permit['status'],
                    permit['status_date'],
                    permit['license_address'],
                    permit['first_name'],
                    permit['last_name'],
                    permit['biz_name'],
                    permit['biz_name_extra'],
                    permit['biz_country'],
                    permit['biz_phone'],
                    permit['biz_email'],
                    permit['org_structure'],
                    permit['app_info_list'],
                    permit['notes'],
                ]
                csv_output.writerow(csv_row_data)
        self.driver.quit()

if __name__ == '__main__':
    task_run = BeginCommand()
    task_run.scrape()
