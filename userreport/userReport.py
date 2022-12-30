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
        self.headLogin = getattr(configs, 'head_login', [])
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
        print("FN->",userReport.getAllToken.__name__)

        allToken = defaultdict(dict)
        if os.path.exists(os.path.join(os.getcwd(), r'tokenfile')):
            files = os.listdir(os.path.join(os.getcwd(), r'tokenfile'))
            files = [f for f in files if os.path.isfile(os.path.join(os.getcwd(), r'tokenfile',f))]
            idx = 1
            for file in files:
                tokenFile = json.load(open(os.path.join(os.getcwd(), r'tokenfile',file)))
                allToken[idx].update({'filename':os.path.join(os.getcwd(), r'tokenfile',file), 'auth_token':tokenFile['auth_token'], 'auth_name':tokenFile['auth_name'], 'id_name':tokenFile['id_name']})
                idx =  idx+1
        return allToken

    def checkSecretKey(self,secretKey):
        print("FN->",userReport.checkSecretKey.__name__)

        if self.secretKey != secretKey:
            return {'success':False,'message':'secret key error','data':{}}
        return {'success':True,'message':'secret key correct','data':{}}

    def getReport(self,agentUser,memberUser,dateStart,dateEnd):
        print("FN->",userReport.getReport.__name__)

        dataRes = defaultdict(dict)
        dataRes = {'success':True,'message':'fetch data success','data':{},'start_date':str(dateStart+'T17:00:00.000Z'),'end_date':str(dateEnd+'T16:59:59.999Z')}

        # check if not found token files
        if not os.path.exists(os.path.join(os.getcwd(), r'tokenfile',agentUser)):
            self.renewTokenWithChromeDriver(agentUser)

        # test by get customer list by current token or request API with current token (403 prem denied)
        getCus = self.getCustomerListsByAPI(agentUser,dateStart,dateEnd)
        # check if 403 (forbidden token expire)
        if getCus['success'] == False and 'statusCode' in getCus and getCus['statusCode'] == 403:
            self.renewTokenWithChromeDriver(agentUser)
            getCus = self.getCustomerListsByAPI(agentUser,dateStart,dateEnd)
            if getCus['success'] == False:
                dataRes['success'] = getCus['success']
                dataRes['message'] = getCus['message']
                return dataRes

        # check if user are not under the agent
        checkUser = self.getRealUserID(agentUser,dateStart,dateEnd,memberUser)
        if checkUser['success'] == False:
            dataRes['success'] = checkUser['success']
            dataRes['message'] = checkUser['message']
            return dataRes

        # get all user transaction
        userTransactions = self.getAllUserTransactionsByAPI(agentUser,memberUser,dateStart,dateEnd)
        if 'success' in userTransactions and userTransactions['success'] == False:
            dataRes['success'] = userTransactions['success']
            dataRes['message'] = userTransactions['message']
            return dataRes

        dataRes['data'] = userTransactions

        return dataRes
    
    def getRealUserID(self,agentUser,dateStart,dateEnd,memberUser):
        print("FN->",userReport.getRealUserID.__name__)

        # if user id is exists
        if os.path.exists(os.path.join(os.getcwd(), r'allUserData.json')):
            allUserData = json.load(open(os.path.join(os.getcwd(), r'allUserData.json')))
            for agent in allUserData['agents']:
                for member in agent['members']:
                    if member['name'] == memberUser:
                        self.memberUserID = member['id']
                        print('member:%s id:%s is is exists in current json file agent(%s)->member(%s)'%(memberUser, member['id'],agent['name'],memberUser))
                        return {'success':True,'message':'success'}

        # if user id is not exists in json file or allUserData.json not exists
        allUserData = defaultdict(dict)
        allUserData['resellers'] = []
        allUserData['agents'] = []

        # get all resellers
        response = self.apiRequest(agentUser, self.winloseAPI, None, dateStart, dateEnd, '1', '100','getRealUserID')
        if response['success'] == False:
            if 'error' in response:
                response['message'] = str(response['message']) + str(response['error'])
            return response
        for resellers in response['data']['list'][0]['rows']:
            if resellers['type'] == 'Reseller':
                allUserData['resellers'].append({'myid':resellers['myId'],'id':resellers['id'],'name':resellers['name']})
            elif resellers['type'] == 'Operator':
                allUserData['agents'].append({'myid':resellers['myId'],'id':resellers['id'],'name':resellers['name'],'members':[]})
        pageRegCount = math.ceil(response['data']['list'][0]['grandCount'] / 100)
        if pageRegCount > 1:
            print('list resellers page count',int(pageRegCount+1))
            for pageCount in range(2, pageRegCount+1):
                print('list resellers request page',pageCount)
                response = self.apiRequest(agentUser, self.winloseAPI, None, dateStart, dateEnd, str(pageCount), '100','getRealUserID')
                if 'success' in response and response['success'] == True and 'rows' in response['data']['list'][0] and  len(response['data']['list'][0]['rows']) != 0 :
                    for resellers in response['data']['list'][0]['rows']:
                        if resellers['type'] == 'Reseller' :
                            allUserData['resellers'].append({'myid':resellers['myId'],'id':resellers['id'],'name':resellers['name']})
                        elif resellers['type'] == 'Operator':
                            allUserData['agents'].append({'myid':resellers['myId'],'id':resellers['id'],'name':resellers['name'],'members':[]})
                else:
                    print('error fetch data resellers %s '%response['message'])

        # get all agents  
        for reseller in allUserData['resellers']:
            response = self.apiRequest(agentUser, self.winloseAPI, reseller['id'], dateStart, dateEnd, '1', '100','getRealUserID')
            if response['success'] == False:
                if 'error' in response:
                    response['message'] = str(response['message']) + str(response['error'])
                with open(os.path.join(os.getcwd(), r'allUserData.json'), "w") as outfile:
                    json.dump(allUserData, outfile, indent=4)
                return response
            for agent in response['data']['list'][0]['rows']:
                if agent['type'] == 'Operator':
                    allUserData['agents'].append({'myid':agent['myId'], 'id':agent['id'], 'name':agent['name'],'members':[]})
            pageRegCount = math.ceil(response['data']['list'][0]['grandCount'] / 100)
            if pageRegCount > 1:
                print('list agent page count',int(pageRegCount+1))
                for pageCount in range(2, pageRegCount+1):
                    print('list resellers request page',pageCount)
                    response = self.apiRequest(agentUser, self.winloseAPI, reseller['id'], dateStart, dateEnd, str(pageCount), '100','getRealUserID')
                    if 'success' in response and response['success'] == True and 'rows' in response['data']['list'][0] and  len(response['data']['list'][0]['rows']) != 0 :
                        for agent in response['data']['list'][0]['rows']:
                            if agent['type'] == 'Operator':
                                allUserData['agents'].append({'myid':agent['myId'], 'id':agent['id'], 'name':agent['name'],'members':[]})
                    else:
                        print('error fetch data resellers %s '%response['message'])
        
        # get all member
        agentIdx = 0
        for agent in allUserData['agents']:
            response = self.apiRequest(agentUser, self.winloseAPI, agent['id'], dateStart, dateEnd, '1', '500','getRealUserID')
            if response['success'] == False:
                if 'error' in response:
                    response['message'] = str(response['message']) + str(response['error'])
                with open(os.path.join(os.getcwd(), r'allUserData.json'), "w") as outfile:
                    json.dump(allUserData, outfile, indent=4)
                return response
            for member in response['data']['list'][0]['rows']:
                if member['type'] == 'Member':
                    allUserData['agents'][agentIdx]['members'].append({'name':member['name'], 'id':member['id']})
            pageRegCount = math.ceil(response['data']['list'][0]['grandCount'] / 500)
            if pageRegCount > 1:
                print('list agent page count',int(pageRegCount+1))
                for pageCount in range(2, pageRegCount+1):
                    print('list resellers request page',pageCount)
                    response = self.apiRequest(agentUser, self.winloseAPI, agent['id'], dateStart, dateEnd, '1', '500','getRealUserID')
                    if 'success' in response and response['success'] == True and 'rows' in response['data']['list'][0] and  len(response['data']['list'][0]['rows']) != 0 :
                        for member in response['data']['list'][0]['rows']:
                            if member['type'] == 'Member':
                                allUserData['agents'][agentIdx]['members'].append({'name':member['name'], 'id':member['id']})
                    else:
                        print('error fetch data resellers %s '%response['message'])
            agentIdx = agentIdx +1
        
        # save to file
        with open(os.path.join(os.getcwd(), r'allUserData.json'), "w") as outfile:
            json.dump(allUserData, outfile, indent=4)
        
        # find member id  
        for agent in allUserData['agents']:
            for member in agent['members']:
                if member['name'] == memberUser:
                    self.memberUserID = member['id']
                    print('member:%s id:%s is exists with renew by api agent(%s)->member(%s)'%(memberUser, member['id'],agent['name'],memberUser))
                    return {'success':True,'message':'success'}

        return {'success':False,'message':'can not file user id by username %s'%memberUser}


    def getAllUserTransactionsByAPI(self,agentUser,memberUser,dateStart,dateEnd):
        print("FN->",userReport.getAllUserTransactionsByAPI.__name__)

        print('user transection request page 1')
        response = self.apiRequest(agentUser, self.betDetails, self.memberUserID, dateStart, dateEnd, '1', str(self.transactionsRowsPerPage),'getAllUserTransactionsByAPI')
        if 'success' in response and  'data' in response and  len(response['data']) == 0: #empty data
            return {'success':False,'message':'not found data transaction for user %s (%s)'%(memberUser,self.memberUserID)}
        elif 'success' in response and response['success'] == False:
            return {'success':response['success'],'message':'cannot get data for user: %s (%s) agent: %s'%(memberUser,self.memberUserID,agentUser)}

        userTransactions = defaultdict(dict)
        userTransactions['cus_member'] = response['data']['id']
        userTransactions['cus_id'] = self.memberUserID
        userTransactions['cus_type'] = response['data']['type']
        userTransactions['cus_currency'] = response['data']['currency']
        userTransactions['cus_agent'] = agentUser
        userTransactions['total']['grand_total'] = response['data']['grandTotal']['realBets']
        userTransactions['total']['cus_winlose'] = response['data']['grandTotal']['total']['member']
        userTransactions['total']['agent_winlose'] = response['data']['grandTotal']['total']['toOperator']
        userTransactions['total']['company_winlose'] = response['data']['grandTotal']['total']['toReseller']
        userTransactions['total_transactions'] = response['data']['grandCount']
        userTransactions['list_transactions'] = response['data']['list']

        pageRegCount = math.ceil(response['data']['grandCount'] / self.transactionsRowsPerPage)
        if pageRegCount <= 1:
            print('user transection page count',pageRegCount)
            return userTransactions

        print('user transection page count',int(pageRegCount+1))
        for pageCount in range(2, pageRegCount+1):
            print('user transection request page',pageCount)
            response = self.apiRequest(agentUser, self.betDetails, self.memberUserID, dateStart, dateEnd, str(pageCount), str(self.transactionsRowsPerPage),'getAllUserTransactionsByAPI')
            if 'success' in response and response['success'] == True and 'data' in response and  len(response['data']) != 0 :
                userTransactions['list_transactions'].extend(response['data']['list'])
            else:
                print('error fetch data for user %s (%s)'%(memberUser,self.memberUserID))

        return userTransactions

    def apiRequest(self, agentUser, urlReg, memberUser, dateStart, dateEnd, page, pageSize, functionCall):
        print("FN->",userReport.apiRequest.__name__)

        tokenFile = json.load(open(os.path.join(os.getcwd(), r'tokenfile',agentUser)))

        self.apiRegHeaders['auth-name'] = tokenFile['auth_name']
        self.apiRegHeaders['auth-token'] = tokenFile['auth_token']

        if functionCall == 'getRealUserID' and memberUser != None:
            urlParam = '?id=%s'%memberUser
        elif functionCall != 'getAllUserTransactionsByAPI':
            urlParam = '?id=%s'%tokenFile['id_name']
        else: 
            urlParam = '?id=%s'%memberUser
        urlParam = urlParam + '&currency=THB'
        if functionCall != 'getAllUserTransactionsByAPI':
            if functionCall == 'getRealUserID' and memberUser != None:
                urlParam = urlParam + '&username='
            elif memberUser != None:
                urlParam = urlParam + '&username=%s'%memberUser
            else: 
                urlParam = urlParam + '&username='
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
            print('response is not return 200OK',response.status_code)
            return {'success':False, 'message':'response status code error %s errorcode:%s'%(urlReg,response.status_code)}

        return responseJSON

    def getCustomerListsByAPI(self,agentUser,dateStart,dateEnd):
        print("FN->",userReport.getCustomerListsByAPI.__name__)

        response = self.apiRequest(agentUser, self.winloseAPI, None, dateStart, dateEnd, '1', '100','getCustomerListsByAPI')

        if 'success' in response and response['success'] == True:
            print('current api worked True')
            return response

        print('can not get customer lists by API')
        return response

    def renewTokenWithChromeDriver(self,agentUser):
        print("FN->",userReport.renewTokenWithChromeDriver.__name__)

        print('create/renew token file by chrome webdriver')
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
            password.send_keys(self.headLogin[agentUser]['password'])
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
                json.dump(token, outfile, indent=4)
                print('create token file',outfile)

        return True

    def ProcessBrowserLogsForNetworkEvents(self,logs):
        print("FN->",userReport.ProcessBrowserLogsForNetworkEvents.__name__)

        """
        Return only logs which have a method that start with "Network.response", "Network.request", or "Network.webSocket"
        since we're interested in the network events specifically.
        """
        for entry in logs:
            log = json.loads(entry["message"])["message"]
            if ("Network.response" in log["method"] or "Network.request" in log["method"]or "Network.webSocket" in log["method"]):
                yield log
