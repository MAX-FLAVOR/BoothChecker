import os.path
import re
import requests
from bs4 import BeautifulSoup
from time import sleep

jsonString = "" 

def crawling(order_num, cookie):
    url = f'https://accounts.booth.pm/orders/{order_num}'
    response = requests.get(url=url, cookies=cookie)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div", class_="u-ml-500")
    download_url_list = list()
    for div in divs:
        download_link = div.select_one("a.nav-reverse")
        href = download_link.get("href")
        href = re.sub(r'[^0-9]', '', href)
        download_url_list.append(href)
    return download_url_list


def file_save(version_file_path, download_url_list, order_num):
    f = open(version_file_path, "w+")
    for result in download_url_list:
        f.write(result + "\n")
    f.close()
    print(f'{order_num} version file saved')
    
def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)


def webhook(webhook_url, name, url, version_list, download_url_list):
    fields = list()
    fields.append({"name": "이름", "value": name})
    fields.append({"name": "URL", "value": url})
    fields.append({"name": "LOCAL", "value": str(version_list), "inline": True})
    fields.append({"name": "BOOTH", "value": str(download_url_list), "inline": True})
    payload = {
        "content": "@here",
        "embeds": [
            {
                "title": "BOOTH 업데이트 발견",
                "color": 65280,
                "fields": fields
            }
        ]  
    }
    requests.post(webhook_url, json=payload)

def error_webhook(webhook_url):
    payload = {
        "content": "@here",
        "embeds": [
            {
                "title": "BOOTH 응답 없음",
                "color": 16711680
            }
        ]  
    }
    requests.post(webhook_url, json=payload)


def update_cheker(name, url, order_num, cookie, webhook_url):
    download_url_list = crawling(order_num, cookie)
    if not download_url_list:
        print(f'BOOTH 응답 없음')
        error_webhook(webhook_url)
    else:
        version_file_path = f'./version/{order_num}.txt'
        if os.path.exists(version_file_path):
            with open(version_file_path) as f:
                version_list = f.readlines()
            version_list = [line.rstrip('\n') for line in version_list]
            print(f'{name} version check')
            print(f'LOCAL : {version_list}')
            print(f'BOOTH : {download_url_list}')
            if sorted(version_list) != sorted(download_url_list):
                print(f'{name} 업데이트 발견')
                webhook(webhook_url, name, url, version_list, download_url_list)
                file_save(version_file_path, download_url_list, order_num)
            else:
                print(f'{name} 업데이트 없음')
        else:
            print("version file not found")
            file_save(version_file_path, download_url_list, order_num)


if __name__ == "__main__":
    file = open('checklist.json')
    jsonString = simdjson.load(file)

    # 계정
    booth_cookie = {"_plaza_session_nktz7u": jsonString['session-cookie']}
    discord_webhook_url = jsonString['discord-webhook-url']

    # 갱신 간격 (초)
    refresh_interval = 600
    createFolder("./version")

    while True:
        for product in jsonString['products']:     
            booth_name = product['booth-product-name']
            booth_url = product['booth-product-url']
            booth_order_number = product['booth-order-number']
            
            update_cheker(booth_name, booth_url, booth_order_number, booth_cookie, discord_webhook_url)

        # 갱신 대기
        print("waiting for refresh")
        sleep(refresh_interval)
