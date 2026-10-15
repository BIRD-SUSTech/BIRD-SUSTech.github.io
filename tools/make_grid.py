#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把多张活动照片拼成等分宫格新闻配图（默认 2x2 四宫格），并可整体调亮。

布局（2x2）：
    ┌──────┬──────┐
    │ 图1  │ 图2  │
    ├──────┼──────┤
    │ 图3  │ 图4  │
    └──────┴──────┘

每格等比裁剪填满（cover），不重叠、不遮挡；格与格之间留细白缝。

用法：
    python tools/make_grid.py --images 图1.jpg 图2.jpg 图3.jpg 图4.jpg \
        --out images/news/2026-10-15.jpg
    可选： --size 1800x1200   --quality 88   --gap 8   --cols 2
           --target-brightness 130   --max-gain 1.25
           --sources-prefix images/news/2026-10-15   # 同时把调亮后的单张另存为 -1.jpg -2.jpg …

调亮：按每张图的平均亮度算增益 gain = 目标亮度 / 当前亮度，
      再夹在 [1.0, --max-gain] 之间（默认最多 +25%），避免过曝。
"""
import argparse
from PIL import Image, ImageEnhance, ImageOps, ImageStat


def brighten(im, target, max_gain):
    """整体调亮，返回 (新图, 实际增益)。已经是亮图则原样返回。"""
    mean = ImageStat.Stat(im.convert("L")).mean[0]
    if mean <= 0:
        return im, 1.0
    gain = min(max_gain, target / mean)
    if gain < 1.01:
        return im, 1.0
    return ImageEnhance.Brightness(im).enhance(gain), gain


def load_brightened(path, cell, target, max_gain, decode_to, source_long_edge):
    """打开图片（解码时按需降采样，省内存），调亮后返回：
       - 宫格用的小图（等比裁剪填满 cell）
       - 归档用的整幅图（长边不超过 source_long_edge，不裁剪）
       - 实际调亮倍数
    """
    im = Image.open(path)
    im.draft("RGB", decode_to)      # JPEG 专用：解码时直接跳到足够大的档位
    im = im.convert("RGB")
    im, gain = brighten(im, target, max_gain)
    tile = ImageOps.fit(im, cell, method=Image.LANCZOS)
    full = im
    if source_long_edge and max(full.size) > source_long_edge:
        full = full.copy()
        full.thumbnail((source_long_edge, source_long_edge), resample=Image.LANCZOS)
    return tile, full, gain


def make_grid(paths, out, size=(1800, 1200), quality=88, gap=8,
              cols=2, target=130.0, max_gain=1.25, sources_prefix=None,
              source_long_edge=1920):
    W, H = size
    rows = (len(paths) + cols - 1) // cols
    cell_w = (W - gap * (cols - 1)) // cols
    cell_h = (H - gap * (rows - 1)) // rows

    canvas = Image.new("RGB", (W, H), "white")
    for i, path in enumerate(paths):
        tile, full, gain = load_brightened(
            path, (cell_w, cell_h), target, max_gain,
            decode_to=(source_long_edge, source_long_edge), source_long_edge=source_long_edge)
        r, c = divmod(i, cols)
        canvas.paste(tile, (c * (cell_w + gap), r * (cell_h + gap)))
        print(f"  {i + 1}. {path}  →  格 {cell_w}x{cell_h}  调亮 x{gain:.2f}")
        if sources_prefix:
            src_out = f"{sources_prefix}-{i + 1}.jpg"
            full.save(src_out, "JPEG", quality=85, optimize=True, progressive=True)
            print(f"     另存 {src_out}（{full.width}x{full.height}）")

    canvas.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
    return canvas.size


def main():
    ap = argparse.ArgumentParser(description="活动照片等分宫格拼图")
    ap.add_argument("--images", nargs="+", required=True, help="参与拼图的图片（按顺序填入各格）")
    ap.add_argument("--out", required=True, help="输出 JPEG 路径")
    ap.add_argument("--size", default="1800x1200", help="画布尺寸，默认 1800x1200（3:2）")
    ap.add_argument("--quality", type=int, default=88)
    ap.add_argument("--gap", type=int, default=8, help="格与格之间的白缝像素")
    ap.add_argument("--cols", type=int, default=2, help="列数，默认 2（2x2 四宫格）")
    ap.add_argument("--target-brightness", type=float, default=130.0,
                    help="目标平均亮度（0-255），默认 130；不想调亮就设 0")
    ap.add_argument("--max-gain", type=float, default=1.25, help="单张最大调亮倍数，默认 1.25")
    ap.add_argument("--sources-prefix", default="",
                    help="可选：把调亮后的整幅图另存为 <prefix>-1.jpg …（便于日后重拼）")
    ap.add_argument("--source-long-edge", type=int, default=1920,
                    help="归档单张的长边上限，默认 1920")
    args = ap.parse_args()

    w, h = (int(x) for x in args.size.lower().split("x"))
    size = make_grid(args.images, args.out, size=(w, h), quality=args.quality, gap=args.gap,
                     cols=args.cols, target=args.target_brightness, max_gain=args.max_gain,
                     sources_prefix=args.sources_prefix or None,
                     source_long_edge=args.source_long_edge)
    print(f"已生成宫格图 {args.out}（{size[0]}x{size[1]}，{args.cols} 列 × {len(args.images)} 张）")


if __name__ == "__main__":
    main()
