# notebooks/iot.ipynb(IoT 設計制作実験)を生成する。
# ESP-IDF の準備・ESP32 ブリッジ・AI のログインのセルは make_haptics_nb.py と共通
from make_haptics_nb import md, code, cells as hcells, save

SETUP_IDF, BRIDGE, AGY_MD, AGY_LINK = hcells[1], hcells[4], hcells[5], hcells[6]

cells = [
md("""# 情報通信実験第5 IoT 設計制作実験(Colab + AI)
手順は https://hasevr.github.io/ICTEx5/iot/ を見てください。

1. 上から順にセルを実行する(「Google Drive is disabled」は OK で閉じる)。
2. **前回の作業の続きなら**「前回の作業を戻す」で、前回ダウンロードした ZIP をアップロードする。
3. 「▶ ESP32 ブリッジを開く」を **Chrome か Edge の新しいタブ**で開き、ESP32 をつないで「ESP32 に接続」。
4. 左下の「ターミナル」で `cd /content/work && agy` として AI エージェントを起動する。
5. **終わる前に、必ず「作業を ZIP でダウンロード」を実行する**(Colab の VM はリセットされると中身が消えます)。"""),
SETUP_IDF,
code("""%%bash
# 2. 作業フォルダと、サンプル・AI への指示ファイルを用意する
set -e
mkdir -p /content/work && cd /content/work
if [ -d ictex5/.git ]; then git -C ictex5 pull -q --ff-only || echo "git pull できませんでした(手元の版で続けます)"
else git clone -q --depth 1 https://github.com/hasevr/ICTEx5 ictex5; fi
# AI への指示ファイル。自分たちのプロジェクトの説明は PROJECT.md に書く(AGENTS.md から読むよう指示してある)
(curl -sfL -o AGENTS.md https://raw.githubusercontent.com/hasevr/ICTEx5/main/agent/AGENTS.md && cp AGENTS.md GEMINI.md) || echo "AGENTS.md を取得できませんでした"
[ -f PROJECT.md ] || printf '# 私たちの IoT システム\\n\\n(構想、この人が担当する部分、ピンの割り当て、通信の仕様をここに書く)\\n' > PROJECT.md
cat > /usr/local/bin/xdg-open <<'EOF'
#!/bin/sh
echo "$1" > /content/agy_url.txt
EOF
chmod +x /usr/local/bin/xdg-open
echo "サンプル: ictex5/firmware/ の HttpHaptic(無線LAN + HTTP)、Mpu9250(9 軸センサ)、I2SHaptic(D 級アンプ)、ictex5/server/app.py(Raspberry Pi のサーバ)"
ls /content/work"""),
md("""## 前回の作業を戻す(2回目以降)
前回の最後にダウンロードした `iot-work-....zip` を選ぶ。"""),
code("""from google.colab import files
import zipfile, io
up = files.upload()
for name, data in up.items():
    zipfile.ZipFile(io.BytesIO(data)).extractall('/content/work')
    print(name, 'を /content/work に戻しました')
!ls /content/work"""),
md("""## 新しいプロジェクトを作る(1回目)
サンプルをコピーして始めるのが簡単です(名前は自由に。下の例は `myiot`)。AI に「HttpHaptic をもとに `myiot` を作って」と頼んでもかまいません。"""),
code("""!test -d /content/work/myiot || cp -r /content/work/ictex5/firmware/HttpHaptic /content/work/myiot; ls /content/work/myiot
!idf.py -C /content/work/myiot build 2>&1 | tail -3"""),
BRIDGE,
AGY_MD,
AGY_LINK,
md("""## 手で書き込む・出力を見る(AI を使わない場合)"""),
code("""!esp flash /content/work/myiot
!esp log --since-flash -n 30"""),
md("""## 作業を ZIP でダウンロードする(毎回、終わる前に必ず)
`/content/work` の中の、自分たちのファイル(ビルドの結果やサンプルの複製を除く)をまとめてダウンロードします。
班のメンバーと共有するときも、この ZIP を渡します。"""),
code("""import os, zipfile, time
from google.colab import files
skip_dirs = {'build', 'managed_components', 'ictex5', '.git', '__pycache__'}
name = time.strftime('iot-work-%Y%m%d-%H%M.zip')
with zipfile.ZipFile('/content/' + name, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, fs in os.walk('/content/work'):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in fs:
            if f in ('sdkconfig.old', 'GEMINI.md'):
                continue
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, '/content/work'))
print(name, os.path.getsize('/content/' + name) // 1024, 'KB')
files.download('/content/' + name)"""),
md("""## Raspberry Pi に送るファイルをダウンロードする
例: サーバのプログラム。PC で `scp app.py pi@<Raspberry Pi の IP アドレス>:` として送る。"""),
code("""from google.colab import files
files.download('/content/work/ictex5/server/app.py')   # 自分たちのファイルに書き換える"""),
md("""## AI 利用の記録
主な依頼・AI の変更・うまくいかなかったこと・測った結果を、ここに書いていく(個人レポートの材料)。

| 日付・時刻 | 依頼したこと | AI がしたこと | 結果・気づき |
|---|---|---|---|
| | | | |"""),
]

if __name__ == '__main__':
    save(cells, 'iot.ipynb')
