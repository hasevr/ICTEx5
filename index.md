---
title: トップ
nav_order: 1
---

# 情報通信実験第5 触覚提示実験

この実験では、マイコン(ESP32)とモータ・力センサで**触感を提示する装置**を作り、
プログラムで振動の波形を変えて、人がどう感じるかを調べます。

**今年度から、プログラムの作成・修正に AI(コーディングエージェント)を使います。**
ただし、全部を AI 任せにする必要はありません。コードを自分で読み、小さな変更は自分で書き換えるのも大歓迎です
(AI の無料枠には週ごとの上限があり、何でも AI に頼むと足りなくなります)。
大きな変更や、調べるのに時間がかかることは AI に、すぐ済むことや確かめたいことは自分で、と使い分けてください。
AI は触感を感じることができません。**感じて、具体的な指示にして返すのは人の仕事です。**

## 進め方

触覚提示実験は **1回(3時間)で実験まで終えます。** 目安は、**前半の1時間半**で開発環境の準備と回路の確認をして一通り動かし、
**後半の1時間半**で実験をします。レポートは実験のあと、**次週までに**提出します。

| 順番 | 内容 | いつ |
|---|---|---|
| 1 | [開発環境の準備](setup.html) — Colab で開発環境を作り、AI と ESP32 をつなぐ | 前半の最初(実験室で。ノートブックの実行は1分ほど) |
| 2 | [AI の使い方と約束](ai.html) — 使ってよい範囲・記録・注意 | 事前に読んでおく |
| 3 | [回路の制作](haptics/circuit.html) — キットを受け取り、回路を確認・修正する | 前半(ここまでで一通り動かす) |
| 4 | [触覚提示の実験](haptics/experiment.html) — 波形と触感・柔らかさの提示(レポート課題) | 後半。レポートは次週までに提出 |

困ったときは [トラブル対応(FAQ)](faq.html)、部品は [部品一覧](parts.html)、
実験のコツは [TIPS](haptics/tips.html) を見てください。

## 使うもの

事前に必要なのは、PC の持参と、大学の Google アカウントにログインできることだけです。

- **PC**(Windows / Mac / Linux / Chromebook どれでもよい)と **Chrome か Edge**。
  開発環境はクラウド(Google Colab)に作るので、PC にソフトウェアをインストールする必要はほとんどありません。
- **大学の Google アカウント**(Colab と、Colab に入っている AI エージェント Antigravity CLI を使う)。
- 実験キット(ESP32 マイコンボード、モータ、力センサなど)。USB Type-A のケーブルをつなぐので、
  Type-C しかない PC では変換アダプタを用意してください。

## 実験キットとマイコンについて

キットの部品は、授業と関係なく使いたくなったときに負担にならないよう、できるだけ安価なものを選びました。
使いたい IoT 機器を作れたら、必要な部品を購入して使い続けてください。

キットの小さいマイコンは [Espressif Systems の ESP32-DevKitC](https://www.espressif.com/en/products/devkits/esp32-devkitc) です。
IoT マイコンとしては大型で高性能な部類です。センサノードを作るときなどには
[モジュールのみ](https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf)や
[SoC のみ](https://www.espressif.com/en/products/socs/esp32-c3)を使います。
[ローム](https://www.rohm.co.jp/iot-kit)、[Silicon Labs](https://www.silabs.com/)、[Nordic](https://www.nordicsemi.com/) なども、
より小型・低消費電力の SoC を出しています。

{: .note }
後半の「組み込みマイコンボードの協調動作実験」「IoT 設計制作実験」の資料は、当面これまでの
[Scrapbox](https://scrapbox.io/ICTEx5/) を参照してください。
