# 触覚提示実験の回路図(KiCad)

| ファイル | 内容 |
|---|---|
| `haptics.kicad_pro` / `haptics.kicad_sch` | KiCad 8 形式(KiCad 8・9 以降で開ける)。記号は回路図に埋め込み済み |
| `ICTEx5.kicad_sym` / `sym-lib-table` | 独自記号(ESP32-DevKitC、TB6612FNG ブレークアウト)のライブラリ |
| `haptics.pdf` / `haptics.svg` | 印刷・表示用 |
| `make_sch.py` | 回路図を生成するスクリプト(KiCad 8.0.9 の標準記号ライブラリを読む) |

ピン割り当てはファームウェア([ICTEx5ActiveHaptic](https://github.com/hasevr/ICTEx5ActiveHaptic) の `main.c`)と同じです。

- 力センサ(R4、FSR400)→ オペアンプ NJU7044D の D 回路 → ESP32 の IO34(ADC1 チャンネル6)。
  `ADC_OUT = 1.65 V × (1 + RV1 / R4)`。
- モータードライバ TB6612FNG: IO5 → AIN1、IO17 → AIN2(50 kHz PWM)、IO16 → PWMA(常に High)。
  STBY・VM・VCC は 3.3 V。モータは AO1・AO2 の間に 4.7 Ω(R3)と直列。
- JTAG デバッガ(FT232H)の配線は省略。ESP32 の IO12=TDI、IO13=TCK、IO14=TMS、IO15=TDO と GND につながる。
- TB6612FNG ブレークアウトのピン番号は基板の並び(入力側 1〜8: PWMA, AIN2, AIN1, STBY, BIN1, BIN2, PWMB, GND、
  出力側 9〜16: VM, VCC, GND, AO1, AO2, BO2, BO1, GND)。
