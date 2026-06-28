[app]
title = NetScan Pro
package.name = netscanpro
package.domain = org.cybersec
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

requirements = python3,kivy==2.3.0,kivymd==1.1.1,cython==0.29.36

orientation = portrait

android.permissions = INTERNET,ACCESS_WIFI_STATE,ACCESS_NETWORK_STATE,CHANGE_WIFI_STATE,ACCESS_FINE_LOCATION
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a

android.allow_backup = True
# android.icon = %(source.dir)s/assets/icon.png
source.include_exts = py,png,jpg,kv,atlas,json,ttf,txt
[buildozer]
log_level = 2
warn_on_root = 1
