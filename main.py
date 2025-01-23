import glob
import os
import subprocess
from pathlib import Path

import numpy as np


def combine_rgb_to_raw(
    filelist, output_file="output.rgb", width=160, height=120, max_frame_count=None
):
    """
    各チャンネルのBINファイルを結合し、FFmpegで扱えるRAW形式に変換する
    """
    filelist.sort()
    # 各チャンネルのデータを読み込む
    with open(filelist[0], "rb") as rf:
        r_data = np.fromfile(rf, dtype=np.uint8)
    with open(filelist[1], "rb") as gf:
        g_data = np.fromfile(gf, dtype=np.uint8)
    with open(filelist[2], "rb") as bf:
        b_data = np.fromfile(bf, dtype=np.uint8)

    # データサイズを確認し、最小のサイズに合わせる
    min_size = min(len(r_data), len(g_data), len(b_data))

    # 最大フレーム数に合わせてデータを調整
    if max_frame_count is not None:
        required_size = max_frame_count * width * height
        if required_size < min_size:
            min_size = required_size

    # データを最小サイズに切り詰め
    r_data = r_data[:min_size]
    g_data = g_data[:min_size]
    b_data = b_data[:min_size]

    # フレーム数を計算
    frame_count = min_size // (width * height)
    if min_size % (width * height) != 0:
        print("データサイズが正しくないため、最後の不完全なフレームを除外します。")
        r_data = r_data[: frame_count * width * height]
        g_data = g_data[: frame_count * width * height]
        b_data = b_data[: frame_count * width * height]

    # 各フレームをインターリーブ形式に結合
    rgb_data = np.empty((frame_count, height, width, 3), dtype=np.uint8)
    rgb_data[..., 0] = r_data.reshape((frame_count, height, width))
    rgb_data[..., 1] = g_data.reshape((frame_count, height, width))
    rgb_data[..., 2] = b_data.reshape((frame_count, height, width))

    # インターリーブ形式で保存
    rgb_data.tofile(output_file)

    return output_file, frame_count, width, height


def convert_raw_to_video(
    raw_file, width=160, height=120, frame_rate=111, output_video_file="output.mp4"
):
    """
    FFmpegを使用してRAWファイルを動画ファイルに変換
    """
    ffmpeg_command = [
        "ffmpeg",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        f"{width}x{height}",
        "-framerate",
        str(frame_rate),
        "-i",
        raw_file,
        "-vf",
        "hflip,grayworld",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-loglevel",
        "error",
        output_video_file,
        "-y",
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpegの実行に失敗しました: {e}")


def combine_videos(video1_path: str, video2_path: str, output_path: str) -> bool:
    """
    2つの動画を結合して新しい動画を生成する
    オーバーレイ動画と結合動画を保存する
    """
    if not all(Path(p).exists() for p in [video1_path, video2_path]):
        print("Error: Input video files not found")
        return False

    # オーバーレイ動画のパス生成
    overlay_path = output_path.replace("_combined.mp4", "_overlay.mp4")

    # オーバーレイ動画の生成
    overlay_command = [
        "ffmpeg",
        "-i",
        video1_path,
        "-i",
        video2_path,
        "-filter_complex",
        "[0:v][1:v]blend=all_expr='A*0.5+B*0.5'",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        overlay_path,
        "-y",  # ファイルを上書き
    ]

    # 結合動画の生成
    combined_command = [
        "ffmpeg",
        "-i",
        video1_path,
        "-i",
        video2_path,
        "-i",
        overlay_path,
        "-filter_complex",
        "[0:v][1:v]hstack=inputs=2[top];[top][2:v]hstack=inputs=2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        output_path,
        "-y",  # ファイルを上書き
    ]

    try:
        subprocess.run(overlay_command, check=True, capture_output=True)
        subprocess.run(combined_command, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing videos: {e.stderr.decode()}")
        return False


def group_bin_files(bin_files):
    """
    BINファイルをLとRで一致するものに分類する
    """
    grouped_files = {}
    for file in bin_files:
        base_identifier = os.path.splitext(os.path.basename(file))[0].rsplit("_", 1)[0]
        channel = file.split("_")[-1].split(".")[0]

        if channel in ["0", "1", "2"]:
            if base_identifier not in grouped_files:
                grouped_files[base_identifier] = {}

            side = "l" if "l" in file.lower() else "r"
            key = f"{side}_{channel}"
            grouped_files[base_identifier][key] = file

    return grouped_files


def delete_processed_files(dir):
    """
    dir内のファイルを削除する
    """
    files = glob.glob(f"{dir}/**/*.*", recursive=True)
    for file in files:
        os.remove(file)


def calculate_frame_count(bin_file, width, height):
    """
    BINファイルのフレーム数を計算する
    """
    file_size = os.path.getsize(bin_file)
    frame_size = width * height
    return file_size // frame_size


def main():
    os.makedirs("video", exist_ok=True)

    dir = r"C:\rec"
    bin_files = glob.glob(f"{dir}/**/*.bin", recursive=True)

    if not bin_files:
        print("ファイルが選択されていません。")
        return

    grouped_files = group_bin_files(bin_files)

    width = 160
    height = 120

    for identifier, files in grouped_files.items():
        l_files = [files[f"l_{i}"] for i in ["0", "1", "2"] if f"l_{i}" in files]
        r_files = [files[f"r_{i}"] for i in ["0", "1", "2"] if f"r_{i}" in files]

        processed_files = []
        if len(l_files) == 3 and len(r_files) == 3:
            # L側のフレーム数を計算
            frame_counts_l = [
                calculate_frame_count(f, width, height) for f in l_files
            ]
            frame_l = min(frame_counts_l)

            # R側のフレーム数を計算
            frame_counts_r = [
                calculate_frame_count(f, width, height) for f in r_files
            ]
            frame_r = min(frame_counts_r)

            min_frame_count = min(frame_l, frame_r)

            print(
                f"{identifier}: size: {width}x{height}, frame counts L:{frame_l}, R:{frame_r}, using: {min_frame_count}"
            )

            # L側の処理
            output_video_file_l = f"video/{identifier}_L.mp4"
            raw_file_l, frame_used_l, _, _ = combine_rgb_to_raw(
                l_files,
                output_file=f"output_l_{identifier}.rgb",
                width=width,
                height=height,
                max_frame_count=min_frame_count,
            )

            # R側の処理
            output_video_file_r = f"video/{identifier}_R.mp4"
            raw_file_r, frame_used_r, _, _ = combine_rgb_to_raw(
                r_files,
                output_file=f"output_r_{identifier}.rgb",
                width=width,
                height=height,
                max_frame_count=min_frame_count,
            )

            # L側の動画を生成
            convert_raw_to_video(
                raw_file_l,
                width=width,
                height=height,
                output_video_file=output_video_file_l,
            )
            processed_files.extend(l_files)

            # R側の動画を生成
            convert_raw_to_video(
                raw_file_r,
                width=width,
                height=height,
                output_video_file=output_video_file_r,
            )
            processed_files.extend(r_files)

            # 中間ファイル削除
            for raw_file in [raw_file_l, raw_file_r]:
                if os.path.exists(raw_file):
                    os.remove(raw_file)

            # L/R動画と結合動画を出力
            combined_video_file = f"video/{identifier}_combined.mp4"
            combine_videos(
                output_video_file_l, output_video_file_r, combined_video_file
            )

    # ファイルを削除
    delete_processed_files(dir)


if __name__ == "__main__":
    main()
