#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.utils.text import slugify
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import pickle
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

class CannabisLicense(object):

    def __init__(self, date_added, details_link, permit_id, permit_type, legal_business_name, expires_on, status, status_date, license_address, first_name, last_name, biz_name, biz_name_extra, biz_country, biz_phone, biz_email, org_structure, app_info_list, notes, *args, **kwargs):
        self.date_added = date_added
        self.details_link = details_link
        self.permit_id = permit_id
        self.permit_type = permit_type
        self.legal_business_name = legal_business_name
        self.expires_on = expires_on
        self.status = status
        self.status_date = status_date
        self.license_address = license_address
        self.first_name = first_name
        self.last_name = last_name
        self.biz_name = biz_name
        self.biz_name_extra = biz_name_extra
        self.biz_country = biz_country
        self.biz_phone = biz_phone
        self.biz_email = biz_email
        self.org_structure = org_structure
        self.app_info_list = app_info_list
        self.notes = notes


class ConstructCannabisLicenses(object):

    help = "Begin request to pull cannabis licenses"

    def __init__(self):
        self.url_prefix = 'https://aca5.accela.com'
        self.url = 'https://aca5.accela.com/bcc/Cap/CapHome.aspx?module=Licenses&ShowMyPermitList=N'
        self.start_date = None
        self.end_date = None
        self.list_of_licenses = []
        self.text_filename = "list_of_permits.txt"
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

    def handle(self):
        # logger.info("Beginning to scrape state licenses" % (len(self.list_of_licenses)))
        # self.scrape()
        # logger.info("Writing %s state licenses to a text file" % (len(self.list_of_licenses)))
        # with open(self.text_filename, 'wb') as text_file:
        #     pickle.dump(self.list_of_licenses, text_file)
        with open (self.text_filename, 'rb') as pickle_file:
            self.list_of_licenses = pickle.load(pickle_file)
        logger.info("Found %s state licenses in the text file" % (len(self.list_of_licenses)))
        with open(self.csv_filename, "wb") as csv_file:
            logger.info("Creating %s" % (self.csv_filename))
            csv_output = csvkit.writer(csv_file, delimiter=",", encoding="utf-8")
            csv_output.writerow(self.csv_headers)
            for i in self.list_of_licenses[1124:]:
                obj = self.structure_data(i)
                csv_output.writerow(obj)
        logger.info("%s has been written" % (self.csv_filename))

    def clear_loading_time(self, driver, seconds, element):
        wait = WebDriverWait(driver, seconds)
        wait.until(lambda driver: driver.find_element_by_id(element).is_displayed() == False)

    def process_table_data(self ,soup):
        '''
        simplified manner of processing table data
        '''
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
                data_dict['date_added'] = datetime.datetime.now()
                data_dict['notes'] = []
                self.list_of_licenses.append(data_dict)
        except Exception, exception:
            error_output = "%s" % (exception)
            return False

    def scrape(self):
        '''
        for each page of licenses, pull in the data
        '''
        driver = webdriver.Chrome('/Users/user/_programming/_lat/_code/calif_cannabis_licenses/chromedriver')
        driver.set_window_size(1200, 960)
        driver.get(self.url);
        driver.find_element_by_id('ctl00_PlaceHolderMain_btnNewSearch').click()
        self.clear_loading_time(driver, 30, 'divGlobalLoading')
        s = BeautifulSoup(driver.page_source, 'html.parser')
        self.process_table_data(s)
        proceed = True
        while proceed == True:
            try:
                next_page_elem = driver.find_element_by_xpath("//a[text()='Next >']")
                logger.info(next_page_elem)
                next_page_elem.click()
                self.clear_loading_time(driver, 30, 'divGlobalLoading')
                s = BeautifulSoup(driver.page_source, 'html.parser')
                self.process_table_data(s)
            except NoSuchElementException, exception:
                error_output = "%s" % (exception)
                logger.info(error_output)
                proceed = False
        driver.quit()

    def structure_data(self, i):
        time.sleep(5)
        driver = webdriver.Chrome('/Users/user/_programming/_lat/_code/calif_cannabis_licenses/chromedriver')
        driver.set_window_size(1200, 960)
        driver.get(i['details_link']);
        try:
            driver.find_element_by_id('lnkMoreDetail').click()
            driver.find_element_by_id('lnkRc').click()
            driver.find_element_by_id('lnkASITableList').click()
        except NoSuchElementException, exception:
            i['license_address'] = None
            i['first_name'] = None
            i['last_name'] = None
            i['biz_name'] = None
            i['biz_name_extra'] = None
            i['biz_country'] = None
            i['biz_phone'] = None
            i['biz_email'] = None
            i['org_structure'] = None
            i['app_info_list'] = None
            i['notes'].append("additional details not available")
            logger.error(exception)
            driver.quit()
            logger.info(i)
            return [
                i['date_added'],
                i['details_link'],
                i['permit_id'],
                i['permit_type'],
                i['legal_business_name'],
                i['expires_on'],
                i['status'],
                i['status_date'],
                i['license_address'],
                i['first_name'],
                i['last_name'],
                i['biz_name'],
                i['biz_name_extra'],
                i['biz_country'],
                i['biz_phone'],
                i['biz_email'],
                i['org_structure'],
                i['app_info_list'],
                i['notes'],
            ]
        s = BeautifulSoup(driver.page_source, 'html.parser')
        try:
            target_address = s.find('div', class_='div_parent_detail').find('tbody').find_all('td')
            i['license_address'] = target_address[0].get_text(separator=u' ', strip=True)
        except NoSuchElementException, exception:
            i['license_address'] = None
            i['notes'].append("license address not found")
        try:
            r = s.find_all('td', class_='MoreDetail_BlockContent')
        except NoSuchElementException, exception:
            r = None
            i['notes'].append("more detail not found")
            pass
        if r:
            try:
                i['first_name'] = r[0].find('span', class_='contactinfo_firstname').get_text(strip=True)
            except Exception, exception:
                i['first_name'] = None
                i['notes'].append("first name not found")
                logger.error(exception)
            try:
                i['last_name'] = r[0].find('span', class_='contactinfo_lastname').get_text(strip=True)
            except Exception, exception:
                i['last_name'] = None
                i['notes'].append("last name not found")
                logger.error(exception)
            try:
                i['biz_name'] = r[0].find('span', class_='contactinfo_businessname').get_text(strip=True)
            except Exception, exception:
                i['biz_name'] = None
                i['notes'].append("business name not found")
                logger.error(exception)
            try:
                i['biz_name_extra'] = r[0].find('span', class_='contactinfo_businessname2').get_text(strip=True)
            except Exception, exception:
                i['biz_name_extra'] = None
                logger.error(exception)
            try:
                i['biz_country'] = r[0].find('span', class_='contactinfo_country').get_text(strip=True)
            except Exception, exception:
                i['biz_country'] = None
                i['notes'].append("business country not found")
                logger.error(exception)
            try:
                i['biz_phone'] = r[0].find('div', class_='ACA_PhoneNumberLTR').get_text(strip=True)
            except Exception, exception:
                i['biz_phone'] = None
                i['notes'].append("business phone not found")
                logger.error(exception)
            try:
                i['biz_email'] = r[0].find('span', class_='contactinfo_email').get_text(strip=True).replace('E-mail:', '')
            except Exception, exception:
                i['biz_email'] = None
                i['notes'].append("business email not found")
                logger.error(exception)
            try:
                org_structure_data = r[0].find('div', class_='ACA_TabRow').find('ul').find('p')
                org_structure_data = org_structure_data.get_text(strip=True).split(':')
                i['org_structure'] = org_structure_data[1].strip()
            except NoSuchElementException, exception:
                i['org_structure'] = None
                i['notes'].append("org structure not found")
                logger.error(exception)
            try:
                span_list = []
                spans = r[-1].find_all('span', class_='ACA_SmLabel ACA_SmLabel_FontSize')
                for s in spans:
                    proper_text = s.get_text(strip=True)
                    span_list.append(proper_text)
                i['app_info_list'] = " ".join(span_list)
            except Exception, exception:
                i['app_info_list'] = None
                i['notes'].append("application info not found")
                logger.error(exception)
        else:
            i['first_name'] = None
            i['last_name'] = None
            i['biz_name'] = None
            i['biz_name_extra'] = None
            i['biz_country'] = None
            i['biz_phone'] = None
            i['biz_email'] = None
            i['org_structure'] = None
            i['app_info_list'] = None
        i['notes'] = "|".join(i['notes'])
        driver.quit()
        logger.info(i)
        return [
            i['date_added'],
            i['details_link'],
            i['permit_id'],
            i['permit_type'],
            i['legal_business_name'],
            i['expires_on'],
            i['status'],
            i['status_date'],
            i['license_address'],
            i['first_name'],
            i['last_name'],
            i['biz_name'],
            i['biz_name_extra'],
            i['biz_country'],
            i['biz_phone'],
            i['biz_email'],
            i['org_structure'],
            i['app_info_list'],
            i['notes'],
        ]

if __name__ == '__main__':
    task_run = ConstructCannabisLicenses()
    task_run.handle()
