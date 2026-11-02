"""扫描媒体并生成静态清单；仅使用 Python 标准库，不启动服务器。"""

import argparse
import json
from pathlib import Path
import shutil


EXTENSIONS = {
    "videos": {".mp4", ".webm", ".mov", ".m4v", ".ogv"},
    "photos": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".bmp"},
}


def scan_media(root):
    root = Path(root).resolve()
    result = {"videos": [], "photos": []}
    for category, extensions in EXTENSIONS.items():
        folder = root / "media" / category
        if not folder.is_dir() or folder.is_symlink():
            continue
        for path in folder.rglob("*"):
            relative = path.relative_to(folder)
            if any(part.startswith(".") for part in relative.parts):
                continue
            if path.is_symlink() or not path.is_file() or path.suffix.lower() not in extensions:
                continue
            if not path.resolve().is_relative_to(folder.resolve()):
                continue
            result[category].append(relative.as_posix())
        result[category].sort(key=str.casefold)
    return result


def media_javascript(media):
    return "// 自动生成，无需手动编辑。本地启动服务后刷新即更新；GitHub 发布时自动生成。\nwindow.LIFE_MEDIA = " + json.dumps(media, ensure_ascii=False, indent=2) + ";\n"


def generate(root, deploy=False):
    root = Path(root).resolve()
    media = scan_media(root)
    output = root
    if deploy:
        output = root / "_site"
        if output.is_symlink():
            raise ValueError("_site 不能是符号链接")
        if output.exists():
            shutil.rmtree(output)
        output.mkdir()
        for name in ("index.html", "styles.css", "app.js", "viewer.js", ".nojekyll"):
            shutil.copy2(root / name, output / name)
        shutil.copytree(root / "assets", output / "assets")
        for category, names in media.items():
            (output / "media" / category).mkdir(parents=True)
            for name in names:
                relative = Path("media") / category / name
                target = output / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root / relative, target)
    (output / "media.js").write_text(media_javascript(media), encoding="utf-8")
    return media


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="自动更新生活空间的媒体清单")
    parser.add_argument("--deploy", action="store_true", help="生成可发布的 _site 目录")
    args = parser.parse_args()
    media = generate(Path(__file__).resolve().parents[1], deploy=args.deploy)
    print(f"已更新：{len(media['videos'])} 个视频，{len(media['photos'])} 张图片。")
