import os.path
import requests
from bs4 import BeautifulSoup


def parser(order_num, cookie):
    url = (f'https://accounts.booth.pm/orders/{order_num}')
    response = requests.get(url=url, cookies=cookie)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div", class_="u-ml-500")
    download_url = list()
    for div in divs:
        download_link = div.select_one("a.nav-reverse")
        href = download_link.get("href")
        download_url.append(href)
    if download_link == []:
        print("BOOTH no response")
    return download_url


def file_save(version_file, order_num):
    f = open(f'./version/{order_num}.txt', "w")
    for result in version_file:
        f.write(result + "\n")
    f.close()
    print(f'{order_num} version file saved')


def discord_webhook(webhook_url, name, content):
    data = {
        "username" : "부스 업데이트 체크",
        "content" : (f'{name} {content}')
    }
    requests.post(webhook_url, json=data)


def update_cheker(name, url, order_num, cookie, version_file, webhook_url):
    download_url = parser(order_num, cookie)
    version_file = (f'./version/{order_num}.txt')
    if os.path.exists(version_file):
        with open(version_file) as f:
            version_file = f.readlines()
        version_file = [line.rstrip('\n') for line in version_file]
        if sorted(version_file) != sorted(download_url):
            result = (f'업데이트 있음 \n {url}')
            print(f'{name} 업데이트 있음')
            discord_webhook(webhook_url, name, result)
        else:
            print(f'{name} 업데이트 없음')
        file_save(version_file, order_num)
    else:
        file_save(version_file, order_num)


if __name__ == "__main__":
    # 계정
    booth_cookie = {"_plaza_session_nktz7u": "(BOOTH 계정 쿠키 값)"}
    discord_webhook_url = "(디스코드 Webhook URL)"

    # 아바타_0
    booth_name = "아바타_0"
    booth_url = "BOOTH 상품 페이지 URL"
    booth_order_number = "BOOTH 주문 번호"
    version_server_url = "app.py에서 생성된 파일 URL"
    update_cheker(booth_name, booth_url, booth_order_number, booth_cookie, version_server_url, discord_webhook_url)

    # 아바타_1
    booth_name = "아바타_1"
    booth_url = "BOOTH 상품 페이지 URL"
    booth_order_number = "BOOTH 주문 번호"
    version_server_url = "app.py에서 생성된 파일 URL"
    update_cheker(booth_name, booth_url, booth_order_number, booth_cookie, version_server_url, discord_webhook_url)
