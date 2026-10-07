# notebooks/haptics.ipynb を生成する(編集はこのスクリプトで行う)
import json
def md(s): return {"cell_type": "markdown", "metadata": {}, "source": s}
def code(s): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s}

cells = [
md("""# 情報通信実験第5 触覚提示実験(Colab + AI)
手順は https://hasevr.github.io/ICTEx5/ を見てください。

1. 上から順にセルを実行する(「Google Drive is disabled」は OK で閉じる)。
2. 最後に出る「▶ ESP32 ブリッジを開く」を **Chrome か Edge の新しいタブ**で開き、ESP32 をつないで「ESP32 に接続」。
3. 左下の「ターミナル」で `cd /content/work && agy` として AI エージェントを起動する。"""),
code("""%%bash
# 1. ESP-IDF v5.5.1 の準備
#    インストール済みの一式(GitHub のリリース。Python 本体・cmake・ninja も同梱)を取ってきて展開する。
#    Colab の Python の版や apt のパッケージには左右されない。万一動かなければ通常のインストール(5分ほど)
set -e
T0=$(date +%s)
REL=https://github.com/hasevr/ICTEx5/releases/download/colab-esp-idf-v5.5.1-r2
export IDF_TOOLS_PATH=/content/.espressif
cd /content
full_install() {
  echo "通常のインストールを行います(5分ほど)"
  PYV=$(/usr/bin/python3 -c 'import sys;print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
  apt-get -qq update > /dev/null && apt-get -qq install -y flex bison gperf ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 python3-venv python${PYV}-venv > /dev/null
  rm -rf /content/esp-idf /content/.espressif
  git clone -q -b v5.5.1 --depth 1 --recursive --shallow-submodules https://github.com/espressif/esp-idf.git /content/esp-idf
  /content/esp-idf/install.sh esp32 > /content/idf-install.log 2>&1 || { tail -30 /content/idf-install.log; exit 1; }
  /usr/bin/python3 /content/esp-idf/tools/idf_tools.py install cmake ninja >> /content/idf-install.log 2>&1
}
if [ ! -d /content/esp-idf ]; then
  # 展開に使う zstd が無ければ入れる
  which zstd > /dev/null || apt-get -qq install -y zstd > /dev/null 2>&1 || { apt-get -qq update > /dev/null; apt-get -qq install -y zstd > /dev/null; }
  curl -sfL "$REL/esp-idf-v5.5.1-colab.tar.zst" | tar -C /content -I zstd -x || full_install
fi
# どのシェル(ターミナル・AI)からでも idf.py が使えるようにする(同梱の Python を優先。ccache は使わない)
cat > /usr/local/bin/idf.py <<'EOF'
#!/bin/bash
export IDF_TOOLS_PATH=/content/.espressif
export PATH="/content/.espressif/python/bin:$PATH"
export IDF_CCACHE_ENABLE=0
. /content/esp-idf/export.sh > /dev/null 2>&1
exec python3 "$IDF_PATH/tools/idf.py" "$@"
EOF
chmod +x /usr/local/bin/idf.py
# 取ってきたものが動かなければ、通常のインストールに切り替える
idf.py --version > /dev/null 2>&1 || { full_install; idf.py --version > /dev/null; }
echo "### ESP-IDF の準備: $(( $(date +%s) - T0 )) 秒($(idf.py --version))" """),
code("""%%bash
# 2. 実験のプロジェクトと、AI への指示ファイルを用意する
set -e
mkdir -p /content/work && cd /content/work
# ビルド済みのプロジェクト一式を取ってくる(初回ビルドが速くなる)。最新のソースは git pull で取り込む
if [ ! -d ActiveHaptic ] && [ ! -d SoftHaptics ]; then
  curl -sfL https://github.com/hasevr/ICTEx5/releases/download/colab-esp-idf-v5.5.1-r2/work-build-cache.tar.zst | tar -C /content -I zstd -x || echo "(ビルド済みのキャッシュなし。通常どおり用意します)"
fi
for p in ActiveHaptic SoftHaptics; do
  if [ -d $p/.git ]; then git -C $p pull -q --ff-only || echo "$p: git pull できませんでした(手元の版で続けます)"
  else rm -rf $p; git clone -q https://github.com/hasevr/ICTEx5$p $p; fi
done
# ファイルの中身が変わるときだけ書く(書き直すとビルドがやり直しになるため)
NEW_CMAKE='idf_component_register(SRCS "main.c"
                    INCLUDE_DIRS "."
                    REQUIRES esp_driver_uart driver spi_flash esp_adc esp_timer)'
[ "$(cat ActiveHaptic/main/CMakeLists.txt)" = "$NEW_CMAKE" ] || echo "$NEW_CMAKE" > ActiveHaptic/main/CMakeLists.txt
# SoftHaptics には sdkconfig が無いので、FreeRTOS の周期 1 kHz を既定値として与える
grep -q CONFIG_FREERTOS_HZ SoftHaptics/sdkconfig.defaults 2>/dev/null || echo 'CONFIG_FREERTOS_HZ=1000' >> SoftHaptics/sdkconfig.defaults
(curl -sfL -o AGENTS.md https://raw.githubusercontent.com/hasevr/ICTEx5/main/agent/AGENTS.md && cp AGENTS.md GEMINI.md) || echo "AGENTS.md を取得できませんでした"
# agy のログイン URL を拾う(ターミナルでは長い URL が途中で切れるため。下の「ログイン用リンク」セルで表示)
cat > /usr/local/bin/xdg-open <<'EOF'
#!/bin/sh
echo "$1" > /content/agy_url.txt
EOF
chmod +x /usr/local/bin/xdg-open
ls /content/work"""),
code("""# 3. 試しに ActiveHaptic をビルドする
!idf.py -C /content/work/ActiveHaptic build 2>&1 | tail -3"""),
code("""# 4. ESP32 ブリッジを起動する(リンクは Chrome / Edge の新しいタブで開く)
!rm -rf /content/esp-bridge && git clone -q https://github.com/hasevr/esp-bridge /content/esp-bridge
import sys; sys.path.insert(0, '/content/esp-bridge')
import esp_bridge; esp_bridge.start()"""),
md("""## AI エージェント(Antigravity CLI)
左下の「ターミナル」で次を実行し、**1. Google OAuth** を選ぶ。
```
cd /content/work && agy
```
ログイン用の URL が出たら、下のセルを実行して出るリンクから大学アカウントでログインし、表示されたコードをターミナルに貼り付ける。
「Terms of Service & Data Use」では、改善への協力のチェックを**スペースで外して** Done。"""),
code("""# ログイン用リンク(agy でログイン方法を選んだ後に実行)
import os
from IPython.display import HTML
u = open('/content/agy_url.txt').read().strip() if os.path.exists('/content/agy_url.txt') else ''
HTML(f'<a href="{u}" target="_blank" style="font-size:18px">▶ Antigravity にログイン</a>' if u else 'まだ URL がありません。ターミナルで agy を起動し、1. Google OAuth を選んでから実行してください。')"""),
md("""## 手で書き込む・出力を見る(AI を使わない場合)
AI は同じコマンドを自分で使います。"""),
code("""!esp status
!esp flash /content/work/ActiveHaptic
!esp log --since-flash -n 30"""),
md("""## AI 利用の記録
主な依頼・AI の変更・うまくいかなかったこと・触って感じたことを、ここに書いていく(レポートの材料)。
Drive に保存できないので、終わったら「ファイル → ダウンロード → .ipynb」で保存する。

| 時刻 | 依頼したこと | AI がしたこと | 触った結果・気づき |
|---|---|---|---|
| | | | |"""),
]
nb = {"cells": cells, "metadata": {"colab": {"provenance": []}, "kernelspec": {"name": "python3", "display_name": "Python 3"},
      "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 0}
json.dump(nb, open(__file__.replace('make_haptics_nb.py', 'haptics.ipynb'), 'w'), ensure_ascii=False, indent=1)
