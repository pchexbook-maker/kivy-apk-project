[app]

title = Kivy App
package.name = kivyapp
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,json,ttf,otf

version = 0.1

requirements = python3,kivy,pillow,arabic-reshaper,python-bidi

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 35
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

p4a.branch = master

[buildozer]

log_level = 2
warn_on_root = 1
