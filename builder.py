import subprocess
import os
import shutil
import argparse
import sys
import datetime
from pathlib import Path

def generate_version_string():
    today = datetime.date.today()
    year, week, _ = today.isocalendar()  # returns (year, week_number, weekday)
    return f"{year}w{week:02d}"  # zero-pad week to 2 digits


# === CONFIGURATION ===
VERSION = generate_version_string() # overwrite if you like!
SCRIPT_NAME = "main.py"
TOOL_NAME = "jpackageupdater"
FINAL_EXE_NAME = TOOL_NAME + '.exe'  # Desired output name
ICON_FILE = None  # Set to "icon.ico" if you have one

# COPY_TO = None # unimplemented




def main():
    # === BUILD COMMAND ===
    command = [
        "pyinstaller",
        "--onefile",
        SCRIPT_NAME,
    ]

    if ICON_FILE:
        command += ["--icon", ICON_FILE]

    # === RUN PYINSTALLER WITH ERROR HANDLING ===
    print("🔧 Building executable with PyInstaller...")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)  # You can remove this if you want it completely silent on success
    except subprocess.CalledProcessError as e:
        print("❌ Build failed!")
        print("------ STDOUT ------")
        print(e.stdout)
        print("------ STDERR ------")
        print(e.stderr)
        sys.exit(1)

    # === RENAME OUTPUT FILE ===
    dist_path = os.path.join("dist", os.path.splitext(SCRIPT_NAME)[0] + ".exe")
    final_dir = os.path.join("dist", VERSION)
    final_path = os.path.join(final_dir, FINAL_EXE_NAME)

    if not os.path.exists(final_dir):
        os.makedirs(final_dir)

    if os.path.exists(final_path):
        os.remove(final_path)

    os.rename(dist_path, final_path)
    print(f"✅ Renamed to: {final_path}")

    # === CLEAN UP ===
    print("🧹 Cleaning up build files...")
    shutil.rmtree("build", ignore_errors=True)
    spec_file = os.path.splitext(SCRIPT_NAME)[0] + ".spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

    # if COPY_TO is not None:
    #     print(f'move {final_dir} -> {COPY_TO}')
    #     shutil.copy(final_dir, COPY_TO)
    #     print(f'moved {final_dir} -> {COPY_TO}')

    print("🚀 Build complete!")

def attempt_auto_update(confirm=False):
    old_script_path = get_script_path_from_env()
    script_path = os.path.dirname(old_script_path)
    print('script_pat =', script_path)
    if not script_path or (not confirm and input(f'Detected script_path @ {script_path}\nWant to auto-update?\n[Y/N] ').lower() != 'y'):
        print('cancelling auto update')
        return
    user_programs = os.path.expanduser(r"~\Programs")
    dest = os.path.join(user_programs, TOOL_NAME, VERSION)
    print('dest =', dest)
    os.makedirs(dest, exist_ok=True)
    # copy your built files into `dest`
    shutil.copy2(f"dist/{VERSION}/jpackageupdater.exe", dest)
    print("✅ Script updated.")

    if old_script_path == dest:
        return
    
    windows_auto_update(old_script_path, dest)
def get_script_path_from_env():
    for p in os.environ["PATH"].split(os.pathsep):
        if TOOL_NAME in p:
            return p

    return None


def windows_auto_update(old_path, new_path):
    import winreg
    import ctypes
    # Read current user PATH from registry
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as key:
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""

    # Split and rebuild
    parts = current_path.split(";")
    updated = []
    for part in parts:
        if part.strip().lower() == old_path.lower():
            continue  # drop old
        updated.append(part)
    updated.append(new_path)

    new_path_value = ";".join(updated)

    # Write new PATH to registry
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path_value)

    # Broadcast WM_SETTINGCHANGE so the change is picked up without reboot
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x1A
    SMTO_ABORTIFHUNG = 0x0002
    result = ctypes.c_long()
    ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0,
                                             "Environment", SMTO_ABORTIFHUNG, 5000,
                                             ctypes.byref(result))
    print("✅ User PATH updated.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Python script -> .exe builder."
    )
    parser.add_argument('--confirm', '-y', action='store_true', help="flag to auto-update")

    args = parser.parse_args()
    main()
    attempt_auto_update(confirm=args.confirm)