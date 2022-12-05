from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager



class userReport():

    name = 'userReport'

    def __init__(self):
        try:
            import configs
        except ImportError:
                configs = {}
        self.secretKey = getattr(configs, 'secret_key', '')
        self.chromeHeadless = True

    def checkSecretKey(self,secretKey):
        if self.secretKey != secretKey:
            return False
        return True

    def getpage(self):
        url = "https://scrapeme.live/shop/"
        options = webdriver.ChromeOptions()
        options.headless = self.chromeHeadless
        with webdriver.Chrome(service=ChromeService(ChromeDriverManager().install())) as driver:
	        driver.get(url)