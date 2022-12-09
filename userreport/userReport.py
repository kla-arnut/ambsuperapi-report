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
from datetime import date
from datetime import datetime
from datetime import timedelta
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
import os
import re
import requests

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
        self.agentLogin = getattr(configs, 'agent_login', [])
        self.winloseAPI = getattr(configs, 'winlose_api', '')

        #chromedriver args
        self.headless = False
        self.chromeArgs = ['--no-sandbox','start-maximized','disable-infobars','--disable-extensions','--disable-gpu'] #'window-size=1024,768',
        if self.headless == True: self.chromeArgs.append('--headless')

        #api request default
        self.apiRegHeaders = {
            'auth-name': None,
            'auth-token': None,
            'authority': 'api.ambsuperapi.com', 
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,th;q=0.7',
            'cache-control': 'no-cache',
            'origin': 'https://ambsuperapi.com',
            'pragma': 'no-cache',
            'referer': 'https://ambsuperapi.com/',
            'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }
        self.pageSize = 500

    def checkSecretKey(self,secretKey):
        if self.secretKey != secretKey:
            return False
        return True

    def getReport(self,agentUser,memberUser,dateStart,dateEnd):

        # check if not found token files or request API with current token (403 prem denied)
        if not os.path.exists(os.path.join(os.getcwd(), r'tokenfile',agentUser)) or self.getCustomerListsByAPI(agentUser,dateStart,dateEnd) == False:
            self.renewTokenWithChromeDriver(agentUser)

        # test by get customer list again after renew token
        if self.getCustomerListsByAPI(agentUser,dateStart,dateEnd) == False:
            
        # check if user are not under the agent 



    def getCustomerListsByAPI(self,agentUser,dateStart,dateEnd):
        
        token = json.load(open(os.path.join(os.getcwd(), r'tokenfile',agentUser)))

        self.apiRegHeaders['auth-name'] = token['auth_name']
        self.apiRegHeaders['auth-token'] = token['auth_token']

        urlParam =            '/?id=%s'%token['id_name']
        urlParam = urlParam + '&currency=THB'
        urlParam = urlParam + '&username='
        urlParam = urlParam + '&startDate=%s'%dateStart+'T17:00:00.000Z'
        urlParam = urlParam + '&endDate=%s'%dateEnd+'T16:59:59.999Z'
        urlParam = urlParam + '&product='
        urlParam = urlParam + '&category='
        urlParam = urlParam + '&reportBy=account'
        urlParam = urlParam + '&page=1'
        urlParam = urlParam + '&pageSize=100'
        urlParam = urlParam + '&timezone=7'
        
        response = requests.get(self.winloseAPI+urlParam,headers=self.apiRegHeaders)
        response = response.json()
        if response['status_code'] != 200: # 403 prem denied
            return False
        return True
    
    def renewTokenWithChromeDriver(self,agentUser):
        options = webdriver.ChromeOptions()
        for arg in self.chromeArgs:
            options.add_argument(arg)
        
        capabilities = DesiredCapabilities.CHROME
        capabilities["goog:loggingPrefs"] = {"performance": "ALL"}

        with webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=options,desired_capabilities=capabilities) as driver:
            # open login page
            driver.get(self.loginPage)
            # wait and input username
            userName = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'inputUserName')))
            userName.send_keys(agentUser)
            # wait and input password
            password = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'inputPassword')))
            password.send_keys(self.agentLogin[agentUser]['password'])
            # click sign in
            submit = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'login')))
            submit.click()
            # wait for logged in
            time.sleep(5)

            # open win lose report page
            driver.get(self.winlosePage)
            time.sleep(5)

            # get XHR log and write to file
            logs = driver.get_log("performance")
            events = self.ProcessBrowserLogsForNetworkEvents(logs)
            
            token = {'id_name': None,'auth_name': None,'auth_token': None}
            regex = r"'auth-name'\s*:\s*'(%s)'.\s*'auth-token'\s*:\s*'([a-zA-Z0-9\-\_]+.[a-zA-Z0-9\-\_]+.[a-zA-Z0-9\-\_]+)'.*|\s*'url'\s*:\s*'.*report\/winLose\?id=(.*?)&"%agentUser
            for event in events:
                matches = re.finditer(regex, str(event), re.MULTILINE)
                for matchNum, match in enumerate(matches, start=1):
                    #print ("Match {matchNum} was found at : {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
                    for groupNum in range(0, len(match.groups())):
                        groupNum = groupNum + 1
                        #print ("Group {groupNum} found at : {group}".format(groupNum = groupNum, start = match.start(groupNum), end = match.end(groupNum), group = match.group(groupNum)))
                        if match.group(groupNum) != None and groupNum == 1:
                            token['auth_name'] = match.group(groupNum)
                        if match.group(groupNum) != None and groupNum == 2:
                            token['auth_token'] = match.group(groupNum)
                        if match.group(groupNum) != None and groupNum == 3:
                            token['id_name'] = match.group(groupNum)
                        if token['auth_name'] != None and token['auth_token'] != None and token['id_name'] != None: 
                            break
            if not os.path.exists(os.path.join(os.getcwd(), r'tokenfile')): os.makedirs(os.path.join(os.getcwd(), r'tokenfile'))
            with open(os.path.join(os.getcwd(), r'tokenfile',agentUser), "w") as outfile:
                json.dump(token, outfile)

        return True

    def ProcessBrowserLogsForNetworkEvents(self,logs):
        """
        Return only logs which have a method that start with "Network.response", "Network.request", or "Network.webSocket"
        since we're interested in the network events specifically.
        """
        for entry in logs:
            log = json.loads(entry["message"])["message"]
            if ("Network.response" in log["method"] or "Network.request" in log["method"]or "Network.webSocket" in log["method"]):
                yield log
                