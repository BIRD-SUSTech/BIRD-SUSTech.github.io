#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把多张活动照片拼成一张新闻配图（活动拼贴）。

布局：
    ┌─────────────────────────────┐
    │      主图（完整显示不裁剪）      │  留白处用该图模糊版填充
    ├──────┬──────┬───────────────┤
    │ 图2  │ 图3  │      图4      │  下排等宽，横向轻微重叠（后者压前者）
    └──────┴──────┴───────────────┘

用法：
    python tools/make_collage.py --main 图1.jpg --others 图2.jpg 图3.jpg 图4.jpg \
        --out images/news/2026-09-26.jpg
    可选： --size 1600x1200   --quality 88   --overlap 40
"""
import argparse
from PIL import Image, ImageFilter, ImageOps


def make_collage(main_path, others, out, size=(1600, 1200), quality=88, overlap=40, top_ratio=0.75):
    W, H = size
    top_h = int(H * top_ratio)
    bottom_h = H - top_h
    n = len(others)

    canvas = Image.new("RGB", (W, H), "white")

    # 主图：等比完整显示（contain），留白用同一张图的模糊放大版填充
    main = Image.open(main_path).convert("RGB")
    bg = ImageOps.fit(main, (W, top_h), method=Image.LANCZOS).filter(ImageFilter.GaussianBlur(30))
    fg = ImageOps.contain(main, (W, top_h), method=Image.LANCZOS)
    canvas.paste(bg, (0, 0))
    canvas.paste(fg, ((W - fg.width) // 2, (top_h - fg.height) // 2))

    # 下排：等宽 cover 裁剪，横向重叠
    if n:
        tile_w = (W + overlap * (n - 1)) // n
        for i, path in enumerate(others):
            im = Image.open(path).convert("RGB")
            tile = ImageOps.fit(im, (tile_w, bottom_h), method=Image.LANCZOS)
            tile = ImageOps.expand(tile, border=3, fill="white")  # 细白边，增强拼贴层次
            x = i * (tile_w - overlap)
            if x + tile.width > W:
                x = W - tile.width
            canvas.paste(tile, (max(0, x), top_h - 3))

    canvas.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
    return canvas.size


def main():
    ap = argparse.ArgumentParser(description="活动照片拼贴")
    ap.add_argument("--main", required=True, help="主图（完整显示，不裁剪不遮挡）")
    ap.add_argument("--others", nargs="*", default=[], help="下排图片（按编号顺序）")
    ap.add_argument("--out", required=True, help="输出 JPEG 路径")
    ap.add_argument("--size", default="1600x1200", help="画布尺寸，默认 1600x1200（4:3）")
    ap.add_argument("--quality", type=int, default=88)
    ap.add_argument("--overlap", type=int, default=40, help="下排图片横向重叠像素")
    args = ap.parse_args()

    w, h = (int(x) for x in args.size.lower().split("x"))
    size = make_collage(args.main, args.others, args.out, size=(w, h),
                        quality=args.quality, overlap=args.overlap)
    print(f"已生成拼图 {args.out}（{size[0]}x{size[1]}，主图 1 张 + 下排 {len(args.others)} 张）")


if __name__ == "__main__":
    main()
