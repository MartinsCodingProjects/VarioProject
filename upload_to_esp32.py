import os
import subprocess

# Define the source directory and target directory on the ESP32
SOURCE_DIR = "./vario"
ESP32_TARGET_DIR = ":"

# Define the serial port for the ESP32
ESP32_PORT = "COM4"

def upload_files():
    """Upload all files and directories from SOURCE_DIR to the ESP32 root."""
    for root, dirs, files in os.walk(SOURCE_DIR):
        # Calculate the relative path from SOURCE_DIR
        relative_path = os.path.relpath(root, SOURCE_DIR)
        target_path = ESP32_TARGET_DIR if relative_path == "." else f"{ESP32_TARGET_DIR}/{relative_path}"

        # Create directories on the ESP32
        if relative_path != ".":
            try:
                subprocess.run(
                    ["mpremote", "connect", ESP32_PORT, "fs", "mkdir", target_path],
                    check=True,
                )
            except subprocess.CalledProcessError:
                pass  # Ignore errors if the directory already exists

        # Upload files
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = f"{target_path}/{file}".replace("\\", "/")
            print(f"Uploading {src_file} to {dst_file}")
            try:
                subprocess.run(
                    ["mpremote", "connect", ESP32_PORT, "fs", "cp", src_file, dst_file],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"Failed to upload {src_file}: {e}")

if __name__ == "__main__":
    upload_files()