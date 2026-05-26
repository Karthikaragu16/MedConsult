"""
create_submission.py
--------------------
Run this script from the "Project folder" directory.
It creates a clean copy of the project with all sensitive
credentials replaced by placeholders, then zips it up
as  "MedConsult_Submission.zip" ready for CD/submission.
"""

import os
import re
import shutil
import zipfile

# ── Config ────────────────────────────────────────────────────────────────────
SOURCE_DIR   = os.path.dirname(os.path.abspath(__file__))   # Project folder
OUTPUT_DIR   = os.path.join(SOURCE_DIR, "MedConsult_Submission")
ZIP_NAME     = os.path.join(SOURCE_DIR, "MedConsult_Submission.zip")

# Folders / files to completely exclude
EXCLUDE_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env",
    "node_modules", ".gemini", "MedConsult_Submission"
}
EXCLUDE_FILES = {
    ".env", ".env.local", "*.pyc", "*.pyo",
    "health_assistant.db",          # local SQLite DB if any
    "create_submission.py",         # this script itself
    "MedConsult_Submission.zip",    # previous zip
}
EXCLUDE_EXTENSIONS = {".pyc", ".pyo", ".db"}

# Folders whose CONTENTS should be excluded (keep the empty folder)
EMPTY_FOLDERS = {"uploads"}

# Sensitive patterns to scrub from any .py file  →  (regex, replacement)
SCRUB_RULES = [
    # MySQL password
    (r"(MYSQL_PASSWORD\s*=\s*)['\"].*?['\"]",       r"\1'YOUR_DB_PASSWORD'"),
    (r"(passwd\s*=\s*)['\"].*?['\"]",               r"\1'YOUR_DB_PASSWORD'"),
    # Email credentials
    (r"(EMAIL_SENDER\s*=\s*)['\"].*?['\"]",         r"\1'your_email@gmail.com'"),
    (r"(EMAIL_PASSWORD\s*=\s*)['\"].*?['\"]",       r"\1'your_app_password_here'"),
    # Flask secret key
    (r"(secret_key\s*=\s*)['\"].*?['\"]",           r"\1'your_secret_key_here'"),
    # Any hardcoded Gmail address in strings
    (r"[a-zA-Z0-9._%+\-]+@gmail\.com",              r"your_email@gmail.com"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def should_exclude_file(filename):
    if filename in EXCLUDE_FILES:
        return True
    _, ext = os.path.splitext(filename)
    return ext in EXCLUDE_EXTENSIONS

def scrub_credentials(content: str) -> str:
    for pattern, replacement in SCRUB_RULES:
        content = re.sub(pattern, replacement, content)
    return content

def copy_and_clean(src_root, dst_root):
    for root, dirs, files in os.walk(src_root):
        # Filter excluded directories in-place so os.walk skips them
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        rel_root = os.path.relpath(root, src_root)
        dst_folder = os.path.join(dst_root, rel_root)
        os.makedirs(dst_folder, exist_ok=True)

        # If this is an "empty folder" target, skip its files
        folder_name = os.path.basename(root)
        if folder_name in EMPTY_FOLDERS:
            dirs[:] = []   # don't descend either
            # Write a placeholder readme
            placeholder = os.path.join(dst_folder, "README.txt")
            with open(placeholder, "w") as f:
                f.write("This folder is intentionally empty.\n"
                        "Place uploaded files here when deploying.\n")
            continue

        for filename in files:
            if should_exclude_file(filename):
                continue

            src_file = os.path.join(root, filename)
            dst_file = os.path.join(dst_folder, filename)

            _, ext = os.path.splitext(filename)
            if ext == ".py":
                # Read, scrub, write
                with open(src_file, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                content = scrub_credentials(content)
                with open(dst_file, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                shutil.copy2(src_file, dst_file)

def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                abs_path = os.path.join(root, file)
                arc_name = os.path.relpath(abs_path, os.path.dirname(folder_path))
                zf.write(abs_path, arc_name)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 1. Clean previous output
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    if os.path.exists(ZIP_NAME):
        os.remove(ZIP_NAME)

    print("[1/3] Copying project files...")
    copy_and_clean(SOURCE_DIR, OUTPUT_DIR)

    print("[2/3] Credentials scrubbed from all .py files")

    print("[3/3] Creating zip file...")
    zip_folder(OUTPUT_DIR, ZIP_NAME)

    print("\n*** DONE! ***")
    print("   Folder : " + OUTPUT_DIR)
    print("   Zip    : " + ZIP_NAME)
    print("\nWhat was removed/replaced:")
    print("   - MySQL password       -> YOUR_DB_PASSWORD")
    print("   - Gmail address        -> your_email@gmail.com")
    print("   - Gmail App Password   -> your_app_password_here")
    print("   - Flask secret key     -> your_secret_key_here")
    print("   - __pycache__ folders  -> excluded")
    print("   - .db database files   -> excluded")
    print("   - uploads/ contents    -> excluded (empty folder kept)")
