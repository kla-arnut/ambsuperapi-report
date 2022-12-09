from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup as bs
from collections import defaultdict
from datetime import date
from datetime import timedelta
from selenium.webdriver.common.action_chains import ActionChains



class userReport():

    name = 'userReport'

    def __init__(self):
        #define config
        try:
            import configs
        except ImportError:
                configs = {}

        #set config
        self.secretKey = getattr(configs, 'secret_key', '')
        self.loginPage = getattr(configs, 'login_page', '')
        self.winlosePage = getattr(configs, 'winlose_page', '')
        self.userLogin = getattr(configs, 'user_login', '')
        self.userPassword = getattr(configs, 'user_password', '')

        #chromedriver args
        self.headless = False
        self.chromeArgs = ['--no-sandbox','start-maximized','disable-infobars','--disable-extensions','--disable-gpu'] #'window-size=1024,768',
        if self.headless == True: self.chromeArgs.append('--headless')


    def checkSecretKey(self,secretKey):
        if self.secretKey != secretKey:
            return False
        return True

    def worker(self,agentUser,memberUser,dateStart,dateEnd):
        options = webdriver.ChromeOptions()
        for arg in self.chromeArgs:
            options.add_argument(arg)

        with webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=options) as driver:
            # open login page
            driver.get(self.loginPage)
            # wait and input username
            userName = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'inputUserName')))
            userName.send_keys(self.userLogin)
            # wait and input password
            password = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'inputPassword')))
            password.send_keys(self.userPassword)
            # click sign in
            submit = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'login')))
            submit.click()
            # wait for logged in
            time.sleep(6)

            # open win lose report page
            driver.get(self.winlosePage)
            # select 500 rows show in table
            selectRows = Select(WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'form-control'))))
            selectRows.select_by_visible_text('500')
            time.sleep(6)
            # select startdate-enddate (only yesterday)
            yesterdayRadio = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/main/div/div[2]/div/div/label[3]')))
            yesterdayRadio.click()
            time.sleep(5)
            
            # open page only agent input
            agentName = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.LINK_TEXT, agentUser)))
            agentName.click()
            time.sleep(5)

            # extract data
            dataRes = defaultdict(dict)
            soup = bs(driver.page_source,'html.parser')
            tr = soup.find('tbody').find_all('tr')
            for row in tr:
                columns = row.find_all('td')
                if (columns != []):
                    if columns[1].text.strip() == memberUser: 
                        dataRes[memberUser]['member_wl_100_percent'] = columns[5].text.strip()
                        dataRes[memberUser]['member_wl'] = columns[8].text.strip()
                        dataRes[memberUser]['member_comm'] = columns[9].text.strip()
                        dataRes[memberUser]['member_total'] = columns[10].text.strip()
                        dataRes[memberUser]['date_start'] = str(date.today() - timedelta(days = 1))
                        dataRes[memberUser]['date_end'] = str(date.today() - timedelta(days = 1))
                        break
            
            driver.save_screenshot('ss.png')
            driver.quit()

            return dataRes

