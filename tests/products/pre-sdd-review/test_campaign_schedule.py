from __future__ import annotations

import unittest
from collections import defaultdict


def waves(order: list[str], files: dict[str, set[str]]) -> list[list[str]]:
    preds: dict[str, set[str]] = defaultdict(set)
    for i, a in enumerate(order):
        for b in order[i + 1 :]:
            if files[a] & files[b]:
                preds[b].add(a)
    remaining = set(order)
    out: list[list[str]] = []
    while remaining:
        wave = [t for t in order if t in remaining and not (preds[t] & remaining)]
        if not wave:
            raise AssertionError(f"stuck {remaining}")
        out.append(wave)
        remaining -= set(wave)
    return out


def dirty_after(
    repaired: str,
    order: list[str],
    files: dict[str, set[str]],
    designs: dict[str, str],
    delta_paths: set[str],
    delta_design: str | None,
) -> set[str]:
    dirty: set[str] = set()
    i = order.index(repaired)
    for later in order[i + 1 :]:
        read = set(files[later]) | {designs[later], later} | set(order[: order.index(later)])
        if delta_paths & read or (delta_design and designs[later] == delta_design):
            dirty.add(later)
    return dirty


def host_k_waves(
    assigned: list[tuple[str, int]], k: int
) -> list[list[tuple[str, int]]]:
    if k < 1:
        raise ValueError("k")
    return [assigned[i : i + k] for i in range(0, len(assigned), k)]


def assign_discovery(plans: list[str], k: int) -> list[tuple[str, int]]:
    if k < 1:
        raise ValueError("k")
    assigned: list[tuple[str, int]] = []
    used: set[int] = set()
    slot = 0
    for plan in plans:
        if len(used) == k:
            used.clear()
        while slot in used:
            slot += 1
        assigned.append((plan, slot))
        used.add(slot)
        slot += 1
    agents = [agent for _, agent in assigned]
    if len(agents) != len(set(agents)):
        raise AssertionError("reused agent across plans")
    return assigned


class CampaignScheduleTests(unittest.TestCase):
    order = ["A", "B", "C", "D"]
    files = {
        "A": {"ui.ts", "spec.md"},
        "B": {"api.java", "spec.md"},
        "C": {"ui.ts"},
        "D": {"other.ts"},
    }
    designs = {"A": "spec.md", "B": "spec.md", "C": "c.md", "D": "d.md"}

    def test_waves_serialize_on_shared_files(self) -> None:
        self.assertEqual(waves(self.order, self.files), [["A", "D"], ["B", "C"]])

    def test_repairs_are_serial_in_order(self) -> None:
        seen: list[str] = []
        for plan in self.order:
            self.assertNotIn(plan, seen)
            seen.append(plan)
        self.assertEqual(seen, self.order)

    def test_shared_design_dirties_later_plan(self) -> None:
        self.assertEqual(
            dirty_after("A", self.order, self.files, self.designs, set(), "spec.md"),
            {"B"},
        )

    def test_file_delta_dirties_consumer(self) -> None:
        self.assertEqual(
            dirty_after("A", self.order, self.files, self.designs, {"ui.ts"}, None),
            {"C"},
        )

    def test_preceding_plan_path_dirties_later(self) -> None:
        self.assertEqual(
            dirty_after("A", self.order, self.files, self.designs, {"A"}, None),
            {"B", "C", "D"},
        )

    def test_zero_findings_skip_closure_unless_dirty(self) -> None:
        dirty = dirty_after("A", self.order, self.files, self.designs, {"ui.ts"}, None)
        skip = {p for p in self.order if p not in dirty and p != "A"}
        self.assertIn("B", skip)
        self.assertIn("D", skip)
        self.assertNotIn("C", skip)

    def test_jobserver_k2_never_reuses_agent(self) -> None:
        assigned = assign_discovery(self.order, 2)
        self.assertEqual(len({agent for _, agent in assigned}), 4)
        self.assertLessEqual(max(agent for _, agent in assigned), 3)

    def test_k1_is_serial_and_legal(self) -> None:
        assigned = assign_discovery(self.order, 1)
        self.assertEqual([p for p, _ in assigned], self.order)
        self.assertEqual(len({agent for _, agent in assigned}), 4)

    def test_host_k_wave_width_uses_fresh_agents(self) -> None:
        assigned_k2 = assign_discovery(self.order, 2)
        waves_k2 = host_k_waves(assigned_k2, 2)
        self.assertEqual([len(wave) for wave in waves_k2], [2, 2])
        self.assertEqual(
            [[plan for plan, _ in wave] for wave in waves_k2],
            [["A", "B"], ["C", "D"]],
        )
        seen_k2: set[int] = set()
        for wave in waves_k2:
            wave_agents = [agent for _, agent in wave]
            self.assertEqual(len(wave_agents), len(set(wave_agents)))
            for agent in wave_agents:
                self.assertNotIn(agent, seen_k2)
                seen_k2.add(agent)
        self.assertEqual(len(seen_k2), 4)

        assigned_k1 = assign_discovery(self.order, 1)
        waves_k1 = host_k_waves(assigned_k1, 1)
        self.assertEqual([len(wave) for wave in waves_k1], [1, 1, 1, 1])
        self.assertEqual(
            [[plan for plan, _ in wave] for wave in waves_k1],
            [["A"], ["B"], ["C"], ["D"]],
        )
        seen_k1: set[int] = set()
        for wave in waves_k1:
            wave_agents = [agent for _, agent in wave]
            self.assertEqual(len(wave_agents), 1)
            for agent in wave_agents:
                self.assertNotIn(agent, seen_k1)
                seen_k1.add(agent)
        self.assertEqual(len(seen_k1), 4)
