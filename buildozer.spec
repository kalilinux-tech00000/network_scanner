[app]
title = NetScan Pro
package.name = netscanpro
package.domain = org.cybersec
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

requirements = python3,kivy==2.3.0,requests

orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0

android.permissions = INTERNET,ACCESS_WIFI_STATE,ACCESS_NETWORK_STATE,CHANGE_WIFI_STATE,ACCESS_FINE_LOCATION
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True
android.icon = %(source.dir)s/assets/icon.png
android.presplash = %(source.dir)s/assets/splash.png

[buildozer]
log_level = 2
warn_on_root = 1
