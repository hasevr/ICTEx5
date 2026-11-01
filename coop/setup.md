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

## 2. Raspberry Pi を起動して、PC から SSH でつなぐ

キットの Raspberry Pi 3 には、準備済みの SD カードが入っています。ディスプレイとキーボードはつなぎません。

1. **LAN ケーブル**で Raspberry Pi と机のハブをつなぐ。
2. **電源**(Micro USB の AC アダプタ)をつなぐ。1分ほどで起動します。
3. PC の **PowerShell**(Windows)か **ターミナル**(Mac)で、次のように SSH でログインします。
   `NN` は SD カード(キット)に書かれた番号です。パスワードは実験室で案内します。
   ```
   ssh pi@ictex5-NN.local
   ```
   初回は `Are you sure you want to continue connecting (yes/no)?` と聞かれるので `yes` と入力します。
4. Raspberry Pi の **IP アドレス**を調べます。ESP32 から Raspberry Pi に送るときに使います。
   ```
   hostname -I
   ```
   `10.0.1.23` のような数字が出ます(人によって違います。次回も同じとは限りません)。

{: .note }
`ictex5-NN.local` で見つからないときは、少し待ってからもう一度試してください。それでもだめなら TA に IP アドレスを調べてもらい、
`ssh pi@10.0.1.23` のように IP アドレスで接続します。

## 3. Raspberry Pi で Web サーバを動かす

SSH でログインした Raspberry Pi で、次を実行します(`ICTEx5` フォルダは SD カードに入っています)。

```
cd ~/ICTEx5 && git pull
cd server && python3 app.py
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

## 4. ESP32 に HttpHaptic を書き込んで、サーバの宛先を設定する

ノートブックの「手で書き込む・設定する・出力を見る」のセル、または AI に頼んで、次の3つを行います
(`10.0.1.23` は 2. で調べた IP アドレスに置き換える)。

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

## 5. 動作を確かめる

- Raspberry Pi の画面(SSH)に、届いた値が1行ずつ表示されているか。
- ブラウザのグラフが動いているか。力センサを押すと値が上がるか。
- ブラウザの「振動の周波数を ESP32 に送る」に `50` と入れて送り、力センサを押すと、ゆっくりした振動になるか。
  `0` に戻すと、押すたびに周波数が切り替わる(触覚提示実験と同じ)動作に戻ります。

ここまでできたら、[協調動作の実験](experiment.html) に進んでください。

## うまくいかないとき

| 症状 | 確かめること |
|---|---|
| `esp log` に `Server is not set` | 4. の `server` コマンドを送ったか |
| `HTTP failed: ESP_ERR_HTTP_CONNECT` | IP アドレスとポート(`:50000`)が正しいか。Raspberry Pi でサーバ(`app.py`)が動いているか |
| `Wi-Fi disconnected, retrying` が続く | 無線LAN の名前とパスワード(`show` で確認)。別の無線LAN にするときは `esp send "wifi 名前 パスワード\n"` |
| ブラウザでページが開かない | PC が実験室の無線LAN につながっているか。`ictex5-NN.local` の代わりに IP アドレスで開く |
| サーバに `Address already in use` | 前の `app.py` が動いたまま。`pkill -f app.py` で止めてから起動し直す |

実験が終わったら、Raspberry Pi で `sudo shutdown now` を実行し、20 秒ほど待ってから電源を抜いてください。
