"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保ったまま続けて質問する（宿題・実装）
    uv run python -m app.ask --chat "最初の質問"

会話モードのコマンド:
    /history  これまでの履歴を表示する
    /reset    履歴を消して最初からやり直す
    /exit     終了する（/quit、Ctrl+D、Ctrl+C でも終了）

ツールは持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

EXIT_COMMANDS = {"/exit", "/quit"}
RESET_COMMAND = "/reset"
HISTORY_COMMAND = "/history"


def print_usage(usage) -> None:
    """トークン数を表示する。"""
    print(f"[入力トークン] {usage.prompt_token_count}")
    print(f"[出力トークン] {usage.candidates_token_count}")


def ask(question: str) -> str:
    """履歴を持たずに1回だけ質問する。"""
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    print_usage(response.usage_metadata)

    return response.text


def content_to_text(content: types.Content) -> str:
    """Content から表示用のテキストを取り出す。思考部分は除く。"""
    texts = []
    for part in content.parts or []:
        if getattr(part, "thought", False):
            continue
        if part.text:
            texts.append(part.text)
    return "".join(texts)


class ChatSession:
    """会話履歴を保持し、毎回すべての履歴を送って続けて質問できるようにする。"""

    def __init__(self, client, model: str = MODEL) -> None:
        self.client = client
        self.model = model
        self.history: list[types.Content] = []

    @property
    def turns(self) -> int:
        """これまでに成立した質問と回答の組の数。"""
        return len(self.history) // 2

    def send(self, message: str) -> str:
        """履歴に新しい質問を足して送り、回答を返す。

        API 呼び出しが例外で失敗した場合や回答が得られなかった場合は、
        履歴を変更しない（同じ質問を送り直せるようにするため）。
        """
        user_content = types.Content(role="user", parts=[types.Part(text=message)])
        contents = [*self.history, user_content]

        response = self.client.models.generate_content(model=self.model, contents=contents)

        if response.usage_metadata is not None:
            print_usage(response.usage_metadata)

        if not response.candidates or response.candidates[0].content is None:
            return "（回答が得られませんでした。この質問は履歴に残していません）"

        model_content = response.candidates[0].content
        self.history.append(user_content)
        self.history.append(model_content)

        return response.text or content_to_text(model_content)

    def reset(self) -> None:
        """履歴を消す。"""
        self.history.clear()

    def format_history(self) -> str:
        """履歴を表示用の文字列にする。"""
        if not self.history:
            return "（履歴はありません）"
        lines = []
        for i, content in enumerate(self.history, start=1):
            role = "あなた" if content.role == "user" else "モデル"
            text = content_to_text(content).replace("\n", " ")
            if len(text) > 60:
                text = text[:60] + "…"
            lines.append(f"{i:>2}. [{role}] {text}")
        return "\n".join(lines)


def run_chat(first_message: str | None) -> None:
    """会話モードの対話ループ。"""
    session = ChatSession(genai.Client(api_key=get_api_key()))
    print("会話モードです。/history で履歴、/reset でやり直し、/exit で終了します。\n")

    pending = first_message
    while True:
        if pending is not None:
            message = pending
            pending = None
            print(f"あなた> {message}")
        else:
            try:
                message = input("あなた> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n終了します。")
                return

        if not message:
            continue
        if message in EXIT_COMMANDS:
            print("終了します。")
            return
        if message == RESET_COMMAND:
            session.reset()
            print("履歴を消しました。\n")
            continue
        if message == HISTORY_COMMAND:
            print(session.format_history() + "\n")
            continue

        try:
            reply = session.send(message)
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            print("この質問は履歴に残していません。時間をおいて送り直せます。\n")
            continue

        print(f"[ターン] {session.turns}")
        print(f"\nモデル> {reply}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保ったまま続けて質問する",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")

    if args.chat:
        run_chat(args.question)
        return

    question = args.question if args.question is not None else DEFAULT_QUESTION
    print(f"[質問] {question}\n")
    try:
        print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()