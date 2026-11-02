# notebooks/coop.ipynb(組み込みマイコンボードの協調動作実験)を生成する。
# ESP-IDF の準備・ESP32 ブリッジ・AI のログインのセルは make_haptics_nb.py と共通
from make_haptics_nb import md, code, cells as hcells, save

SETUP_IDF, BRIDGE, AGY_MD, AGY_LINK = hcells[1], hcells[4], hcells[5], hcells[6]

cells = [
md("""# 情報通信実験第5 組み込みマイコンボードの協調動作実験(Colab + AI)
手順は https://hasevr.github.io/ICTEx5/coop/ を見てください。

1. 上から順にセルを実行する(「Google Drive is disabled」は OK で閉じる)。
2. 最後に出る「▶ ESP32 ブリッジを開く」を **Chrome か Edge の新しいタブ**で開き、ESP32 をつないで「ESP32 に接続」。
3. 左下の「ターミナル」で `cd /content/work && agy` として AI エージェントを起動する。"""),
SETUP_IDF,
code("""%%bash
# 2. 実験のプロジェクト(ESP32 の HttpHaptic と、Raspberry Pi のサーバ)と、AI への指示ファイルを用意する
set -e
mkdir -p /content/work && cd /content/work
if [ -d ictex5/.git ]; then git -C ictex5 pull -q --ff-only || echo "git pull できませんでした(手元の版で続けます)"
else git clone -q --depth 1 https://github.com/hasevr/ICTEx5 ictex5; fi
# 自分で書き換える作業用のコピー(すでにあれば上書きしない)
[ -d HttpHaptic ] || cp -r ictex5/firmware/HttpHaptic .
[ -d server ] || cp -r ictex5/server .
(curl -sfL -o AGENTS.md https://raw.githubusercontent.com/hasevr/ICTEx5/main/agent/AGENTS.md && cp AGENTS.md GEMINI.md) || echo "AGENTS.md を取得できませんでした"
# agy のログイン URL を拾う(ターミナルでは長い URL が途中で切れるため。下の「ログイン用リンク」セルで表示)
cat > /usr/local/bin/xdg-open <<'EOF'
#!/bin/sh
echo "$1" > /content/agy_url.txt
EOF
chmod +x /usr/local/bin/xdg-open
ls /content/work"""),
code("""# 3. HttpHaptic をビルドする(初回は3分ほど)
!idf.py -C /content/work/HttpHaptic build 2>&1 | tail -3"""),
BRIDGE,
AGY_MD,
AGY_LINK,
md("""## 手で書き込む・設定する・出力を見る(AI を使わない場合)
AI は同じコマンドを自分で使います。`10.0.1.23` は自分の Raspberry Pi の IP アドレスに置き換えてください。"""),
code("""!esp flash /content/work/HttpHaptic
!esp send "server 10.0.1.23:50000\\n"
!esp log --since-flash -n 30"""),
md("""## Raspberry Pi のサーバのプログラムを PC にダウンロードする
最初のサンプルも、AI が書き換えた後も、下のセルで `/content/work/server/app.py` を PC にダウンロードし、
PC の PowerShell(Mac は ターミナル)で Raspberry Pi に送ります(`NN` はキットの番号)。
```
cd ~/Downloads
scp app.py pi@ictex5-NN.local:
```"""),
code("""from google.colab import files
files.download('/content/work/server/app.py')"""),
md("""## AI 利用の記録
主な依頼・AI の変更・うまくいかなかったこと・測った結果を、ここに書いていく(レポートの材料)。
Drive に保存できないので、終わったら「ファイル → ダウンロード → .ipynb」で保存する。

| 時刻 | 依頼したこと | AI がしたこと | 結果・気づき |
|---|---|---|---|
| | | | |"""),
]

if __name__ == '__main__':
    save(cells, 'coop.ipynb')
