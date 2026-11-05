# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
    -  素のLLMでは根拠のない内容をもっともらしく回答していたが、エージェントでは文言は異なっていてもglossary.jsonと同じ内容が回答として問いして得られた。

- `--trace` で見えたツール呼び出し（ツール名と引数）：
- `search_glossary({'query': 'LoRA'})`
    - `search_glossary({'query': 'QLoRA'})`- `search_glossary({'query': 'LoRA'})`
    - `search_glossary({'query': 'QLoRA'})`
  - `search_glossary` の docstring に「query には調べたい用語を1つだけ入れる」とあるため、2つの用語を別々に検索していた。
  - 回答の説明文と「関係する回: 第2回」は、ツールの返り値（`definition` と `"lecture": 2`）をもとに作られていた。

- 1つの質問での LLM 呼び出し回数（`requests`）：
  - `requests=2`、`tool_calls=2`（`input_tokens=1196`、`output_tokens=195`）

- 追加したツールと、docstring に書いた説明：
  - [make_quiz]
  指定した回の用語から 1つを選び、
  確認問題と答えを返す。
  「第2回の確認問題を出して」のように、
  復習用の問題を求められたときに使う。
  返り値は {"question": 問題文, "answer": 答え, "lecture": 回} のJSON。
  出題するときは、利用者が求めない限り answer をすぐには見せないこと。
  引数: {"lecture": {"type": "integer"}}

## 宿題

- 取り組んだレベル：基礎

- やったこと：
  - `app/tools.py` の `search_glossary` の docstring を「query には調べたい用語を1つだけ入れる」から「query には調べたい用語をまとめて入れる（例: "LoRA QLoRA"）」に変更した。`INSTRUCTIONS` は変えていない。
  - 変更前後で、同じ質問を `--trace` 付きで実行して比べた。
    - 質問：「LoRAとQLoRAの違いは？」

- 結果：

  | 条件 | ツール呼び出し（引数） | requests | tool_calls | input_tokens | output_tokens | 回答 |
  |---|---|---|---|---|---|---|
  | 変更前（演習時、make_quiz 追加前） | `search_glossary('LoRA')`, `search_glossary('QLoRA')` | 2 | 2 | 1196 | 195 | 用語集の定義をほぼ言い換えた内容 |
  | 変更前（make_quiz 追加後） | `search_glossary('LoRA')`, `search_glossary('QLoRA')` | 2 | 2 | 1440 | 202 | 正しいが、「Parameter-Efficient Fine-Tuning」など返り値に無い英語表記が混ざった |
  | 変更後（1回目） | `search_glossary('LoRA QLoRA')` | 2 | 1 | 1135 | 219 | 正しいが、正式名称・「16ビット精度」など返り値に無い記述が混ざった |
  | 変更後（2回目） | `search_glossary('LoRA QLoRA')` | 2 | 1 | 1135 | 194 | 正式名称は出たが、「16ビット精度」は出なかった |

- 気づき・疑問：

  - 変更後（まとめて検索）したほうが入力トークンが少なくなった。
  - 演習時の 1196 トークンは make_quiz を追加する前の値で、ツールを1つ足すだけで入力が約 240 トークン増えた。ツールの説明文は毎回のリクエストでモデルに渡るためと考えられる。
  - ツールの返り値に無い表記や名称は、変更前・変更後のどちらでも回答に混ざった。docstring の変更とは関係のない、モデルの一般的な傾向であると言える。
  - output_tokens とコストは実行ごとに揺れ、1回だけの実行で判断すると誤った結論になりうる。
