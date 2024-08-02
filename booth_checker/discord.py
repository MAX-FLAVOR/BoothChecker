import requests
import simdjson
import datetime
from requests_toolbelt.multipart.encoder import MultipartEncoder

from shared import changelog_img_path

def webhook(webhook_url, url, name, version_list, download_short_list, author_info, thumb, number_show, changelog_show):
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
    
    payload = {
        "content": "@here",
        "embeds": [
            {
                "title": name,
                "description": "업데이트 발견!",
                "color": 65280,
                "fields": fields,
                "author": {
                    "name": author_name,
                    "icon_url": author_icon
                },
                "footer": {
                    "icon_url": "https://booth.pm/static-images/pwa/icon_size_128.png",
                    "text": "BOOTH.pm"
                },
                "thumbnail": {
                    "url": thumb
                },
                "url": url
            }
        ]
    }

    fields = dict()
    
    if changelog_show is not False:
        payload["embeds"].append({
            "title": "CHANGELOG",
            "color": 65280,
            "image": {
                "url": f'attachment://{changelog_img_path}'
            },
            "timestamp": datetime.utcnow() + datetime.timedelta(hours=9)
        })
        payload["attachments"] = [
            {
                "id": 0,
                "description": "BOOTH Download Changelog",
                "filename": changelog_img_path
            }
        ]
        fields["files[0]"] = (changelog_img_path, open(changelog_img_path, 'rb'), 'image/png')

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
