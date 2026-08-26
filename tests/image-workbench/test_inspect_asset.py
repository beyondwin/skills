from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from types import ModuleType


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INSPECTOR_PATH = (
    REPOSITORY_ROOT / "skills" / "image-workbench" / "scripts" / "inspect_asset.py"
)
INSPECTOR_PATH = Path(
    os.environ.get("IMAGE_WORKBENCH_INSPECTOR", DEFAULT_INSPECTOR_PATH)
)


def load_inspector(path: Path = INSPECTOR_PATH) -> ModuleType:
    spec = importlib.util.spec_from_file_location("inspect_asset", path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bind_inspector(module: ModuleType) -> None:
    globals().update(
        {
            "INSPECTOR": module,
            "parse_png": module.parse_png,
            "parse_jpeg": module.parse_jpeg,
            "parse_webp": module.parse_webp,
            "inspect_bytes": module.inspect_bytes,
            "inspect_file": module.inspect_file,
            "main": module.main,
        }
    )


if INSPECTOR_PATH.is_file():
    _bind_inspector(load_inspector(INSPECTOR_PATH))
else:
    INSPECTOR = None


class StringSink:
    def __init__(self):
        self.value = ""

    def write(self, text):
        self.value += text


def make_png(width, height, color_type, trns=False, trns_payload=None, before_trns=(), after_trns=()):
    def chunk(kind, payload):
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    chunks = [chunk(b"IHDR", ihdr)]
    chunks.extend(chunk(kind, payload) for kind, payload in before_trns)
    if trns:
        transparency = trns_payload if trns_payload is not None else (b"\0\0\0\0\0\0" if color_type == 2 else b"\0\0")
        chunks.append(chunk(b"tRNS", transparency))
    chunks.extend(chunk(kind, payload) for kind, payload in after_trns)
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type, 1)
    raw_scanlines = b"".join(b"\0" + b"\0" * (width * channels) for _ in range(height))
    adler_s1 = 1
    adler_s2 = 0
    for value in raw_scanlines:
        adler_s1 = (adler_s1 + value) % 65521
        adler_s2 = (adler_s2 + adler_s1) % 65521
    compressed = (
        b"\x78\x01\x01"
        + struct.pack("<H", len(raw_scanlines))
        + struct.pack("<H", 0xFFFF - len(raw_scanlines))
        + raw_scanlines
        + struct.pack(">I", (adler_s2 << 16) | adler_s1)
    )
    chunks.append(chunk(b"IDAT", compressed))
    chunks.append(chunk(b"IEND", b""))
    return b"\x89PNG\r\n\x1a\n" + b"".join(chunks)


def make_png_with_idat(width, height, color_type, compressed):
    return make_png_with_idat_chunks(width, height, color_type, (compressed,))


def make_png_with_idat_chunks(width, height, color_type, compressed_chunks):
    def chunk(kind, payload):
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + b"".join(
        (chunk(b"IHDR", ihdr), *(chunk(b"IDAT", payload) for payload in compressed_chunks), chunk(b"IEND", b""))
    )


def make_jpeg(width, height):
    if (width, height) != (1, 1):
        raise ValueError("self-test JPEG fixture is fixed at 1x1")
    return bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffdb0043000302020302020303030304030304050805050404050a070706080c0a0c0c0b0a0b0b0d0e12100d0e110e0b0b1016101113141515150c0f171816141812141514ffdb00430103040405040509050509140d0b0d1414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414ffc00011080001000103012200021101031101ffc4001500010100000000000000000000000000000008ffc40014100100000000000000000000000000000000ffc4001501010100000000000000000000000000000709ffc40014110100000000000000000000000000000000ffda000c03010002110311003f009d00062a9bffd9")


def make_webp_vp8x(width, height, alpha, extra_payload=b""):
    flags = 0x10 if alpha else 0
    payload = bytes([flags, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little") + extra_payload
    padding = b"\0" if len(payload) % 2 else b""
    body = b"WEBPVP8X" + struct.pack("<I", len(payload)) + payload + padding
    return b"RIFF" + struct.pack("<I", len(body)) + body


def make_webp_vp8(width, height):
    if (width, height) != (1, 1):
        raise ValueError("self-test VP8 fixture is fixed at 1x1")
    return bytes.fromhex("524946463c000000574542505650382030000000d001009d012a0100010002003425a00274ba01f80003b000fef0c40bff20b96175c8d7ff203fe407fc80fff8f2000000")


def make_webp_vp8l(width, height):
    if (width, height) != (1, 1):
        raise ValueError("self-test VP8L fixture is fixed at 1x1")
    return bytes.fromhex("524946461e000000574542505650384c110000002f0000000007d0fffef7bfff8188e87f0000")


def make_webp_extended_vp8(width, height, alpha):
    if (width, height) != (1, 1):
        raise ValueError("self-test extended WebP fixture is fixed at 1x1")
    vp8l_chunk = make_webp_vp8l(1, 1)[12:]
    vp8x_payload = bytes([0x10 if alpha else 0, 0, 0, 0]) + b"\0\0\0\0\0\0"
    vp8x_chunk = b"VP8X" + struct.pack("<I", len(vp8x_payload)) + vp8x_payload
    body = b"WEBP" + vp8x_chunk + vp8l_chunk
    return b"RIFF" + struct.pack("<I", len(body)) + body


class AssetInspectorTests(unittest.TestCase):
    def test_png_fixture_has_valid_chunk_crcs(self):
        data = make_png(width=3, height=2, color_type=6)
        offset = 8
        while offset < len(data):
            length = struct.unpack(">I", data[offset:offset + 4])[0]
            chunk = data[offset + 4:offset + 8 + length]
            actual = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
            self.assertEqual(actual, zlib.crc32(chunk) & 0xFFFFFFFF)
            offset += 12 + length

    def test_png_reports_dimensions_and_alpha(self):
        data = make_png(width=3, height=2, color_type=6)
        self.assertIn(b"IDAT", data)
        self.assertEqual(parse_png(data), (3, 2, True))

    def test_png_trns_reports_alpha(self):
        self.assertEqual(parse_png(make_png(3, 2, color_type=2, trns=True)), (3, 2, True))

    def test_palette_png_trns_requires_valid_preceding_palette(self):
        palette = b"\0\0\0\xff\xff\xff"
        self.assertEqual(
            parse_png(make_png(3, 2, color_type=3, trns=True, trns_payload=b"\0\xff", before_trns=[(b"PLTE", palette)])),
            (3, 2, True),
        )
        with self.assertRaises(ValueError):
            parse_png(make_png(3, 2, color_type=3, trns=True, trns_payload=b"\0"))
        with self.assertRaises(ValueError):
            parse_png(make_png(3, 2, color_type=3, trns=True, trns_payload=b"\0", after_trns=[(b"PLTE", palette)]))
        with self.assertRaises(ValueError):
            parse_png(make_png(3, 2, color_type=3, trns=True, trns_payload=b"\0\xff\x80", before_trns=[(b"PLTE", palette)]))
        with self.assertRaises(ValueError):
            parse_png(make_png(3, 2, color_type=3, trns=True, trns_payload=b"\0", before_trns=[(b"PLTE", b"\0\0\0\xff")]))

    def test_jpeg_reports_dimensions_without_alpha(self):
        data = make_jpeg(width=1, height=1)
        self.assertEqual(parse_jpeg(data), (1, 1, False))

    def test_jpeg_requires_scan_and_eoi_after_sof(self):
        data = make_jpeg(width=1, height=1)
        self.assertEqual(parse_jpeg(data), (1, 1, False))
        with self.assertRaisesRegex(ValueError, "JPEG scan"):
            parse_jpeg(data[:-2])

    def test_webp_vp8x_reports_dimensions_and_alpha_flag(self):
        data = make_webp_extended_vp8(width=1, height=1, alpha=True)
        self.assertEqual(parse_webp(data), (1, 1, True))

    def test_webp_vp8x_without_alpha_is_false(self):
        self.assertEqual(parse_webp(make_webp_extended_vp8(1, 1, alpha=False)), (1, 1, False))

    def test_webp_vp8x_requires_image_data_and_precedes_it(self):
        with self.assertRaisesRegex(ValueError, "image data"):
            parse_webp(make_webp_vp8x(1, 1, alpha=False))
        valid = make_webp_extended_vp8(1, 1, alpha=False)
        vp8x = valid[12:30]
        vp8 = valid[30:]
        reordered_body = b"WEBP" + vp8 + vp8x
        reordered = b"RIFF" + struct.pack("<I", len(reordered_body)) + reordered_body
        with self.assertRaisesRegex(ValueError, "VP8X"):
            parse_webp(reordered)

    def test_webp_vp8_reports_dimensions_without_alpha(self):
        self.assertEqual(parse_webp(make_webp_vp8(1, 1)), (1, 1, False))

    def test_webp_vp8l_reports_dimensions_with_unknown_alpha(self):
        self.assertEqual(parse_webp(make_webp_vp8l(1, 1)), (1, 1, None))

    def test_unsupported_input_is_an_explicit_error(self):
        with self.assertRaisesRegex(ValueError, "unsupported image format"):
            inspect_bytes(b"not-an-image")

    def test_truncated_or_malformed_png_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_png(b"\x89PNG\r\n\x1a\n")
        with self.assertRaises(ValueError):
            parse_png(make_png(0, 2, color_type=6))
        with self.assertRaises(ValueError):
            parse_png(make_png(3, 2, color_type=2, trns=True, trns_payload=b"\0"))

    def test_png_without_iend_is_rejected(self):
        valid = make_png(3, 2, color_type=6)
        self.assertEqual(parse_png(valid), (3, 2, True))
        with self.assertRaisesRegex(ValueError, "missing PNG IEND"):
            parse_png(valid[:-12])

    def test_png_without_idat_is_rejected(self):
        valid = make_png(3, 2, color_type=6)
        idat_offset = valid.index(b"IDAT") - 4
        idat_length = struct.unpack(">I", valid[idat_offset:idat_offset + 4])[0]
        missing_idat = valid[:idat_offset] + valid[idat_offset + 12 + idat_length:]
        with self.assertRaisesRegex(ValueError, "missing PNG IDAT"):
            parse_png(missing_idat)

    def test_png_rejects_oversized_or_dimension_mismatched_decoded_data(self):
        oversized = make_png_with_idat(1, 1, 6, zlib.compress(b"\0" * 10_000_000))
        with self.assertRaisesRegex(ValueError, "PNG image data size mismatch"):
            parse_png(oversized)
        declared_too_large = make_png_with_idat(10_000, 10_000, 6, zlib.compress(b""))
        with self.assertRaisesRegex(ValueError, "PNG image data exceeds"):
            parse_png(declared_too_large)
        mismatched = make_png_with_idat(1, 1, 6, zlib.compress(b"\0" * 6))
        with self.assertRaisesRegex(ValueError, "PNG image data size mismatch"):
            parse_png(mismatched)

    def test_png_accepts_empty_trailing_idat_after_zlib_eof_only(self):
        compressed = zlib.compress(b"\0" * 5)
        self.assertEqual(
            parse_png(make_png_with_idat_chunks(1, 1, 6, (compressed, b""))),
            (1, 1, True),
        )
        with self.assertRaisesRegex(ValueError, "invalid PNG image data"):
            parse_png(make_png_with_idat_chunks(1, 1, 6, (compressed, b"\0")))

    def test_truncated_or_malformed_jpeg_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_jpeg(b"\xff\xd8\xff\xc0\x00")
        with self.assertRaises(ValueError):
            parse_jpeg(b"\xff\xd8\xff\xc0\x00\x08\x08\x00\x00\x00\x05\x01\x01\x11\x00")

    def test_truncated_or_malformed_webp_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_webp(b"RIFF\x04\0\0\0WEBP")
        with self.assertRaises(ValueError):
            parse_webp(b"RIFF\xff\xff\xff\xffWEBPVP8X\x00\0\0\0")
        with self.assertRaises(ValueError):
            parse_webp(make_webp_vp8x(1, 1, alpha=False)[:-1])
        with self.assertRaises(ValueError):
            parse_webp(make_webp_vp8x(1, 1, alpha=False, extra_payload=b"\0"))

    def test_inspect_file_reports_hash_and_byte_size(self):
        data = make_png(3, 2, color_type=6)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "asset.png"
            path.write_bytes(data)
            facts = inspect_file(path)
        self.assertEqual(facts.byte_size, len(data))
        self.assertEqual(facts.sha256, hashlib.sha256(data).hexdigest())
        self.assertEqual(facts.format, "png")

    def test_missing_file_cli_exits_one_with_error_json(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.png"
            stdout = StringSink()
            stderr = StringSink()
            result = main([str(missing)], output_stream=stdout, error_stream=stderr)
        self.assertEqual(result, 1)
        self.assertEqual(stdout.value, "")
        self.assertEqual(
            stderr.value,
            json.dumps({"error": "No such file or directory", "path": str(missing)}, sort_keys=True) + "\n",
        )

    def test_malformed_and_unsupported_cli_errors_use_stderr_only(self):
        with tempfile.TemporaryDirectory() as directory:
            malformed = Path(directory) / "broken.png"
            unsupported = Path(directory) / "note.txt"
            malformed.write_bytes(b"\x89PNG\r\n\x1a\n")
            unsupported.write_bytes(b"not-an-image")
            for path in (malformed, unsupported):
                with self.subTest(path=path):
                    stdout = StringSink()
                    stderr = StringSink()
                    self.assertEqual(main([str(path)], output_stream=stdout, error_stream=stderr), 1)
                    self.assertEqual(stdout.value, "")
                    self.assertIn('"error"', stderr.value)

    def test_output_file_equals_sorted_success_json(self):
        data = make_png(3, 2, color_type=6)
        expected = json.dumps(
            {
                "alpha": True,
                "byte_size": len(data),
                "format": "png",
                "height": 2,
                "sha256": hashlib.sha256(data).hexdigest(),
                "width": 3,
            },
            sort_keys=True,
        ) + "\n"
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "asset.png"
            output_path = Path(directory) / "facts.json"
            input_path.write_bytes(data)
            self.assertEqual(main([str(input_path), "--output", str(output_path)]), 0)
            self.assertEqual(output_path.read_text(), expected)

    def test_output_write_error_cli_exits_one_with_error_json(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "asset.png"
            input_path.write_bytes(make_png(3, 2, color_type=6))
            stdout = StringSink()
            stderr = StringSink()
            result = main([str(input_path), "--output", directory], output_stream=stdout, error_stream=stderr)
        self.assertEqual(result, 1)
        self.assertEqual(stdout.value, "")
        payload = json.loads(stderr.value)
        self.assertEqual(payload["path"], str(input_path))
        # Unix EISDIR vs Windows EACCES when --output is a directory.
        self.assertIn(payload["error"], {"Is a directory", "Permission denied", "Access is denied"})


class PublicInspectorContractTests(unittest.TestCase):
    def test_png_reports_dimensions_alpha_size_and_hash(self):
        self.assertTrue(INSPECTOR_PATH.is_file(), "public inspector is absent")
        inspector = load_inspector(INSPECTOR_PATH)
        data = make_png(width=3, height=2, color_type=6)
        facts = inspector.inspect_bytes(data)
        self.assertEqual((facts.width, facts.height, facts.alpha), (3, 2, True))
        self.assertEqual(facts.byte_size, len(data))
        self.assertEqual(facts.sha256, hashlib.sha256(data).hexdigest())

    def test_runtime_script_contains_no_unittest_suite(self):
        self.assertTrue(INSPECTOR_PATH.is_file(), "public inspector is absent")
        text = INSPECTOR_PATH.read_text(encoding="utf-8")
        self.assertNotIn("import unittest", text)
        self.assertNotIn("class AssetInspectorTests", text)


if __name__ == "__main__":
    unittest.main()
