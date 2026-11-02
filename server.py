"""本地启动一次，刷新页面时自动读取最新媒体；不影响 GitHub 静态发布。"""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urlsplit
import webbrowser

from scripts.build_media import media_javascript, scan_media


ROOT = Path(__file__).resolve().parent


class LifeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        self.range_remaining = None
        root = Path(self.directory).resolve()
        url_path = unquote(urlsplit(self.path).path)
        path = Path(self.translate_path(self.path))
        if any(part.startswith(".") for part in PurePosixPath(url_path).parts):
            self.send_error(403)
            return None
        if not path.resolve().is_relative_to(root):
            self.send_error(403)
            return None

        # 页面仍然加载 media.js；本地每次请求现扫目录，GitHub 则使用生成的静态文件。
        if url_path == "/media.js":
            body = media_javascript(scan_media(root)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return io.BytesIO(body)

        if path.is_dir():
            if url_path != "/":
                self.send_error(404)
                return None
            path = path / "index.html"
        requested = self.headers.get("Range")
        if not requested or not path.is_file():
            return super().send_head()

        # 支持视频拖动进度时的分段读取，不把整个视频读入内存。
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", requested.strip())
        if not match or not any(match.groups()):
            self.send_error(400, "Invalid byte range")
            return None
        size = path.stat().st_size
        first, last = match.groups()
        try:
            start = int(first) if first else max(0, size - int(last))
            end = min(int(last), size - 1) if first and last else size - 1
        except ValueError:
            self.send_error(400, "Invalid byte range")
            return None
        if start >= size or end < start:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        try:
            stream = path.open("rb")
        except OSError:
            self.send_error(404)
            return None
        stream.seek(start)
        self.range_remaining = end - start + 1
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(self.range_remaining))
        self.end_headers()
        return stream

    def copyfile(self, source, outputfile):
        try:
            if self.range_remaining is None:
                return super().copyfile(source, outputfile)
            while self.range_remaining:
                chunk = source.read(min(65536, self.range_remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                self.range_remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass  # 关闭预览或切换视频时，浏览器会主动中断请求。

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="启动 W 的生活空间")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--open", action="store_true", help="启动后自动打开浏览器")
    args = parser.parse_args()
    handler = partial(LifeHandler, directory=str(ROOT))
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as error:
        parser.exit(1, f"无法启动：{error}\n如果已经启动，请直接访问网页；端口被其他程序占用时，可运行 python3 server.py --port 8001 --open\n")
    url = f"http://127.0.0.1:{httpd.server_port}"
    print(f"\nW 的生活空间已启动：{url}\n\n保持这个窗口打开，添加或删除媒体后刷新网页即可。\n按 Ctrl+C 停止，下次使用时再次启动。\n", flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
