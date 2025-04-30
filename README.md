Enable Long Path Support in Windows
Use gradlew.bat in the zip file instead of the one in "client/android" if facing java compatibility issues
Install pillow library of python
Add signConfigs to build.gradle
Release apk will be in divkit-demo-app/build/outputs/apk/release
Keystore path should be full path like: Desktop/fol/phplus.jks
Icon name should be the same as the 'name' variant and inside icons folder
Place sdui project, icons folder on the same level of folder structure
Correct Project Structure:
├── apk_builder_script.py
├── sdui/
├── icons/
