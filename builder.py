import subprocess
import os
import shutil
import sys
 
# === CONFIGURATION ===
VERSION = "2025w26"
SCRIPT_NAME = "main.py"
FINAL_EXE_NAME = "jpackageupdater.exe"  # Desired output name
ICON_FILE = None  # Set to "icon.ico" if you have one

# COPY_TO = None # unimplemented

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