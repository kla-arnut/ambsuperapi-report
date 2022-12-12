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
from collections import defaultdict
import math


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
        self.betDetails = getattr(configs, 'bet_details', '')

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

        self.memberUserID = None
        self.transactionsRowsPerPage = 500

    def getAllToken(self):
        allToken = defaultdict(dict)
        files = os.listdir(os.path.join(os.getcwd(), r'tokenfile'))
        files = [f for f in files if os.path.isfile(os.path.join(os.getcwd(), r'tokenfile',f))]
        idx = 1
        for file in files:
            tokenFile = json.load(open(os.path.join(os.getcwd(), r'tokenfile',file)))
            allToken[idx].update({'filename':os.path.join(os.getcwd(), r'tokenfile',file), 'auth_token':tokenFile['auth_token'], 'auth_name':tokenFile['auth_name'], 'id_name':tokenFile['id_name']})
            idx =  idx+1
        return allToken

    def checkSecretKey(self,secretKey):
        if self.secretKey != secretKey:
            return False
        return True

    def getReport(self,agentUser,memberUser,dateStart,dateEnd):

        dataRes = defaultdict(dict)
        dataRes = {'success':True,'message':'fetch data success','data':{},'start_date':str(dateStart+'T17:00:00.000Z'),'end_date':str(dateEnd+'T16:59:59.999Z')}

        # check if not found token files or request API with current token (403 prem denied)
        if not os.path.exists(os.path.join(os.getcwd(), r'tokenfile',agentUser)) or self.getCustomerListsByAPI(agentUser,dateStart,dateEnd)['success'] == False:
            self.renewTokenWithChromeDriver(agentUser)

        # test by get customer list again after renew token
        getCus = self.getCustomerListsByAPI(agentUser,dateStart,dateEnd)
        if getCus['success'] == False:
            dataRes['success'] = getCus['success']
            dataRes['message'] = getCus['message']
            return dataRes

        # check if user are not under the agent
        checkUser = self.checkUserUnderAgentByAPI(agentUser,dateStart,dateEnd,memberUser)
        if checkUser['success'] == False:
            dataRes['success'] = checkUser['success']
            dataRes['message'] = checkUser['message']
            return dataRes

        # get all user transaction
        userTransactions = self.getAllUserTransactionsByAPI(agentUser,memberUser,dateStart,dateEnd)
        if userTransactions['success'] == False:
            dataRes['success'] = userTransactions['success']
            dataRes['message'] = userTransactions['message']
            return dataRes

        dataRes['data'] = userTransactions
        return dataRes

    def getAllUserTransactionsByAPI(self,agentUser,memberUser,dateStart,dateEnd):

        userTransactions = defaultdict(dict)

        response = self.apiRequest(agentUser, self.betDetails, self.memberUserID, dateStart, dateEnd, '1', str(self.transactionsRowsPerPage),'getAllUserTransactionsByAPI')
        if 'success' in response and  'data' in response and  len(response['data']) == 0: #empty data
            return {'success':False,'message':'not found data transaction for user %s (%s)'%(memberUser,self.memberUserID)}
        elif 'success' in response and response['success'] == False:
            return {'success':response['success'],'message':'cannot get data for user: %s (%s) agent: %s'%(memberUser,self.memberUserID,agentUser)}


        userTransactions['cus_id'] = response['data']['id']
        userTransactions['cus_type'] = response['data']['type']
        userTransactions['cus_currency'] = response['data']['currency']
        userTransactions['total']['grand_total'] = response['data']['grandTotal']['realBets']
        userTransactions['total']['cus_winlose'] = response['data']['grandTotal']['total']['member']
        userTransactions['total']['agent_winlose'] = response['data']['grandTotal']['total']['toOperator']
        userTransactions['total']['company_winlose'] = response['data']['grandTotal']['total']['toReseller']
        userTransactions['list_transactions'] = response['data']['list']

        pageRegCount = math.ceil(response['data']['grandCount'] / self.transactionsRowsPerPage)
        if pageRegCount <= 1:
            return userTransactions

        for pageCount in range(2, pageRegCount+1):
            response = self.apiRequest(agentUser, self.betDetails, self.memberUserID, dateStart, dateEnd, str(pageCount), str(self.transactionsRowsPerPage),'getAllUserTransactionsByAPI')
            if 'success' in response and response['success'] == True and 'data' in response and  len(response['data']) != 0 :
                userTransactions['list_transactions'].extend(response['data']['list'])
            else:
                print('error fetch data for user %s (%s)'%(memberUser,self.memberUserID))

        return userTransactions

    def checkUserUnderAgentByAPI(self,agentUser,dateStart,dateEnd,memberUser):

        response = self.apiRequest(agentUser, self.winloseAPI, memberUser, dateStart, dateEnd, '1', '100','checkUserUnderAgentByAPI')
        if 'success' in response and response['success']  == True:
            self.memberUserID = response['data']['username']
            response['message'] = '%s is under %s'%(memberUser, agentUser)
        elif response['success']  == False and 'error' in response:
            response['message'] = '%s (user %s not found OR not under the agent %s OR user has no transactions on selected dat)'%(response['error']['message'],memberUser,agentUser)

        return response

    def apiRequest(self, agentUser, urlReg, memberUser, dateStart, dateEnd, page, pageSize, functionCall):

        tokenFile = json.load(open(os.path.join(os.getcwd(), r'tokenfile',agentUser)))

        self.apiRegHeaders['auth-name'] = tokenFile['auth_name']
        self.apiRegHeaders['auth-token'] = tokenFile['auth_token']

        urlParam = '?id=%s'%tokenFile['id_name'] if functionCall != 'getAllUserTransactionsByAPI' else '?id=%s'%memberUser
        urlParam = urlParam + '&currency=THB'
        if functionCall != 'getAllUserTransactionsByAPI':
            urlParam = urlParam + '&username=%s'%memberUser if memberUser != None else urlParam + '&username='
        urlParam = urlParam + '&product='
        urlParam = urlParam + '&category='
        urlParam = urlParam + '&startDate=%s'%dateStart+'T17:00:00.000Z'
        urlParam = urlParam + '&endDate=%s'%dateEnd+'T16:59:59.999Z'
        if functionCall != 'getAllUserTransactionsByAPI':
            urlParam = urlParam + '&reportBy=account'
        urlParam = urlParam + '&page=%s'%page
        urlParam = urlParam + '&pageSize=%s'%pageSize
        urlParam = urlParam + '&timezone=7'

        try:
            response = requests.get(urlReg+urlParam,headers=self.apiRegHeaders)
        except requests.exceptions.RequestException as e:
            print('error',e)
            print('request error url:',urlReg+urlParam)
            return {'success':False ,'message':'request error url: %s%s'%(urlReg,urlParam) }

        try:
            responseJSON = response.json()
        except ValueError as e:  # includes simplejson.decoder.JSONDecodeError
            print('decoding JSON from',urlReg+urlParam,'has failed')
            return {'success':False,'message':'cannot decode json from %s%s'%(urlReg,urlParam)}

        if 'statusCode' in responseJSON and responseJSON['statusCode'] == 403: # Forbidden
            print('api request error code: %s message: %s'%(responseJSON['statusCode'],responseJSON['message']))
            return {'success':False,'message':'Forbidden resource (403)','statusCode':403,'error':'Forbidden(403)'}

        if response.status_code != 200:
            return {'success':False, 'message':'response status code error %s errorcode:%s'%(urlReg,response.status_code)}

        return responseJSON

    def getCustomerListsByAPI(self,agentUser,dateStart,dateEnd):

        response = self.apiRequest(agentUser, self.winloseAPI, None, dateStart, dateEnd, '1', '100','getCustomerListsByAPI')
        return(response)

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
