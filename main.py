import os
import argparse
import re

def detect_line_ending(text):
    """Detect line endings from the original file."""
    if '\r\n' in text:
        return '\r\n'
    elif '\r' in text:
        return '\r'
    return '\n'

def calculate_package(file_path, base_path):
    rel_path = os.path.relpath(file_path, base_path)
    package_path = os.path.dirname(rel_path).replace(os.sep, ".")
    return package_path

def update_package_declaration(file_path, new_package):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    line_ending = detect_line_ending(content)
    lines = content.splitlines()

    updated_lines = lines[:]
    package_updated = False
    found_package = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("package "):
            found_package = True
            current = stripped[len("package "):].rstrip(";")
            if current == new_package:
                return False  # Already correct
            updated_lines[i] = f"package {new_package};"
            package_updated = True
            break
        elif stripped and not stripped.startswith("//"):
            updated_lines.insert(i, f"package {new_package};")
            package_updated = True
            break

    if not found_package and not package_updated:
        updated_lines.insert(0, f"package {new_package};")
        package_updated = True

    if package_updated:
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            f.write(line_ending.join(updated_lines) + line_ending)
        # print(f"✅ Updated: {file_path} -> package {new_package}")

    return package_updated

def process_java_files(base_path):
    n_changed = 0
    t_files = 0
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                new_package = calculate_package(file_path, base_path)
                if update_package_declaration(file_path, new_package):
                    n_changed += 1
                t_files += 1

    print(f"Updated {n_changed}/{t_files} files.")

def main():
    parser = argparse.ArgumentParser(
        description="Update Java package declarations based on folder structure."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=os.getcwd(),
        help="Root path to start scanning (defaults to current directory)."
    )
    args = parser.parse_args()

    base_path = os.path.abspath(args.path)
    if not os.path.isdir(base_path):
        print(f"❌ Error: Provided path '{base_path}' is not a valid directory.")
        return

    # print(f"📂 Scanning Java files under: {base_path}")
    process_java_files(base_path)

if __name__ == "__main__":
    main()