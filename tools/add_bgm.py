# -*- coding: utf-8 -*-
"""
给渲染好的视频加 BGM

功能：
  1. 把 assets/bgm/ 里的多首音乐按顺序串成一个"歌单"
  2. 相邻两首之间做交叉淡入淡出（避免硬切）
  3. 歌单不够长时自动循环，直到填满视频
  4. 整段开头淡入、结尾淡出
  5. 音量按 dB 衰减（BGM 要压得比人声低很多）
  6. 视频流直接复制，不重新编码（快，且无损）

用法：
    python tools/add_bgm.py                       # 自动找最新视频
    python tools/add_bgm.py <视频路径>             # 指定视频
    python tools/add_bgm.py <视频路径> -12         # 音量 -12 dB（越大声）

输出到：media/with_bgm/<原文件名>_bgm.mp4
"""
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path(__file__).resolve().parent.parent
BGM_DIR = ROOT / "assets" / "bgm"
OUT_DIR = ROOT / "media" / "with_bgm"
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}

FADE_BETWEEN = 2.0    # 两首之间的交叉淡化秒数
FADE_IN = 2.0         # 开头淡入秒数
FADE_OUT = 3.0        # 结尾淡出秒数


def newest_video():
    vids = [p for p in (ROOT / "media" / "videos").rglob("*.mp4")
            if "partial" not in str(p) and "with_bgm" not in str(p)]
    if not vids:
        sys.exit("未找到渲染好的视频")
    return max(vids, key=lambda p: p.stat().st_mtime)


def probe_duration(path):
    r = subprocess.run(
        [FFMPEG, "-i", str(path)], capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    for line in r.stderr.splitlines():
        if "Duration:" in line:
            hms = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    sys.exit("无法读取视频时长")


def list_bgm():
    files = sorted([p for p in BGM_DIR.iterdir() if p.suffix.lower() in AUDIO_EXT])
    if not files:
        sys.exit(f"未在 {BGM_DIR} 找到音乐文件（支持 mp3/wav/m4a/aac/flac/ogg）")
    return files


def build(video, gain_db):
    duration = probe_duration(video)
    tracks = list_bgm()

    print(f"视频：{video.name}")
    print(f"时长：{duration:.1f} 秒")
    print(f"音乐：{len(tracks)} 首，按顺序：")
    for i, t in enumerate(tracks):
        print(f"   {i + 1}. {t.name}")

    # ---- 构建滤镜链 ----
    # 1. 每首统一格式，方便后续拼接
    #    注意：输入 0 是视频（通常无音轨），音乐从输入 1 开始，索引要 +1
    parts = []
    for i in range(len(tracks)):
        parts.append(
            f"[{i + 1}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a{i}]"
        )

    # 2. 依次交叉淡化拼接
    cur = "a0"
    for i in range(1, len(tracks)):
        out = f"x{i}"
        parts.append(f"[{cur}][a{i}]acrossfade=d={FADE_BETWEEN}:c1=tri:c2=tri[{out}]")
        cur = out
    playlist = cur

    # 3. 循环 + 截断到视频长度 + 首尾淡化 + 音量
    parts.append(f"[{playlist}]aloop=loop=-1:size=2e9,atrim=0:{duration:.2f},"
                 f"afade=t=in:st=0:d={FADE_IN},"
                 f"afade=t=out:st={max(duration - FADE_OUT, 0):.2f}:d={FADE_OUT},"
                 f"volume={gain_db}dB[bgm]")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{video.stem}_bgm.mp4"

    cmd = [FFMPEG, "-y"]
    cmd += ["-i", str(video)]
    for t in tracks:
        cmd += ["-i", str(t)]
    cmd += ["-filter_complex", ";".join(parts)]
    cmd += ["-map", "0:v:0", "-map", "[bgm]"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [str(out_path)]

    print("\n开始合成（视频流直接复制，很快）…")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        print(r.stderr[-2500:])
        sys.exit("合成失败")
    print(f"\n完成：{out_path}")


if __name__ == "__main__":
    vid = Path(sys.argv[1]) if len(sys.argv) > 1 else newest_video()
    gain = float(sys.argv[2]) if len(sys.argv) > 2 else -18.0
    build(vid, gain)
