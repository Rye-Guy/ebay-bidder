import logging
import time
import os
import zipfile
from urllib.request import urlopen

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

import undetected_chromedriver as uc
from bs4 import BeautifulSoup

chrome_options = webdriver.ChromeOptions()


class EbayBidder:
    def __init__(self, proxy=False, headless=False):
        self.options = uc.ChromeOptions()
        if headless:
            self.options.headless = True
            self.options.add_argument('--headless')

        if proxy:
            self.set_proxy()

        self.driver = uc.Chrome(options=self.options, driver_executable_path='/usr/bin/chromedriver')
        self.logger = logging.getLogger(__name__)
        self.driver.implicitly_wait(0)

    def get(self, url):
        self.driver.get(url)

    def sign_in(self, email, password):
        # Get login url and click on ebay sign in element as well as the google auth sign in as this code works by targeting email and password inputs and not the ones on ebay themselves. 
        self.driver.get('https://www.ebay.ca/')
        self.driver.find_element(By.CSS_SELECTOR, "span[id=gh-ug] > a").click()
        self.driver.find_element(By.ID, 'signin_ggl_btn').click()
        # Send input data to functions that update the input and then program a mouse action to click on the next button which will generate the password input after the action we update the password input and the form will auto submit after the input 'cools'. 
        self.input_update(By.CSS_SELECTOR, 'input[id=identifierId]', email)
        action = webdriver.ActionChains(self.driver)
        action.move_to_element(
            self.driver.find_element(By.XPATH, '//*[@id="identifierNext"]/div/button')).click()
        action.perform()
        self.input_update(By.XPATH,  '//*[@id="password"]/div[1]/div/div[1]/input', password)
        action.move_to_element(
            self.driver.find_element(By.XPATH, '//*[@id="passwordNext"]/div/button')).click()
        action.perform()
        ###KEEPS PAGE OPEN FOR DEV PERPOSES
        
        WebDriverWait(self.driver, 100).until(ec.presence_of_element_located((By.ID,  'afsdjkldfaskljasdfk;jl')))

    def input_update(self, filter_type, target_id, input_val):
        try:
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((filter_type,  target_id))).send_keys(f'{input_val}')
        except NoSuchElementException as e:
            self.logger.error(e)

    def wait_for_id(self, id, waittime):
        try:
            WebDriverWait(self.driver, waittime).until(
                ec.presence_of_element_located((By.ID, id))
            )
        except (NoSuchElementException, TimeoutException) as e:
            self.logger.error(e)


    def click_to_button_with_id_when_ready(self, id, waittime=5):
        self.wait_for_id(id, waittime)
        button = self.driver.find_element(By.CSS_SELECTOR, f'button#{id}')
        click_to_button_if_present = webdriver.ActionChains(self.driver)
        click_to_button_if_present.move_to_element(button).click()
        try:
            click_to_button_if_present.perform()
        except NoSuchElementException as e:
            self.logger.error(e)

    def find_items_from_list_with_value_less_than(self, urls, limit_amount=0.05):
        items_in_query = []
        print(urls)
        for item in urls:
            html = urlopen(item)
            bs_obj = BeautifulSoup(html, "html.parser")
            listing_li_eles = bs_obj.findAll("li", {"class": "s-item"})
            self.logger.info(item)
            for el in listing_li_eles:
                el_heading = el.find(role="heading")
                #CODE WILL BREAK IF THE PRICE OF LISTINGS HAVE MORE THAN 1 COMMA
                el_price = el.find(attrs={'class',"s-item__price"}).text.replace('$', '').replace('C', '').replace(',', '').strip()
                if el_price.find('to') > 0:
                    continue
                el_listing_url = el.div.div.div.a['href']
                print((el_listing_url.find('signin')), (el_listing_url.find('.com')))
                if el_listing_url.find('.com') > 0:
                    continue
                
                print(el_heading, el_price, limit_amount, el_listing_url)
                #self.logger.info(name.li.span.get_text()[:1])
                if float(el_price) <= limit_amount:
                    if el_price == '':
                        continue
                    print('found price under limit, adding listing url to list for later use')
                    items_in_query.append(el_listing_url)
                    #self.logger.info('Match ->' + name.h3.a['href'])
                    #items_in_query.append(name.h3.a['href'])
        #self.logger.info("Found " + str(len(items_in_query)) + " items")
        return items_in_query
#https://www.ebay.ca/itm/375249822802?hash=item575ea1e452:g:GIkAAOSwqWplyPfe&itmprp=enc%3AAQAIAAAA4FSetKNc34b4CsArYrptopdoOPCDbwecRJ0X1ZzO8MoiPywgxCxaDktRJOlrJ7it4NJdPj%2F4ILQEepGOu6kGPPiWsLFXyTCDvWcd%2BonKzouh%2FIp1NkTPz8AdPvvkQ%2BDywbaawdJBwmm--vMj549OlilPFyUOcpyrqT0LQUhecPn087YBBm3Id9mpYgTO0t3kiWdesJNHHdtvDJRDfXEiySsAL3%2FdYsGGaiymtPoKx5QDY1VnTU3TWxARQ%2F48h%2B%2Bd4DVX2QLN71JRHx8l44XBSdcDY577lAlTvINenRPGWkek%7Ctkp%3ABFBM1M2RrL5j
#https://www.ebay.com/itm/123456?hash=item28caef0a3a:g:E3kAAOSwlGJiMikD&amdata=enc%3AAQAHAAAAsJoWXGf0hxNZspTmhb8%2FTJCCurAWCHuXJ2Xi3S9cwXL6BX04zSEiVaDMCvsUbApftgXEAHGJU1ZGugZO%2FnW1U7Gb6vgoL%2BmXlqCbLkwoZfF3AUAK8YvJ5B4%2BnhFA7ID4dxpYs4jjExEnN5SR2g1mQe7QtLkmGt%2FZ%2FbH2W62cXPuKbf550ExbnBPO2QJyZTXYCuw5KVkMdFMDuoB4p3FwJKcSPzez5kyQyVjyiIq6PB2q%7Ctkp%3ABlBMULq7kqyXYA
    def bid_on_items(self, search_items, bid_amount=0.06):
        
        if len(search_items) > 0:
            for each in search_items:
                self.driver.get(each)
                try:
                    # if not(driver.find_elements_by_xpath("//*[contains(text(), 're the highest bidder.')]")):
                    #self.driver.get(self.driver.find_element(By.XPATH, "//*[@id='bidBtn_btn']").get_attribute("href"))
                    # if not(driver.find_elements_by_xpath("//*[contains(text(), 'Your max bid:')]")):
                    self.driver.implicitly_wait(2)
                    act = webdriver.ActionChains(self.driver)
                    self.logger.info(str(bid_amount))
                    #act.move_to_element(self.driver.find_element(By.XPATH, "//*[@id='maxbid']")).click().send_keys(str(bid_amount))
                    act.perform()

                    self.driver.implicitly_wait(2)
                    #act.move_to_element(self.driver.find_element(By.XPATH, "//*[@id='but_v4-1']")).click()
                    #act.perform()
                    # driver.find_element_by_id("but_v4-1").click()

                    #self.driver.implicitly_wait(2)
                    #act.move_to_element(self.driver.find_element(By.XPATH, "//*[@id='but_v4-2']")).click()
                    #act.perform()
                    # driver.find_element_by_id("but_v4-2").click()

                    #self.driver.implicitly_wait(2)
                    #act.move_to_element(self.driver.find_element(By.XPATH, "//*[@id='bidBtn_btn']")).click()
                    #act.perform()

                except Exception as e:
                    self.logger.error(e)

                if self.driver.find_elements(By.XPATH, "//*[contains(@id, 'but_v4-0')]"):
                    try:
                        self.driver.find_element(By.ID, "but_v4-0").click()
                    except Exception as e:
                        self.logger.error(e)

    def set_proxy(self):
        PROXY_HOST = os.getenv('PROXY_HOST')
        PROXY_PORT = os.getenv('PROXY_PORT')
        PROXY_USER = os.getenv('PROXY_USER')
        PROXY_PASS = os.getenv('PROXY_PASS')

        manifest_json = """
                {
                    "version": "1.0.0",
                    "manifest_version": 2,
                    "name": "Chrome Proxy",
                    "permissions": [
                        "proxy",
                        "tabs",
                        "unlimitedStorage",
                        "storage",
                        "<all_urls>",
                        "webRequest",
                        "webRequestBlocking"
                    ],
                    "background": {
                        "scripts": ["background.js"]
                    },
                    "minimum_chrome_version":"22.0.0"
                }
                """

        background_js = """
                var config = {
                        mode: "fixed_servers",
                        rules: {
                        singleProxy: {
                            scheme: "http",
                            host: "%s",
                            port: parseInt(%s)
                        },
                        bypassList: ["localhost"]
                        }
                    };

                chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

                function callbackFn(details) {
                    return {
                        authCredentials: {
                            username: "%s",
                            password: "%s"
                        }
                    };
                }

                chrome.webRequest.onAuthRequired.addListener(
                            callbackFn,
                            {urls: ["<all_urls>"]},
                            ['blocking']
                );
                """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

        pluginfile = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        self.options.add_extension(pluginfile)
        # use explicit waits for each element that must be clicked on.
