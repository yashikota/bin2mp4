import datetime
import os
import subprocess
import tkinter
import tkinter.filedialog as tkfd

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
    raw_file, width=160, height=120, frame_rate=30, output_video_file="output.mp4"
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
        output_video_file,
    ]

    try:
        print("FFmpegで動画ファイルを生成中...")
        subprocess.run(ffmpeg_command, check=True)
        print(f"動画ファイルが生成されました: {output_video_file}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpegの実行に失敗しました: {e}")


def main():
    os.makedirs("video", exist_ok=True)

    tk = tkinter.Tk()
    filename = tkfd.askopenfilenames()  # ファイルダイアログの呼び出し
    tk.withdraw()  # rootウィンドウを消す
    tk.destroy()

    # ファイルが選択されていない場合は終了
    if not filename:
        print("ファイルが選択されていません。")
        exit()

    # 出力ファイル名
    output_video_file = (
        f"video/output_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
    )

    # RAW形式に変換
    raw_file = combine_rgb_to_raw(list(filename))

    # FFmpegで動画ファイルに変換
    convert_raw_to_video(raw_file, output_video_file=output_video_file)

    # 処理完了後、中間ファイルを削除する場合（オプション）
    if os.path.exists(raw_file):
        os.remove(raw_file)
        print(f"中間ファイルを削除しました: {raw_file}")


if __name__ == "__main__":
    main()
