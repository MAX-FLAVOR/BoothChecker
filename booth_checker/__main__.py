import shutil
import zipfile
import hashlib
import os
import requests
import re
import uuid
import logging
from datetime import datetime
from time import sleep
from jinja2 import Environment, FileSystemLoader

from operator import length_hint
from unitypackage_extractor.extractor import extractPackage

from shared import *
import booth
import booth_sqlite
import cloudflare

# mark_as
#   - 0: Nothing
#   - 1: Added
#   - 2: Deleted
#   - 3: Changed

# download_short_list 
#   - [download_number]
# download_url_list
#   - [download_number, filename]

def init_update_check(item):
    order_num = item[0]
    name = item[1]
    if item[2] is not None:
        check_only_list = item[2].split(',')
    else:
        check_only_list = None
    encoding = item[3]
    number_show = bool(item[4])
    changelog_show = bool(item[5])
    archive_this = bool(item[6])
    gift_item = bool(item[7])
    booth_cookie = {"_plaza_session_nktz7u": item[8]}
    discord_user_id = item[9]
    discord_channel_id = item[10]

    download_short_list = list()
    thumblist = list()
    if gift_item:
        download_url_list = booth.crawling_gift(order_num, booth_cookie, download_short_list, thumblist)
    else:
        download_url_list = booth.crawling(order_num, check_only_list, booth_cookie, download_short_list, thumblist)
    
    if download_url_list is None:
        logger.error(f'[{order_num}] BOOTH no responding')
        send_error_message(discord_channel_id, discord_user_id)
    
    try:
        item_name = download_url_list[1][0][0]
        item_url = download_url_list[1][0][1]
    except:
        logger.error(f'[{order_num}] BOOTH no responding')
        send_error_message(discord_channel_id, discord_user_id)
        raise Exception(f'[{order_num} download_url_list] : {download_url_list}')

    if name is None:
        name = item_name
            
    url = item_url

    download_url_list = download_url_list[0]

    version_filename = order_num
    
    version_file_path = f'./version/{version_filename}.json'

    if not os.path.exists(version_file_path):
        logger.info(f'[{order_num}] version file not found')
        createVersionFile(version_file_path)
        logger.info(f'[{order_num}] version file created')
    
    file = open(version_file_path, 'r+')
    try:
        version_json = simdjson.load(file)
    except:
        logger.warning(f'[{order_num}] version file corrupted')
        createVersionFile(version_file_path)
        version_json = simdjson.load(file)
    
    local_list = version_json['short-list'] 

    if (length_hint(local_list) == length_hint(download_short_list)
        and ((length_hint(local_list) == 0 and length_hint(download_short_list) == 0)
            or (local_list[0] == download_short_list[0] and local_list[-1] == download_short_list[-1]))):
        return
             
    if (length_hint(download_short_list) == 0):
        logger.error(f'[{order_num}] BOOTH no responding')
        return
    else:
        logger.info(f'[{order_num}] something has changed')
    
    global saved_prehash
    saved_prehash = {}
    
    # give 'marked_as' = 2 on all elements
    for local_file in version_json['files'].keys():
        element_mark(version_json['files'][local_file], 2, local_file, saved_prehash)
    
    def build_tree(paths):
        tree = {}
        path_stack = []
        for item in paths:
            line_str = item.get('line_str', '')
            status = item.get('status', 0)

            # 후행 공백만 제거하여 선행 공백을 보존
            line_str = line_str.rstrip()

            # 선행 공백의 수를 계산하여 들여쓰기 수준 결정
            indent_match = re.match(r'^(\s*)(.*)', line_str)
            if indent_match:
                leading_spaces = indent_match.group(1)
                indent = len(leading_spaces)
                content = indent_match.group(2)
            else:
                indent = 0
                content = line_str

            # content에서 상태 문자열 제거
            content = re.sub(r'\s*\(.*\)$', '', content)

            # 깊이 계산 (들여쓰기 수준에 따라)
            depth = indent // 4  # 공백 4칸당 한 레벨로 설정 (필요에 따라 조정)

            # 현재 깊이에 맞게 경로 스택 조정
            path_stack = path_stack[:depth]
            path_stack.append(content)

            # 트리 빌드
            node = tree
            for part in path_stack[:-1]:
                node = node.setdefault(part, {})
            # 현재 노드에 상태 정보 저장
            current_node = node.setdefault(path_stack[-1], {})
            current_node['_status'] = status
        return tree

    def tree_to_html(tree):
        html = '<ul>\n'  # 시작 태그에 줄바꿈 추가
        for key, subtree in tree.items():
            if key == '_status':
                continue  # 상태 정보는 별도로 처리
            status = subtree.get('_status', 0)

            # 상태에 따른 컬러 지정
            line_color = 'rgb(255, 255, 255)'  # 기본 색상 (흰색)
            if status == 1:
                line_color = 'rgb(125, 164, 68)'  # Added (녹색 계열)
            elif status == 2:
                line_color = 'rgb(252, 101, 89)'  # Deleted (빨간색 계열)
            elif status == 3:
                line_color = 'rgb(128, 161, 209)'  # Changed (파란색 계열)

            # 상태 문자열 추가
            status_str = ''
            if status == 1:
                status_str = ' (Added)'
            elif status == 2:
                status_str = ' (Deleted)'
            elif status == 3:
                status_str = ' (Changed)'

            # '_status' 키를 제외한 나머지로 재귀 호출
            child_subtree = {k: v for k, v in subtree.items() if k != '_status'}

            if child_subtree:
                # 자식이 있는 경우
                html += f'<li><span style="color:{line_color}">{key}{status_str}</span>\n'
                html += tree_to_html(child_subtree)
                html += '</li>\n'
            else:
                # 자식이 없는 경우
                html += f'<li><span style="color:{line_color}">{key}{status_str}</span></li>\n'
        html += '</ul>\n'  # 마지막 태그에 줄바꿈 추가
        return html

    archive_folder = f'./archive/{strftime_now()}'

    # 먼저 다운로드 및 아카이브 처리
    for item in download_url_list: 
        # download stuff
        download_path = f'./download/{item[1]}'
        
        if changelog_show is True or archive_this is True:
            logger.info(f'[{order_num}] downloading {item[0]} to {download_path}')
            booth.download_item(item[0], download_path, booth_cookie)
        
        # archive stuff
        if archive_this and item[0] not in local_list:
            os.makedirs(archive_folder, exist_ok=True)
            archive_path = archive_folder + '/' + item[1]
            shutil.copyfile(download_path, archive_path)

    # 다운로드 및 아카이브 처리가 끝난 후에 changelog 생성
    if changelog_show is True:
        global path_list, current_level, current_count, highest_level

        html_list_items = ""
        tree = ""

        for booth_item in download_url_list:  # 각 파일에 대해 처리
            download_path = f'./download/{booth_item[1]}'
            logger.info(f'[{order_num}] parsing {booth_item[0]} structure')
            init_file_process(download_path, booth_item[1], version_json, encoding)

            # 초기화
            path_list = []
            current_level = 0
            current_count = 0
            highest_level = 0
            init_pathinfo(version_json)

        if not path_list:
            logger.warning(f'[{order_num}] path_list for {booth_item[0]} is empty. Changelog will not be generated.')
        else:
            tree = build_tree(path_list)
            html_list_items = tree_to_html(tree)  # 각 파일의 트리 구조를 추가

        file_loader = FileSystemLoader('./templates')
        env = Environment(loader=file_loader)
        changelog_html = env.get_template('changelog.html')
        data = {
            'html_list_items': html_list_items
        }
        output = changelog_html.render(data)

        changelog_html_path = "changelog.html"

        with open(changelog_html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(output)

        if s3:
            html_upload_name = uuid.uuid5(uuid.NAMESPACE_DNS, str(order_num))
            try:
                cloudflare.s3_init(s3['endpoint_url'], s3['access_key_id'], s3['secret_access_key'])
                cloudflare.s3_upload(changelog_html_path, s3['bucket_name'], f'changelog/{html_upload_name}.html')
                logger.info(f'[{order_num}] Changelog uploaded to S3')
            except Exception as e:
                logger.error(f'[{order_num}] Error occurred while uploading changelog to S3: {e}')
                s3_object_url = None
            s3_object_url = f'https://{s3['bucket_access_url']}/changelog/{html_upload_name}.html'
        else:
            s3_object_url = None

    # discord author info
    author_info = booth.crawling_product(url)
    
    # FIXME: This was not supposed to exist.
    # But somehow getting error because of this empty thumblist.  
    thumb = "https://asset.booth.pm/assets/thumbnail_placeholder_f_150x150-73e650fbec3b150090cbda36377f1a3402c01e36ff9fa96158de6016fa067d01.png"
    if length_hint(thumblist) > 0: 
        thumb = thumblist[0]

    api_url = f'{discord_api_url}/send_message'

    data = {
        'name': name,
        'url': url,
        'thumb': thumb,
        'local_version_list': local_list,
        'download_short_list': download_short_list,
        'author_info': author_info,
        'number_show': number_show,
        'changelog_show': changelog_show,
        'channel_id': discord_channel_id,
        's3_object_url': s3_object_url
    }

    response = requests.post(api_url, json=data)

    if response.status_code == 200:
        logger.info('send_message API 요청 성공')
    else:
        logger.error(f'send_message API 요청 실패: {response.text}')
    
    if changelog_show is True:
        if not s3:
            api_url = f'{discord_api_url}/send_changelog'
            data = {
                'file': changelog_html_path,
                'channel_id': discord_channel_id
            }
            response = requests.post(api_url, json=data)
            if response.status_code == 200:
                logger.info('send_changelog API 요청 성공')
            else:
                logger.error(f'send_changelog API 요청 실패: {response.text}')
            os.remove(changelog_html_path)
    
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
    global path_list, current_level, highest_level, current_count, saved_prehash
    
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

        hash = root['files'][file]['hash']
        old_name = saved_prehash.get(hash, None)

        # UM..
        if old_name is not None:
            if file_info['status'] == 2: 
                continue
            elif file != old_name:
                file_info['status'] = 0
                file_info['line_str'] += f'{old_name} → {file} {symbol}'
            else:
                file_info['line_str'] += f'{file} {symbol}'
        else:
            file_info['line_str'] += f'{file} {symbol}'

        path_list.append(file_info)
        current_count += 1
        
        init_pathinfo(root['files'][file])
        
    current_level -= 1

json_level = []
saved_prehash = {}
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


def element_mark(root, mark_as, current_filename, prehash_dict): 
    root['mark_as'] = mark_as

    hash = root['hash']
    if (prehash_dict is not None and hash is not None
        and hash != 'DIRECTORY'):
        prehash_dict[hash] = current_filename

    files = root.get('files', None)
    if files is None:
        return
        
    for file in files.keys():
        element_mark(root['files'][file], mark_as, file, prehash_dict)

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


def send_error_message(discord_channel_id, discord_user_id):
    api_url = f'{discord_api_url}/send_error_message'

    data = {
        'channel_id': discord_channel_id,
        'user_id': discord_user_id
    }

    response = requests.post(api_url, json=data)

    if response.status_code == 200:
        logger.info('booth_discord API 요청 성공')
    else:
        logger.error(f'booth_discord API 요청 실패: {response.text}')
    return

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)

    current_time = ''
    def strftime_now():
        global current_time
        current_time = datetime.now().strftime('%Y%m%d-%H%M%S')
        return current_time
    
    with open("config.json") as file:
        config_json = simdjson.load(file)
    discord_api_url = config_json['discord_api_url']
    refresh_interval = int(config_json['refresh_interval'])
    try:
        s3 = config_json['s3']
    except:
        s3 = None
    
    booth_db = booth_sqlite.BoothSQLite('./version/booth.db')

    createFolder("./version")
    createFolder("./archive")
    createFolder("./changelog")
    createFolder("./download")
    createFolder("./process")

    # booth_discord 컨테이너 시작 대기
    sleep(5)

    while True:
        booth_items = booth_db.get_booth_items()
    
        # FIXME: Due to having PermissionError issue, clean temp stuff on each initiation.
        shutil.rmtree("./download")
        shutil.rmtree("./process")

        createFolder("./download")
        createFolder("./process")
        
        current_time = strftime_now()
        
        for item in booth_items:
            order_num = item[0]
            # BOOTH Heartbeat
            # SKT™, KT™, U+™ Sucks. Thank you.
            
            try:
                logger.info(f'[{order_num}] Checking BOOTH heartbeat')
                requests.get("https://booth.pm")
            except:
                logger.error(f'[{order_num}] BOOTH heartbeat failed')
                break
        
            try:
                init_update_check(item)
            except PermissionError:
                logger.error(f'[{order_num}] PermissionError occured')
            except Exception as e:
                logger.error(f'[{order_num}] error occured on checking\n{e}')
            
        # 갱신 대기
        logger.info("waiting for refresh")
        sleep(refresh_interval)