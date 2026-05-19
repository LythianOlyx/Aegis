[app]

# (str) Title of your application
title = Aegis

# (str) Package name
package.name = aegis

# (str) Package domain (needed for android/ios packaging)
package.domain = com.aegis

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts =

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, dist, build, .git, __pycache__, ui/desktop

# (list) List of exclusions using pattern matching
source.exclude_patterns = main_desktop.py, aegis_desktop.spec, compile.py

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.1,kivymd==2.0.1,cryptography,requests,pillow,certifi

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (str) Presplash of the application
presplash.filename = %(source.dir)s/assets/logo.png

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/logo.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Extra flags to pass to the Android NDK build system
#android.ndk_api = 21

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (str) Android NDK version to use
#android.ndk = 25b

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (list) Android additional libraries to copy into libs/armeabi
#android.add_libs_armeabi =

# (list) Gradle dependencies to add
#android.gradle_dependencies =

# (bool) Enable AndroidX support
android.enable_androidx = True

# (list) add android specific permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (str) The format used to package the app for release mode (aab or apk).
android.release_artifact = apk

# (str) The format used to package the app for debug mode (apk).
android.debug_artifact = apk

#
# Python for android (p4a) specific
#

# (str) python-for-android branch to use, defaults to master
#p4a.branch = master

# (str) Bootstrap to use for the application
p4a.bootstrap = sdl2

# (str) The directory in which python-for-android should look for your own build recipes
#p4a.local_recipes =

#
# iOS specific
#

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios

# (str) Name of the certificate to use for signing the debug version
#ios.codesign.debug =

# (str) Name of the certificate to use for signing the release version
#ios.codesign.release =

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
