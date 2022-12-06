from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys


class userReport():

    name = 'userReport'

    def __init__(self):
        try:
            import configs
        except ImportError:
                configs = {}
        self.secretKey = getattr(configs, 'secret_key', '')
        
        self.headless = True
        self.chromeArgs = ['--no-sandbox','start-maximized','disable-infobars','--disable-extensions','window-size=1024,768']
        if self.headless == True: self.chromeArgs.append('--headless')
        

    def checkSecretKey(self,secretKey):
        if self.secretKey != secretKey:
            return False
        return True

    def getpage(self):
        url = "https://scrapeme.live/shop/"
        options = webdriver.ChromeOptions()
        options.headless = self.headless
        for arg in self.chromeArgs:
            options.add_argument(arg)
    
        with webdriver.Chrome(service=ChromeService(ChromeDriverManager().install())) as driver:
	        driver.get(url)