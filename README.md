# 情報通信実験第5 触覚提示実験(AI コーディング前提版)

公開ページ: https://hasevr.github.io/ICTEx5/

ESP32 とモータ・力センサで触感を提示する実験の資料です。開発環境は Google Colab、
プログラムの作成・修正は Colab に入っている AI エージェント(Antigravity CLI)が行い、
手元の ESP32 への書き込みとシリアル通信は [esp-bridge](https://github.com/hasevr/esp-bridge) で行います。

| パス | 内容 |
|---|---|
| `*.md`, `haptics/` | 公開ページ(GitHub Pages + Jekyll、テーマは just-the-docs) |
| `notebooks/haptics.ipynb` | 学生が使う Colab ノートブック(`make_haptics_nb.py` で生成する) |
| `agent/AGENTS.md` | AI エージェントへの指示(ノートブックが作業フォルダに置く) |
| `assets/img/` | 回路・部品の写真 |
| `hardware/haptics-circuit/` | 回路図(KiCad)。写真とファームウェアから起こしたもの |

これまでの資料(後半の協調動作実験・IoT 設計制作実験を含む)は [Scrapbox](https://scrapbox.io/ICTEx5/) にあります。
