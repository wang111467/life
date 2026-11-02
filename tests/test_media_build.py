import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_media.py"


class MediaBuildTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.exists(), "需要自动读取媒体目录的生成脚本")
        spec = importlib.util.spec_from_file_location("media_build", SCRIPT)
        self.build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.build)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for folder in ["media/videos", "media/photos", "assets"]:
            (self.root / folder).mkdir(parents=True)
        for name in ["index.html", "app.js", "viewer.js", "styles.css", ".nojekyll"]:
            (self.root / name).write_text("", encoding="utf-8")

    def test_discovers_nested_media_without_manual_list(self):
        (self.root / "media/videos/2026年11月1日.MP4").touch()
        (self.root / "media/photos/旅行").mkdir()
        (self.root / "media/photos/旅行/2026年11月2日 #记忆.jpg").touch()
        (self.root / "media/photos/.隐藏.jpg").touch()
        (self.root / "media/videos/说明.txt").touch()
        self.assertEqual(self.build.scan_media(self.root), {
            "videos": ["2026年11月1日.MP4"],
            "photos": ["旅行/2026年11月2日 #记忆.jpg"],
        })

    def test_regeneration_reflects_additions_and_deletions(self):
        first = self.root / "media/videos/2026年11月1日.mp4"
        first.touch()
        self.build.generate(self.root)
        self.assertIn(first.name, (self.root / "media.js").read_text())
        first.unlink()
        self.build.generate(self.root)
        text = (self.root / "media.js").read_text()
        data = json.loads(text.split("window.LIFE_MEDIA = ")[1].rstrip(";\n"))
        self.assertEqual(data, {"videos": [], "photos": []})

    def test_deploy_output_contains_current_media_and_no_source_tools(self):
        photo = self.root / "media/photos/2026年11月1日.png"
        photo.write_bytes(b"test photo")
        self.build.generate(self.root, deploy=True)
        output = self.root / "_site"
        self.assertTrue((output / "index.html").exists())
        self.assertEqual((output / "media/photos" / photo.name).read_bytes(), b"test photo")
        self.assertFalse((output / "scripts").exists())
        photo.unlink()
        self.build.generate(self.root, deploy=True)
        self.assertFalse((output / "media/photos" / photo.name).exists())

    def test_symlinks_are_excluded(self):
        outside = self.root / "outside.mp4"
        outside.touch()
        (self.root / "media/videos/link.mp4").symlink_to(outside)
        self.assertEqual(self.build.scan_media(self.root)["videos"], [])

    def test_shared_viewer_script_is_included_in_deployment(self):
        self.build.generate(self.root, deploy=True)
        self.assertTrue((self.root / "_site/viewer.js").is_file())


if __name__ == "__main__":
    unittest.main()
