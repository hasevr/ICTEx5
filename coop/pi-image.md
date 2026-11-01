---
title: (教員・TA 向け)授業前の確認
parent: 組み込みマイコンボードの協調動作実験
nav_order: 9
---

# (教員・TA 向け)授業前の確認
{: .no_toc }

学生は実験の最初に、Raspberry Pi Imager で SD カードに Raspberry Pi OS Lite を書き込みます([準備と動作確認](setup.html) の 2.)。
前年度までの、2019 年の Raspbian Buster のイメージ(Google Drive / USB メモリで配布)と、その更新作業は使いません。

1. TOC
{:toc}

## 用意するもの

- SD カードリーダー(PC に SD スロットが無い学生向け)。Type-A と Type-C の両方があるとよい。
- 机ごとの有線LAN のハブと、LAN ケーブル(キットのケーブル袋)。

## 授業の前に確かめること

1. **1 台、学生と同じ手順で作ってみる**([準備と動作確認](setup.html) の 2.〜4.)。
   Raspberry Pi Imager の画面や OS の選び方が変わっていないか、所要時間(書き込み・初回起動・`apt install`)を確かめる。
2. **ネットワーク**
   - 無線LAN(`ICT_EX5_2G` / `ICT_EX5_5G`)の ESP32・PC から、有線LAN の Raspberry Pi の 50000 番ポートに届くこと。
   - 学生の PC(Windows・Mac)から `ictex5-NN.local` で Raspberry Pi が見つかること(mDNS)。
     見つからない環境なら、IP アドレスで接続する手順(TA が `hostname -I` を調べる、DHCP の割り当て一覧を見るなど)を決めておく。
   - Raspberry Pi から、Raspberry Pi OS の更新サーバと GitHub に届くこと(`apt install` と `git clone` のため)。
3. **ダウンロードの量**: Raspberry Pi Imager は OS(約 0.5 GB)をその場でダウンロードします。人数分が一度にダウンロードして
   遅くなるようなら、OS のイメージファイル(`.img.xz`)を USB メモリや学内のサーバで配り、Imager の
   「OS: Use custom(カスタム)」で選ばせる(OS のカスタマイズはそのまま使える)。

## よくあるつまずき

- ホスト名が他の人と同じ(`ictex5-NN` の番号の付け間違い)→ `.local` で別の人の Raspberry Pi につながる。キットの番号を使わせる。
- OS のカスタマイズで SSH を有効にし忘れた → 書き込み直すのが早い。
- PC のストレージを書き込み先に選びかける → Imager の確認画面で、容量と名前を必ず確かめさせる。
