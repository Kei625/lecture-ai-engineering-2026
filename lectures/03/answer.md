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

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
