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
      - ./[ONLY_TTF_FILE]:/root/booth-update-checker/font.ttf
    restart: unless-stopped
```


### Checklist Configuration

`checklist.json`
```
{
    "session-cookie": "YOUR_COOKIE_HERE",
    "discord-webhook-url": "YOUR_DISCORD_WEBHOOK_URL_HERE",

    "products":
    [
        {
            "booth-product-name": "BOOTH_PRODUCT_NAME_HERE",
            "booth-product-url": "https://[SOMEONE].booth.pm/items/[ITEM_NUMBER]",
            "booth-order-number": "BOOTH_ORDER_NUMBER_HERE",

            "booth-check-only": [
                "BOOTH_PRODUCT_NUMBER_1_HERE",
                "BOOTH_PRODUCT_NUMBER_2_HERE"
            ],
            "intent-encoding": "shift_jis"
        },
        {
            "booth-product-name": "BOOTH_PRODUCT2_NAME_HERE",
            "booth-product-url": "https://[SOMEONE].booth.pm/items/[ITEM_NUMBER]",
            "booth-order-number": "BOOTH_ORDER_NUMBER_HERE"
        }
    ]
}
```

`"intent-encoding"`

Reference: https://learn.microsoft.com/ko-kr/windows/win32/intl/code-page-identifiers
- Chinese Simplified: 936 (gb2312)
- Japanese: 932 (shift_jis)
- Korean: 949 (ks_c_5601-1987)
- UTF-8: 65001 (utf-8)

