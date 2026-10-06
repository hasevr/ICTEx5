---
title: 開発環境の準備
nav_order: 2
---

# 開発環境の準備(第1回の最初に、実験室で)
{: .no_toc }

開発環境は **Google Colab**(クラウド上の Linux)に作ります。PC には、ESP32 の USB ドライバ以外のインストールは不要で、
全部で10分ほどで済むので、**第1回の最初に実験室で行います。** 事前にやっておくことは次の2つだけです。

- PC を持参する(USB Type-A をつなぐので、Type-C しかない PC は変換アダプタも)。
- **大学の Google アカウントにログインできる**ことを確かめておく。

当日は、**3 のノートブックの実行を最初に始めてください。** インストールとビルドで5分ほどかかるので、
その間に [回路の制作](haptics/circuit.html) のキットの受け取りと確認を進めます。

1. TOC
{:toc}

## 1. PC とブラウザ

- **Chrome か Edge** を使います(ESP32 との通信に使う Web Serial が Safari・Firefox では動きません)。
- 大学の Google アカウントでログインしておきます。

## 2. USB シリアルドライバ(CP210x)

ESP32-DevKitC は USB シリアル変換 IC CP210x を使っています。

ESP32 をつなぐ直前に確認すれば十分です。

- **Windows 10/11**: ESP32 をつなぐと自動で入ることが多いです。デバイスマネージャーの「ポート(COM と LPT)」に
  「Silicon Labs CP210x … (COMx)」が出れば OK。出なければ
  [Silicon Labs のページ](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads)の
  「CP210x Universal Windows Driver」を入れます(展開した `silabser.inf` を右クリック →「インストール」)。
- **Mac**: macOS の版によっては標準で認識します。ターミナルで `ls /dev/cu.*` を実行し、ESP32 をつないだときに増えるものがあれば OK。
  無ければ同じページの「CP210x VCP Mac OSX Driver」を入れます。
- **Chromebook / Linux**: 追加の作業は不要です。

## 3. 実験用ノートブックを開く

[**実験用ノートブックを Colab で開く**](https://colab.research.google.com/github/hasevr/ICTEx5/blob/main/notebooks/haptics.ipynb){: .btn .btn-primary }

- 「Google Drive is disabled」と出たら **OK** で閉じてください(大学アカウントは Drive が使えない設定です。
  ノートブックは Drive に保存できないので、記録は「ファイル → ダウンロード」で .ipynb を保存します)。
- 右上の「接続」でランタイムにつなぎ、**上から順にセルを実行**します。ESP-IDF のインストールで3分ほどかかります。
- 最後に「▶ ESP32 ブリッジを開く」というリンクが出ます。ESP32 をつなぐのは、回路の確認が済んでから(5)です。

{: .note }
Colab の VM は、しばらく操作しないと切れ、最長でも十数時間でリセットされます。
その場合はノートブックを上から実行し直してください(作業中のファイルは消えるので、
`main.c` など大事な変更はダウンロードしておくか、AI に「変更点をまとめて」と頼んで記録しておく)。

## 4. AI エージェント(Antigravity CLI)にログインする

1. Colab の左下の「**ターミナル**」を開き、次を実行します。
   ```sh
   cd /content/work && agy
   ```
2. 「Select login method」で **1. Google OAuth** を選びます。表示された URL を開き
   (ターミナルでは折り返されて途中で切れることがあるので、ノートブックのセルに出るリンクを使う方が確実です)、
   大学のアカウントを選んで「ログイン」。表示されたコードをターミナルに貼り付けて Enter。
3. 色の選択は Enter でかまいません。
4. 「Terms of Service & Data Use」の画面: **`[x] Yes, I agree to help improve …` のチェックはスペースキーで外し**、
   下の **Done** を選んで Enter([AI の使い方と約束](ai.html) を参照)。
5. 「Do you trust the contents of this project?」は **Yes**。
6. `>` が出たら準備完了です。試しに次のように頼んでみます。
   ```
   AGENTS.md を読んでから、ActiveHaptic をビルドして、結果を教えて。
   ```

## 5. ESP32 をつなぐ(回路の確認が済んでから)

1. [回路の制作](haptics/circuit.html) の「注意点」を確認してから、ESP32 を USB で PC につなぎます。
2. ノートブックの「▶ ESP32 ブリッジを開く」を **新しいタブ**で開き、「**ESP32 に接続**」を押してポートを選びます。
   - Windows は「CP210x … (COMx)」、Mac は「CP2102 …」や `cu.usbserial…` を選びます。
   - **緑色の基板(FT232H、デバッガ用)のポートは選ばない**こと。
3. 「ESP32: 接続中」になったら、タブは閉じずに置いておきます。ESP32 の出力がタブとColabの両方に流れます。
4. ターミナルで `esp status` を実行し、`"connected": true` なら OK。

## 付録: PC にローカルの開発環境を作る場合

自宅でも続けたい場合は、Colab のノートブックをもう一度上から実行すればよいだけです。
Colab が使えない状況(ネットワークが無いなど)や、デバッガ(JTAG)を使いたい場合は、
従来どおり VS Code と [ESP-IDF 拡張](https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/) を
PC に入れることもできます(ESP-IDF v5.5.1、15 GB 程度の空きが必要)。
その場合も AI は使えますが、Antigravity CLI を PC で使うには個人の Google アカウントが必要です。
