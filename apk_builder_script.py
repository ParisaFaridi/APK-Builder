# ============ IMPORTANT_NOTES ============ 
# Enable Long Path Support in Windows
# Use gradlew.bat in the zip file instead of the one in "client/android" if facing java compatibility issues
# Install pillow library of python
# Add signConfigs to build.gradle
# Release apk will be in divkit-demo-app/build/outputs/apk/release
# Keystore path should be full path like: Desktop/fol/phplus.jks
# Icon name should be the same as the 'name' variant and inside icons folder
# Place sdui project, icons folder on the same level of folder structure
# Correct Project Structure:
# ├── apk_builder_script.py
# ├── sdui/
# ├── icons/

variants = [
    {
        "name": "op",
        "screen_name": "op",
        "package_name": "com.op.divkit",
        "keystore":"C:/Users/prs.faridi/Desktop/fol/phplus.jks",
        "alias":"phplus",
        "key_pass":"123456",
        "store_pass":"123456",
        "BASE_URL":"10.33"
    }
]
# ============ IMPORTS ============        
import os
import shutil
import fileinput
import subprocess
import re
import subprocess
import os
from PIL import Image
import json


# ============ CONFIGURATION ============
base_dir = os.path.dirname(os.path.abspath(__file__))
sdui_dir = os.path.join(base_dir, "sdui")
build_output_dir = os.path.join(base_dir, "build_output")

items_to_copy = [
    ("shared_data", "shared_data"),
    ("schema", "schema"),
    ("version", "version"),
    ("client/android", "client/android"),
    ("api_generator", "api_generator"),
    ("test_data", "test_data")
]

old_package = "com.yandex.divkit.demo"
app_name_default = "Divkit Demo App"

# ============ UTILITIES ============
def ensure_folder(path):
    os.makedirs(path, exist_ok=True)

MAX_PATH = 260  # Windows max path limit

def copy_items(destination):
    for src_rel, dst_rel in items_to_copy:
        src = os.path.join(sdui_dir, src_rel)
        dst = os.path.join(destination, dst_rel)

        if not os.path.exists(src):
            print(f"⚠️ Skipped missing source: {src_rel}")
            continue

        try:
            if os.path.isfile(src):
                ensure_folder(os.path.dirname(dst))
                shutil.copy2(src, dst)
                print(f"✅ Copied file: {src_rel}")
            else:
                shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns('*.lock', 'build', '.git'))
                print(f"✅ Copied directory: {src_rel}")
        except Exception as e:
            print(f"❌ Error copying {src_rel}: {e}")


def update_base_url(variant_dir, package_name, new_url):
    # Construct the full path to Constants.kt
    const_file_path = os.path.join(
        variant_dir,
        "client", "android", "divkit-demo-app", "src", "main", "java",
        *package_name.split('.'),
        "data", "Constants.kt"
    )

    if not os.path.exists(const_file_path):
        print(f"⚠️ Constants.kt not found at {const_file_path}")
        return

    with open(const_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(const_file_path, "w", encoding="utf-8") as f:
        for line in lines:
            if "BASE_URL" in line and "=" in line:
                # Replace the URL string in the assignment
                line = re.sub(r'BASE_URL\s*=\s*".*?"', f'BASE_URL = "{new_url}"', line)
            f.write(line)

    print(f"✅ Updated BASE_URL to {new_url} in Constants.kt")


def replace_in_file(file_path, old_str, new_str):
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            content = file.read()
        content = content.replace(old_str, new_str)
        with open(file_path, "w", encoding="utf-8", errors="replace") as file:
            file.write(content)
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")


def update_package_references(base_path, old_pkg, new_pkg):
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith((".kt", ".java", ".xml", ".gradle")):
                replace_in_file(os.path.join(root, file), old_pkg, new_pkg)



def update_package_folders(base_path, old_pkg, new_pkg, variant_dir, package_name, BASE_URL):
    old_path = os.path.join(base_path, *old_pkg.split('.'))
    new_path = os.path.join(base_path, *new_pkg.split('.'))

    if os.path.exists(old_path):
        ensure_folder(os.path.dirname(new_path))
        shutil.move(old_path, new_path)
        print(f"✅ Renamed package folder: {old_pkg} → {new_pkg}")

        # Update BASE_URL inside Constants.kt
        update_base_url(variant_dir, package_name, BASE_URL)
    else:
        print(f"❌ Old package path does not exist: {old_path}")

def update_app_name(strings_file, new_name):
    if not os.path.exists(strings_file):
        print("⚠️ Warning: strings.xml not found")
        return

    try:
        with open(strings_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Match: <string name="app_name">...</string>
        new_content = re.sub(
            r'(<string\s+name="app_name">)(.*?)(</string>)',
            r'\1' + new_name + r'\3',
            content
        )

        with open(strings_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ Updated app name in strings.xml to: {new_name}")
    except Exception as e:
        print(f"❌ Failed to update app name: {e}")


def update_start_point_json(variant_dir, screen_name):
    start_point_path = os.path.join(
        variant_dir, "client", "android", "divkit-demo-app","src","main", "assets", "application", "startPoint.json"
    )
    
    if not os.path.exists(start_point_path):
        print("⚠️ startPoint.json not found, skipping update.")
        return

    try:
        with open(start_point_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Recursively replace "ph/splash" with screen_name in string values
        def replace_in_obj(obj):
            if isinstance(obj, dict):
                return {k: replace_in_obj(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_in_obj(i) for i in obj]
            elif isinstance(obj, str):
                return obj.replace("ph/splash", screen_name)
            return obj

        updated_data = replace_in_obj(data)

        with open(start_point_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)

        print("✅ Updated screenName in startPoint.json")

    except Exception as e:
        print(f"❌ Failed to update startPoint.json: {e}")



def generate_density_icons(source_icon_path, target_res_dir):
    if not os.path.exists(source_icon_path):
        print(f"❌ Source icon not found at {source_icon_path}")
        return

    # Define target sizes
    sizes = {
        "mdpi": 48,
        "hdpi": 72,
        "xhdpi": 96,
        "xxhdpi": 144,
        "xxxhdpi": 192
    }

    try:
        img = Image.open(source_icon_path).convert("RGBA")
    except Exception as e:
        print(f"❌ Failed to load source image: {e}")
        return

    for density, size in sizes.items():
        mipmap_folder = os.path.join(target_res_dir, f"mipmap-{density}")
        ensure_folder(mipmap_folder)
        output_path = os.path.join(mipmap_folder, "ic_logo.png")

        resized = img.resize((size, size), Image.LANCZOS)
        resized.save(output_path, format="PNG")
        print(f"✅ Generated {size}x{size} icon in {mipmap_folder}")


def build_apk(project_path):
    gradlew = os.path.join(project_path, "gradlew.bat")
    if os.path.exists(gradlew):
        print("🚀 Building APK...")
        subprocess.run([gradlew, "assembleDebug"], cwd=project_path)
    else:
        print("❌ gradlew.bat not found, skipping build")


def build_signed_apk(project_path, keystore, store_pass, alias, key_pass):
    gradlew = os.path.join(project_path, "gradlew.bat")

    if not os.path.exists(gradlew):
        print("❌ gradlew.bat not found, skipping build")
        return

    print("🚀 Building signed release APK...")

    cmd = [
        gradlew,
        "assembleRelease",
        f"-PRELEASE_STORE_FILE={keystore.replace('\\', '/')}",
        f"-PRELEASE_STORE_PASSWORD={store_pass}",
        f"-PRELEASE_KEY_ALIAS={alias}",
        f"-PRELEASE_KEY_PASSWORD={key_pass}"
    ]

    subprocess.run(cmd, cwd=project_path)


# ================== MAIN =====================
for variant in variants:
    print(f"\n📦 Preparing variant: {variant['name']}")
    variant_dir = os.path.join(build_output_dir, variant["name"])

    if os.path.exists(variant_dir):
        shutil.rmtree(variant_dir, ignore_errors=True)
    ensure_folder(variant_dir)

    copy_items(variant_dir)

    java_base = os.path.join(variant_dir, "client", "android", "divkit-demo-app", "src", "main", "java")
    update_package_references(variant_dir, old_package, variant["package_name"])
    
    variant_dir = "C:/Users/prs.faridi/Desktop/fol/build_output/op"
    base_path = os.path.join(
        variant_dir,
        "client", "android", "divkit-demo-app", "src", "main", "java"
    )

    old_package_name = "com.ph.divkit"
    new_package_name = variant["package_name"]
    base_url = variant["BASE_URL"]

    update_package_folders(
    base_path=base_path,
    old_pkg=old_package_name,
    new_pkg=new_package_name,
    variant_dir=variant_dir,
    package_name=new_package_name,
    BASE_URL=base_url
    )

    strings_file = os.path.join(variant_dir, "client", "android", "divkit-demo-app", "src", "main", "res", "values", "strings.xml")
    update_app_name(strings_file, variant["screen_name"])

    update_start_point_json(variant_dir, variant["screen_name"])

    # Path to high-res icon (e.g., 1024x1024 PNG)
    source_icon = os.path.join(base_dir, "icons", f"{variant['name']}.png")

    # Target Android res/ folder
    res_path = os.path.join(
        variant_dir,
        "client", "android", "divkit-demo-app", "src", "main", "res"
    )

    generate_density_icons(source_icon, res_path)

    project_root = os.path.join(variant_dir, "client", "android")

    # build_apk(project_root)

    build_signed_apk(
    project_path=project_root,
    keystore = variant['keystore'],
    store_pass=variant['store_pass'],
    alias=variant['alias'],
    key_pass=variant['key_pass']
    )

    print(f"🎉 Done preparing variant: {variant['name']}")