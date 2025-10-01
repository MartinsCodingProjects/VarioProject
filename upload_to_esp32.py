import os
import subprocess

# Define the files and directories to exclude
EXCLUDE = {".git", "__pycache__", ".gitignore", "older_versions", "upload_to_esp32.py", "debug_api.py", "todo.md"}
EXCLUDE_EXTENSIONS = {".md"}

# Define the target directory on the ESP32
ESP32_TARGET_DIR = ":"

# Define the serial port for the ESP32
ESP32_PORT = "COM4"

def should_exclude(path):
    """Check if a file or directory should be excluded."""
    # Check for excluded directories or files
    for pattern in EXCLUDE:
        if pattern in path:
            return True

    # Check for excluded file extensions
    _, ext = os.path.splitext(path)
    if ext in EXCLUDE_EXTENSIONS:
        return True

    return False

def upload_files():
    """Upload relevant files to the ESP32."""
    for root, dirs, files in os.walk("."):
        # Remove excluded directories from the walk
        dirs[:] = [d for d in dirs if not should_exclude(d)]

        for file in files:
            if should_exclude(file):
                continue

            # Construct the source and destination paths
            src_path = os.path.join(root, file)
            dst_path = os.path.join(ESP32_TARGET_DIR, root, file).replace("\\", "/")

            # Upload the file using mpremote
            print(f"Uploading {src_path} to {dst_path}")
            try:
                subprocess.run([
                    "mpremote", "connect", ESP32_PORT, "fs", "cp", src_path, dst_path
                ], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to upload {src_path}: {e}")

if __name__ == "__main__":
    upload_files()