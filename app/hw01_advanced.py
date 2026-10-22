"""第1回 宿題（発展）: 応答時間とトークン数を、モデル・質問ごとに計測する。

実行例:
    uv run python -m app.hw01_advanced
    uv run python -m app.hw01_advanced --models gemini-3.5-flash-lite

API キーは Codespaces secret の GEMINI_API_KEY から読み込む（コードには書かない）。
結果は lectures/01/logs/advanced_<日時>.csv に保存する。
"""

import argparse
import csv
import statistics
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import errors

# モデルごとの試行回数とリクエスト間隔（無料枠のレート制限に合わせる）
#   flash-lite: 毎分15 → 4秒以上空ける / 1日500
#   3.8-flash : 毎分5  → 12秒以上空ける / 1日10〜20前後 → 3質問×3回=9回に抑える
MODELS = {
    "gemini-3.5-flash-lite": {"runs": 5, "interval": 5.0},
    "gemini-3.8-flash": {"runs": 3, "interval": 15.0},
}

QUESTIONS = {
    "short": "LoRA とは何ですか？一文で答えてください。",
    "general": "LoRA とは何ですか？",
    "course": "AIE2026 の講座の宿題にある「3レベル」とは何ですか？",
}

MAX_RETRIES = 3
RETRY_STATUS = {429, 503}
LOG_DIR = Path("lectures/01/logs")


def call_once(client, model, prompt):
    """1回呼び出し、計測値を dict で返す。429/503 は指数バックオフで再試行する。"""
    retries = 0
    errors_seen = []
    total_start = time.perf_counter()
    while True:
        start = time.perf_counter()
        try:
            resp = client.models.generate_content(model=model, contents=prompt)
            latency = time.perf_counter() - start
            usage = resp.usage_metadata
            out_tokens = usage.candidates_token_count or 0
            return {
                "status": "ok",
                "latency_s": round(latency, 3),
                "total_with_retry_s": round(time.perf_counter() - total_start, 3),
                "input_tokens": usage.prompt_token_count or 0,
                "output_tokens": out_tokens,
                "thinking_tokens": usage.thoughts_token_count or 0,
                "total_tokens": usage.total_token_count or 0,
                "output_tok_per_s": round(out_tokens / latency, 2) if latency > 0 else 0,
                "retries": retries,
                "errors": ";".join(errors_seen),
            }
        except errors.APIError as e:
            errors_seen.append(str(e.code))
            if e.code in RETRY_STATUS and retries < MAX_RETRIES:
                wait = 10 * (2 ** retries)
                print(f"    {e.code} を受信。{wait} 秒待って再試行します")
                time.sleep(wait)
                retries += 1
                continue
            return {
                "status": f"error_{e.code}",
                "latency_s": round(time.perf_counter() - start, 3),
                "total_with_retry_s": round(time.perf_counter() - total_start, 3),
                "input_tokens": 0,
                "output_tokens": 0,
                "thinking_tokens": 0,
                "total_tokens": 0,
                "output_tok_per_s": 0,
                "retries": retries,
                "errors": ";".join(errors_seen),
            }


def summarize(rows):
    """モデル×質問ごとに平均・最小・最大を表示する（成功した試行のみ）。"""
    groups = defaultdict(list)
    for r in rows:
        if r["status"] == "ok":
            groups[(r["model"], r["question"])].append(r)

    print("\n| モデル | 質問 | n | 応答時間 平均[s] | 最小 | 最大 | 出力tok 平均 | 思考tok 平均 | 出力tok/s 平均 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for (model, q), rs in sorted(groups.items()):
        lat = [r["latency_s"] for r in rs]
        print(
            f"| {model} | {q} | {len(rs)} "
            f"| {statistics.mean(lat):.2f} | {min(lat):.2f} | {max(lat):.2f} "
            f"| {statistics.mean(r['output_tokens'] for r in rs):.0f} "
            f"| {statistics.mean(r['thinking_tokens'] for r in rs):.0f} "
            f"| {statistics.mean(r['output_tok_per_s'] for r in rs):.1f} |"
        )

    failed = [r for r in rows if r["status"] != "ok" or r["retries"] > 0]
    print(f"\n再試行またはエラーが発生した試行: {len(failed)} 件")
    for r in failed:
        print(f"  {r['model']} / {r['question']} / run{r['run']}: {r['status']} (errors={r['errors']})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=list(MODELS), help="計測するモデル")
    args = parser.parse_args()

    client = genai.Client()  # GEMINI_API_KEY 環境変数を自動で読む
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = LOG_DIR / f"advanced_{datetime.now():%Y%m%d_%H%M%S}.csv"

    fields = [
        "timestamp", "model", "question", "run", "status", "latency_s",
        "total_with_retry_s", "input_tokens", "output_tokens", "thinking_tokens",
        "total_tokens", "output_tok_per_s", "retries", "errors",
    ]
    rows = []
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for model in args.models:
            cfg = MODELS[model]
            for q_name, prompt in QUESTIONS.items():
                for run in range(1, cfg["runs"] + 1):
                    print(f"[{model}] {q_name} run{run}")
                    result = call_once(client, model, prompt)
                    row = {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "model": model,
                        "question": q_name,
                        "run": run,
                        **result,
                    }
                    writer.writerow(row)
                    f.flush()
                    rows.append(row)
                    time.sleep(cfg["interval"])

    print(f"\n保存しました: {out_path}")
    summarize(rows)


if __name__ == "__main__":
    main()