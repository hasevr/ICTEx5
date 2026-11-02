---
title: 準備と動作確認
parent: 組み込みマイコンボードの協調動作実験
nav_order: 1
---

# 準備と動作確認(前半の1時間半)
{: .no_toc }

ここまでで、ESP32 が力センサの値を Raspberry Pi に送り、PC のブラウザでグラフが動くところまでを確かめます。

1. TOC
{:toc}

## 0. 回路と PC

- 回路は触覚提示実験のもの(力センサ・モータ)をそのまま使います。
- PC は実験室の無線LAN(`ICT_EX5_2G` か `ICT_EX5_5G`)につないでください。ESP32 と Raspberry Pi と同じネットワークにいないと、
  Raspberry Pi のページを開けません。

## 1. Colab のノートブックを実行する

触覚提示実験と同じ手順で、**協調動作実験用のノートブック**を実行します。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hasevr/ICTEx5/blob/main/notebooks/coop.ipynb)

- 上から順にセルを実行します。「3. HttpHaptic をビルドする」は初回3分ほどかかります。その間に 2. に進んでください。
- 最後に出る「▶ ESP32 ブリッジを開く」を Chrome / Edge の新しいタブで開き、ESP32 をつないで「ESP32 に接続」を押します。
- AI を使うときは、左下の「ターミナル」で `cd /content/work && agy`(ログインは前回と同じ)。

## 2. Raspberry Pi の SD カードを作る

キットの Raspberry Pi 3 の SD カードに、OS(Raspberry Pi OS Lite)を書き込みます。
書き込むときに、ホスト名・ユーザー・SSH の設定もしておくので、ディスプレイとキーボードはつながずに使えます。

1. PC に [Raspberry Pi Imager](https://www.raspberrypi.com/software/) をインストールする(この実験で PC に入れるのはこれだけです)。
2. SD カードを、カードリーダー(実験室で貸し出します)で PC につなぐ。
3. Raspberry Pi Imager で次を選ぶ。
   - デバイス: **Raspberry Pi 3**
   - OS: **Raspberry Pi OS (other) → Raspberry Pi OS Lite (64-bit)**(デスクトップの無い版)。
     実験室で USB メモリを配っている場合は、**Use custom** を選び、USB メモリの中のイメージファイル(`.img.xz`)を選ぶ(ダウンロードを待たずに済む)
   - ストレージ: つないだ SD カード(容量で確かめる。**PC の他のディスクを選ばないこと**)
4. 「OS のカスタマイズ」(「設定を編集する」)で次を設定する。
   - ホスト名: **`ictex5-NN`**(`NN` はキットの番号。他の人と重ならないこと)
   - ユーザー名 **`pi`** と、自分で決めたパスワード(忘れないようメモしておく)
   - 無線LAN の設定: しない(有線LAN でつなぐ)
   - ロケール: タイムゾーン `Asia/Tokyo`、キーボード `jp`
   - サービス: **SSH を有効にする**(パスワード認証を使う)
5. 書き込む(5〜10分)。終わったら SD カードを取り出し、Raspberry Pi に挿す。

書き込みを待つ間に、1. のノートブックや 5. の ESP32 の書き込みを進めておくと効率的です。

## 3. Raspberry Pi を起動して、PC から SSH でつなぐ

1. **LAN ケーブル**で Raspberry Pi と机のハブをつなぐ。
2. **電源**をつなぐ。キットの **5 V 3 A の USB 電源**と Micro USB ケーブルを使います(PC の USB からでは電流が足りず、不安定になります)。
   初回の起動は 2〜3 分かかります。
3. PC の **PowerShell**(Windows)か **ターミナル**(Mac)で、SSH でログインする。パスワードは 2. で決めたものです。
   ```
   ssh pi@ictex5-NN.local
   ```
   初回は `Are you sure you want to continue connecting (yes/no)?` と聞かれるので `yes` と入力します。
4. Raspberry Pi の **IP アドレス**を調べる。ESP32 から Raspberry Pi に送るときに使います。
   ```
   hostname -I
   ```
   `10.0.1.23` のような数字が出ます(人によって違います。次回も同じとは限りません)。

{: .note }
`ictex5-NN.local` で見つからないときは、1分ほど待ってからもう一度試してください。それでもだめなら、下の「うまくいかないとき」の方法で
IP アドレスを調べ、`ssh pi@10.0.1.23` のように IP アドレスで接続します。

## 4. Raspberry Pi で Web サーバを動かす

サーバのプログラム `app.py` は Python の標準ライブラリだけで動くので、Raspberry Pi に何かをインストールする必要はありません。
PC から `scp` で Raspberry Pi に送って起動します。AI が書き換えたものを送るときも、同じ手順です。

1. Colab のノートブックの「**サーバのプログラムを PC にダウンロードする**」のセルを実行し、`app.py` を PC に保存する
   (ダウンロードのフォルダに入ります)。
2. PC の PowerShell(Mac は ターミナル)で、ダウンロードのフォルダに移って Raspberry Pi に送る。
   ```
   cd ~/Downloads
   scp app.py pi@ictex5-NN.local:
   ```
   (最後の `:` を忘れないこと。Raspberry Pi のホームフォルダに送られます)
3. SSH でログインした Raspberry Pi で起動する。
   ```
   python3 app.py
   ```

`Running on http://...:50000` と出たら、PC のブラウザで次を開きます。

```
http://ictex5-NN.local:50000/
```

「ESP32 から届いた力センサの値」というページが出れば成功です(まだ何も届いていないので、グラフは空です)。
サーバは動かしたままにしておきます。止めるときは `Ctrl+C` です。

{: .note }
サーバのプログラムは [`server/app.py`](https://github.com/hasevr/ICTEx5/blob/main/server/app.py) です。
ESP32 から値を受け取る `/getadc`、グラフのページ `/`、周波数を設定する `/freq`、記録を CSV で返す `/data.csv` があります。

## 5. ESP32 に HttpHaptic を書き込んで、サーバの宛先を設定する

ノートブックの「手で書き込む・設定する・出力を見る」のセル、または AI に頼んで、次の3つを行います
(`10.0.1.23` は 3. で調べた IP アドレスに置き換える)。

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
| ブラウザでページが開かない | PC が実験室の無線LAN につながっているか。`ictex5-NN.local` の代わりに IP アドレスで開く |
| サーバに `Address already in use` | 前の `app.py` が動いたまま。`pkill -f app.py` で止めてから起動し直す |
| `ictex5-NN.local` が見つからない | 1分ほど待つ。それでもだめなら、実験室のディスプレイに HDMI-DVI ケーブルで、キーボードを USB でつなぎ、`pi` でログインして `hostname -I` で IP アドレスを調べる。以後は名前の代わりに IP アドレスを使う |

実験が終わったら、Raspberry Pi で `sudo shutdown now` を実行し、20 秒ほど待ってから電源を抜いてください。
