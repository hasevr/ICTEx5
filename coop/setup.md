---
title: 準備と動作確認
parent: 組み込みマイコンボードの協調動作実験
nav_order: 1
---

# 準備と動作確認(前半の約90分)
{: .no_toc }

ここまでで、ESP32 が力センサの値を Raspberry Pi に送り、PC のブラウザでグラフが動くところまでを確かめます。

1. TOC
{:toc}

## 0. 回路と PC

- 回路は触覚提示実験のもの(力センサ・モータ)をそのまま使います。
- PC は実験室の無線LAN に、**なるべく `ICT_EX5_5G`** でつないでください(ESP32 は 2.4 GHz の `ICT_EX5_2G` にしかつながらないので、2.4 GHz を空けておくため)。ESP32 と Raspberry Pi と同じネットワークにいないと、
  Raspberry Pi のページを開けません。

## 1. Colab のノートブックを実行する

触覚提示実験と同じ手順で、**協調動作実験用のノートブック**を実行します。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hasevr/ICTEx5/blob/main/notebooks/coop.ipynb)

- 上から順にセルを実行します。「3. HttpHaptic をビルドする」は初回3分ほどかかります。その間に 2. に進んでください。
- 最後に出る「▶ ESP32 ブリッジを開く」を Chrome / Edge の新しいタブで開き、ESP32 をつないで「ESP32 に接続」を押します。
- AI を使うときは、左下の「ターミナル」で `cd /content/work && agy`(ログインは前回と同じ)。

## 2. Raspberry Pi の SD カードを作る

イメージファイル **`ictex5-coop.img.xz`** を、キットの Raspberry Pi 3 の SD カードに書き込みます。
このイメージは Raspberry Pi OS Lite に、この実験用の設定(ユーザー `pi`、SSH、画面への IP アドレスの表示)を加えたものです。
書き込むときに設定することは何もありません。

1. PC に書き込みツール [balenaEtcher](https://etcher.balena.io/) をインストールする(この実験で PC に入れるのはこれだけです)。
   Windows・Mac の両方で使えます。
   - **Windows**: 「Download for Windows」のインストーラ(x64)。Arm の Windows PC でも動きます。
   - **Mac**: 「Download for macOS」で、Apple シリコン(M1 以降)なら arm64 版、Intel Mac なら x64 版。
     ダウンロードした `.dmg` を開き、balenaEtcher をアプリケーションフォルダにドラッグする。
     初回の起動で「開発元を確認できない」などと出たら、「システム設定 → プライバシーとセキュリティ」で「このまま開く」。
2. `ictex5-coop.img.xz`(約 0.6 GB)を、**大学の Box(リンクは LMS で案内)からダウンロード**する。
   全員が一度にダウンロードして遅いときは、実験室で配る **USB メモリ**から PC にコピーしてもよい(TA の指示に従う)。
   展開しなくてよい。Mac で自動的に展開されても、展開後の `.img` を使えばよい。
   balenaEtcher のインストールとダウンロードは、同時に進めてかまいません。
3. SD カードを、カードリーダー(実験室で貸し出します)で PC につなぐ。
4. balenaEtcher で「Flash from file」→ `ictex5-coop.img.xz`、「Select target」→ SD カード(**容量で確かめる。PC の他のディスクを選ばないこと**)、
   「Flash!」。5〜10分かかります。
   書き込みの開始時に、Windows では「このアプリがデバイスに変更を加えることを許可しますか」、Mac ではパスワードを聞かれます。許可してください。
5. 終わったら SD カードを取り出し、Raspberry Pi に挿す。

{: .warning }
書き込みが終わると、**Windows では「ドライブ X: を使うにはフォーマットする必要があります」、Mac では「このコンピュータで読み取れないディスク」**
と表示されることがあります。SD カードの中に Windows・Mac が読めない形式(Linux 用)の部分があるためで、異常ではありません。
**フォーマットせず、「キャンセル」(Mac は「無視」か「取り出す」)を選んでください。** フォーマットすると、書き込んだ内容が消えます。

書き込みを待つ間に、1. のノートブックや 5. の ESP32 の書き込みを進めておくと効率的です。

{: .note }
Raspberry Pi Imager で書き込んでもかまいません。その場合は OS に「Use custom」でこのファイルを選び、
「OS のカスタマイズを適用しますか」には **「いいえ」** と答えてください(「はい」にすると、このイメージの設定が上書きされます)。

## 3. Raspberry Pi を起動して、画面で IP アドレスを確かめ、SSH でつなぐ

1. **ディスプレイ**(実験室のもの)を HDMI-DVI ケーブルで、**LAN ケーブル**を机のハブに、それぞれ Raspberry Pi につなぐ。
   ディスプレイの入力を Raspberry Pi に切り替える。**電源を入れる前につなぐ**こと(後からつなぐと画面が出ないことがあります)。
2. **電源**をつなぐ。キットの **5 V 3 A の USB 電源**と Micro USB ケーブルを使います(PC の USB からでは電流が足りず、不安定になります)。
3. 初回の起動は 3〜5 分かかります(途中で一度再起動することがあります)。しばらくすると、画面に次のように表示されます。
   ```
     ICTEx5 Raspberry Pi
     IP address : 10.0.1.23
     Host name  : ictex5-a1b2
     Connect from your PC:  ssh pi@10.0.1.23
   ```
   この **IP アドレス**を、以後のすべて(SSH、ファイルの転送、ブラウザ、ESP32 の宛先)で使います。メモしておいてください。
   IP アドレスは毎回同じとは限りません。次回も、起動したら画面で確かめます。キーボードは要りません。
4. PC の **PowerShell**(Windows)か **ターミナル**(Mac)で SSH でログインする。パスワードは実験室で案内します。
   ```
   ssh pi@10.0.1.23
   ```
   初回は `Are you sure you want to continue connecting (yes/no)?` と聞かれるので `yes` と入力します。

{: .note }
同じネットワークの環境によっては、IP アドレスの代わりにホスト名(`ssh pi@ictex5-a1b2.local`)でもつながります。
つながればどちらを使ってもかまいません。

## 4. Raspberry Pi で Web サーバを動かす

サーバのプログラム `app.py` は Python の標準ライブラリだけで動くので、Raspberry Pi に何かをインストールする必要はありません。
PC から `scp` で Raspberry Pi に送って起動します。AI が書き換えたものを送るときも、同じ手順です。

1. Colab のノートブックの「**サーバのプログラムを PC にダウンロードする**」のセルを実行し、`app.py` を PC に保存する
   (ダウンロードのフォルダに入ります)。
2. PC の PowerShell(Mac は ターミナル)で、ダウンロードのフォルダに移って Raspberry Pi に送る。
   ```
   cd ~/Downloads
   scp app.py pi@10.0.1.23:
   ```
   (最後の `:` を忘れないこと。Raspberry Pi のホームフォルダに送られます)
3. SSH でログインした Raspberry Pi で起動する。
   ```
   python3 app.py
   ```

`Running on http://...:50000` と出たら、PC のブラウザで次を開きます。

```
http://10.0.1.23:50000/
```

「ESP32 から届いた力センサの値」というページが出れば成功です(まだ何も届いていないので、グラフは空です)。
サーバは動かしたままにしておきます。止めるときは `Ctrl+C` です。

{: .note }
サーバのプログラムは [`server/app.py`](https://github.com/hasevr/ICTEx5/blob/main/server/app.py) です。
ESP32 から値を受け取る `/getadc`、グラフのページ `/`、周波数を設定する `/freq`、記録を CSV で返す `/data.csv` があります。

## 5. ESP32 に HttpHaptic を書き込んで、サーバの宛先を設定する

ノートブックの「手で書き込む・設定する・出力を見る」のセル、または AI に頼んで、次の3つを行います
(`10.0.1.23` は 3. で画面に出た IP アドレスに置き換える)。

```
esp flash /content/work/HttpHaptic
esp send "server 10.0.1.23:50000\n"
esp log -n 30
```

`esp log` に次のような行が出れば、ESP32 から Raspberry Pi に届いています。

```
I (5123) main: Wi-Fi connected, my IP: 10.0.2.45
I (6201) HTTP: status=200 rtt=12.3 ms ADC=1934 resp={"adc":1934,"freq":0.0}
```

- サーバの宛先は ESP32 の中に保存されるので、書き込み直しても設定し直す必要はありません(`show` で確認できます)。
- 無線LAN は `ICT_EX5_2G`(2.4 GHz)につながります。ESP32 は 5 GHz の無線LAN には接続できません。

## 6. 動作を確かめる

- Raspberry Pi の画面(SSH)に、届いた値が1行ずつ表示されているか。
- ブラウザのグラフが動いているか。力センサを押すと値が上がるか。
- ブラウザの「振動の周波数を ESP32 に送る」に `50` と入れて送り、力センサを押すと、ゆっくりした振動になるか。
  `0` に戻すと、押すたびに周波数が切り替わる(触覚提示実験と同じ)動作に戻ります。

ここまでできたら、[協調動作の実験](experiment.html) に進んでください。

## うまくいかないとき

| 症状 | 確かめること |
|---|---|
| `esp log` に `Server is not set` | 5. の `server` コマンドを送ったか |
| `HTTP failed: ESP_ERR_HTTP_CONNECT` | IP アドレスとポート(`:50000`)が正しいか。Raspberry Pi でサーバ(`app.py`)が動いているか |
| `Wi-Fi disconnected, retrying` が続く | 無線LAN の名前とパスワード(`show` で確認)。別の無線LAN にするときは `esp send "wifi 名前 パスワード\n"` |
| ブラウザでページが開かない | PC が実験室の無線LAN につながっているか。URL の IP アドレスとポート(`:50000`)が正しいか |
| サーバに `Address already in use` | 前の `app.py` が動いたまま。`pkill -f app.py` で止めてから起動し直す |
| `ssh` で `Connection refused` | 初回の起動の設定がまだ終わっていない。1〜2分待ってから試す。画面に IP アドレスが出てからつなぐ |
| 画面の IP address が空のまま | LAN ケーブルがハブにつながっているか。ハブの電源。ケーブルを挿し直して1分待つ |
| 画面に何も出ない | 電源を入れる前にディスプレイをつないだか。ディスプレイの入力の切り替え。電源を抜いて挿し直す |

実験が終わったら、Raspberry Pi で `sudo shutdown now` を実行し、20 秒ほど待ってから電源を抜いてください。
