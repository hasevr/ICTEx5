---
title: (教員・TA 向け)Raspberry Pi のイメージと授業前の確認
parent: 組み込みマイコンボードの協調動作実験
nav_order: 9
---

# (教員・TA 向け)Raspberry Pi のイメージと授業前の確認
{: .no_toc }

学生は実験の最初に、配布するイメージ `ictex5-coop.img.xz` を balenaEtcher などで SD カードにそのまま書き込みます
([準備と動作確認](setup.html) の 2.)。書き込みツールでの設定は不要です。
前年度までの 2019 年の Raspbian Buster のイメージと、その更新作業は使いません。

1. TOC
{:toc}

## イメージの中身

公式の **Raspberry Pi OS Lite(64-bit、Trixie、2026-10-06 版)** の起動用の領域(FAT)にある cloud-init の設定ファイル `user-data` だけを
書き換えたものです(OS 本体には手を加えていません)。初回の起動で次が行われます。

- ユーザー `pi` を作る。パスワードは全員共通(**教員用の Scrapbox に記載**。この公開サイトには書かない)。sudo はパスワードなし。
- SSH を有効にし、パスワードでのログインを許可する。
- ホスト名を `ictex5-<有線LAN の MAC アドレスの末尾4桁>` にする(全員が同じイメージでも名前が重ならない)。
- ログイン画面(ディスプレイ)に IP アドレスとホスト名を表示する。IP アドレスが割り当てられた後に画面を表示し直す
  (`ictex5-show-ip.service`)。2回目以降の起動でも表示される。
- タイムゾーン `Asia/Tokyo`、キーボード `jp`。

Raspberry Pi にはソフトウェアを追加しません。サーバ(`app.py`)は Python の標準ライブラリだけで動き、PC から `scp` で送ります。
そのため、Raspberry Pi からインターネットに届かなくても、時計が合っていなくても、実験には影響しません。

## 作り直すとき

1. 公式の Raspberry Pi OS Lite(64-bit)の `.img.xz` を取り、展開する。
2. 最初のパーティション(FAT)の `user-data` を、このリポジトリの [`hardware/raspberrypi/user-data`](https://github.com/hasevr/ICTEx5/blob/main/hardware/raspberrypi/user-data)
   で置き換える。パスワードの行(`passwd:`)は、`openssl passwd -6 '<パスワード>'` で作ったハッシュにする。
   Windows・Mac なら、イメージを一度 SD カードに書き込み、PC で見える `bootfs` の `user-data` を書き換えてから吸い出してもよい。
3. `xz -T0` で圧縮して配る。

## 用意するもの

- 配布用の USB メモリ(`ictex5-coop.img.xz`、約 0.5 GB)。数本あるとよい。
- SD カードリーダー(PC に SD スロットが無い学生向け)。Type-A と Type-C の両方があるとよい。
- 実験室のディスプレイ(DVI 入力)と、キットの HDMI-DVI ケーブル。机のハブと LAN ケーブル。

## 授業の前に確かめること

1. **1 台、学生と同じ手順で作ってみる**([準備と動作確認](setup.html) の 2.〜4.)。
   画面に IP アドレスとホスト名が出ること、その IP アドレスで `ssh pi@...` と共通のパスワードでログインできること、
   所要時間(書き込み・初回の起動)を確かめる。
2. **ネットワーク**
   - 無線LAN(`ICT_EX5_2G` / `ICT_EX5_5G`)の ESP32・PC から、有線LAN の Raspberry Pi の 50000 番ポートに届くこと。
   - ルーター(ASUS)の管理画面で、2.4 GHz・5 GHz とも「AP を隔離する」が「いいえ」、`ICT_EX5_2G` / `ICT_EX5_5G` がゲストネットワークでないこと、
     机のハブがルーターの LAN ポート(WAN ではない)につながっていること。

## よくあるつまずき

- Raspberry Pi Imager で書き込み、「OS のカスタマイズ」を適用した → イメージの設定が上書きされる。「いいえ」と答えるか、balenaEtcher を使わせる。
- 電源を入れてからディスプレイをつないだ → 画面が出ない。電源を入れ直す。
- PC の USB から Raspberry Pi に給電している → 電流不足で不安定になる。キットの 5 V 3 A の USB 電源を使わせる。
- PC のストレージを書き込み先に選びかける → 書き込みツールの画面で、容量と名前を必ず確かめさせる。
