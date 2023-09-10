# booth-update-checker

### Docker-Compose
```
version: "3"

services:
  booth-update-checker:
    build: .
    container_name: booth-update-checker
    volumes:
      - ./checklist.json:/root/booth-update-checker/checklist.json
      - ./version:/root/booth-update-checker/version
    restart: unless-stopped
```

---

### Checklist Configuration

`checklist.json`
```
{
    "session-cookie": "YOUR_COOKIE_HERE",
    "discord-webhook-url": "YOUR_DISCORD_WEBHOOK_URL_HERE",

    "products":
    [
        {
            "booth-order-number": "BOOTH_ORDER_NUMBER_HERE",
            "booth-product-name": "BOOTH_PROUCT_NAME_HERE",
            "booth-check-only": [
                "ITEM_NUMBER_1",
                "ITEM_NUMBER_2"
            ],
            "intent-encoding": "shift_jis",
            "download-number-show": false,
            "changelog-show": false
        },
        {
            "booth-order-number": "BOOTH_ORDER_NUMBER_HERE"
        }
    ]
}
```

### 옵션

booth-order-number를 제외한 나머지는 옵션입니다.

`booth-product-name`

아이템의 이름을 지정할 수 있습니다.

지정을 안하면 아이템 페이지의 이름을 가져옵니다.

`booth-check-only`

하나의 오더 넘버에 여러 개의 아이템이 있을 때 특정 아이템만 알림을 받기 위한 부분입니다.

업데이트 체크를 하고 싶은 아이템의 아이템 넘버를 입력하면 해당하는 아이템 넘버의 아이템만 체크합니다.

`intent-encoding`

Reference: https://learn.microsoft.com/ko-kr/windows/win32/intl/code-page-identifiers
- Chinese Simplified: 936 (gb2312)
- Japanese: 932 (shift_jis)
- Korean: 949 (ks_c_5601-1987)
- UTF-8: 65001 (utf-8)

`download-number-show`

Discord 알림에 다운로드 넘버를 표시할지 설정할 수 있습니다.

기본 값은 true입니다.

`changelog-show`

Discord 알림에 체인지로그 이미지를 표시할지 설정할 수 있습니다.

기본 값은 true입니다.

---
### Font
이 프로젝트에는 네이버에서 제공한 나눔글꼴이 적용되어 있습니다.

https://help.naver.com/service/30016/contents/18088?osType=PC&lang=ko
