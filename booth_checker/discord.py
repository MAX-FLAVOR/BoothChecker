import requests
import simdjson
from pytz import timezone
from datetime import datetime
from requests_toolbelt.multipart.encoder import MultipartEncoder

from shared import changelog_html_path

def webhook(webhook_url, url, name, version_list, download_short_list, author_info, thumb, number_show, changelog_show, s3_upload_file):
    fields = list()
    if number_show is not False:
        fields.append({"name": "LOCAL", "value": str(version_list), "inline": True})
        fields.append({"name": "BOOTH", "value": str(download_short_list), "inline": True})
    
    if author_info is not None:
        author_icon = author_info[0]
        author_name = author_info[1] + " "
    else:
        author_name = ""
        author_icon = ""

    payload = dict()
    payload["content"] = "@here"
    payload["embeds"] = list()
    payload["fields"] = fields
    payload_embed = dict()
    payload_embed["title"] = name
    payload_embed["color"] = 65280
    payload_embed["author"] = dict([("name", author_name), ("icon_url", author_icon)])
    payload_embed["description"] = "업데이트 발견! "
    payload_embed["footer"] = dict([("text", "BOOTH.pm"), ("icon_url", "https://booth.pm/static-images/pwa/icon_size_128.png")])
    payload_embed["thumbnail"] = dict([("url", thumb)])
    payload_embed["url"] = url
    payload_embed["timestamp"] = datetime.now(timezone('Asia/Seoul')).isoformat()
    payload["embeds"].append(payload_embed)

    fields = dict()
    
    if changelog_show is not False:
        payload_embed["description"] = f'# 업데이트 발견! \n ## [변경사항 보기]({s3_upload_file})'

    # This convert dict to string with keep double quote like: "content": "@here"
    payload_str = simdjson.dumps(payload)

    fields["payload_json"] = payload_str
    
    mpe = MultipartEncoder(fields)
    
    requests.post(webhook_url, data=mpe, headers={'Content-Type': mpe.content_type})

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
