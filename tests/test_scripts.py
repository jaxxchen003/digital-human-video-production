from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> ModuleType:
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pip_geometry = load_script("build_pip_geometry")
provider_jobs = load_script("record_provider_job")
delivery = load_script("validate_delivery")


class PipGeometryTests(unittest.TestCase):
    def test_measured_crop_centers_average_face(self) -> None:
        report = pip_geometry.build_geometry(
            [{"x": 1011.8, "y": 354.4}, {"x": 1012.2, "y": 354.6}],
            source_width=1920,
            source_height=1080,
            crop_size=600,
            pip_diameter=220,
            target_face_x_ratio=0.5,
            target_face_y_ratio=130 / 220,
            canvas_width=1920,
            canvas_height=1080,
            margin_x=42,
            bottom_margin=66,
            tolerance_px=2.0,
        )
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["crop"]["x"], 712.0)
        self.assertEqual(report["crop"]["y"], 0)
        self.assertEqual(report["canvas_positions"]["bottom_right"], {"x": 1658, "y": 794})
        self.assertLessEqual(report["pip"]["average_offset"]["distance"], 2.0)


class ProviderLedgerTests(unittest.TestCase):
    def test_duplicate_full_master_requires_reason(self) -> None:
        events = [{"stage": "full-master", "status": "completed", "audio_sha256": "locked"}]
        with self.assertRaises(ValueError):
            provider_jobs.assert_full_master_budget(
                events,
                audio_sha256="locked",
                status="completed",
                allow_regeneration_reason=None,
            )
        provider_jobs.assert_full_master_budget(
            events,
            audio_sha256="locked",
            status="completed",
            allow_regeneration_reason="provider output failed technical QC",
        )

    def test_duplicate_submission_is_blocked_before_paid_call(self) -> None:
        events = [{"stage": "full-master", "status": "submitted", "audio_sha256": "locked"}]
        with self.assertRaises(ValueError):
            provider_jobs.assert_full_master_budget(
                events,
                audio_sha256="locked",
                status="submitted",
                allow_regeneration_reason=None,
            )


class FreezeClassificationTests(unittest.TestCase):
    def test_readability_holds_are_distinct_from_unexpected_freezes(self) -> None:
        approved, unexpected = delivery.classify_freezes(
            [
                {"start": 10.0, "end": 12.5, "duration": 2.5},
                {"start": 30.0, "end": 32.5, "duration": 2.5},
            ],
            [{"from": 9.8, "to": 12.8}],
        )
        self.assertEqual(len(approved), 1)
        self.assertEqual(len(unexpected), 1)
        self.assertEqual(unexpected[0]["start"], 30.0)


class DeliveryCliTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_synthetic_delivery_passes_and_writes_contact_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "synthetic.mp4"
            report = root / "qc.json"
            contact_sheet = root / "contact.jpg"
            command = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=320x180:rate=30:duration=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=880:sample_rate=48000:duration=1",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                str(video),
            ]
            subprocess.run(command, check=True)
            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "validate_delivery.py"),
                    "--video",
                    str(video),
                    "--output",
                    str(report),
                    "--contact-sheet",
                    str(contact_sheet),
                    "--width",
                    "320",
                    "--height",
                    "180",
                    "--duration-ceiling",
                    "2",
                    "--lufs-tolerance",
                    "20",
                    "--allow-partial",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "CANDIDATE")
            self.assertEqual(payload["checks"]["full_decode"], "PASS")
            self.assertTrue(contact_sheet.exists())


if __name__ == "__main__":
    unittest.main()
