import os
import argparse
import re

class_map = {}  # class name -> new package

def detect_line_ending(text):
    if '\r\n' in text:
        return '\r\n'
    elif '\r' in text:
        return '\r'
    return '\n'

def calculate_package(file_path, base_path):
    rel_path = os.path.relpath(file_path, base_path)
    package_path = os.path.dirname(rel_path).replace(os.sep, ".")
    return package_path

def get_class_name(file_path):
    return os.path.splitext(os.path.basename(file_path))[0]

def update_package_declaration(file_path, new_package, base_path, dry_run=False):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    line_ending = detect_line_ending(content)
    lines = content.splitlines()

    updated_lines = lines[:]
    package_updated = False
    found_package = False
    current_package = None

    for i, line in enumerate(lines):
        if line.strip().startswith("package "):
            found_package = True
            current_package = line.strip()[len("package "):].rstrip(";")
            if current_package == new_package:
                return None
            updated_lines[i] = f"package {new_package};"
            package_updated = True
            break
        elif line.strip() and not line.strip().startswith("//"):
            updated_lines.insert(i, f"package {new_package};")
            package_updated = True
            break

    if not found_package and not package_updated:
        updated_lines.insert(0, f"package {new_package};")
        package_updated = True

    if package_updated:
        class_name = get_class_name(file_path)
        print(f"✅ Package change: {file_path}\n    {current_package or '(none)'} -> {new_package}")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write(line_ending.join(updated_lines) + line_ending)
        return (class_name, new_package)

    return None

def process_java_files_and_track_packages(base_path, dry_run=False):
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                new_package = calculate_package(file_path, base_path)
                result = update_package_declaration(file_path, new_package, base_path, dry_run)
                if result:
                    class_name, updated_package = result
                    class_map[class_name] = updated_package

def update_imports(base_path, dry_run=False):
    if not class_map:
        return

    # Precompute regexes for efficiency
    import_regexes = []
    for class_name, new_package in class_map.items():
        # matches normal import: import old.package.ClassName;
        import_regexes.append((re.compile(rf'^\s*import\s+([\w\.]+)\.{class_name};'), class_name, new_package))
        # matches static import: import static old.package.ClassName.SOMETHING;
        import_regexes.append((re.compile(rf'^\s*import\s+static\s+([\w\.]+)\.{class_name}\.'), class_name, new_package))

    # wildcard imports: we need to know old package (we assume old package was wrong)
    # For wildcard, we just replace old package with new
    wildcard_regex = re.compile(r'^\s*import\s+([\w\.]+)\.\*;')

    for root, _, files in os.walk(base_path):
        for file in files:
            if not file.endswith(".java"):
                continue

            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            line_ending = detect_line_ending(content)
            lines = content.splitlines()
            updated = False

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Match specific class imports
                for regex, class_name, new_package in import_regexes:
                    m = regex.match(stripped)
                    if m:
                        old_package = m.group(1)
                        if old_package != new_package:
                            new_import = f"import {new_package}.{class_name};"
                            if stripped.startswith("import static"):
                                new_import = f"import static {new_package}.{class_name}."
                            print(f"🔄 Import update in {file_path}\n    {line.strip()} -> {new_import}")
                            lines[i] = new_import
                            updated = True

                # Match wildcard imports
                m = wildcard_regex.match(stripped)
                if m:
                    old_package = m.group(1)
                    # If wildcard matches any of our changed packages
                    for _, new_package in class_map.items():
                        # Only replace if same leaf dir as new_package?
                        # Safer: match last segment of old_package against new_package last segment
                        if old_package.split('.')[-1] == new_package.split('.')[-1] and old_package != new_package:
                            new_import = f"import {new_package}.*;"
                            print(f"🔄 Wildcard import update in {file_path}\n    {line.strip()} -> {new_import}")
                            lines[i] = new_import
                            updated = True

            if updated and not dry_run:
                with open(file_path, "w", encoding="utf-8", newline="") as f:
                    f.write(line_ending.join(lines) + line_ending)

def main():
    parser = argparse.ArgumentParser(
        description="Fix Java package declarations and auto-update imports."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=os.getcwd(),
        help="Root path to start scanning (defaults to current directory)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying any files."
    )
    args = parser.parse_args()
    base_path = os.path.abspath(args.path)

    if not os.path.isdir(base_path):
        print(f"❌ Error: Path '{base_path}' is not a valid directory.")
        return

    print(f"📂 Scanning under: {base_path}\n")
    process_java_files_and_track_packages(base_path, args.dry_run)

    print(f"\n🔍 Second pass: Updating imports...\n")
    update_imports(base_path, args.dry_run)

    if args.dry_run:
        print("\n✅ Dry run complete. No files were modified.")
    else:
        print("\n🎉 All done!")

if __name__ == "__main__":
    main()