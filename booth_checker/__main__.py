import shutil
import zipfile
import hashlib
import requests
import uuid

from time import sleep
from operator import length_hint
from unitypackage_extractor.extractor import extractPackage

from log import *
from shared import *
import booth
import discord
import re
import cloudflare
import booth_sqlite

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
    order_num = item[1]
    name = item[2]
    check_only_list = item[3]
    encoding = item[4]
    number_show = item[5]
    changelog_show = item[6]
    archive_this = item[7]
            
    download_short_list = list()
    thumblist = list()
    download_url_list = booth.crawling(order_num, check_only_list, booth_cookie, download_short_list, thumblist)

    if name is None:
        name = download_url_list[1][0][0]
    url = download_url_list[1][0][1]

    download_url_list = download_url_list[0]

    version_filename = order_num
    
    version_file_path = f'./version/{version_filename}.json'

    if not os.path.exists(version_file_path):
        log_print(order_num, 'version file not found')
        createVersionFile(version_file_path)
        log_print(order_num, 'version file created')
    
    file = open(version_file_path, 'r+')
    try:
        version_json = simdjson.load(file)
    except:
        log_print(order_num, 'version file corrupted')
        createVersionFile(version_file_path)
        version_json = simdjson.load(file)
    
    local_list = version_json['short-list'] 

    if (length_hint(local_list) == length_hint(download_short_list)
        and ((length_hint(local_list) == 0 and length_hint(download_short_list) == 0)
            or (local_list[0] == download_short_list[0] and local_list[-1] == download_short_list[-1]))):
        return
             
    if (length_hint(download_short_list) == 0):
        log_print(order_num, 'BOOTH no responding')
        return
    else:
        log_print(order_num, 'something has changed')
    
    global saved_prehash
    saved_prehash = {}
    
    # give 'marked_as' = 2 on all elements
    for local_file in version_json['files'].keys():
        element_mark(version_json['files'][local_file], 2, local_file, saved_prehash)
    
    for item in download_url_list: 
        # download stuff
        download_path = f'./download/{item[1]}'
        
        if changelog_show is True or archive_this is True:
            log_print(order_num, f'downloading {item[0]} to {download_path}')
            booth.download_item(item[0], download_path, booth_cookie)
        
        # archive stuff
        if archive_this and item[0] not in local_list:
            archive_folder = f'./archive/{current_time}'
            os.makedirs(archive_folder, exist_ok=True)
            archive_path = archive_folder + '/' + item[1]
            shutil.copyfile(download_path, archive_path)

    changelog_html_path = 'changelog_temp.html'

    if changelog_show is True:
        log_print(order_num, f'parsing {item[0]} structure')
        init_file_process(download_path, item[1], version_json, encoding)

        # 필요한 전역 변수 선언
        global path_list, current_level, current_count, highest_level

        # 초기화
        path_list = []
        current_level = 0
        current_count = 0
        highest_level = 0
        init_pathinfo(version_json)

        # path_list가 비어 있으면 경고 출력
        if not path_list:
            print("Warning: path_list is empty. Changelog will not be generated.")
        else:
            # path_list로부터 트리 구조 생성
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

            # 트리 구조를 HTML로 변환하며 상태에 따른 텍스트 색상 지정
            def tree_to_html(tree):
                html = '<ul>'
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
                        html += f'<li><span style="color:{line_color}">{key}{status_str}</span>'
                        html += tree_to_html(child_subtree)
                        html += '</li>'
                    else:
                        # 자식이 없는 경우
                        html += f'<li><span style="color:{line_color}">{key}{status_str}</span></li>'
                html += '</ul>'
                return html

            tree = build_tree(path_list)
            html_list_items = tree_to_html(tree)

            # HTML 문서 생성
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Changelog</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Noto+Sans+JP&family=Noto+Sans+KR&display=swap');
                    body {{
                        font-family: "JetBrains Mono", monospace, "Noto Sans JP", sans-serif, "Noto Sans KR", sans-serif;
                        font-weight: 400;
                        font-style: normal;
                        font-size: 16px;
                        line-height: 1.6;
                        background-color: #1e1e1e;
                        color: #ffffff;
                    }}
                    h1 {{
                        font-size: 24px;
                        font-weight: 700;
                    }}
                    ul {{
                        list-style-type: disc;
                        padding-left: 20px;
                    }}
                    li {{
                        margin-bottom: 5px;
                    }}
                </style>
            </head>
            <body>
                <h1>Changelog</h1>
                {html_list_items}
            </body>
            </html>
            """

        with open(changelog_html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(html_content)


    # add webhook
    author_info = booth.crawling_product(url)
    
    # FIXME: This was not supposed to exist.
    # But somehow getting error because of this empty thumblist.  
    thumb = "https://asset.booth.pm/assets/thumbnail_placeholder_f_150x150-73e650fbec3b150090cbda36377f1a3402c01e36ff9fa96158de6016fa067d01.png"
    if length_hint(thumblist) > 0: 
        thumb = thumblist[0]
    
    html_upload_name = uuid.uuid5(uuid.NAMESPACE_DNS, str(order_num))
    cloudflare.s3_init(os.getenv('s3_endpoint_url'), os.getenv('s3_access_key_id'), os.getenv('s3_secret_access_key'))
    cloudflare.s3_upload(changelog_html_path, os.getenv('s3_bucket_name'), f'changelog/{html_upload_name}.html')
    s3_upload_file = os.getenv('s3_url') + f'/changelog/{html_upload_name}.html'

    discord.webhook(discord_webhook_url, url, name, local_list, download_short_list, author_info, thumb, number_show, changelog_show, s3_upload_file)
    
    if changelog_show is True:
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
        

if __name__ == "__main__":
    global booth_cookie, discord_webhook_url
    
    createFolder("./version")
    createFolder("./archive")
    createFolder("./download")
    createFolder("./process")

    refresh_interval = int(os.getenv('refresh_interval'))
        
    while True:
        booth_orders = booth_sqlite.BoothSQLite('./version/booth.db')
        booth_items = booth_orders.get_items()
        
        # FIXME: Due to having PermissionError issue, clean temp stuff on each initiation.
        shutil.rmtree("./download")
        shutil.rmtree("./process")

        createFolder("./download")
        createFolder("./process")
        
        current_time = strftime_now()
        
        for item in booth_items:
            booth_cookie = {"_plaza_session_nktz7u": item[0]}
            order_num = item[1]
            # BOOTH Heartbeat
            # KT™ Sucks. Thank you.
            
            try:
                log_print(order_num, 'Checking BOOTH heartbeat')
                requests.get("https://booth.pm")
            except:
                log_print(order_num, 'BOOTH heartbeat failed')
                break
        
            try:
                init_update_check(item)
            except PermissionError:
                log_print(order_num, 'error occured on checking')
            
        # 갱신 대기
        print("waiting for refresh")
        sleep(refresh_interval)
