import shutil
import zipfile
import hashlib
import requests

from time import sleep
from datetime import datetime
from PIL import Image, ImageDraw
from operator import length_hint
from unitypackage_extractor.extractor import extractPackage

from log import *
from shared import *
import booth
import image
import discord

# mark_as
#   - 0: Nothing
#   - 1: Added
#   - 2: Deleted
#   - 3: Changed

# download_short_list 
#   - [download_number]
# download_url_list
#   - [download_number, filename]

def init_update_check(product):
    order_num = product['booth-order-number']
    name = product.get('booth-product-name')
    check_only_list = product.get('booth-check-only')
    encoding = product.get('intent-encoding')
    number_show = product.get('download-number-show')
    changelog_show = product.get('changelog-show')
    archive_this = product.get('archive_this', True)
            
    download_short_list = list()
    thumblist = list()
    download_url_list = booth.crawling(order_num, check_only_list, booth_cookie, download_short_list, thumblist)

    if name is None:
        name = download_url_list[1][0][0]
    url = download_url_list[1][0][1]

    download_url_list = download_url_list[0]

    version_filename = product.get('custom-version-filename')
    if version_filename is None:
        version_filename = order_num
    
    version_file_path = f'./version/{version_filename}.json'

    if not os.path.exists(version_file_path):
        log_print(order_num, 'version file not found')
        createVersionFile(version_file_path)
        log_print(order_num, 'version file created')
    
    file = open(version_file_path, 'r+')    
    version_json = simdjson.load(file)
    
    local_list = version_json['short-list'] 

    if (length_hint(local_list) == length_hint(download_short_list)
        and ((length_hint(local_list) == 0 and length_hint(download_short_list) == 0)
            or (local_list[0] == download_short_list[0] and local_list[-1] == download_short_list[-1]))):
        return
             
    log_print(order_num, 'something has changed')
    
    # give 'marked_as' = 2 on all elements
    for local_file in version_json['files'].keys():
        element_mark(version_json['files'][local_file], 2)
    
    archive_folder = f'./archive/{current_time}'
    os.makedirs(archive_folder, exist_ok=True)
    
    for item in download_url_list: 
        # download stuff
        download_path = f'./download/{item[1]}'
        
        log_print(order_num, f'downloading {item[0]} to {download_path}')
        booth.download_item(item[0], download_path, booth_cookie)
        
        # archive stuff
        if archive_this and item[0] not in local_list:
            archive_path = archive_folder + '/' + item[1]
            shutil.copyfile(download_path, archive_path)
        
        log_print(order_num, f'parsing {item[0]} structure')
        init_file_process(download_path, item[1], version_json, encoding)
        
    # create image from 'files' tree
    global path_list, current_level, current_count, highest_level

    path_list = []
    current_level = 0
    current_count = 0
    highest_level = 0
    init_pathinfo(version_json)
    
    offset = image.get_image_size(highest_level, current_count)
    img = image.make_image(1024, offset[1])
    image.make_pathinfo_line(img, path_list)
    img.save(changelog_img_path)
    
    # add webhook
    author_info = booth.crawling_product(url)
    
    # FIXME: This was not supposed to exist.
    # But somehow getting error because of this empty thumblist.  
    thumb = "https://asset.booth.pm/assets/thumbnail_placeholder_f_150x150-73e650fbec3b150090cbda36377f1a3402c01e36ff9fa96158de6016fa067d01.png"
    if length_hint(thumblist) > 0: 
        thumb = thumblist[0]
        
    discord.webhook(discord_webhook_url, url, name, local_list, download_short_list, author_info, thumb, number_show, changelog_show)
    
    os.remove(changelog_img_path)
    
    # delete all of 'marked_as'
    global delete_keys
    for local_file in version_json['files'].keys():
        remove_element_mark(version_json['files'], version_json['files'][local_file], local_file)
        
    for [previous, root_name] in delete_keys:
        process_delete_keys(previous, root_name)
    delete_keys = []
    
    version_json['short-list'] = download_short_list
    
    file.seek(0)
    file.truncate()
    simdjson.dump(version_json, fp = file, indent = 4)
    
    file.close()

path_list = []
current_level = 0
highest_level = 0
current_count = 0
def init_pathinfo(root):
    global path_list, current_level, highest_level, current_count
    
    if highest_level < current_level:
        highest_level = current_level
    
    files = root.get('files', None)
    if files is None:
        return
    
    current_level += 1
    
    for file in files.keys():
        file_info = {'line_str': "", 'status': root['files'][file]['mark_as']}

        for loop in range(0, current_level - 1):
            file_info['line_str'] += '        '

        symbol = ''
        if file_info['status'] == 1:
            symbol = '(Added)'
        elif file_info['status'] == 2:
            symbol = '(Deleted)'
        elif file_info['status'] == 3:
            symbol = '(Changed)'

        file_info['line_str'] += f'{file} {symbol}'

        path_list.append(file_info)
        current_count += 1
        
        init_pathinfo(root['files'][file])
        
    current_level -= 1

json_level = []
def init_file_process(input_path, filename, version_json, encoding):
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
    zip_type = try_extract(input_path, filename, process_path, encoding)
    
    json = version_json['files']
    for entry in range(0, len(json_level) - 1, 1):
        pre_json = json.get(json_level[entry], None)
        json = pre_json.get('files', None)

    if json is None:
        json = pre_json['files'] = {}
        
    pre_json = json
    json = pre_json.get(filename, None)
    
    if json is None:
        pre_json[filename] = {'hash': filehash, 'mark_as': 1}
    else:
        pre_json[filename]['mark_as'] = 0 if pre_json[json_level[-1]]['hash'] == filehash else 3
        
    if zip_type > 0 or os.path.isdir(process_path):
        for new_filename in os.listdir(process_path):
            new_process_path = os.path.join(process_path, new_filename)
            init_file_process(new_process_path, new_filename, version_json, encoding)

    json_level.pop()
    end_file_process(zip_type, process_path)
    
        
def end_file_process(zip_type, process_path):
    if zip_type > 0:
        shutil.rmtree(process_path)
    elif os.path.isdir(process_path):
        os.rmdir(process_path)
    else:
        os.remove(process_path)
    
# NOTE: Currently, @encoding only applies on zip_type == 1
def try_extract(input_path, input_filename, output_path, encoding):
    zip_type = is_compressed(input_path)
    
    if zip_type == 1:
        temp_output = f'./{input_filename}'
        shutil.move(input_path, temp_output)
        zip_file = zipfile.ZipFile(temp_output, 'r', metadata_encoding=encoding)

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
    with open(path, 'rb') as f:
        data = f.read()
        hash = hashlib.md5(data).hexdigest()
    return hash


def element_mark(root, mark_as): 
    root['mark_as'] = mark_as

    files = root.get('files', None)
    if files is None:
        return
        
    for file in files.keys():
        element_mark(root['files'][file], mark_as)

delete_keys = []
def remove_element_mark(previous, root, root_name):
    global delete_keys
    
    if root['mark_as'] == 2:
        delete_keys.append([previous, root_name])
        return
    
    del root['mark_as']

    files = root.get('files', None)
    if files is None:
        return
        
    for file in files.keys():
        remove_element_mark(root['files'], root['files'][file], file)


def process_delete_keys(previous, root_name):
    del previous[root_name]
        

if __name__ == "__main__":
    global booth_cookie, discord_webhook_url

    # 갱신 간격 (초)
    refresh_interval = 600
    
    createFolder("./version")
    createFolder("./archive")
    createFolder("./download")
    createFolder("./process")

    while True:
        config_json = {}
        with open("checklist.json") as file:
            config_json = simdjson.load(file)
            
        # 계정
        booth_cookie = {"_plaza_session_nktz7u": config_json['session-cookie']}
        discord_webhook_url = config_json['discord-webhook-url']

        # Preference
        image.font_init(config_json.get('changelog-font-file', 'NanumSquareNeo-bRg.ttf'), config_json.get('changelog-font-size', 16))

        # FIXME: Due to having PermissionError issue, clean temp stuff on each initiation.
        shutil.rmtree("./download")
        shutil.rmtree("./process")

        createFolder("./download")
        createFolder("./process")
        
        current_time = strftime_now()

        for product in config_json['products']:
            order_num = product['booth-order-number']
            # BOOTH Heartbeat
            # KT™ Sucks. Thank you.
            
            try:
                log_print(order_num, 'Checking BOOTH heartbeat')
                requests.get("https://booth.pm")
            except:
                log_print(order_num, 'BOOTH heartbeat failed')
                break
        
            try:
                init_update_check(product)
            except PermissionError:
                log_print(order_num, 'error occured on checking')
            
        # 갱신 대기
        print("waiting for refresh")
        sleep(refresh_interval)
