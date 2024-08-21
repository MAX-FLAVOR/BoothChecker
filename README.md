# booth-update-checker

[![docker-build-push](https://github.com/5ignal/booth-update-checker/actions/workflows/docker-build-push.yml/badge.svg)](https://github.com/5ignal/booth-update-checker/actions/workflows/docker-build-push.yml)

[Docker Hub](https://hub.docker.com/r/ogunarmaya/booth-update-checker)

***
### Docker-Compose
```
services:
  booth-update-checker:
    image: ogunarmaya/booth-update-checker:latest
    container_name: booth-update-checker
    volumes:
      - ./checklist.json:/root/booth-update-checker/checklist.json
      - ./version:/root/booth-update-checker/version
      - ./archive:/root/booth-update-checker/archive
    restart: unless-stopped
```

---

### Checklist

```
{
    "refresh-interval": 600,
    "session-cookie": "YOUR_COOKIE_HERE",
    "discord-webhook-url": "YOUR_DISCORD_WEBHOOK_URL_HERE",

    "changelog-font-size": 16,

    "products":
    [
        {
            "custom-version-filename": "my-version",

            "booth-order-number": "BOOTH_ORDER_NUMBER_HERE (Required)",
            "booth-product-name": "BOOTH_PROUCT_NAME_HERE",
            "booth-check-only": [
                "ITEM_NUMBER_1",
                "ITEM_NUMBER_2"
            ],
            "intent-encoding": "utf-8",
            "download-number-show": false,
            "changelog-show": true,
            "archive_this": true
        },
        {
            "booth-order-number": "BOOTH_ORDER_NUMBER_HERE"
        }
    ]
}
```

### 옵션

`refresh-interval` `Required`

업데이트 확인 주기을 입력합니다. (초)

`booth-order-number` `Required`

BOOTH Order Detail 페이지에서 확인할 수 있는 Order Number를 입력합니다.

`custom-version-filename`

버전 파일의 이름을 지정할 수 있습니다.

`booth-product-name`

아이템의 이름을 지정할 수 있습니다.

Default : 아이템 페이지의 제목

`booth-check-only`

하나의 오더 넘버에 여러 개의 아이템이 있을 때 특정 아이템만 알림을 받기 위한 부분입니다.

업데이트 체크를 하고 싶은 아이템의 아이템 넘버를 입력하면 해당하는 아이템 넘버의 아이템만 체크합니다.

`intent-encoding`

- Japanese: shift_jis
- Korean: ks_c_5601-1987
- UTF-8: utf-8

Reference: https://learn.microsoft.com/ko-kr/windows/win32/intl/code-page-identifiers

`download-number-show` (Default : `true`)

Discord Webhook에 아이템 다운로드 번호를 표시할지 설정할 수 있습니다.

`changelog-show` (Default : `true`)

Discord Webhook에 체인지로그 이미지를 표시할지 설정할 수 있습니다.

`archive_this` (Default : `true`)

해당 아이템을 archive 폴더에 저장할지 설정할 수 있습니다.

---
### Font
`JetBrains Mono`

https://www.jetbrains.com/lp/mono/
