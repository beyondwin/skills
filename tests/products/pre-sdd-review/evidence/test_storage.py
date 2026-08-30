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
        corrupt.mkdir(mode=0o700, parents=True)
        if os.name == "posix":
            corrupt.chmod(0o700)
        (corrupt / "review.json").write_bytes(b"{broken")
        if os.name == "posix":
            (corrupt / "review.json").chmod(0o600)
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

    def test_start_collision_preserves_matching_pending_destination_with_extra_entry(self) -> None:
        paths = storage.EvidencePaths.from_home(self.root / "start-race-identical-extra")
        pending = pending_record()
        original_publish = storage.publish_directory_no_replace
        captured: dict[str, object] = {}

        def race(source: Path, destination: Path) -> None:
            destination.mkdir(mode=0o700)
            pending_path = destination / ".pending.json"
            extra_path = destination / "extra"
            pending_path.write_bytes(canonical_json_bytes(pending))
            extra_path.write_bytes(b"preserve-extra")
            if os.name == "posix":
                pending_path.chmod(0o600)
                extra_path.chmod(0o600)
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
        self.assertTrue((paths.runs / f".staging-{pending['run_id']}").exists())

    def test_recovery_preserves_matching_pending_destination_with_extra_entry(self) -> None:
        paths = storage.EvidencePaths.from_home(self.root / "recovery-identical-extra")
        pending = pending_record()
        with self.assertRaises(RuntimeError):
            storage.create_pending(
                paths, pending,
                interruption_hook=lambda point, _path: (
                    (_ for _ in ()).throw(RuntimeError("stop"))
                    if point == "pending-fsynced" else None
                ),
            )
        staging = paths.runs / f".staging-{pending['run_id']}"
        destination = paths.run_directory(str(pending["run_id"]), str(pending["started_at"]))
        destination.parent.mkdir(parents=True, exist_ok=True)
        if os.name == "posix":
            destination.parent.parent.chmod(0o700)
            destination.parent.chmod(0o700)
        destination.mkdir(mode=0o700)
        pending_path = destination / ".pending.json"
        extra_path = destination / "extra"
        pending_path.write_bytes(canonical_json_bytes(pending))
        extra_path.write_bytes(b"preserve-extra")
        if os.name == "posix":
            pending_path.chmod(0o600)
            extra_path.chmod(0o600)
        before = sorted(
            (entry.name, entry.read_bytes()) for entry in destination.iterdir()
        )

        unresolved = storage.recover_staging(paths)

        self.assertEqual(unresolved, (pending["run_id"],))
        self.assertTrue(staging.exists())
        self.assertEqual(
            sorted((entry.name, entry.read_bytes()) for entry in destination.iterdir()),
            before,
        )

    def test_start_collision_never_follows_symlinked_destination(self) -> None:
        paths = storage.EvidencePaths.from_home(self.root / "start-symlink-race")
        pending = pending_record()
        outside = self.root / "outside-start"
        outside.mkdir(mode=0o700)
        external = outside / ".pending.json"
        external.write_bytes(canonical_json_bytes(pending))
        if os.name == "posix":
            external.chmod(0o600)
        original_publish = storage.publish_directory_no_replace

        def race(source: Path, destination: Path) -> None:
            destination.symlink_to(outside, target_is_directory=True)
            original_publish(source, destination)

        with mock.patch.object(storage, "publish_directory_no_replace", side_effect=race):
            with self.assertRaisesRegex(EvidenceError, "unsafe"):
                storage.create_pending(paths, pending)
        destination = paths.run_directory(str(pending["run_id"]), str(pending["started_at"]))
        self.assertTrue(destination.is_symlink())
        self.assertEqual(external.read_bytes(), canonical_json_bytes(pending))
        self.assertTrue((paths.runs / f".staging-{pending['run_id']}").exists())

    def test_recovery_never_follows_symlinked_destination(self) -> None:
        paths = storage.EvidencePaths.from_home(self.root / "recovery-symlink-race")
        pending = pending_record()
        with self.assertRaises(RuntimeError):
            storage.create_pending(
                paths, pending,
                interruption_hook=lambda point, _path: (
                    (_ for _ in ()).throw(RuntimeError("stop"))
                    if point == "pending-fsynced" else None
                ),
            )
        outside = self.root / "outside-recovery"
        outside.mkdir(mode=0o700)
        external = outside / ".pending.json"
        external.write_bytes(canonical_json_bytes(pending))
        if os.name == "posix":
            external.chmod(0o600)
        destination = paths.run_directory(str(pending["run_id"]), str(pending["started_at"]))
        destination.parent.mkdir(parents=True, exist_ok=True)
        if os.name == "posix":
            destination.parent.parent.chmod(0o700)
            destination.parent.chmod(0o700)
        destination.symlink_to(outside, target_is_directory=True)

        unresolved = storage.recover_staging(paths)

        self.assertEqual(unresolved, (pending["run_id"],))
        self.assertTrue(destination.is_symlink())
        self.assertEqual(external.read_bytes(), canonical_json_bytes(pending))
        self.assertTrue((paths.runs / f".staging-{pending['run_id']}").exists())

    def test_terminal_reconciliation_never_follows_symlinked_review(self) -> None:
        pending = pending_record()
        handle = storage.create_pending(self.paths, pending)
        review = completed_review(pending)
        outside = self.root / "outside-review.json"
        outside.write_bytes(canonical_json_bytes(review))
        if os.name == "posix":
            outside.chmod(0o600)
        final = handle.directory / "review.json"
        final.symlink_to(outside)

        with self.assertRaises(EvidenceError) as caught:
            storage.finish_review(self.paths, handle.run_id, review)
        self.assertEqual(caught.exception.code, "unsafe-evidence-path")

        self.assertTrue(final.is_symlink())
        self.assertEqual(outside.read_bytes(), canonical_json_bytes(review))
        self.assertTrue((handle.directory / ".pending.json").exists())

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

    def test_pending_review_scan_and_doctor_read_exactly_limit_plus_one(self) -> None:
        pending_only = pending_record()
        pending_handle = storage.create_pending(self.paths, pending_only)
        completed_pending = pending_record()
        completed_handle = storage.create_pending(self.paths, completed_pending)
        storage.finish_review(
            self.paths, completed_handle.run_id, completed_review(completed_pending)
        )
        original_open = Path.open
        reads: list[tuple[str, int]] = []

        class StreamProxy:
            def __init__(self, stream: object, name: str) -> None:
                self.stream = stream
                self.name = name

            def __enter__(self) -> "StreamProxy":
                self.stream.__enter__()
                return self

            def __exit__(self, *args: object) -> object:
                return self.stream.__exit__(*args)

            def read(self, size: int = -1) -> bytes:
                if size != storage.REVIEW_HARD_LIMIT + 1:
                    raise AssertionError(f"unbounded or wrong read size: {size}")
                reads.append((self.name, size))
                return self.stream.read(size)

            def __getattr__(self, name: str) -> object:
                return getattr(self.stream, name)

        def spy_open(path: Path, *args: object, **kwargs: object) -> StreamProxy:
            return StreamProxy(original_open(path, *args, **kwargs), path.name)

        with mock.patch.object(Path, "open", spy_open), mock.patch.object(
            Path, "read_bytes", side_effect=AssertionError("Path.read_bytes forbidden")
        ), mock.patch.object(
            Path, "read_text", side_effect=AssertionError("Path.read_text forbidden")
        ):
            storage.load_pending(self.paths, pending_handle.run_id)
            storage.load_review(self.paths, completed_handle.run_id)
            storage.scan_runs(self.paths)
            storage.doctor(self.paths)

        self.assertIn((".pending.json", storage.REVIEW_HARD_LIMIT + 1), reads)
        self.assertIn(("review.json", storage.REVIEW_HARD_LIMIT + 1), reads)
        self.assertTrue(all(size == storage.REVIEW_HARD_LIMIT + 1 for _, size in reads))

    def test_recovery_promotion_races_preserve_empty_corrupt_and_nonempty_destinations(self) -> None:
        original_publish = storage.publish_directory_no_replace
        for case in ("empty", "corrupt", "nonempty"):
            with self.subTest(case=case):
                paths = storage.EvidencePaths.from_home(self.root / f"recover-race-{case}")
                pending = pending_record()
                with self.assertRaises(RuntimeError):
                    storage.create_pending(
                        paths, pending,
                        interruption_hook=lambda point, _path: (
                            (_ for _ in ()).throw(RuntimeError("stop"))
                            if point == "pending-fsynced" else None
                        ),
                    )
                captured: dict[str, object] = {}

                def race(source: Path, destination: Path) -> None:
                    destination.mkdir(mode=0o700)
                    if case == "corrupt":
                        file = destination / ".pending.json"
                        file.write_bytes(b"{broken")
                        if os.name == "posix":
                            file.chmod(0o600)
                    elif case == "nonempty":
                        file = destination / "winner"
                        file.write_bytes(b"preserve")
                        if os.name == "posix":
                            file.chmod(0o600)
                    captured["destination"] = destination
                    captured["before"] = sorted(
                        (item.name, item.read_bytes()) for item in destination.iterdir()
                    )
                    original_publish(source, destination)

                with mock.patch.object(storage, "publish_directory_no_replace", side_effect=race):
                    unresolved = storage.recover_staging(paths)
                destination = captured["destination"]
                assert isinstance(destination, Path)
                self.assertEqual(unresolved, (pending["run_id"],))
                self.assertEqual(
                    sorted((item.name, item.read_bytes()) for item in destination.iterdir()),
                    captured["before"],
                )
                self.assertTrue((paths.runs / f".staging-{pending['run_id']}").exists())

    def test_doctor_reports_safety_staleness_and_compatibility_without_repair(self) -> None:
        if os.name == "posix":
            unsafe_home = self.root / "doctor-unsafe-home"
            unsafe_home.mkdir(mode=0o755)
            unsafe_home.chmod(0o755)
            home_mode = stat.S_IMODE(unsafe_home.stat().st_mode)
            home_codes = {
                item["code"]
                for item in storage.doctor(storage.EvidencePaths.from_home(unsafe_home))
            }
            self.assertIn("unsafe-evidence-home", home_codes)
            self.assertEqual(stat.S_IMODE(unsafe_home.stat().st_mode), home_mode)

            unsafe_runs_home = self.root / "doctor-unsafe-runs"
            unsafe_runs_home.mkdir(mode=0o700)
            unsafe_runs = unsafe_runs_home / "runs"
            unsafe_runs.mkdir(mode=0o755)
            unsafe_runs.chmod(0o755)
            runs_mode = stat.S_IMODE(unsafe_runs.stat().st_mode)
            runs_codes = {
                item["code"]
                for item in storage.doctor(storage.EvidencePaths.from_home(unsafe_runs_home))
            }
            self.assertIn("unsafe-runs-root", runs_codes)
            self.assertEqual(stat.S_IMODE(unsafe_runs.stat().st_mode), runs_mode)

        unsafe_entry_paths = storage.EvidencePaths.from_home(self.root / "doctor-run-link")
        storage._ensure_roots(unsafe_entry_paths)
        month = unsafe_entry_paths.runs / "2026/08"
        month.mkdir(parents=True)
        if os.name == "posix":
            month.parent.chmod(0o700)
            month.chmod(0o700)
        outside = self.root / "doctor-outside-run"
        outside.mkdir(mode=0o700)
        run_id = "00000000-0000-4000-8000-000000000000"
        (month / run_id).symlink_to(outside, target_is_directory=True)
        link_codes = {item["code"] for item in storage.doctor(unsafe_entry_paths)}
        self.assertIn("unsafe-run-entry", link_codes)
        self.assertTrue((month / run_id).is_symlink())

        stale_paths = storage.EvidencePaths.from_home(self.root / "doctor-stale")
        stale = pending_record(started_at="2000-01-01T00:00:00Z")
        stale_handle = storage.create_pending(stale_paths, stale)
        stale_bytes = (stale_handle.directory / ".pending.json").read_bytes()
        stale_codes = {item["code"] for item in storage.doctor(stale_paths)}
        self.assertIn("stale-pending", stale_codes)
        self.assertEqual((stale_handle.directory / ".pending.json").read_bytes(), stale_bytes)

        for label, mutation, expected_code in (
            ("schema", lambda review: review.__setitem__("schema_version", 2), "unsupported-schema-version"),
            ("cli", lambda review: review["skill"].__setitem__("cli_version", "2.0.0"), "incompatible-cli"),
        ):
            with self.subTest(label=label):
                paths = storage.EvidencePaths.from_home(self.root / f"doctor-{label}")
                pending = pending_record()
                handle = storage.create_pending(paths, pending)
                review = completed_review(pending)
                mutation(review)
                final = handle.directory / "review.json"
                final.write_bytes(canonical_json_bytes(review))
                if os.name == "posix":
                    final.chmod(0o600)
                before = final.read_bytes()
                codes = {item["code"] for item in storage.doctor(paths)}
                self.assertIn(expected_code, codes)
                self.assertEqual(final.read_bytes(), before)

        for label, mutation, expected_code in (
            ("pending-schema", lambda pending: pending.__setitem__("schema_version", 2), "unsupported-schema-version"),
            ("pending-cli", lambda pending: pending["skill"].__setitem__("cli_version", "2.0.0"), "incompatible-cli"),
        ):
            with self.subTest(label=label):
                paths = storage.EvidencePaths.from_home(self.root / f"doctor-{label}")
                pending = pending_record()
                handle = storage.create_pending(paths, pending)
                mutation(pending)
                pending_path = handle.directory / ".pending.json"
                pending_path.write_bytes(canonical_json_bytes(pending))
                if os.name == "posix":
                    pending_path.chmod(0o600)
                before = pending_path.read_bytes()
                codes = {item["code"] for item in storage.doctor(paths)}
                self.assertIn(expected_code, codes)
                self.assertEqual(pending_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
