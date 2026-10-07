#!/bin/bash
# Colab 用の「インストール済み ESP-IDF」一式を作る(GitHub のリリースに置くファイル)。
# Colab の VM(root)で実行する。Python 本体・cmake・ninja も /content/.espressif に入れるので、
# 展開した先では Colab の Python の版や apt のパッケージに左右されない。
#
#   bash build_colab_idf.sh        → /content/esp-idf-v5.5.1-colab.tar.zst と /content/work-build-cache.tar.zst
set -euo pipefail
IDF_VER=v5.5.1
PY_VER=3.13
export IDF_TOOLS_PATH=/content/.espressif
cd /content
rm -rf esp-idf .espressif work

# 1. Python 本体(python-build-standalone。場所を移しても動く)
pip -q install uv
uv python install "$PY_VER" > /dev/null
PYBIN=$(readlink -f "$(uv python find "$PY_VER")")      # リンクではなく実体の場所
PYDIR=$(dirname "$(dirname "$PYBIN")")
mkdir -p "$IDF_TOOLS_PATH"
cp -aL "$PYDIR" "$IDF_TOOLS_PATH/python"
PY="$IDF_TOOLS_PATH/python/bin/python$PY_VER"
ln -sf "python$PY_VER" "$IDF_TOOLS_PATH/python/bin/python3"
"$PY" -c 'import sys, ssl, venv; print("python", sys.version.split()[0], sys.prefix)'
case "$("$PY" -c 'import sys; print(sys.prefix)')" in /content/.espressif/python) ;; *) echo "Python が同梱先から動いていません"; exit 1;; esac
export PATH="$IDF_TOOLS_PATH/python/bin:$PATH"

# 2. ESP-IDF と、ESP32 用のツール一式(cmake・ninja も ESP-IDF 側のものを入れる)
git clone -q -b "$IDF_VER" --depth 1 --recursive --shallow-submodules https://github.com/espressif/esp-idf.git
./esp-idf/install.sh esp32 > /content/idf-install.log 2>&1 || { tail -30 /content/idf-install.log; exit 1; }
python3 esp-idf/tools/idf_tools.py install cmake ninja >> /content/idf-install.log 2>&1

# 3. どのシェルからでも使える idf.py(同梱の Python を先に置く。ccache は使わない)
cat > /usr/local/bin/idf.py <<'EOF'
#!/bin/bash
export IDF_TOOLS_PATH=/content/.espressif
export PATH="/content/.espressif/python/bin:$PATH"
export IDF_CCACHE_ENABLE=0
. /content/esp-idf/export.sh > /dev/null 2>&1
exec python3 "$IDF_PATH/tools/idf.py" "$@"
EOF
chmod +x /usr/local/bin/idf.py
idf.py --version

# 4. 配る形(.git・docs・ダウンロード済みの圧縮ファイルを除いた形)にしてから、実験のプロジェクトをビルドしておく。
#    .git の有無で ESP-IDF の版の文字列が変わり、それが全コンパイルのコマンドに入るので、先に消しておかないと
#    展開した先で全部ビルドし直しになる
cd /content
rm -rf .espressif/dist esp-idf/docs
find esp-idf -name .git -prune -exec rm -rf {} +
idf.py --version
cd /content
mkdir -p work && cd work
git clone -q https://github.com/hasevr/ICTEx5ActiveHaptic ActiveHaptic
git clone -q https://github.com/hasevr/ICTEx5SoftHaptics SoftHaptics
printf '%s\n' 'idf_component_register(SRCS "main.c"' '                    INCLUDE_DIRS "."' \
  '                    REQUIRES esp_driver_uart driver spi_flash esp_adc esp_timer)' > ActiveHaptic/main/CMakeLists.txt
echo 'CONFIG_FREERTOS_HZ=1000' >> SoftHaptics/sdkconfig.defaults
for p in ActiveHaptic SoftHaptics; do idf.py -C $p build > /content/build-$p.log 2>&1 || { tail -30 /content/build-$p.log; exit 1; }; done
grep -h "CMAKE_MAKE_PROGRAM:\|CMAKE_COMMAND:" ActiveHaptic/build/CMakeCache.txt
cd /content

# 5. 固める(zstd は Colab に入っていないことがある)
which zstd > /dev/null || apt-get -qq install -y zstd > /dev/null 2>&1 || { apt-get -qq update > /dev/null; apt-get -qq install -y zstd > /dev/null; }
tar -C /content -I 'zstd -T0 -12' -cf /content/esp-idf-$IDF_VER-colab.tar.zst esp-idf .espressif
tar -C /content -I 'zstd -T0 -12' -cf /content/work-build-cache.tar.zst work/ActiveHaptic work/SoftHaptics
ls -l /content/*.tar.zst
