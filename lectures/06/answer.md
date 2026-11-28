# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：
  - `[tool call]   aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要', 'topics': ['general']})`
  - `[tool call]   aws_aws___search_documentation({'search_phrase': 'Using versioning in S3 buckets', 'topics': ['general']})`
  
- 気づき・疑問：ツールやエージェントを変えなくても、mcpサーバーを使うことで簡単にツールを用意して検索や情報取得ができるようになることが分かった。一方、stepu4のAWSで検索を行なった場合の入力トークンがそれ以外の時と比較して非常に多くなっているのでツールを増やしすぎるのも良くないと分かった。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：app/mcp_server.pyのみを書き換えてget_lecture_summaryを公開し実際に呼び出されることを確認した。
- 結果：get_lecture_summaryが正常に公開され、実際に呼び出されることが確認できた。

- 気づき・疑問：ツールの一覧はサーバーが決めてエージェントは起動のたびにサーバーに問い合わせていることが分かった。エージェントのツールの一覧を増やす場合はサーバー側でツールを公開する必要があることが分かった。また、エージェントを特に変えなくてもサーバー側でツールを公開することでエージェントが使えるようになることが分かった。
