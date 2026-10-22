"""第1回 宿題（基礎）: 同じ質問をモデル・temperature を変えて3回ずつ実行し、結果を記録する。

使い方:
    uv run python -m app.hw01_basic                          # 全条件を実行
    uv run python -m app.hw01_basic --conditions lite-default lite-t0
    uv run python -m app.hw01_basic --questions course       # 講座固有の質問だけ

出力:
    lectures/01/logs/<日時>.jsonl  … 1回の呼び出しにつき1行の生データ
    lectures/01/logs/<日時>.md     … 回答を並べて読むための一覧
APIキーはログに書き出さない。
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import errors, types

from app.config import api_error_message, get_api_key

QUESTIONS = {
    "general": "LoRAとは何ですか？",
    "course": "AIE2026の講座の宿題にある「3レベル」とは何ですか？",
}

RUNS = 3

# (ラベル, モデル, temperature)。temperature が None のときはモデルの既定値を使う
CONDITIONS = [
    ("lite-default", "gemini-3.5-flash-lite", None),
    ("lite-t0", "gemini-3.5-flash-lite", 0.0),
    ("lite-t2", "gemini-3.5-flash-lite", 2.0),
    ("flash-default", "gemini-3.8-flash", None),
]

# 毎分の上限に引っかからないための待ち時間（秒）
WAIT_SECONDS = {
    "gemini-3.5-flash-lite": 5,
    "gemini-3.8-flash": 15,
}

# 503（混雑）・429（レート制限）のときの再試行
RETRY_CODES = {429, 503}
MAX_RETRIES = 2
RETRY_WAIT_SECONDS = 30

LOG_DIR = Path("lectures/01/logs")


def call_once(client: genai.Client, model: str, temperature: float | None, question: str) -> dict:
    """1回だけ呼び出し、結果を辞書で返す。失敗してもエラー内容を記録して返す。"""
    config = None
    if temperature is not None:
        config = types.GenerateContentConfig(temperature=temperature)

    for attempt in range(MAX_RETRIES + 1):
        start = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=model,
                contents=question,
                config=config,
            )
            elapsed = time.perf_counter() - start

            usage = response.usage_metadata
            finish_reason = None
            if response.candidates:
                finish_reason = str(response.candidates[0].finish_reason)

            return {
                "ok": True,
                "elapsed_sec": round(elapsed, 2),
                "prompt_tokens": getattr(usage, "prompt_token_count", None),
                "output_tokens": getattr(usage, "candidates_token_count", None),
                "thoughts_tokens": getattr(usage, "thoughts_token_count", None),
                "finish_reason": finish_reason,
                "text": response.text or "",
                "error": None,
            }
        except errors.APIError as e:
            elapsed = time.perf_counter() - start
            if e.code in RETRY_CODES and attempt < MAX_RETRIES:
                print(f"    {e.code} が返ったため {RETRY_WAIT_SECONDS} 秒待って再試行します")
                time.sleep(RETRY_WAIT_SECONDS)
                continue
            return {
                "ok": False,
                "elapsed_sec": round(elapsed, 2),
                "prompt_tokens": None,
                "output_tokens": None,
                "thoughts_tokens": None,
                "finish_reason": None,
                "text": "",
                "error": {"code": e.code, "message": api_error_message(e.code, e.message)},
            }

    raise RuntimeError("到達しないはずの分岐です")


def write_markdown(path: Path, records: list[dict]) -> None:
    """回答を「質問 → 条件 → 回数」の順に並べた Markdown を書き出す。"""
    lines = ["# 第1回 宿題（基礎）実行ログ", ""]

    for q_key, question in QUESTIONS.items():
        q_records = [r for r in records if r["question_key"] == q_key]
        if not q_records:
            continue
        lines += [f"## 質問: {question}", ""]

        for label, model, temperature in CONDITIONS:
            c_records = [r for r in q_records if r["condition"] == label]
            if not c_records:
                continue
            temp_str = "既定値" if temperature is None else str(temperature)
            lines += [f"### {label}（{model} / temperature={temp_str}）", ""]

            for r in c_records:
                lines.append(
                    f"#### {r['run']}回目 — 入力 {r['prompt_tokens']} / 出力 {r['output_tokens']} "
                    f"/ 思考 {r['thoughts_tokens']} トークン / {r['elapsed_sec']} 秒"
                )
                lines.append("")
                if r["ok"]:
                    lines += ["````text", r["text"].strip(), "````", ""]
                else:
                    lines += [f"**エラー {r['error']['code']}**: {r['error']['message']}", ""]

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="第1回 宿題（基礎）の実験を実行する")
    parser.add_argument(
        "--conditions",
        nargs="+",
        choices=[c[0] for c in CONDITIONS],
        default=[c[0] for c in CONDITIONS],
        help="実行する条件のラベル",
    )
    parser.add_argument(
        "--questions",
        nargs="+",
        choices=list(QUESTIONS.keys()),
        default=list(QUESTIONS.keys()),
        help="実行する質問のキー",
    )
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    jsonl_path = LOG_DIR / f"{stamp}.jsonl"
    md_path = LOG_DIR / f"{stamp}.md"

    client = genai.Client(api_key=get_api_key())
    records: list[dict] = []

    selected = [c for c in CONDITIONS if c[0] in args.conditions]
    total = len(selected) * len(args.questions) * RUNS
    count = 0

    with jsonl_path.open("w", encoding="utf-8") as f:
        for label, model, temperature in selected:
            for q_key in args.questions:
                question = QUESTIONS[q_key]
                for run in range(1, RUNS + 1):
                    count += 1
                    print(f"[{count}/{total}] {label} / {q_key} / {run}回目")

                    result = call_once(client, model, temperature, question)
                    record = {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "condition": label,
                        "model": model,
                        "temperature": temperature,
                        "question_key": q_key,
                        "question": question,
                        "run": run,
                        **result,
                    }
                    records.append(record)
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()

                    if result["ok"]:
                        print(f"    出力 {result['output_tokens']} トークン / {result['elapsed_sec']} 秒")
                    else:
                        print(f"    エラー {result['error']['code']}")

                    if count < total:
                        time.sleep(WAIT_SECONDS.get(model, 10))

    write_markdown(md_path, records)
    print(f"\n生データ: {jsonl_path}")
    print(f"一覧    : {md_path}")


if __name__ == "__main__":
    main()