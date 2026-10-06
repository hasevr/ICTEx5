# 触覚提示実験の回路図(KiCad)

完成品の写真とファームウェア([ICTEx5ActiveHaptic](https://github.com/hasevr/ICTEx5ActiveHaptic) の `main.c`)から
起こした回路図です(元の回路図は残っていません)。

| ファイル | 内容 |
|---|---|
| `haptics.kicad_pro` / `haptics.kicad_sch` | KiCad 8 形式(KiCad 8・9 以降で開ける)。記号は回路図に埋め込み済み |
| `ICTEx5.kicad_sym` / `sym-lib-table` | 独自記号(ESP32-DevKitC、TB6612FNG ブレークアウト)のライブラリ |
| `haptics.pdf` / `haptics.svg` | 印刷・表示用 |
| `make_sch.py` | 回路図を生成するスクリプト(KiCad 8.0.9 の標準記号ライブラリを読む) |

KiCad 9.0.9 の `kicad-cli sch erc` でエラー 0 を確認済み(警告は標準ライブラリ未登録の環境で出るものだけ)。

## 確認事項

- **R4(力センサ FSR400)の、オペアンプにつながらない側の端子**は、写真では電源レールの + / − のどちらの列か
  確定できなかった。ファームウェアが「押すと ADC の値が上がる」前提であることから **GND** とした
  (+3V3 につなぐと、押すと値が下がる)。
- JTAG デバッガ(FT232H)の配線は省略。ESP32 の IO12=TDI、IO13=TCK、IO14=TMS、IO15=TDO と GND につながる。
- NJU7044D の A・B・C 回路は実物でも未接続。
- TB6612FNG ブレークアウトのピン番号は、基板の並び(入力側 1〜8: PWMA, AIN2, AIN1, STBY, BIN1, BIN2, PWMB, GND、
  出力側 9〜16: VM, VCC, GND, AO1, AO2, BO2, BO1, GND)。
