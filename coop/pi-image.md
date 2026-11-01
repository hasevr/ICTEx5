---
title: (教員・TA 向け)Raspberry Pi の SD カードの準備
parent: 組み込みマイコンボードの協調動作実験
nav_order: 9
---

# (教員・TA 向け)Raspberry Pi の SD カードの準備
{: .no_toc }

前年度までは、学生が実験の最初に 2019 年の Raspbian Buster のイメージを SD カードに書き込み、更新していました。
ダウンロード・書き込み・更新で授業時間の多くを使い、Buster はすでにサポートも終わっています。
今年度は、**授業の前に SD カードを準備しておき**、学生は電源を入れて SSH でつなぐだけにします。

1. TOC
{:toc}

## 方針

- OS: **Raspberry Pi OS Lite(64-bit)**、最新版。Raspberry Pi 3 Model B で動きます。デスクトップは不要です。
- ホスト名: キットごとに **`ictex5-NN`**(NN はキットの番号、01〜)。学生は `ssh pi@ictex5-NN.local` で接続します
  (Windows 10 以降と Mac は `.local` の名前解決ができます)。
- ユーザー: `pi`。パスワードは実験室で口頭か板書で伝えるものを1つ決める。
- SSH: 有効(パスワード認証)。無線LAN の設定はしない(有線LAN で机のハブにつなぐ)。
- 入れておくもの: `python3-flask`、`git`、このリポジトリ(`~/ICTEx5`)。

## 手順

### 1. 1 枚目を作る

1. PC に [Raspberry Pi Imager](https://www.raspberrypi.com/software/) を入れ、デバイス「Raspberry Pi 3」、
   OS「Raspberry Pi OS (other) → Raspberry Pi OS Lite (64-bit)」、書き込み先の SD カードを選ぶ。
2. 「設定を編集する」で次を設定して書き込む。
   - ホスト名 `ictex5-01`、ユーザー名 `pi` とパスワード
   - ロケール: タイムゾーン `Asia/Tokyo`、キーボード `jp`
   - サービス: SSH を有効にする(パスワード認証)
3. Raspberry Pi に挿して有線LAN と電源をつなぎ、`ssh pi@ictex5-01.local` でログインして次を実行する。
   ```
   sudo apt update && sudo apt full-upgrade -y
   sudo apt install -y python3-flask git
   git clone https://github.com/hasevr/ICTEx5 ~/ICTEx5
   ```
4. 動作確認: `cd ~/ICTEx5/server && python3 app.py` で起動し、PC のブラウザで `http://ictex5-01.local:50000/` が開くこと。
   `curl "http://localhost:50000/getadc?ADC=2000&TIME=1"` で `{"adc":2000,"freq":0.0}` が返ること。
5. `sudo shutdown now` で止める。

### 2. 残りのカードを作る

1 枚目のイメージを PC に吸い出して複製するか、各カードで 1. を繰り返します。どちらの場合も、**ホスト名をカードごとに変えて**ください。
同じホスト名が並ぶと `.local` での接続がうまくいきません。

- 複製した場合は、各カードで1回起動してホスト名を変える。
  ```
  sudo raspi-config nonint do_hostname ictex5-02
  sudo reboot
  ```
- SD カードとキットの箱に番号(`NN`)を書いておく。

## 授業の前に確かめること

- 実験室の有線LAN(机のハブ)と無線LAN(`ICT_EX5_2G` / `ICT_EX5_5G`)が同じネットワークで、
  無線LAN の ESP32・PC から有線LAN の Raspberry Pi の 50000 番ポートに届くこと。
- 学生の PC(Windows・Mac)から `ictex5-NN.local` が引けること。引けない環境なら、IP アドレスを机ごとに掲示する。
- Raspberry Pi から GitHub に届くこと(`git pull` でサンプルを最新にするため)。
