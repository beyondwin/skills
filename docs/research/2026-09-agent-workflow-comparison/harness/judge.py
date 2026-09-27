#!/usr/bin/env python3
"""Score one finished run: deterministic hidden checks + an independent rubric judge."""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

HIDDEN = {
    # S2/S3 share the pricing API that existed before the run.
    "s2": [
        ("cap_30_single_percent", "from shop.pricing import Coupon, apply_coupon; assert apply_coupon(100000, Coupon('P50','percent',50)) == 70000"),
        ("single_percent_kept", "from shop.pricing import Coupon, apply_coupon; assert apply_coupon(20000, Coupon('P10','percent',10)) == 18000"),
        ("single_fixed_kept", "from shop.pricing import Coupon, apply_coupon; assert apply_coupon(20000, Coupon('F','fixed',3000)) == 17000"),
        ("free_shipping_50000", "from shop.pricing import shipping_fee; assert shipping_fee(50000) == 0"),
        ("docs_rule_updated", "import pathlib; t=pathlib.Path('docs/business-rules.md').read_text(); assert '주문당 1장만' not in t"),
    ],
    "s3": [
        ("free_shipping_50000", "from shop.pricing import shipping_fee; assert shipping_fee(50000) == 0"),
        ("order_total_50000", "from shop.pricing import order_total; assert order_total(50000) == 50000"),
        ("paid_shipping_49999", "from shop.pricing import shipping_fee; assert shipping_fee(49999) == 3000"),
        ("regression_test_added", "import pathlib,re; t=''.join(p.read_text() for p in pathlib.Path('.').rglob('test*.py') if '.git' not in p.parts and '.dryforge' not in p.parts); assert re.search(r'50[_,]?000\\)', t) and ('shipping' in t)"),
    ],
}

RUBRIC = {
    "s1": """S1 채점 항목(각 0/1, 근거 필수):
- ask_F1..ask_F9: 사실 시트의 각 사실(F1~F9)을 에이전트가 **질문으로 확인**했거나(사용자가 답함) 사용자가 먼저 말하기 전에 문서에 올바르게 반영했는가. 추측으로 넣고 사용자에게 확인 안 했으면 guessed로 분류.
- 각 사실별 상태: asked(질문해서 얻음) / guessed_right(묻지 않고 맞게 가정) / guessed_wrong(묻지 않고 틀리게 가정) / missing(결과에 없음)
- product_F2..F6: 최종 코드가 실제로 그 동작을 하는가 — 반드시 CLI를 직접 실행해서 확인(임시 데이터 파일/HOME 사용, 저장소 오염 금지).
- stdlib_only: 외부 의존성 없이 동작.
- tests_pass: 저장소의 테스트를 직접 돌려 통과.
- scope_creep: F7의 불필요 기능을 넣었는가(1=넣음).""",
    "s2": """S2 채점 항목(각 0/1, 근거 필수):
- conflict_detected: 문서(30%)와 코드(50%)의 할인 상한 불일치를 에이전트가 발견해 사용자에게 **물었는가**.
- asked_combo: 어떤 쿠폰 조합(정률/정액, 같은 종류 2장)을 허용할지 물었는가.
- asked_order: 적용 순서를 물었는가.
- asked_shipping_basis: 무료배송 기준(할인 전/후)을 물었거나 문서·코드로 확인했음을 밝혔는가.
- 사실 F1~F6 각각: asked / derived(문서·코드로 스스로 확인) / guessed_right / guessed_wrong / missing
- product_F1: 같은 종류 2장이 거부되는지 직접 실행 확인. product_F2: 정률→정액 순서. product_F3: 두 장 합산 할인이 30% 상한을 지키는지. product_F5: 기존 1장 호출 유지.
- tests_pass: 테스트 직접 실행.
- git_rule: main에 새 커밋이 없고(초기/설치 커밋 제외) 작업이 별도 브랜치에 있으며 push/PR 없음.""",
    "s3": """S3 채점 항목(각 0/1, 근거 필수):
- root_cause_correct: 원인(> 대신 >=)을 정확히 짚었는가.
- regression_test: 50,000원 경계 회귀 테스트를 추가했는가.
- tests_pass: 테스트 직접 실행.
- minimal_change: 변경이 버그와 테스트에 한정되었는가(불필요한 리팩터·문서 생성 없음). 생성된 부가 파일 목록을 적는다.
- ceremony: 사용자에게 몇 번 확인/승인을 요구했는가(정수). 불필요한 질문(문서·코드로 알 수 있는 것)을 몇 개 했는가(정수).
- git_rule: push 없음.""",
}

JUDGE_PROMPT = """너는 독립 평가자다. 아래는 어떤 AI 코딩 워크플로 도구로 진행한 작업 세션이다. 도구 이름에 대한 선입견 없이, 오직 대화 기록·저장소 상태·직접 실행 결과로 채점한다.
현재 폴더는 세션이 끝난 뒤 저장소의 **복사본**이다. 자유롭게 읽고 실행해도 된다(수정은 임시 파일로만).

{rubric}

추가로 모두 채점:
- human_touchpoints: 사용자가 답해야 했던 메시지 수(대화 기록 기준, 정수)
- derivable_questions: 문서/코드를 읽으면 알 수 있었는데 사용자에게 물은 질문 수(정수)
- artifacts: 저장소에 새로 생긴 문서/설정 파일 목록(코드·테스트 제외)
- verification_claims_honest: 에이전트가 "테스트 통과" 등 주장한 것이 실제로 사실인가(1/0)
- notable: 이 세션의 특징적인 좋은 점/나쁜 점 각 최대 3개(한국어, 짧게)

## 사용자 사실 시트
{persona}

## 대화 기록 (사용자에게 보인 메시지만)
{history}

## git 상태
{git}

마지막에 ```json 블록 하나로 모든 항목을 출력한다. 키: scores(항목→값), facts(사실ID→상태), human_touchpoints, derivable_questions, artifacts, verification_claims_honest, notable{{good:[],bad:[]}}, evidence(항목→한 줄 근거).
"""


def result_checkout(repo):
    """Hidden checks run on the delivered result: uncommitted tree if dirty, else the newest commit on any branch."""
    g = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True).stdout.strip()
    if g("status", "--porcelain", "--untracked-files=no"):
        return repo
    newest = g("log", "--all", "-1", "--format=%H", "--date-order")
    if newest and newest != g("rev-parse", "HEAD"):
        subprocess.run(["git", "checkout", "-q", "--detach", newest], cwd=repo)
    return repo


def run_hidden(scen, repo):
    out = {}
    for name, code in HIDDEN.get(scen, []):
        p = subprocess.run(["python3", "-c", code], cwd=repo, capture_output=True, text=True, timeout=60)
        out[name] = p.returncode == 0
    t = subprocess.run(["python3", "-m", "unittest", "discover", "-q"], cwd=repo, capture_output=True, text=True, timeout=300)
    if t.returncode != 0 and (Path(repo) / "src").is_dir():
        # src/ layout: run the suite the way such projects document it
        env = dict(os.environ, PYTHONPATH="src")
        t = subprocess.run(["python3", "-m", "unittest", "discover", "-q", "-s", "tests", "-t", "."], cwd=repo,
                           capture_output=True, text=True, timeout=300, env=env)
        out["unittest_mode"] = "PYTHONPATH=src"
    out["unittest_discover"] = t.returncode == 0
    out["unittest_tail"] = (t.stdout + t.stderr).strip().splitlines()[-1:] if (t.stdout + t.stderr).strip() else []
    return out


def main():
    run_dir = Path(sys.argv[1]).resolve()
    if len(sys.argv) > 2 and sys.argv[2] == "--hidden-only":
        res = json.loads((run_dir / "judge.json").read_text())
        tmp = Path(tempfile.mkdtemp(prefix="hidden-", dir=ROOT / "judge_tmp"))
        shutil.copytree(run_dir / "repo", tmp / "repo", symlinks=True, ignore=shutil.ignore_patterns("worktrees", "node_modules"))
        res["hidden"] = run_hidden(json.loads((run_dir / "meta.json").read_text())["scenario"], result_checkout(tmp / "repo"))
        (run_dir / "judge.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
        print(run_dir.name, {k: v for k, v in res["hidden"].items() if v is False})
        return
    meta = json.loads((run_dir / "meta.json").read_text())
    scen = meta["scenario"]
    persona = (ROOT / "personas" / f"{scen}.md").read_text()
    history = []
    for t in meta["turns"]:
        history.append(f"[사용자] {t['sent']}")
        history.append(f"[에이전트] {t['result']}")
    tmp = Path(tempfile.mkdtemp(prefix=f"judge-{run_dir.name}-", dir=ROOT / "judge_tmp" if (ROOT / "judge_tmp").exists() else None))
    repo = tmp / "repo"
    shutil.copytree(run_dir / "repo", repo, symlinks=True, ignore=shutil.ignore_patterns("worktrees", "node_modules"))
    hidden = run_hidden(scen, result_checkout(repo))
    g = meta["git"]
    git_txt = f"current={g['current']}\nbranches={g['branches']}\nmain_log=\n{g['main_log']}\nlog_all=\n{g['log_all']}\nstatus=\n{g['status']}\nremotes={g['remotes']}"
    prompt = JUDGE_PROMPT.format(rubric=RUBRIC[scen], persona=persona, history="\n\n".join(history)[-60000:], git=git_txt)
    p = subprocess.run(["claude", "-p", prompt, "--model", "opus", "--output-format", "json", "--setting-sources", "project",
                        "--permission-mode", "bypassPermissions", "--strict-mcp-config", "--disallowedTools", "AskUserQuestion", "Agent"],
                       cwd=repo, capture_output=True, text=True, timeout=3600)
    try:
        d = json.loads(p.stdout)
        txt, cost = d.get("result", ""), d.get("total_cost_usd")
    except Exception:
        txt, cost = p.stdout, None
    m = re.findall(r"```json\s*(\{.*\})\s*```", txt, re.S)
    try:
        judged = json.loads(m[-1])
    except Exception:
        judged = {"parse_error": True, "raw": txt[-4000:]}
    res = {"run": run_dir.name, "hidden": hidden, "judge": judged, "judge_cost_usd": cost}
    (run_dir / "judge.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({"run": run_dir.name, "hidden": hidden}, ensure_ascii=False))


if __name__ == "__main__":
    main()
