# bin2mp4

## 準備

実行は初回だけで良い。  

1. FFmpeg

    ```sh
    winget install ffmpeg
    ```
    
    ※ wingetがない場合は [GitHub](https://github.com/GyanD/codexffmpeg/releases/latest) から `ffmpeg-{バージョン番号}-full_build.zip` DLしてパスを通す

3. numpy

    ```sh
    pip install numpy
    ```

    ※ [uv](https://github.com/astral-sh/uv) を使っている場合は `uv sync` でOK

## 実行

```sh
python main.py
```

ファイル選択ウィンドウが出るのでファイルを選択する。  
あとは自動でmp4が出力される。  
