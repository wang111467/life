from functools import partial
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


SERVER = Path(__file__).resolve().parents[1] / "server.py"


class LocalServerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SERVER.exists(), "需要支持刷新自动读取媒体的本地服务")
        spec = importlib.util.spec_from_file_location("life_server", SERVER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for category in ["videos", "photos"]:
            (self.root / "media" / category).mkdir(parents=True)
        (self.root / "index.html").write_text("<h1>W 的生活空间</h1>")
        handler = partial(module.LifeHandler, directory=str(self.root))
        self.server = module.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def get_manifest(self):
        with urlopen(self.url + "/media.js") as response:
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            text = response.read().decode()
        return json.loads(text.split("window.LIFE_MEDIA = ")[1].rstrip(";\n"))

    def test_refresh_discovers_added_and_deleted_files_without_restart(self):
        self.assertEqual(self.get_manifest(), {"videos": [], "photos": []})
        photo = self.root / "media/photos/2026年11月1日.png"
        video = self.root / "media/videos/2026年11月2日.mp4"
        photo.touch()
        video.touch()
        self.assertEqual(self.get_manifest(), {"videos": [video.name], "photos": [photo.name]})
        photo.unlink()
        self.assertEqual(self.get_manifest()["photos"], [])
        self.assertFalse((self.root / "media.js").exists(), "动态清单无需写回磁盘")

    def test_home_and_unicode_media_paths(self):
        with urlopen(self.url + "/") as response:
            self.assertIn("W 的生活空间", response.read().decode())
        photo = self.root / "media/photos/2026年11月1日 #训练.png"
        photo.write_bytes(b"photo content")
        with urlopen(self.url + "/" + quote(photo.relative_to(self.root).as_posix())) as response:
            self.assertEqual(response.read(), b"photo content")

    def test_video_seek_and_head_requests(self):
        (self.root / "media/videos/clip.mp4").write_bytes(b"0123456789")
        url = self.url + "/media/videos/clip.mp4"
        with urlopen(Request(url, headers={"Range": "bytes=2-5"})) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.headers["Content-Range"], "bytes 2-5/10")
            self.assertEqual(response.read(), b"2345")
        with urlopen(Request(url, method="HEAD", headers={"Range": "bytes=-3"})) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.headers["Content-Length"], "3")
            self.assertEqual(response.read(), b"")
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(url, headers={"Range": "bytes=10-"}))
        self.assertEqual(error.exception.code, 416)

    def test_private_paths_and_escaping_symlinks_are_not_served(self):
        (self.root / ".secret").write_text("private")
        (self.root / "media/photos/link.png").symlink_to(self.root.parent / "outside.png")
        for path in ["/.secret", "/media/photos/", "/media/photos/link.png"]:
            with self.assertRaises(HTTPError) as error:
                urlopen(self.url + path)
            self.assertIn(error.exception.code, [403, 404])


if __name__ == "__main__":
    unittest.main()
