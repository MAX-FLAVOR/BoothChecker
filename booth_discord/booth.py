import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

class BoothCrawler():
    def __init__(self, selenium_url):
        self.selenium_url = selenium_url

    def get_booth_order_info(self, item_number, cookie):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Remote(
            command_executor=self.selenium_url,
            options=chrome_options
        )

        driver.get(f"https://booth.pm/ko/items/{item_number}")
        driver.add_cookie({"name": cookie[0], "value": cookie[1]})
        driver.refresh()

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "flex.desktop\\:flex-row.mobile\\:flex-col"))
            )

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
            product_div = soup.find("div", class_="flex desktop:flex-row mobile:flex-col")
            if not product_div:
                raise Exception("상품이 존재하지 않거나, 구매하지 않은 상품입니다.")
            
            order_page = product_div.find("a").get("href")
            order_parse = self.parse_url(order_page)
            return order_parse
        
        finally:
            driver.quit()

    def parse_url(self, url):
        # 정규식 정의
        pattern = r"https://(?:accounts\.)?booth\.pm/(orders|gifts)/([\w-]+)"
        match = re.match(pattern, url)
        
        if match:
            gift_flag = match.group(1) == "gifts"  # gifts이면 True, orders이면 False
            order_number = match.group(2)
            return gift_flag, order_number
        else:
            raise ValueError("URL 형식이 잘못되었습니다.")