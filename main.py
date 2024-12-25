import datetime
import os
import subprocess
import tkinter
import tkinter.filedialog as tkfd


def combine_rgb_to_raw(filelist, output_file="output.rgb", width=160, height=120, chunk_frames=100):
    """
    各チャンネルのBINファイルを結合し、FFmpegで扱えるRAW形式に変換する
    """
    filelist.sort()
    chunk_size = width * height * chunk_frames

    # ファイルサイズを確認
    r_size = os.path.getsize(filelist[0])
    g_size = os.path.getsize(filelist[1])
    b_size = os.path.getsize(filelist[2])

    if not (r_size == g_size == b_size):
        raise ValueError("R, G, Bのファイルサイズが一致していません。")

    # フレーム数を計算
    frame_count = r_size // (width * height)
    if r_size % (width * height) != 0:
        raise ValueError("データサイズが正しくないため、フレーム数が計算できません。")

    print(f"フレーム数: {frame_count}, サイズ: {width}x{height}")

    # チャンク単位で処理
    with open(filelist[0], "rb") as rf, \
         open(filelist[1], "rb") as gf, \
         open(filelist[2], "rb") as bf, \
         open(output_file, "wb") as outf:

        while True:
            # チャンク単位でデータを読み込む
            r_chunk = rf.read(chunk_size)
            g_chunk = gf.read(chunk_size)
            b_chunk = bf.read(chunk_size)

            if not r_chunk:  # ファイル終端
                break

            # インターリーブ処理
            for i in range(0, len(r_chunk)):
                outf.write(bytes([r_chunk[i], g_chunk[i], b_chunk[i]]))

            print(f"Progress: {rf.tell() / r_size * 100:.1f}%", end="\r")

    print("\nRAW形式のファイルを生成しました:", output_file)
    return output_file, frame_count


def convert_raw_to_video(
    raw_file, width=160, height=120, frame_rate=30, output_video_file="output.mp4"
):
    """
    FFmpegを使用してRAWファイルを動画ファイルに変換
    """
    ffmpeg_command = [
        "ffmpeg.exe",
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


if __name__ == "__main__":
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
    raw_file, frame_count = combine_rgb_to_raw(list(filename))

    # FFmpegで動画ファイルに変換
    convert_raw_to_video(raw_file, output_video_file=output_video_file)

    # 処理完了後、中間ファイルを削除する場合（オプション）
    # if os.path.exists(raw_file):
    #     os.remove(raw_file)
    #     print(f"中間ファイルを削除しました: {raw_file}")
