import glob
import json
import os
import urllib.request
import zipfile


def install_ffmpeg(repo_url, file_keyword, output_dir):
    ffmpeg_path = os.path.join(output_dir, "ffmpeg.exe")
    if os.path.exists(ffmpeg_path) and os.path.isfile(ffmpeg_path):
        print(f"ffmpeg.exe already exists at: {ffmpeg_path}")
        return

    api_url = f"{repo_url}/latest"

    try:
        with urllib.request.urlopen(api_url) as response:
            release_data = json.load(response)

        assets = release_data.get("assets", [])
        for asset in assets:
            if file_keyword in asset["name"]:
                download_url = asset["browser_download_url"]
                print(f"Found: {asset['name']}")
                print(f"Downloading from: {download_url}")

                zip_path = os.path.join(output_dir, asset["name"])
                with urllib.request.urlopen(download_url) as file_response:
                    with open(zip_path, "wb") as file:
                        file.write(file_response.read())
                print(f"Downloaded: {zip_path}")

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(output_dir)
                print(f"Extracted to: {output_dir}")

                os.remove(zip_path)
                print(f"Deleted ZIP file: {zip_path}")

                ffmpeg_base_path = os.path.join(
                    output_dir, "ffmpeg-*-full_build", "bin", "ffmpeg.exe"
                )
                ffmpeg_path = glob.glob(ffmpeg_base_path)[0]
                new_ffmpeg_path = os.path.join(output_dir, "ffmpeg.exe")
                os.rename(ffmpeg_path, new_ffmpeg_path)
                print(f"Moved ffmpeg.exe to: {new_ffmpeg_path}")
                break
        else:
            print("No 'full_build.zip' file found in the latest release.")
    except Exception as e:
        print(f"Error: {e}")


def main():
    output_dir = "third_party"
    os.makedirs(output_dir, exist_ok=True)

    install_ffmpeg(
        repo_url="https://api.github.com/repos/GyanD/codexffmpeg/releases",
        file_keyword="full_build.zip",
        output_dir=output_dir,
    )


if __name__ == "__main__":
    main()
