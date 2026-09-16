# SDDx attempt status tells the truth — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository's own product `$sddx` / `/sddx` is the matching external-implementer path when the orchestrator must stay native.

**Goal:** `run.json` and `run_worker.py status` expose the session ID while the worker is still running, record a wrapper SIGTERM as `interrupted`, and give the controller `pid_alive` plus a bounded tools index without dumping the log.

**Architecture:** Keep `schema_version` 2 and the `run.json` field set. Stamp `session_id` as soon as the stream reports it. Map the runner's SIGTERM to the existing `interrupted` path. Add `pid_alive` and `tools` only on the read-only status payload. Do not grow `SKILL.md` with new rule chapters.

**Tech Stack:** Python 3.11+, existing `unittest` product tests, no provider CLIs, no new dependencies.

**Spec:** [docs/history/specs/2026-09-16-sddx-attempt-status-design.md](../specs/2026-09-16-sddx-attempt-status-design.md)

## File map

- `skills/sddx/scripts/run_worker.py` — wait loop, SIGTERM handler, `pid_alive`, tools index, status payload
- `tests/products/sddx/test_run_worker.py` — session-while-running and wrapper SIGTERM
- `tests/products/sddx/test_worker_status.py` — `pid_alive` and `tools`
- `tests/products/sddx/test_contract.py` — dispatch/status contract strings
- `skills/sddx/references/dispatch.md` — Watch/Evidence facts
- `skills/sddx/SKILL.md` — one Implementer sentence
- `docs/maintainers/products/sddx/contract.md` — status and session timing
- `docs/maintainers/products/sddx/testing.md` — status keys
- `skills/sddx/CHANGELOG.md` — Unreleased `2.0.0`

Do not edit Superpowers, `worker-prompt.md`, `schema_version`, or catalog files.

## Global Constraints

- 지원 OS는 macOS뿐이다. Windows 분기를 추가하지 않는다.
- `schema_version`은 2로 둔다. 과거 schema 2 `run.json`은 그대로 읽는다.
- `run.json` 필드 집합은 바꾸지 않는다. `session_id`의 기록 시점만 바꾼다.
- `status`는 읽기 전용이다. 죽은 pid를 보고 `run.json`을 고치지 않는다.
- 로그 본문, 도구 결과 `content`/`stdout`/`stderr`, thinking을 status 기본 응답에 넣지 않는다.
- DONE·402·역할 준수를 러너가 판정하지 않는다.
- `SKILL.md`에 규칙 장을 더하지 않는다. Implementer status 문장만 고친다.
- Superpowers 파일을 고치지 않는다. 오케스트레이터 세션에서 제품 코드를 구현하지 않는 것은 실행 단계의 일이지 이 계획의 파일 목록이 아니다.
- 라이브 Cursor/Grok 호출은 이 계획의 완료 조건이 아니다.
- 필수 검증은 `python3 scripts/verify.py --skill sddx`이다.
- 커밋 메시지 본문은 영어, `fix(sddx):` / `docs(sddx):` 관례를 따른다.
- 테스트는 합성 CLI만 쓰고 PATH의 실제 `cursor-agent`/`grok`을 호출하지 않는다.

---

### Task 1: Record session_id while the worker is still running

**Files:**
- Modify: `skills/sddx/scripts/run_worker.py` (`WAIT_SLICE_SECONDS`, `remember_session_id`, wait loop around the existing `process.wait`)
- Modify: `tests/products/sddx/test_run_worker.py` (`SessionIdRecordingTests`)
- Modify: `skills/sddx/references/dispatch.md` (session_id timing sentence)
- Modify: `docs/maintainers/products/sddx/contract.md` (같은 문장)

**Interfaces:**
- Consumes: existing `read_session_id(path: Path) -> str | None`, `write_metadata`, `RunOptions.timeout`
- Produces: `WAIT_SLICE_SECONDS = 1.0`; `remember_session_id(metadata: dict, path: Path) -> bool` — if `metadata["session_id"]` is already a non-empty str, return False without reading. Otherwise call `read_session_id`; on a non-empty str, set `metadata["session_id"]` and return True. After `state: running` is written, call it and write metadata when it returns True. Then wait in slices of `min(WAIT_SLICE_SECONDS, remaining)` when a timeout is set, or `WAIT_SLICE_SECONDS` when `--timeout 0`. On each `TimeoutExpired`, call it again. Do not use `wait(timeout=0)`. Do not overwrite a recorded id on exit/timeout/interrupt.

- [ ] **Step 1: Write the failing tests**

Add these methods to `SessionIdRecordingTests` in `tests/products/sddx/test_run_worker.py`. Reuse `behaviour_session_then_sleep`, `pinned_resolver`, `ready_popen`, and `TIMED_OUT_SESSION_ID` already in that file.

```python
    def test_session_id_is_recorded_while_state_is_still_running(self) -> None:
        # Break: session_id stays null until the process exits or times out.
        module = self.load()
        ready = self.base / "session-reported"
        self.write_grok(behaviour_session_then_sleep(ready))
        observed: list[dict] = []
        real = module.write_metadata

        def spy(path, value):
            observed.append(dict(value))
            real(path, value)

        with self.pinned_resolver(module):
            with self.ready_popen(module, ready):
                with mock.patch.object(module, "write_metadata", spy):
                    self.invoke(module, self.options(module, timeout=0.5))
        running_with_id = [
            entry for entry in observed
            if entry.get("state") == "running"
            and entry.get("session_id") == TIMED_OUT_SESSION_ID
        ]
        self.assertTrue(running_with_id)
        self.assertEqual(self.metadata()["session_id"], TIMED_OUT_SESSION_ID)

    def test_a_later_stream_id_does_not_replace_the_recorded_session(self) -> None:
        # Break: exit/timeout overwrites the id that was already recorded.
        module = self.load()
        self.write_grok(BEHAVIOUR_SESSION_INIT)
        observed: list[dict] = []
        real = module.write_metadata

        def spy(path, value):
            observed.append(dict(value))
            real(path, value)

        with mock.patch.object(module, "write_metadata", spy):
            with mock.patch.object(
                module, "read_session_id",
                side_effect=["synthetic-session-first", "synthetic-session-later"],
            ):
                self.invoke(module, self.options(module))
        ids = [entry.get("session_id") for entry in observed if entry.get("session_id")]
        self.assertEqual(ids[0], "synthetic-session-first")
        self.assertTrue(all(item == "synthetic-session-first" for item in ids))
```

- [ ] **Step 2: Run the new tests and confirm they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.products.sddx.test_run_worker.SessionIdRecordingTests.test_session_id_is_recorded_while_state_is_still_running \
  tests.products.sddx.test_run_worker.SessionIdRecordingTests.test_a_later_stream_id_does_not_replace_the_recorded_session \
  -v
```

Expected: FAIL. The running snapshots have `session_id is None`, or the second test sees `synthetic-session-later`.

- [ ] **Step 3: Implement session capture in the wait loop**

In `skills/sddx/scripts/run_worker.py`, next to `SESSION_SCAN_LINES`, add:

```python
WAIT_SLICE_SECONDS = 1.0
```

Add:

```python
def remember_session_id(metadata: dict[str, Any], path: Path) -> bool:
    """Copy the first stream session id into the record. Never replace one."""
    if isinstance(metadata.get("session_id"), str) and metadata["session_id"]:
        return False
    found = read_session_id(path)
    if not found:
        return False
    metadata["session_id"] = found
    return True
```

The file does not import `time` today. Add `import time`.

Replace the single `process.wait(...)` block with: write `running`, call `remember_session_id` and `write_metadata` if it returned True, then loop. If `options.timeout` is 0, `process.wait(timeout=WAIT_SLICE_SECONDS)` until the child exits. If `options.timeout` is positive, set `deadline = time.monotonic() + options.timeout` and wait `min(WAIT_SLICE_SECONDS, remaining)`. On `TimeoutExpired`, remember the session id; if the deadline has passed, take the existing timed-out path (still calling `remember_session_id` rather than assigning `read_session_id` over a stored value). On a real child exit, remember then write `exited`. The `interrupted()` helper must also call `remember_session_id` instead of blindly assigning.

Keep `test_zero_timeout_waits_for_a_slow_worker`: timeout 0 must still wait for `BEHAVIOUR_DELAYED`, never `wait(timeout=0)`.

- [ ] **Step 4: Run the session tests plus the existing timeout/session tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.products.sddx.test_run_worker.SessionIdRecordingTests \
  tests.products.sddx.test_run_worker.AttemptTimeoutTests \
  tests.products.sddx.test_run_worker.WorkerExecutionTests.test_controller_interrupt_is_recorded_without_killing_the_tree \
  -v
```

Expected: PASS.

- [ ] **Step 5: Update the two contract sentences**

In `skills/sddx/references/dispatch.md` and `docs/maintainers/products/sddx/contract.md`, replace the claim that `session_id` is only what the finished stream reported. Write that the runner copies the first reported id into `run.json` as soon as the stream has it, including while `state` is `running`, and never replaces it. `status` still mirrors the record; it does not invent an id from the log when the record is missing.

- [ ] **Step 6: Commit**

```bash
git add \
  skills/sddx/scripts/run_worker.py \
  tests/products/sddx/test_run_worker.py \
  skills/sddx/references/dispatch.md \
  docs/maintainers/products/sddx/contract.md
git commit -m "$(cat <<'EOF'
fix(sddx): stamp worker session_id while the attempt is still running

EOF
)"
```

---

### Task 2: Treat wrapper SIGTERM as interrupted

**Files:**
- Modify: `skills/sddx/scripts/run_worker.py` (SIGTERM handler around wait only)
- Modify: `tests/products/sddx/test_run_worker.py` (`WorkerExecutionTests` or `SessionIdRecordingTests`)
- Modify: `skills/sddx/references/dispatch.md` (interrupt paragraph)

**Interfaces:**
- Consumes: existing `interrupted()` path, exit 130, `error="the controller interrupted the attempt"`
- Produces: during wait, `signal.signal(signal.SIGTERM, handler)` where the handler raises `KeyboardInterrupt`; restore the previous handler in `finally`. Child SIGTERM remains `state: exited` with negative `exit_code`. Do not kill the process tree.

- [ ] **Step 1: Write the failing tests**

```python
    def test_wrapper_sigterm_is_recorded_as_interrupted(self) -> None:
        # Break: SIGTERM to the runner leaves state=running or treats it as
        # the child's signal death.
        import signal

        module = self.load()
        self.write_grok(BEHAVIOUR_SLEEP)
        handlers: list = []
        started: list[subprocess.Popen] = []

        def capture(sig, handler):
            if sig == signal.SIGTERM:
                handlers.append(handler)
                return signal.SIG_DFL
            return signal.signal(sig, handler)

        class SignallingPopen(subprocess.Popen):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                started.append(self)

            def wait(self, timeout=None):  # noqa: D102 - controller sent SIGTERM
                if not handlers:
                    raise AssertionError("SIGTERM handler was not installed before wait")
                handlers[-1](signal.SIGTERM, None)
                raise AssertionError("SIGTERM handler returned")

        with self.pinned_resolver(module):
            with mock.patch.object(module.signal, "signal", capture):
                with mock.patch.object(module.subprocess, "Popen", SignallingPopen):
                    code = self.invoke(module, self.options(module, timeout=5))
        self.assertEqual(len(started), 1)
        process = started[0]
        self.addCleanup(lambda: subprocess.Popen.wait(process))
        self.addCleanup(process.kill)
        self.assertEqual(code, 130)
        metadata = self.metadata()
        self.assertEqual(metadata["state"], "interrupted")
        self.assertEqual(metadata["error"], "the controller interrupted the attempt")
        self.assertIsNone(process.poll(), "runner must not kill the worker process tree")

    def test_child_sigterm_is_still_an_exit_not_an_interrupt(self) -> None:
        # Break: the wrapper SIGTERM handler also rewrites a child SIGTERM.
        import signal

        module = self.load()
        self.write_grok(BEHAVIOUR_SIGNAL)
        code = self.invoke(module, self.options(module))
        self.assertEqual(code, 128 + signal.SIGTERM)
        metadata = self.metadata()
        self.assertEqual(metadata["state"], "exited")
        self.assertEqual(metadata["exit_code"], -signal.SIGTERM)
```

The second test already exists as `test_signal_termination_keeps_the_negative_returncode`. Do not duplicate it; run that existing test after the handler lands. Add only `test_wrapper_sigterm_is_recorded_as_interrupted`. Mark it `@unittest.skipUnless(os.name != "nt", ...)`.

The file does not import `signal` today. Add `import signal` at module level so tests can patch `module.signal.signal`.

- [ ] **Step 2: Run the new test and confirm it fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.products.sddx.test_run_worker.WorkerExecutionTests.test_wrapper_sigterm_is_recorded_as_interrupted \
  -v
```

Expected: FAIL with `SIGTERM handler was not installed before wait` or `state != interrupted`.

- [ ] **Step 3: Install a wait-scoped SIGTERM handler**

In `run_worker.py`, after the child is started and `state: running` is written, install:

```python
def _raise_keyboard_interrupt(signum, frame):
    raise KeyboardInterrupt
```

`previous = signal.signal(signal.SIGTERM, _raise_keyboard_interrupt)` immediately before the wait loop, restore `signal.signal(signal.SIGTERM, previous)` in `finally` after wait/timeout/interrupt handling finishes. Do not install it before `Popen` (a launch failure must not change signal disposition). Do not send signals to the child from this handler.

- [ ] **Step 4: Run interrupt, signal, and timeout tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.products.sddx.test_run_worker.WorkerExecutionTests.test_wrapper_sigterm_is_recorded_as_interrupted \
  tests.products.sddx.test_run_worker.WorkerExecutionTests.test_controller_interrupt_is_recorded_without_killing_the_tree \
  tests.products.sddx.test_run_worker.WorkerExecutionTests.test_signal_termination_keeps_the_negative_returncode \
  tests.products.sddx.test_run_worker.AttemptTimeoutTests \
  tests.products.sddx.test_run_worker.SessionIdRecordingTests \
  -v
```

Expected: PASS.

- [ ] **Step 5: Document the two SIGTERM routes**

In `skills/sddx/references/dispatch.md`, next to the existing interrupt paragraph, state: SIGTERM to the runner uses the same `interrupted` / 130 record as Ctrl-C and does not kill the tree; SIGTERM to the worker remains `exited` (or `timed_out` when the runner sent it) with the negative returncode. SIGKILL still cannot write a terminal state.

- [ ] **Step 6: Commit**

```bash
git add \
  skills/sddx/scripts/run_worker.py \
  tests/products/sddx/test_run_worker.py \
  skills/sddx/references/dispatch.md
git commit -m "$(cat <<'EOF'
fix(sddx): record a runner SIGTERM as interrupted

EOF
)"
```

---

### Task 3: Report pid_alive from status

**Files:**
- Modify: `skills/sddx/scripts/run_worker.py` (`pid_alive`, `read_status`)
- Modify: `tests/products/sddx/test_worker_status.py` (`DEFAULT_KEYS`, new tests)
- Modify: `skills/sddx/references/dispatch.md` (Watch default payload)

**Interfaces:**
- Consumes: `metadata["pid"]`
- Produces: `pid_alive(pid: int | None) -> bool | None`. `None` pid → `None`. `os.kill(pid, 0)` success or `PermissionError` → `True`. `ProcessLookupError` → `False`. `read_status` adds `pid_alive` beside `session_id`. It never writes `run.json`.

- [ ] **Step 1: Write the failing tests**

Update `DEFAULT_KEYS` in `tests/products/sddx/test_worker_status.py` to include `"pid_alive"`. Then add:

```python
    def test_pid_alive_is_true_for_this_process(self) -> None:
        # Break: status omits pid_alive or reports the current pid as dead.
        module = self.load()
        self.write_metadata(pid=os.getpid())
        payload = module.read_status(self.attempt)
        self.assertIs(payload["pid_alive"], True)

    def test_pid_alive_is_false_when_the_process_is_gone(self) -> None:
        # Break: a missing pid is reported as alive or omitted.
        module = self.load()
        self.write_metadata(pid=2**22)
        payload = module.read_status(self.attempt)
        self.assertIs(payload["pid_alive"], False)

    def test_pid_alive_is_null_when_the_record_has_no_pid(self) -> None:
        # Break: a launch-style record is reported as a boolean.
        module = self.load()
        self.write_metadata(pid=None)
        payload = module.read_status(self.attempt)
        self.assertIsNone(payload["pid_alive"])

    def test_status_does_not_rewrite_a_stale_running_record(self) -> None:
        # Break: status "heals" run.json into interrupted.
        module = self.load()
        before = self.write_metadata(state="running", pid=2**22, session_id=None)
        snapshot = (self.attempt / "run.json").read_bytes()
        payload = module.read_status(self.attempt)
        self.assertIs(payload["pid_alive"], False)
        self.assertEqual((self.attempt / "run.json").read_bytes(), snapshot)
        self.assertEqual(payload["metadata"]["state"], "running")
```

`test_default_status_never_carries_the_log_body` already asserts `set(payload) == DEFAULT_KEYS`. Updating the set is required. Keep `assertLess(len(rendered), 4096)` and the ban on `"z" * 64`.

- [ ] **Step 2: Run the pid_alive tests and confirm they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.products.sddx.test_worker_status.DefaultStatusTests \
  -v
```

Expected: FAIL on missing `pid_alive` key.

- [ ] **Step 3: Implement pid_alive**

```python
def pid_alive(pid: int | None) -> bool | None:
    if not isinstance(pid, int) or isinstance(pid, bool):
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
```

In `read_status`, set `"pid_alive": pid_alive(metadata.get("pid") if metadata else None)`. Do not catch `OSError` broadly enough to hide a programming error.

- [ ] **Step 4: Run the full status file**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.sddx.test_worker_status -v
```

Expected: PASS.

- [ ] **Step 5: Document Watch**

In `skills/sddx/references/dispatch.md` Watch section, add `pid_alive` to the default status facts. State that `state: running` and `pid_alive: false` means the record is stale, and that status does not rewrite it.

- [ ] **Step 6: Commit**

```bash
git add \
  skills/sddx/scripts/run_worker.py \
  tests/products/sddx/test_worker_status.py \
  skills/sddx/references/dispatch.md
git commit -m "$(cat <<'EOF'
fix(sddx): report whether the recorded worker pid is still alive

EOF
)"
```

---

### Task 4: Bounded tools index on default status

**Files:**
- Modify: `skills/sddx/scripts/run_worker.py` (`read_tools_index`, status payload, caps)
- Modify: `tests/products/sddx/test_worker_status.py`
- Modify: `tests/products/sddx/test_contract.py` (`test_dispatch_runs_the_worker_through_the_runner`)
- Modify: `skills/sddx/references/dispatch.md`
- Modify: `skills/sddx/SKILL.md` (one Implementer sentence only)
- Modify: `docs/maintainers/products/sddx/contract.md`
- Modify: `docs/maintainers/products/sddx/testing.md`
- Modify: `skills/sddx/CHANGELOG.md`

**Interfaces:**
- Consumes: `worker.jsonl` lines
- Produces: `read_tools_index(path: Path) -> dict` with keys `reads` (list[str]), `searches` (list[dict] with `pattern` and `path`), `shells` (list[dict] with `exit_code` and `command`), `truncated` (bool). Caps: 64 reads, 32 searches, 32 shells, 200 command chars. Default status includes `"tools": read_tools_index(attempt / STDOUT_NAME)` even without `--stream`. Missing file → empty lists, `truncated: false`. No new CLI flag.

- [ ] **Step 1: Write the failing tests**

Add `"tools"` to `DEFAULT_KEYS`. Then:

```python
    def test_tools_index_copies_cursor_read_grep_and_shell_fields(self) -> None:
        # Break: status has no tools index, or looks inside result bodies.
        module = self.load()
        self.write_metadata()
        secret = "SYNTHETIC_PLAN_BODY_SHOULD_NOT_LEAK"
        events = [
            {"type": "thinking", "subtype": "delta", "text": secret},
            {
                "type": "tool_call",
                "subtype": "started",
                "tool_call": {
                    "readToolCall": {"args": {"path": "/work/brief.md"}},
                },
            },
            {
                "type": "tool_call",
                "subtype": "completed",
                "tool_call": {
                    "readToolCall": {
                        "args": {"path": "/work/brief.md"},
                        "result": {"success": {"content": secret}},
                    },
                },
            },
            {
                "type": "tool_call",
                "subtype": "started",
                "tool_call": {
                    "grepToolCall": {
                        "args": {"pattern": "def gate\\(", "path": "/work/src.py"},
                    },
                },
            },
            {
                "type": "tool_call",
                "subtype": "completed",
                "tool_call": {
                    "shellToolCall": {
                        "args": {"command": "python3 -m unittest"},
                        "result": {"failure": {"exitCode": 1, "stderr": secret}},
                    },
                },
            },
        ]
        self.write_stdout(("\n".join(json.dumps(item) for item in events) + "\n").encode("utf-8"))
        payload = module.read_status(self.attempt)
        self.assertEqual(payload["tools"]["reads"], ["/work/brief.md"])
        self.assertEqual(
            payload["tools"]["searches"],
            [{"pattern": "def gate\\(", "path": "/work/src.py"}],
        )
        self.assertEqual(
            payload["tools"]["shells"],
            [{"exit_code": 1, "command": "python3 -m unittest"}],
        )
        self.assertIs(payload["tools"]["truncated"], False)
        rendered = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn(secret, rendered)

    def test_unknown_tool_shapes_are_an_empty_index_not_an_error(self) -> None:
        # Break: a non-Cursor event or a broken line fails the query.
        module = self.load()
        self.write_metadata()
        self.write_stdout(
            b"not json\n"
            + json.dumps({"type": "tool_call", "subtype": "started", "tool_call": {"fn": {"args": {"path": "/x"}}}}).encode()
            + b"\n"
        )
        payload = module.read_status(self.attempt)
        self.assertEqual(payload["tools"], {
            "reads": [],
            "searches": [],
            "shells": [],
            "truncated": False,
        })

    def test_tools_index_truncates_instead_of_growing_without_bound(self) -> None:
        # Break: every path is returned, or truncated stays false.
        module = self.load()
        self.write_metadata()
        lines = []
        for index in range(70):
            lines.append(json.dumps({
                "type": "tool_call",
                "subtype": "started",
                "tool_call": {
                    "readToolCall": {"args": {"path": f"/work/file-{index}.py"}},
                },
            }))
        self.write_stdout(("\n".join(lines) + "\n").encode("utf-8"))
        payload = module.read_status(self.attempt)
        self.assertEqual(len(payload["tools"]["reads"]), 64)
        self.assertEqual(payload["tools"]["reads"][0], "/work/file-0.py")
        self.assertEqual(payload["tools"]["reads"][-1], "/work/file-63.py")
        self.assertIs(payload["tools"]["truncated"], True)

    def test_glob_search_uses_globPattern_and_targetDirectory(self) -> None:
        module = self.load()
        self.write_metadata()
        self.write_stdout((json.dumps({
            "type": "tool_call",
            "subtype": "started",
            "tool_call": {
                "globToolCall": {
                    "args": {
                        "globPattern": "tests/*.py",
                        "targetDirectory": "/work",
                    },
                },
            },
        }) + "\n").encode("utf-8"))
        payload = module.read_status(self.attempt)
        self.assertEqual(
            payload["tools"]["searches"],
            [{"pattern": "tests/*.py", "path": "/work"}],
        )
```

Also add a shell success case with `result.success.exitCode` 0 in `test_tools_index_copies_cursor_read_grep_and_shell_fields` or a one-liner sibling if that test gets too large — keep one completed failure (exit 1) and add:

```python
            {
                "type": "tool_call",
                "subtype": "completed",
                "tool_call": {
                    "shellToolCall": {
                        "args": {"command": "python3 -m unittest discover -s tests"},
                        "result": {"success": {"exitCode": 0, "stdout": secret}},
                    },
                },
            },
```

Then expect two shells: exit 1 then exit 0.

- [ ] **Step 2: Run the new tests and confirm they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.sddx.test_worker_status -v
```

Expected: FAIL on missing `tools`.

- [ ] **Step 3: Implement read_tools_index**

Constants: `TOOLS_READ_CAP = 64`, `TOOLS_SEARCH_CAP = 32`, `TOOLS_SHELL_CAP = 32`, `TOOLS_COMMAND_CHARS = 200`.

Parse only objects with `type == "tool_call"`. For each key in `tool_call` that is a dict and whose name ends with `ToolCall`:

- started + `"read" in name.lower()` → unique `args.path` strings
- started + any of `grep`/`glob`/`search` in the lowercased name → `{pattern, path}` from `pattern` or `globPattern`, and `path` or `targetDirectory` or `target_directory`
- completed + `"shell" in name.lower()` → `{exit_code, command}` where `exit_code` is the first int (not bool) found at `result.exitCode`, `result.success.exitCode`, or `result.failure.exitCode`; `command` is `args.command` cut to 200 chars

Skip other keys (`hookAdditionalContexts`, `fn`, non-dicts). Skip non-JSON lines. Do not copy `content`, `stdout`, `stderr`, or thinking text. If a list is already at cap, set `truncated True` and do not append.

Wire it into `read_status` as `"tools": read_tools_index(attempt / STDOUT_NAME)`.

Update the module docstring at the top of `run_worker.py`. It currently says the runner parses only the session id and that `status` interprets nothing. Change that to: the runner also copies a bounded tools index from `tool_call` JSON objects on status; it still does not judge DONE, 402, or role compliance, and it still does not put log bodies in the default status payload.

Keep `test_an_unreported_session_is_null_rather_than_absent` and `test_status_without_metadata_reports_no_session`: `session_id` still comes only from the record. The tools index may still read `worker.jsonl` on a metadata-less attempt — that is file projection, not a session id. If metadata is missing, `session_id` stays `None`.

- [ ] **Step 4: Run status tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.sddx.test_worker_status -v
```

Expected: PASS. `test_default_status_never_carries_the_log_body` still forbids the 1 MiB `z` run and stays under 4096 bytes because that fixture has no tool_call events.

- [ ] **Step 5: Align docs and the dispatch contract test**

Replace the Watch sentence that says the default answer is only metadata, sizes, and `report.md`. Default answer is metadata, sizes, `report.md` existence, `pid_alive`, and `tools`. It still never includes a log body. Role compliance is still the controller's.

In `skills/sddx/SKILL.md` Implementer section, replace:

```
Read a running or finished attempt only through `run_worker.py status`, which answers within a bounded window; never dump a whole worker log into this session.
```

with:

```
Read a running or finished attempt only through `run_worker.py status`, which answers with metadata, `pid_alive`, a bounded tools index, and optional log windows; never dump a whole worker log into this session.
```

Do not add a new SKILL.md section.

In `docs/maintainers/products/sddx/contract.md`, update the status paragraph the same way, and keep the `run.json` field list unchanged.

In `docs/maintainers/products/sddx/testing.md`, in the `test_worker_status.py` sentence, mention `pid_alive` and the tools index, and that the default payload still has no log body.

In `tests/products/sddx/test_contract.py` `test_dispatch_runs_the_worker_through_the_runner`, add:

```python
        self.assertIn("pid_alive", text)
        self.assertIn("tools", text)
```

In `skills/sddx/CHANGELOG.md` Unreleased Added:

```
- `run.json.session_id` is copied from the worker stream as soon as it appears,
  including while `state` is `running`. A later stream id does not replace it.
- SIGTERM to the runner uses the existing `interrupted` record (exit 130) and
  does not kill the worker tree.
- `run_worker.py status` adds `pid_alive` and a bounded `tools` index (read
  paths, search patterns, shell exit codes and commands). It still does not
  include log bodies or judge role compliance.
```

- [ ] **Step 6: Run the product verification**

Run:

```bash
python3 scripts/verify.py --skill sddx
```

Expected: exit 0. Do not treat this as live Cursor/Grok evidence.

- [ ] **Step 7: Commit**

```bash
git add \
  skills/sddx/scripts/run_worker.py \
  tests/products/sddx/test_worker_status.py \
  tests/products/sddx/test_contract.py \
  skills/sddx/references/dispatch.md \
  skills/sddx/SKILL.md \
  docs/maintainers/products/sddx/contract.md \
  docs/maintainers/products/sddx/testing.md \
  skills/sddx/CHANGELOG.md
git commit -m "$(cat <<'EOF'
feat(sddx): expose a bounded tools index on worker status

EOF
)"
```

---

## Spec coverage

| Spec requirement | Task |
| --- | --- |
| session_id while `running`; first id wins | 1 |
| wait slices; `--timeout 0` is not `wait(timeout=0)` | 1 |
| `status` does not invent session_id without a record | 1 (existing status test kept in 4) |
| wrapper SIGTERM → `interrupted` / 130; tree left alone | 2 |
| child SIGTERM stays `exited` | 2 |
| `pid_alive` on status, not in `run.json`; no rewrite | 3 |
| tools index: reads / searches / shells / truncated; no bodies | 4 |
| unknown tool shape → empty lists | 4 |
| caps 64 / 32 / 32 / 200 | 4 |
| `schema_version` 2; no new status flag | 1–4 |
| SKILL.md one sentence; no new rule chapter | 4 |
| `python3 scripts/verify.py --skill sddx` | 4 |
| no live provider call | all |

## Self-review

- No TBD/placeholder steps. Each task has the test code to type.
- Names: `remember_session_id`, `WAIT_SLICE_SECONDS`, `pid_alive`, `read_tools_index` are used consistently.
- Task 2 reuses Task 1's wait loop; Task 3–4 only change `status`.
- `DEFAULT_KEYS` grows in Task 3 (`pid_alive`) and again in Task 4 (`tools`). Task 4 must not revert Task 3's key.
- `test_signal_termination_keeps_the_negative_returncode` is the child-SIGTERM lock; Task 2 must not replace it with `interrupted`.
