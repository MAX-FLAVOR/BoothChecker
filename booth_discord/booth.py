import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

class BoothCrawler():
    def __init__(self, selenium_url):
        self.selenium_url = selenium_url

    def get_booth_order_info(self, item_number, cookie):
        wait_timeout_seconds = 30

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
            WebDriverWait(driver, wait_timeout_seconds).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "#js-item-order a[href*='/orders/'], #js-item-gift a[href*='/gifts/']"
                    )
                )
            )

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Prefer direct purchase order when both order/gift sections are present.
            order_link = soup.select_one("#js-item-order a[href*='/orders/']")
            if order_link is None:
                order_link = soup.select_one("#js-item-gift a[href*='/gifts/']")
            if order_link is None:
                raise Exception("주문/기프트 링크를 찾지 못했습니다. 쿠키 만료 또는 미구매 상품일 수 있습니다.")

            order_parse = self.parse_url(order_link.get("href", ""))
            return order_parse
        except TimeoutException as exc:
            raise Exception(
                f"페이지 로딩이 지연되어 주문 정보를 찾지 못했습니다. ({wait_timeout_seconds}초 대기)"
            ) from exc
        finally:
            driver.quit()

    def parse_url(self, url):
        pattern = r"(?:https://(?:accounts\.)?booth\.pm)?/(orders|gifts)/([\w-]+)"
        match = re.search(pattern, url)
        
        if match:
            gift_flag = match.group(1) == "gifts"  # gifts이면 True, orders이면 False
            order_number = match.group(2)
            return gift_flag, order_number
        else:
            raise ValueError("URL 형식이 잘못되었습니다.")
