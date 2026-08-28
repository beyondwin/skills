#!/usr/bin/env python3
"""Inspect basic facts from local PNG, JPEG, and WebP image assets."""

import argparse
import dataclasses
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib


@dataclasses.dataclass(frozen=True)
class AssetFacts:
    alpha: bool | None
    byte_size: int
    format: str
    height: int
    sha256: str
    width: int


def _require_dimensions(width, height):
    if width == 0 or height == 0:
        raise ValueError("image dimensions must be non-zero")
    return width, height


MAX_PNG_DECODED_BYTES = 64 * 1024 * 1024
PNG_BIT_DEPTHS = {
    0: {1, 2, 4, 8, 16},
    2: {8, 16},
    3: {1, 2, 4, 8},
    4: {8, 16},
    6: {8, 16},
}
PNG_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
ADAM7_PASSES = (
    (0, 0, 8, 8),
    (4, 0, 8, 8),
    (0, 4, 4, 8),
    (2, 0, 4, 4),
    (0, 2, 2, 4),
    (1, 0, 2, 2),
    (0, 1, 1, 2),
)


def _png_row_bytes(width, bit_depth, color_type):
    return (width * PNG_CHANNELS[color_type] * bit_depth + 7) // 8


def _png_decoded_byte_count(width, height, bit_depth, color_type, interlace):
    if interlace == 0:
        return height * (1 + _png_row_bytes(width, bit_depth, color_type))
    total = 0
    for start_x, start_y, step_x, step_y in ADAM7_PASSES:
        pass_width = max(0, (width - start_x + step_x - 1) // step_x)
        pass_height = max(0, (height - start_y + step_y - 1) // step_y)
        if pass_width and pass_height:
            total += pass_height * (1 + _png_row_bytes(pass_width, bit_depth, color_type))
    return total


def _decode_png_idat(image_data, expected_size):
    decompressor = zlib.decompressobj()
    decoded_size = 0
    for chunk in image_data:
        if decompressor.eof:
            if chunk:
                raise ValueError("invalid PNG image data")
            continue
        try:
            decoded = decompressor.decompress(chunk, expected_size - decoded_size + 1)
        except zlib.error as error:
            raise ValueError("invalid PNG image data") from error
        decoded_size += len(decoded)
        if decoded_size > expected_size or decompressor.unconsumed_tail:
            raise ValueError("PNG image data size mismatch")
        if decompressor.unused_data:
            raise ValueError("invalid PNG image data")
    if not decompressor.eof:
        raise ValueError("invalid PNG image data")
    if decoded_size != expected_size:
        raise ValueError("PNG image data size mismatch")


def parse_png(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("invalid PNG signature")
    if len(data) < 33:
        raise ValueError("truncated PNG IHDR")

    length = struct.unpack(">I", data[8:12])[0]
    if data[12:16] != b"IHDR" or length != 13:
        raise ValueError("invalid PNG IHDR")
    chunk_end = 16 + length
    if chunk_end + 4 > len(data):
        raise ValueError("truncated PNG IHDR")

    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data[16:29]
    )
    _require_dimensions(width, height)
    if color_type not in PNG_BIT_DEPTHS or compression != 0 or filtering != 0 or interlace not in (0, 1):
        raise ValueError("invalid PNG IHDR")
    if bit_depth not in PNG_BIT_DEPTHS[color_type]:
        raise ValueError("invalid PNG bit depth")
    expected_decoded_size = _png_decoded_byte_count(width, height, bit_depth, color_type, interlace)
    if expected_decoded_size > MAX_PNG_DECODED_BYTES:
        raise ValueError("PNG image data exceeds 64 MiB limit")

    alpha = color_type in (4, 6)
    seen_image_data = False
    seen_trns = False
    seen_iend = False
    idat_sequence_closed = False
    palette_entries = None
    image_data: list[bytes] = []
    offset = chunk_end + 4
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("truncated PNG chunk")
        chunk_length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + chunk_length
        if payload_end + 4 > len(data):
            raise ValueError("truncated PNG chunk")
        chunk_payload = data[payload_start:payload_end]
        actual_crc = struct.unpack(">I", data[payload_end:payload_end + 4])[0]
        expected_crc = zlib.crc32(chunk_type + chunk_payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError("invalid PNG chunk CRC")
        if chunk_type == b"IDAT":
            if idat_sequence_closed:
                raise ValueError("invalid PNG IDAT ordering")
            seen_image_data = True
            image_data.append(chunk_payload)
        else:
            if seen_image_data:
                idat_sequence_closed = True
        if chunk_type == b"PLTE" and color_type == 3:
            if seen_image_data or seen_trns or palette_entries is not None or chunk_length == 0 or chunk_length > 768 or chunk_length % 3:
                raise ValueError("invalid PNG PLTE chunk")
            palette_entries = chunk_length // 3
        elif chunk_type == b"tRNS":
            valid_trns = (
                (color_type == 0 and chunk_length == 2)
                or (color_type == 2 and chunk_length == 6)
                or (color_type == 3 and palette_entries is not None and 1 <= chunk_length <= palette_entries)
            )
            if seen_image_data or seen_trns or not valid_trns:
                raise ValueError("invalid PNG tRNS chunk")
            seen_trns = True
            alpha = True
        elif chunk_type == b"IEND":
            if chunk_length != 0 or payload_end + 4 != len(data):
                raise ValueError("invalid PNG IEND chunk")
            if not seen_image_data:
                raise ValueError("missing PNG IDAT")
            seen_iend = True
            break
        offset = payload_end + 4
    if not seen_iend:
        raise ValueError("missing PNG IEND")
    _decode_png_idat(image_data, expected_decoded_size)
    return width, height, alpha


def parse_jpeg(data):
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("invalid JPEG SOI")
    offset = 2
    sof_markers = set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0))
    standalone_markers = {0x01, 0xD8, 0xD9} | set(range(0xD0, 0xD8))
    dimensions = None
    while offset < len(data):
        if data[offset] != 0xFF:
            raise ValueError("invalid JPEG marker")
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            raise ValueError("truncated JPEG marker")
        marker = data[offset]
        offset += 1
        if marker == 0x00:
            raise ValueError("invalid JPEG marker")
        if marker in standalone_markers:
            if marker == 0xD9:
                raise ValueError("missing JPEG scan or EOI")
            continue
        if offset + 2 > len(data):
            raise ValueError("truncated JPEG segment")
        segment_length = struct.unpack(">H", data[offset:offset + 2])[0]
        if segment_length < 2 or offset + segment_length > len(data):
            raise ValueError("invalid JPEG segment length")
        if marker in sof_markers:
            if segment_length < 8:
                raise ValueError("truncated JPEG SOF")
            height, width = struct.unpack(">HH", data[offset + 3:offset + 7])
            components = data[offset + 7]
            if components == 0 or segment_length < 8 + 3 * components:
                raise ValueError("invalid JPEG SOF")
            _require_dimensions(width, height)
            dimensions = (width, height, False)
        if marker == 0xDA:
            if dimensions is None:
                raise ValueError("JPEG SOS before SOF")
            scan_start = offset + segment_length
            if scan_start >= len(data) - 2 or data[-2:] != b"\xff\xd9":
                raise ValueError("missing JPEG scan or EOI")
            scan = data[scan_start:-2]
            if not scan:
                raise ValueError("missing JPEG scan or EOI")
            return dimensions
        offset += segment_length
    if dimensions is not None:
        raise ValueError("missing JPEG scan or EOI")
    raise ValueError("JPEG SOF marker not found")


def parse_webp(data):
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("invalid WebP RIFF header")
    declared_size = struct.unpack("<I", data[4:8])[0]
    riff_end = declared_size + 8
    if declared_size < 4 or riff_end != len(data):
        raise ValueError("truncated WebP RIFF")

    offset = 12
    vp8x = None
    image = None
    previous_rank = 0
    while offset < riff_end:
        if offset + 8 > riff_end:
            raise ValueError("truncated WebP chunk")
        chunk_type = data[offset:offset + 4]
        chunk_length = struct.unpack("<I", data[offset + 4:offset + 8])[0]
        payload_start = offset + 8
        payload_end = payload_start + chunk_length
        padded_end = payload_end + (chunk_length % 2)
        if padded_end > riff_end:
            raise ValueError("truncated WebP chunk")
        if chunk_length % 2 and data[payload_end] != 0:
            raise ValueError("invalid WebP chunk padding")
        payload = data[payload_start:payload_end]
        if chunk_type == b"VP8X":
            if vp8x is not None or image is not None or offset != 12:
                raise ValueError("invalid WebP VP8X ordering")
            if len(payload) != 10 or payload[1:4] != b"\0\0\0" or payload[0] & 0xC1:
                raise ValueError("invalid WebP VP8X header")
            vp8x = payload
        elif chunk_type in (b"VP8 ", b"VP8L"):
            if image is not None:
                raise ValueError("multiple WebP image chunks")
            if vp8x is not None and previous_rank > 3:
                raise ValueError("invalid WebP image ordering")
            image = (chunk_type, payload)
            previous_rank = 3
        elif vp8x is not None:
            ranks = {b"ICCP": 1, b"ALPH": 2, b"EXIF": 4, b"XMP ": 5}
            rank = ranks.get(chunk_type)
            if rank is not None:
                if rank < previous_rank:
                    raise ValueError("invalid WebP extended chunk ordering")
                previous_rank = rank
        offset = padded_end
    if offset != riff_end:
        raise ValueError("invalid WebP chunk layout")
    if image is None and vp8x is not None:
        raise ValueError("missing WebP image data")
    if image is None:
        raise ValueError("unsupported WebP primary chunk")

    chunk_type, payload = image
    if chunk_type == b"VP8 ":
        if len(payload) <= 10 or payload[3:6] != b"\x9d\x01\x2a":
            raise ValueError("invalid WebP VP8 header")
        width = struct.unpack("<H", payload[6:8])[0] & 0x3FFF
        height = struct.unpack("<H", payload[8:10])[0] & 0x3FFF
        _require_dimensions(width, height)
        alpha = False
    elif len(payload) <= 5 or payload[0] != 0x2F:
        raise ValueError("invalid WebP VP8L header")
    else:
        packed = int.from_bytes(payload[1:5], "little")
        width = (packed & 0x3FFF) + 1
        height = ((packed >> 14) & 0x3FFF) + 1
        _require_dimensions(width, height)
        alpha = None
    if vp8x is None:
        return width, height, alpha
    canvas_width = int.from_bytes(vp8x[4:7], "little") + 1
    canvas_height = int.from_bytes(vp8x[7:10], "little") + 1
    _require_dimensions(canvas_width, canvas_height)
    if (canvas_width, canvas_height) != (width, height):
        raise ValueError("WebP VP8X canvas does not match image data")
    return canvas_width, canvas_height, bool(vp8x[0] & 0x10)


def inspect_bytes(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        image_format = "png"
        width, height, alpha = parse_png(data)
    elif data.startswith(b"\xff\xd8"):
        image_format = "jpeg"
        width, height, alpha = parse_jpeg(data)
    elif data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP":
        image_format = "webp"
        width, height, alpha = parse_webp(data)
    else:
        raise ValueError("unsupported image format")
    return AssetFacts(
        alpha=alpha,
        byte_size=len(data),
        format=image_format,
        height=height,
        sha256=hashlib.sha256(data).hexdigest(),
        width=width,
    )


def inspect_file(path):
    return inspect_bytes(Path(path).read_bytes())


def _write_json(value, output_stream):
    output_stream.write(json.dumps(value, sort_keys=True) + "\n")


def main(argv=None, output_stream=None, error_stream=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    if not args.path:
        parser.error("path is required")
    output_stream = output_stream or sys.stdout
    error_stream = error_stream or sys.stderr
    try:
        facts = inspect_file(args.path)
    except (OSError, ValueError) as error:
        message = error.strerror if isinstance(error, OSError) and error.strerror else str(error)
        _write_json({"error": message, "path": args.path}, error_stream)
        return 1
    rendered = json.dumps(dataclasses.asdict(facts), sort_keys=True) + "\n"
    if args.output:
        try:
            Path(args.output).write_text(rendered)
        except OSError as error:
            message = error.strerror if error.strerror else str(error)
            _write_json({"error": message, "path": args.path}, error_stream)
            return 1
    else:
        output_stream.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
