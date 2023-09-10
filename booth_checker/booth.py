import requests
import re
from bs4 import BeautifulSoup

def crawling(order_num, product_only, cookie, shortlist = None, thumblist = None):
    url = f'https://accounts.booth.pm/orders/{order_num}'
    response = requests.get(url=url, cookies=cookie)
    html = response.content
    
    download_url_list = list()
    product_info_list = list()
    soup = BeautifulSoup(html, "html.parser")
    
    product_divs = soup.find_all("div", class_="sheet sheet--p400 mobile:pt-[13px] mobile:px-16 mobile:pb-8")
    for product_div in product_divs:
        product_info = product_div.select("a")[1]
        product_name = product_info.get_text()
        product_url = product_info.get("href")
        product_number = re.sub(r'[^0-9]', '', product_url)
        
        if product_only is not None and product_number not in product_only:
            continue
        
        product_info_list.append([product_name, product_url])

        thumb_link = product_div.select_one("img")
        thumb_url = thumb_link.get("src")
        if not thumblist is None:
            thumblist.append(thumb_url)
        
        divs = product_div.select("div.legacy-list-item__center")
        for div in divs:
            download_link = div.select_one("a.nav-reverse")
            filename_div = div.select_one("div.u-flex-1")
            
            href = download_link.get("href")
            filename = filename_div.get_text()

            href = re.sub(r'[^0-9]', '', href)
            download_url_list.append([href, filename])
            
            if not shortlist is None:
                shortlist.append(href)
            
    return download_url_list, product_info_list


def download_item(download_number, filepath, cookie):
    url = f'https://booth.pm/downloadables/{download_number}'
    
    response = requests.get(url=url, cookies=cookie)
    open(filepath, "wb").write(response.content)


def crawling_product(url):
    response = requests.get(url)
    html = response.content
    
    soup = BeautifulSoup(html, "html.parser")
    author_div = soup.find("a", class_="flex gap-4 items-center no-underline preserve-half-leading !text-current typography-16 w-fit")
    # None: private store
    if author_div is None:
        return None
    
    author_image = author_div.select_one("img")
    author_image_url = author_image.get("src")
    author_name = author_image.get("alt")
    
    return [author_image_url, author_name]