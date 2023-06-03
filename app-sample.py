import os.path
import shutil
import zipfile
import hashlib
import re
import requests
import simdjson
from bs4 import BeautifulSoup
from time import sleep
from operator import length_hint
# from jsonpointer import resolve_pointer
from unitypackage_extractor.extractor import extractPackage

# mark_as
#   - 0: Nothing
#   - 1: Added
#   - 2: Deleted
#   - 3: Changed

# download_short_list 
#   - [download_number]
# download_url_list
#   - [download_number, filename]

def crawling(order_num, products, cookie, shortlist = None):
    url = f'https://accounts.booth.pm/orders/{order_num}'
    response = requests.get(url=url, cookies=cookie)
    html = response.content
    
    soup = BeautifulSoup(html, "html.parser")
    
    product_divs = soup.find_all("div", class_="sheet sheet--p400 mobile:pt-[13px] mobile:px-16 mobile:pb-8")
    for product_div in product_divs:
        product_link = product_div.select_one("a")
        product_number = product_link.get("href")
        product_number = re.sub(r'[^0-9]', '', product_number)
        
        if products is not None and product_number not in products:
            continue
        
        divs = product_div.select("div.legacy-list-item__center")
        download_url_list = list()
        
        for div in divs:
            download_link = div.select_one("a.nav-reverse")
            filename_div = div.select_one("div.u-flex-1")
            
            href = download_link.get("href")
            filename = filename_div.get_text()

            href = re.sub(r'[^0-9]', '', href)
            download_url_list.append([href, filename])
            
            if not shortlist is None:
                shortlist.append(href)
            
    return download_url_list


def download_item(download_number, filepath, cookie):
    url = f'https://booth.pm/downloadables/{download_number}'
    
    response = requests.get(url=url, cookies=cookie)
    open(filepath, "wb").write(response.content)
    

def createVersionFile(version_file_path, order_num):
    f = open(version_file_path, 'w')
    
    short_list = {'short-list': [], 'files': {}}
    # shortlist = {"short-list": download_url_list, 'files': {}}
    
    # for fileroot in download_url_list:
    #     shortlist['files'][f'{fileroot}'] = {}
    
    simdjson.dump(short_list, fp = f, indent = 4)
    f.close()
    
    print(f'{order_num} version file created')
    
    
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

def init_update_check(name, url, order_num, products, cookie, webhook_url):
    download_short_list = list()
    download_url_list = crawling(order_num, products, cookie, download_short_list)

    version_file_path = f'./version/{order_num}.json'
    if not os.path.exists(version_file_path):
        print('version file not found')
        createVersionFile(version_file_path, order_num)
    
    file = open(version_file_path, 'r+')    
    version_json = simdjson.load(file)
    
    local_list = version_json['short-list'] 
        
    if length_hint(local_list) > 0 and local_list[0] == download_short_list[0] and local_list[-1] == download_short_list[-1]:
        return
             
    print(f'something has changed on {order_num}')
    
    # give 'marked_as' = 2 on all elements
    for local_file in version_json['files'].keys():
        element_mark(version_json['files'][local_file], 2)
    
    for item in download_url_list: 
        # download stuff
        download_path = f'./download/{item[1]}'
        
        print(f'downloading {item[0]} to {download_path}')
        download_item(item[0], download_path, cookie)
        
        print('parsing its structure')
        init_file_process(download_path, item[1], version_json)
        
    # add webhook
    webhook(webhook_url, name, url, local_list, download_short_list)
    
    # delete all of 'marked_as'
    for local_file in version_json['files'].keys():
        remove_element_mark(version_json['files'][local_file])
    
    version_json['short-list'] = download_short_list
    
    file.seek(0)
    file.truncate()
    simdjson.dump(version_json, fp = file, indent = 4)
    
    file.close()
    

json_level = []

def init_file_process(input_path, filename, version_json):
    json_level.append(filename)
    
    pathstr = ''
    for entry in json_level:
        pathstr += f'{entry}/' 
    pathstr = pathstr[:-1]
    
    isdir = os.path.isdir(input_path)
    filehash = ""
    if not isdir:
        filehash = calc_file_hash(input_path)
        # print(f'{process_path} ({filehash})')
    else:
        filehash = "DIRECTORY"
        
    process_path = f'./process/{pathstr}'
    zip_type = try_extract(input_path, filename, process_path)
    if zip_type > 0 or os.path.isdir(process_path):
        json = version_json.get('files', {})
        pre_json = json
        for entry in json_level:
            # check entry exists in version_json first
            pre_json = json
            json = json.get(entry, None)
            
            if json is None:
                pre_json[entry] = {'hash': filehash, 'mark_as': 1, 'files': {}}
            elif zip_type > 0 and not os.path.isdir(process_path):
                pre_json[entry]['mark_as'] = 0 if pre_json[entry]['hash'] == filehash else 3
                
            json = pre_json[entry]['files']
        
        for new_filename in os.listdir(process_path):
            new_process_path = os.path.join(process_path, new_filename)
            init_file_process(new_process_path, new_filename, version_json)
    
    # print(f'{json_level} + {filename}: zip_type({zip_type}), isdir({isdir})')
    if zip_type == 0 and not isdir:
        json = version_json['files']
        for entry in range(0, len(json_level) - 1, 1):
            json = json[json_level[entry]]['files']
            
        pre_json = json
        json = pre_json.get(filename, None)
        
        if json is None:
            pre_json[filename] = {'hash': filehash, 'mark_as': 1}
        else:
            pre_json[filename]['mark_as'] = 0 if pre_json[json_level[-1]]['hash'] == filehash else 3
        
    json_level.pop()
    end_file_process(zip_type, process_path)
    
        
def end_file_process(zip_type, process_path):
    if zip_type > 0:
        shutil.rmtree(process_path)
    elif os.path.isdir(process_path):
        os.rmdir(process_path)
    else:
        os.remove(process_path)
    
             
def try_extract(input_path, input_filename, output_path):
    zip_type = is_compressed(input_path)
    if zip_type == 1:
        temp_output = f'./{input_filename}'
        shutil.move(input_path, temp_output)
        zip_file = zipfile.ZipFile(temp_output, 'r')
        os.makedirs(output_path, exist_ok=True)
        zip_file.extractall(output_path)
        zip_file.close()
        os.remove(temp_output)
    elif zip_type == 2:
        temp_output = f'./{input_filename}'
        shutil.move(input_path, temp_output)
        os.makedirs(output_path, exist_ok=True)
        extractPackage(temp_output, outputPath=output_path)
        os.remove(temp_output)
    else:
        shutil.move(input_path, output_path)
        
    return zip_type

        

def is_compressed(path):
###
# return
#   - 0: normal
#   - 1: zip
#   - 2: unitypackage
###
    
    if path.endswith('.zip'):
        return 1
    elif path.endswith('.unitypackage'):
        return 2
    
    return 0

def calc_file_hash(path):
    data = open(path, 'rb').read()
    hash = hashlib.md5(data).hexdigest()
    return hash
    
    
def element_mark(root, mark_as): 
    root['mark_as'] = mark_as

    files = root.get('files', None)
    if files is None:
        return
        
    for file in files.keys():
        element_mark(root['files'][file], mark_as)
        
def remove_element_mark(root):
    if root['mark_as'] == 2:
        del root
        return
    
    del root['mark_as']

    files = root.get('files', None)
    if files is None:
        return
        
    for file in files.keys():
        remove_element_mark(root['files'][file])
        

if __name__ == "__main__":
    file = open('checklist.json')
    config_json = simdjson.load(file)

    # 계정
    booth_cookie = {"_plaza_session_nktz7u": config_json['session-cookie']}
    discord_webhook_url = config_json['discord-webhook-url']

    # 갱신 간격 (초)
    refresh_interval = 600
    
    createFolder("./version")
    createFolder("./download")
    createFolder("./process")

    while True:
        for product in config_json['products']:     
            booth_name = product['booth-product-name']
            booth_url = product['booth-product-url']
            booth_order_number = product['booth-order-number']
            booth_products = product.get('booth-check-only')
            
            init_update_check(booth_name, booth_url, booth_order_number, booth_products, booth_cookie, discord_webhook_url)

        # 갱신 대기
        print("waiting for refresh")
        sleep(refresh_interval)
