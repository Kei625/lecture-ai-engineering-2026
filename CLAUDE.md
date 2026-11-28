# CLAUDE.md

AIエンジニアリング実践講座（AIE2026）の演習・宿題リポジトリ（自分の fork）。
講座を通して、Pydantic AI + Gemini API の「学習支援エージェント」を回ごとに育てていく。
全体像・各ファイルの役割は README.md の「構成」を参照。

## リポジトリの前提

- `origin` = Kei625/lecture-ai-engineering-2026（自分の fork）、`upstream` = matsuolab/lecture-ai-engineering-2026（配布元）
- 回ごとに `lecNN` ブランチを切り、`lectures/NN/answer.md` に記入して **fork 内で** `lecNN → main` の PR を出す
- 各回の指示は `lectures/NN/problem.md` が正。作業前に必ず該当回の problem.md を読む
- 宿題は「基礎・実装・発展」のいずれか1つで完了

## コマンド

```bash
uv sync --frozen                                  # 依存関係（uv.lock 固定。--frozen を外さない）
uv run pytest -q                                  # テスト（APIキー不要・LLMを呼ばない）
uv run python -m app.ask "質問"                    # 素のLLM（第1回）
uv run python -m app.agent --trace "質問"          # エージェント（--graph / --tree / --full-context / --mcp）
uv run python -m app.agent --list-tools           # モデルに見えるツール一覧（APIキー不要）
uv run python -m app.mcp_agent --trace "質問"      # MCPクライアント（第6回、app/mcp_servers.json を読む）
uv run python -m app.retrieval "検索語"            # 検索のみ（第5回）
uv run python -m app.judge --model test           # 採点の動作確認（APIを呼ばない）
```

## 守ること（重要）

- **APIキーを扱わない。** `GEMINI_API_KEY` は環境変数のみ。コード・コミット・出力にキーを書かない。`.env*` を読まない・作らない
- **依存パッケージの版を変えない。** `pyproject.toml` / `uv.lock` を編集しない、`uv add` や `uv lock --upgrade` をしない。一時的に必要なものは `uv run --with <pkg>` で済ませる
- **API呼び出しは最小限に。** Gemini 無料枠にはレート制限がある。エージェント系コマンドは1回の質問でLLMを複数回呼ぶため、検証はまず `pytest` や `--list-tools`、`--model test` で行い、実APIを叩くコマンドは実行前に確認を取る
- **同梱の検索DB `data/rag_data/index.sqlite3` を上書きしない。** 実験用DBは `AIE_RAG_DB="$PWD/.cache/rag/custom.sqlite3"` を設定して作る
- **配布元のファイル構成を崩さない。** upstream から毎回マージするため、課題で指示されていないファイルの改名・整形・大規模リファクタはしない（コンフリクトの原因になる）
- テストは「含む」で判定する設計（演習でツールを足しても壊れない）。既存テストを弱める・消す変更はしない

## answer.md の扱い

- 提出物は本人の学習記録。**実行結果・`[tool call]` の行・気づきを推測や創作で埋めない。** 実際に表示された出力だけを記入する
- 記入を頼まれた場合は、実行ログから事実を転記し、「気づき・疑問」は下書きとして提示して本人に確認を取る
- HTMLコメント（`<!-- -->`）の記入ルールに従う

## 進め方

- これは学習用リポジトリ。コードを書き換えるときは、**何をなぜ変えたか**を短く説明する（受講者はコードを理解したうえで採用する決まり）
- problem.md が「読むだけ」としているファイルは、指示がない限り編集しない
- 変更後は `uv run pytest -q` が通ることを確認する
- コミット・push・PR作成は、明示的に頼まれたときだけ行う。コミットメッセージは日本語

## コードの慣習

- Python 3.12。モデル名・パス・定数は `app/config.py` に集約し、APIキーとモデル名は環境変数から読む（既定モデル `gemini-3.5-flash-lite`、`AIE_MODEL` で切替）
- docstring・コメント・ユーザー向けメッセージは日本語
- APIエラーの表示は `config.api_error_message()` を使う
- テストは `pydantic_ai.models.test.TestModel` と `monkeypatch` で外部呼び出しを差し替え、APIキーなしで動かす
