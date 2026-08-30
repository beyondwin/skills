from __future__ import annotations

import copy
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import completed_review, pending_record

from pre_sdd_review_evidence import storage
from pre_sdd_review_evidence.schema import EvidenceError, canonical_json_bytes


class StorageLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.paths = storage.EvidencePaths.from_home(self.root / "evidence")

    def test_evidence_home_is_canonical_absolute_and_rejects_invalid_override(self) -> None:
        target = self.root / "same"
        target.mkdir()
        alias = self.root / "alias"
        alias.symlink_to(target, target_is_directory=True)
        first = storage.evidence_home({"PRE_SDD_REVIEW_HOME": str(target)}, self.root)
        second = storage.evidence_home({"PRE_SDD_REVIEW_HOME": str(alias)}, self.root)
        self.assertEqual(first, second)
        with self.assertRaisesRegex(EvidenceError, "absolute"):
            storage.evidence_home({"PRE_SDD_REVIEW_HOME": "relative"}, self.root)
        with self.assertRaises(EvidenceError):
            storage.evidence_home({"PRE_SDD_REVIEW_HOME": "   "}, self.root)

    def test_finish_review_is_atomic_create_only_and_idempotent(self) -> None:
        pending = pending_record()
        handle = storage.create_pending(self.paths, pending)
        review = completed_review(pending)
        first = storage.finish_review(self.paths, handle.run_id, review)
        second = storage.finish_review(self.paths, handle.run_id, review)
        self.assertEqual(first.sha256, second.sha256)
        self.assertFalse((handle.directory / ".pending.json").exists())
        with self.assertRaisesRegex(EvidenceError, "conflicting retry"):
            storage.finish_review(
                self.paths, handle.run_id, completed_review(pending, verdict="REVISE")
            )
        self.assertEqual((handle.directory / "review.json").read_bytes(), canonical_json_bytes(review))

    def test_finish_review_cannot_change_pending_identity_or_target(self) -> None:
        pending = pending_record()
        handle = storage.create_pending(self.paths, pending)
        changed = completed_review(pending)
        changed["target"]["repo_id"] = "8" * 64
        with self.assertRaisesRegex(EvidenceError, "pending"):
            storage.finish_review(self.paths, handle.run_id, changed)
        self.assertFalse((handle.directory / "review.json").exists())
        self.assertTrue((handle.directory / ".pending.json").exists())

    def test_final_file_race_never_overwrites_winning_bytes(self) -> None:
        pending = pending_record()
        handle = storage.create_pending(self.paths, pending)
        winner = b'{"winner":true}\n'

        def race(point: str, _path: Path) -> None:
            if point == "review-temp-fsynced":
                (handle.directory / "review.json").write_bytes(winner)

        with self.assertRaises(EvidenceError):
            storage.finish_review(
                self.paths, handle.run_id, completed_review(pending),
                interruption_hook=race,
            )
        self.assertEqual((handle.directory / "review.json").read_bytes(), winner)
        self.assertFalse((handle.directory / ".write.lock").exists())
        self.assertFalse(any(path.name.endswith(".tmp") for path in handle.directory.iterdir()))

    def test_pending_layout_permissions_locking_and_no_global_lock(self) -> None:
        pending = pending_record(started_at="2026-02-03T10:00:00Z")
        handle = storage.create_pending(self.paths, pending)
        self.assertEqual(handle.directory.relative_to(self.paths.runs).parts[:2], ("2026", "02"))
        self.assertFalse((self.paths.home / ".write.lock").exists())
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(handle.directory.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE((handle.directory / ".pending.json").stat().st_mode), 0o600)
        lock = handle.directory / ".write.lock"
        lock.touch(mode=0o600)
        with self.assertRaisesRegex(EvidenceError, "run is locked"):
            storage.finish_review(self.paths, handle.run_id, completed_review(pending))

    def test_interruption_after_pending_fsync_recovers_exact_bytes(self) -> None:
        pending = pending_record()
        with self.assertRaisesRegex(RuntimeError, "interrupt"):
            storage.create_pending(
                self.paths,
                pending,
                interruption_hook=lambda point, _path: (_ for _ in ()).throw(RuntimeError("interrupt")) if point == "pending-fsynced" else None,
            )
        staging = self.paths.runs / f".staging-{pending['run_id']}"
        expected = canonical_json_bytes(pending)
        self.assertEqual((staging / ".pending.json").read_bytes(), expected)
        reports = storage.recover_staging(self.paths)
        self.assertEqual(reports, ())
        run_dir = self.paths.run_directory(str(pending["run_id"]), str(pending["started_at"]))
        self.assertEqual((run_dir / ".pending.json").read_bytes(), expected)
        self.assertFalse(staging.exists())

    def test_recovery_preserves_conflicting_destination_and_cleans_only_identical(self) -> None:
        for identical in (False, True):
            with self.subTest(identical=identical):
                paths = storage.EvidencePaths.from_home(self.root / f"recovery-{identical}")
                pending = pending_record()
                with self.assertRaises(RuntimeError):
                    storage.create_pending(
                        paths, pending,
                        interruption_hook=lambda point, _path: (_ for _ in ()).throw(RuntimeError("stop")) if point == "pending-fsynced" else None,
                    )
                staging = paths.runs / f".staging-{pending['run_id']}"
                destination = paths.run_directory(str(pending["run_id"]), str(pending["started_at"]))
                destination.parent.mkdir(parents=True, exist_ok=True)
                if os.name == "posix":
                    destination.parent.parent.chmod(0o700)
                    destination.parent.chmod(0o700)
                destination.mkdir(mode=0o700)
                winner = copy.deepcopy(pending)
                if not identical:
                    winner["start_locator_binding"] = "7" * 64
                (destination / ".pending.json").write_bytes(canonical_json_bytes(winner))
                if os.name == "posix":
                    (destination / ".pending.json").chmod(0o600)
                before = (destination / ".pending.json").read_bytes()
                unresolved = storage.recover_staging(paths)
                self.assertEqual((destination / ".pending.json").read_bytes(), before)
                self.assertEqual(staging.exists(), not identical)
                self.assertEqual(bool(unresolved), not identical)

    def test_terminal_interruption_preserves_final_bytes_and_retry_cleans_pending(self) -> None:
        for transition in ("finish", "abandon"):
            with self.subTest(transition=transition):
                paths = storage.EvidencePaths.from_home(self.root / transition)
                pending = pending_record()
                handle = storage.create_pending(paths, pending)
                with self.assertRaisesRegex(RuntimeError, "interrupt"):
                    if transition == "finish":
                        record = completed_review(pending)
                        storage.finish_review(paths, handle.run_id, record, interruption_hook=lambda point, _path: (_ for _ in ()).throw(RuntimeError("interrupt")) if point == "review-published" else None)
                    else:
                        storage.abandon_run(paths, handle.run_id, "client-interrupted", completed_at="2026-08-30T10:05:00Z", recorder_elapsed_ms=2, interruption_hook=lambda point, _path: (_ for _ in ()).throw(RuntimeError("interrupt")) if point == "review-published" else None)
                        record = storage.load_review(paths, handle.run_id)
                final_bytes = (handle.directory / "review.json").read_bytes()
                self.assertTrue((handle.directory / ".pending.json").exists())
                if transition == "finish":
                    result = storage.finish_review(paths, handle.run_id, record)
                else:
                    result = storage.abandon_run(paths, handle.run_id, "client-interrupted", completed_at="2026-08-30T10:05:00Z", recorder_elapsed_ms=2)
                self.assertEqual(final_bytes, (handle.directory / "review.json").read_bytes())
                self.assertEqual(result.sha256, storage.sha256_payload(final_bytes))
                self.assertFalse((handle.directory / ".pending.json").exists())

    def test_abandon_has_exact_canonical_projection_and_conflict_rules(self) -> None:
        pending = pending_record(mode="review-only")
        handle = storage.create_pending(self.paths, pending)
        first = storage.abandon_run(
            self.paths, handle.run_id, "client-interrupted",
            completed_at="2026-08-30T10:05:00Z", recorder_elapsed_ms=7,
        )
        review = storage.load_review(self.paths, handle.run_id)
        self.assertEqual(review["protocol"], {
            "mode": "review-only", "execution": "unknown", "reviewer_count": 0,
            "fresh_reviewer": False, "read_only_enforced": False,
            "conditional_trigger": None, "degraded_reasons": [],
        })
        self.assertEqual(review["result"], {
            "completion": "abandoned", "verdict": None, "block_reason": None,
            "completion_reason": "client-interrupted", "review_passes": 0,
            "repair_passes": 0, "findings": [],
        })
        self.assertEqual(set(review["freshness"].values()), {None})
        self.assertEqual(review["metrics"], {
            "elapsed_ms": 300000, "recorder_elapsed_ms": 7, "reviewer_count": 0,
            "review_passes": 0, "repair_passes": 0, "token_usage": None,
        })
        again = storage.abandon_run(self.paths, handle.run_id, "client-interrupted", completed_at="2026-08-30T10:05:00Z", recorder_elapsed_ms=7)
        self.assertEqual(first.sha256, again.sha256)
        with self.assertRaisesRegex(EvidenceError, "conflicting retry"):
            storage.abandon_run(self.paths, handle.run_id, "different-reason", completed_at="2026-08-30T10:05:00Z", recorder_elapsed_ms=7)
        for invalid in ("", "UPPER", "has space", "x" * 101):
            with self.subTest(invalid=invalid):
                other = pending_record()
                storage.create_pending(self.paths, other)
                with self.assertRaises(EvidenceError):
                    storage.abandon_run(self.paths, str(other["run_id"]), invalid, completed_at="2026-08-30T10:05:00Z", recorder_elapsed_ms=1)

    def test_scans_exclude_corrupt_records_and_classify_pending_without_deletion(self) -> None:
        active = pending_record(started_at="2026-08-30T09:30:00Z")
        interrupted = pending_record(started_at="2026-08-28T09:00:00Z")
        stale = pending_record(started_at="2026-08-20T09:00:00Z")
        for record in (active, interrupted, stale):
            storage.create_pending(self.paths, record)
        corrupt = self.paths.runs / "2026/08/00000000-0000-4000-8000-000000000000"
        corrupt.mkdir(parents=True)
        (corrupt / "review.json").write_bytes(b"{broken")
        scan = storage.scan_runs(self.paths, now="2026-08-30T10:00:00Z")
        self.assertEqual(
            sorted(item.age_class for item in scan.pending),
            ["active", "interrupted", "stale"],
        )
        self.assertEqual(len(scan.corrupt), 1)
        self.assertTrue(corrupt.exists())

    def test_directory_publication_never_replaces_existing_destination(self) -> None:
        for existing in (b"", b"broken", b"preserve-me"):
            with self.subTest(existing=existing):
                source = self.root / f"source-{len(existing)}"
                destination = self.root / f"destination-{len(existing)}"
                source.mkdir()
                (source / ".pending.json").write_bytes(b"source")
                destination.mkdir()
                (destination / "marker").write_bytes(existing)
                before = sorted((path.name, path.read_bytes()) for path in destination.iterdir())
                with self.assertRaises(EvidenceError):
                    storage.publish_directory_no_replace(source, destination)
                after = sorted((path.name, path.read_bytes()) for path in destination.iterdir())
                self.assertEqual(before, after)
                self.assertTrue(source.exists())

    def test_start_publication_races_preserve_every_destination_byte(self) -> None:
        original_publish = storage.publish_directory_no_replace
        cases = ("empty", "corrupt", "nonempty", "conflicting")
        for case in cases:
            with self.subTest(case=case):
                paths = storage.EvidencePaths.from_home(self.root / f"start-race-{case}")
                pending = pending_record()
                captured: dict[str, object] = {}

                def race(source: Path, destination: Path) -> None:
                    destination.mkdir(mode=0o700)
                    if case == "corrupt":
                        (destination / ".pending.json").write_bytes(b"{broken")
                    elif case == "nonempty":
                        (destination / "marker").write_bytes(b"winner")
                    elif case == "conflicting":
                        winner = copy.deepcopy(pending)
                        winner["start_locator_binding"] = "6" * 64
                        (destination / ".pending.json").write_bytes(canonical_json_bytes(winner))
                    for entry in destination.iterdir():
                        if os.name == "posix":
                            entry.chmod(0o600)
                    captured["destination"] = destination
                    captured["before"] = sorted(
                        (entry.name, entry.read_bytes()) for entry in destination.iterdir()
                    )
                    original_publish(source, destination)

                with mock.patch.object(storage, "publish_directory_no_replace", side_effect=race):
                    with self.assertRaises(EvidenceError):
                        storage.create_pending(paths, pending)
                destination = captured["destination"]
                assert isinstance(destination, Path)
                self.assertEqual(
                    sorted((entry.name, entry.read_bytes()) for entry in destination.iterdir()),
                    captured["before"],
                )

    def test_start_race_cleans_staging_only_for_identical_destination(self) -> None:
        paths = storage.EvidencePaths.from_home(self.root / "start-race-identical")
        pending = pending_record()
        original_publish = storage.publish_directory_no_replace

        def race(source: Path, destination: Path) -> None:
            destination.mkdir(mode=0o700)
            file = destination / ".pending.json"
            file.write_bytes(canonical_json_bytes(pending))
            if os.name == "posix":
                file.chmod(0o600)
            original_publish(source, destination)

        with mock.patch.object(storage, "publish_directory_no_replace", side_effect=race):
            handle = storage.create_pending(paths, pending)
        self.assertEqual(
            (handle.directory / ".pending.json").read_bytes(), canonical_json_bytes(pending)
        )
        self.assertFalse((paths.runs / f".staging-{pending['run_id']}").exists())

    def test_injected_linux_binding_uses_renameat2_noreplace(self) -> None:
        calls: list[tuple[object, ...]] = []

        class Function:
            argtypes = None
            restype = None

            def __call__(self, *args: object) -> int:
                calls.append(args)
                return 0

        library = type("Library", (), {"renameat2": Function()})()
        with mock.patch.object(storage.sys, "platform", "linux"), mock.patch.object(
            storage.ctypes, "CDLL", return_value=library
        ):
            storage.publish_directory_no_replace(Path("source"), Path("destination"))
        self.assertEqual(calls, [(-100, b"source", -100, b"destination", 1)])

    def test_injected_windows_binding_uses_movefileexw_zero_flags(self) -> None:
        calls: list[tuple[object, ...]] = []

        class Function:
            argtypes = None
            restype = None

            def __call__(self, *args: object) -> int:
                calls.append(args)
                return 1

        kernel = type("Kernel", (), {"MoveFileExW": Function()})()
        with mock.patch.object(storage.sys, "platform", "win32"), mock.patch.object(
            storage.ctypes, "WinDLL", return_value=kernel, create=True
        ):
            storage.publish_directory_no_replace(Path("source"), Path("destination"))
        self.assertEqual(calls, [("source", "destination", 0)])

    def test_injected_windows_collision_uses_thread_local_last_error(self) -> None:
        class Function:
            argtypes = None
            restype = None

            def __call__(self, *_args: object) -> int:
                return 0

        kernel = type("Kernel", (), {"MoveFileExW": Function()})()
        with mock.patch.object(storage.sys, "platform", "win32"), mock.patch.object(
            storage.ctypes, "WinDLL", return_value=kernel, create=True
        ), mock.patch.object(storage.ctypes, "get_last_error", return_value=183, create=True):
            with self.assertRaisesRegex(EvidenceError, "already exists"):
                storage.publish_directory_no_replace(Path("source"), Path("destination"))

    def test_reader_consumers_use_shared_bounded_reader(self) -> None:
        pending = pending_record()
        handle = storage.create_pending(self.paths, pending)
        review = completed_review(pending)
        storage.finish_review(self.paths, handle.run_id, review)
        with mock.patch("pre_sdd_review_evidence.storage.read_bounded_json", wraps=storage.read_bounded_json) as reader:
            self.assertEqual(storage.load_review(self.paths, handle.run_id)["run_id"], handle.run_id)
            storage.scan_runs(self.paths)
            storage.doctor(self.paths)
        self.assertGreaterEqual(reader.call_count, 3)


if __name__ == "__main__":
    unittest.main()
