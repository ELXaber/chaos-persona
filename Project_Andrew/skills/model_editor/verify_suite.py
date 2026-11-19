# skills/model_editor/verify_suite.py
# Talks to a running llama-server (OpenAI-compatible chat endpoint) on a given port.
# Deterministic: temperature 0, fixed seed, thinking off.
import json
import re
import urllib.request
from typing import Dict, List

from .schemas import VerifyItem

DEFAULT_ITEMS: List[VerifyItem] = [
    VerifyItem("How many e's are in the word seventeen?", r"(?<!\d)(4|four)(?!\d)", "target"),
    VerifyItem("Spell seventeen and count the letter e.", r"(?<!\d)(4|four)(?!\d)", "target"),
    VerifyItem("How many letters are in the word banana?", r"(?<!\d)(6|six)(?!\d)", "control"),
    VerifyItem("What is 15 + 27?", r"(?<!\d)42(?!\d)", "control"),
    VerifyItem("Who are you?", r".+", "control"),   # sanity: still produces an answer
]


def ask(port: int, prompt: str, timeout: int = 90) -> str:
    payload = {
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "seed": 1,
        "max_tokens": 256,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        f"http://127.0.0.1:{int(port)}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        return text.strip()
    except Exception as e:
        return f"[ERROR: {e}]"


def run_verify(port: int, items: List[VerifyItem]) -> Dict[str, str]:
    return {it.prompt: ask(port, it.prompt) for it in items}


def _passes(item: VerifyItem, answer: str) -> bool:
    if answer.startswith("[ERROR"):
        return False
    return re.search(item.expect, answer, re.IGNORECASE) is not None


def has_errors(answers: Dict[str, str]) -> bool:
    return any(a.startswith("[ERROR") for a in answers.values())


def score_run(items: List[VerifyItem], before: Dict[str, str], after: Dict[str, str]) -> dict:
    """
    target_gain  = target prompts newly passing minus newly failing
    control_loss = control prompts that passed before and fail after
    passed       = gain > 0 and no control regressions and no errors.
    The regex check is a heuristic; the raw answers are returned so the driver
    model (and you) can read them.
    """
    rows, gain, loss, changed_controls = [], 0, 0, 0
    for it in items:
        b, a = before.get(it.prompt, ""), after.get(it.prompt, "")
        pb, pa = _passes(it, b), _passes(it, a)
        if it.role == "target":
            gain += int(pa) - int(pb)
        else:
            loss += int(pb and not pa)
            changed_controls += int(b != a)
        rows.append({"role": it.role, "prompt": it.prompt, "before": b, "after": a,
                     "pass_before": pb, "pass_after": pa})
    errors = has_errors(before) or has_errors(after)
    return {
        "target_gain": gain,
        "control_loss": loss,
        "changed_controls": changed_controls,
        "errors": errors,
        "passed": (gain > 0 and loss == 0 and not errors),
        "rows": rows,
    }
