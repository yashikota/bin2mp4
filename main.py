import datetime
import glob
import os
import subprocess

import numpy as np


def combine_rgb_to_raw(filelist, output_file="output.rgb", width=160, height=120):
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

    # データサイズを確認
    if not (len(r_data) == len(g_data) == len(b_data)):
        raise ValueError("R, G, Bのファイルサイズが一致していません。")

    # フレーム数を計算
    frame_count = len(r_data) // (width * height)
    if len(r_data) % (width * height) != 0:
        raise ValueError("データサイズが正しくないため、フレーム数が計算できません。")

    print(f"フレーム数: {frame_count}, サイズ: {width}x{height}")

    # 緑チャンネルを補正
    g_data = (g_data * 0.5).astype(np.uint8)

    # 各フレームをインターリーブ形式に結合
    rgb_data = np.empty((frame_count, height, width, 3), dtype=np.uint8)
    rgb_data[..., 0] = r_data.reshape((frame_count, height, width))
    rgb_data[..., 1] = g_data.reshape((frame_count, height, width))
    rgb_data[..., 2] = b_data.reshape((frame_count, height, width))

    # インターリーブ形式で保存
    rgb_data.tofile(output_file)
    print(f"RAW形式のファイルを生成しました: {output_file}")

    return output_file


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
        "hflip",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-loglevel",
        "error",
        output_video_file,
    ]

    # print(f"FFmpegコマンド: {' '.join(ffmpeg_command)}")

    try:
        print("FFmpegで動画ファイルを生成中...")
        subprocess.run(ffmpeg_command, check=True)
        print(f"動画ファイルが生成されました: {output_video_file}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpegの実行に失敗しました: {e}")


def main():
    os.makedirs("video", exist_ok=True)

    # ファイル一覧を再帰的に取得
    dir = r"C:\rec"
    bin_files = glob.glob(f"{dir}/**/*.bin", recursive=True)

    # ファイルが選択されていない場合は終了
    if not bin_files:
        print("ファイルが選択されていません。")
        exit()

    bin_files.sort()

    # 3つずつに分割
    rgb = [bin_files[i : i + 3] for i in range(0, len(bin_files), 3)]

    for i, files in enumerate(rgb):
        print(f"i: {files}")

        # 出力ファイル名
        output_video_file = (
            f"video/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
        )

        # RAW形式に変換
        raw_file = combine_rgb_to_raw(files, output_file=f"output_{i}.rgb")

        # FFmpegで動画ファイルに変換
        convert_raw_to_video(raw_file, output_video_file=output_video_file)

        # 処理完了後、中間ファイルを削除する場合（オプション）
        if os.path.exists(raw_file):
            os.remove(raw_file)
            print(f"中間ファイルを削除しました: {raw_file}")


if __name__ == "__main__":
    main()
