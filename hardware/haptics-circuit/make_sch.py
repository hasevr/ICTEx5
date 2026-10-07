#!/usr/bin/env python3
"""触覚提示実験の回路図(KiCad 8 形式)を生成する。

ピン割り当てはファームウェア(ICTEx5ActiveHaptic の main.c)と同じ。標準記号は KiCad 8.0.9 の
ライブラリから取り出して回路図に埋め込む(KiCad 8 以降で開ける)。

  python3 make_sch.py <KiCad 8 の symbols ディレクトリ(Device.kicad_sym などがある)>
"""
import math
import os
import re
import sys
import uuid

LIBDIR = sys.argv[1] if len(sys.argv) > 1 else '.'
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = 'haptics'
NS = uuid.UUID('6f1d2a0e-4c5b-4c1e-9a77-1c7e5a5d0001')
ROOT_UUID = str(uuid.uuid5(NS, 'root'))


def uid(*k):
    return str(uuid.uuid5(NS, '/'.join(map(str, k))))


# ------------------------------------------------------------------ S 式の最小限の扱い
def extract_block(text, start):
    """text[start] が '(' のブロックを返す。"""
    depth, i, instr = 0, start, False
    while True:
        c = text[i]
        if instr:
            if c == '\\':
                i += 1
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1


def lib_symbol(libfile, name, newname=None):
    text = open(os.path.join(LIBDIR, libfile + '.kicad_sym'), encoding='utf-8').read()
    m = re.search(r'\n\t\(symbol "%s"' % re.escape(name), text)
    blk = extract_block(text, m.start() + 2)
    lib = libfile
    top = newname or name
    blk = blk.replace('(symbol "%s"' % name, '(symbol "%s:%s"' % (lib, top), 1)
    if newname:
        blk = blk.replace('(symbol "%s_' % name, '(symbol "%s_' % newname)
    return '%s:%s' % (lib, top), blk


def parse_pins(blk):
    """埋め込み記号のピン: {(unit, number): (x, y, angle, name)}(記号座標、Y 上向き)。"""
    pins = {}
    for sub in re.finditer(r'\(symbol "[^"]*_(\d+)_(\d+)"', blk):
        unit = int(sub.group(1))
        sb = extract_block(blk, sub.start())
        for pm in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', sb):
            pb = extract_block(sb, pm.start())
            num = re.search(r'\(number "([^"]*)"', pb).group(1)
            nm = re.search(r'\(name "([^"]*)"', pb).group(1)
            pins[(unit, num)] = (float(pm.group(1)), float(pm.group(2)), float(pm.group(3)), nm)
    return pins


# ------------------------------------------------------------------ 独自記号
def box_symbol(name, ref, value, left, right, width=20.32, desc=''):
    """左右にピンが並ぶ箱型の記号。left/right: [(number, name, type)]。"""
    n = max(len(left), len(right))
    h = n * 2.54 + 2.54
    top = (n - 1) * 2.54 / 2
    out = []
    out.append('(symbol "ICTEx5:%s" (exclude_from_sim no) (in_bom yes) (on_board yes)' % name)
    out.append('(property "Reference" "%s" (at 0 %.2f 0) (effects (font (size 1.27 1.27))))' % (ref, top + 3.81))
    out.append('(property "Value" "%s" (at 0 %.2f 0) (effects (font (size 1.27 1.27))))' % (value, -top - 3.81))
    out.append('(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    out.append('(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    out.append('(property "Description" "%s" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))' % desc)
    out.append('(symbol "%s_0_1" (rectangle (start %.2f %.2f) (end %.2f %.2f) (stroke (width 0.254) (type default)) (fill (type background))))'
               % (name, -width / 2, top + 2.54, width / 2, -top - 2.54))
    out.append('(symbol "%s_1_1"' % name)
    for i, (num, nm, typ) in enumerate(left):
        out.append('(pin %s line (at %.2f %.2f 0) (length 2.54) (name "%s" (effects (font (size 1.27 1.27)))) (number "%s" (effects (font (size 1.27 1.27)))))'
                   % (typ, -width / 2 - 2.54, top - i * 2.54, nm, num))
    for i, (num, nm, typ) in enumerate(right):
        out.append('(pin %s line (at %.2f %.2f 180) (length 2.54) (name "%s" (effects (font (size 1.27 1.27)))) (number "%s" (effects (font (size 1.27 1.27)))))'
                   % (typ, width / 2 + 2.54, top - i * 2.54, nm, num))
    out.append(')')   # unit 1
    out.append(')')   # symbol
    return 'ICTEx5:%s' % name, '\n'.join(out)


ESP_L = [('1', '3V3', 'passive'), ('2', 'EN', 'passive'), ('3', 'SENSOR_VP/IO36', 'passive'), ('4', 'SENSOR_VN/IO39', 'passive'),
         ('5', 'IO34', 'passive'), ('6', 'IO35', 'passive'), ('7', 'IO32', 'passive'), ('8', 'IO33', 'passive'),
         ('9', 'IO25', 'passive'), ('10', 'IO26', 'passive'), ('11', 'IO27', 'passive'), ('12', 'IO14', 'passive'),
         ('13', 'IO12', 'passive'), ('14', 'GND', 'passive'), ('15', 'IO13', 'passive'), ('16', 'SD2', 'passive'),
         ('17', 'SD3', 'passive'), ('18', 'CMD', 'passive'), ('19', '5V', 'passive')]
ESP_R = [('20', 'GND', 'passive'), ('21', 'IO23', 'passive'), ('22', 'IO22', 'passive'), ('23', 'TXD0', 'passive'),
         ('24', 'RXD0', 'passive'), ('25', 'IO21', 'passive'), ('26', 'GND', 'passive'), ('27', 'IO19', 'passive'),
         ('28', 'IO18', 'passive'), ('29', 'IO5', 'passive'), ('30', 'IO17', 'passive'), ('31', 'IO16', 'passive'),
         ('32', 'IO4', 'passive'), ('33', 'IO0', 'passive'), ('34', 'IO2', 'passive'), ('35', 'IO15', 'passive'),
         ('36', 'SD1', 'passive'), ('37', 'SD0', 'passive'), ('38', 'CLK', 'passive')]
# SparkFun TB6612FNG ブレークアウト(ピン番号は基板の並び。1-8 が入力側、9-16 が出力側)
TB_L = [('4', 'STBY', 'input'), ('1', 'PWMA', 'input'), ('3', 'AIN1', 'input'), ('2', 'AIN2', 'input'),
        ('7', 'PWMB', 'input'), ('5', 'BIN1', 'input'), ('6', 'BIN2', 'input'), ('8', 'GND', 'power_in')]
TB_R = [('9', 'VM', 'power_in'), ('10', 'VCC', 'power_in'), ('12', 'AO1', 'output'), ('13', 'AO2', 'output'),
        ('15', 'BO1', 'output'), ('14', 'BO2', 'output'), ('11', 'GND', 'passive'), ('16', 'GND', 'passive')]


# ------------------------------------------------------------------ 回路図の組み立て
class Sch:
    def __init__(self):
        self.libs = {}       # lib_id -> (block, pins)
        self.items = []
        self.npwr = 0

    def add_lib(self, lib_id, blk):
        self.libs[lib_id] = (blk, parse_pins(blk))

    def pin_point(self, comp, unit, num):
        lib_id, x, y, rot = comp['lib_id'], comp['x'], comp['y'], comp['rot']
        px, py, pa, _ = self.libs[lib_id][1].get((unit, num)) or self.libs[lib_id][1][(0, num)]
        r = math.radians(rot)
        # 記号座標(Y 上)→ 回路図座標(Y 下)。回転は画面上で反時計回り
        sx = px * math.cos(r) - py * math.sin(r)
        sy = px * math.sin(r) + py * math.cos(r)
        ang = (pa + rot) % 360
        # ピンの向き(接続点から本体へ)を回路図座標で。外向きはその逆
        bx, by = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
        return round(x + sx, 2), round(y - sy, 2), (-round(bx), -round(by))

    def symbol(self, lib_id, ref, value, x, y, rot=0, unit=1, fields=None, show_value=True, ref_off=(0, -5.08), val_off=(0, 5.08)):
        blk, pins = self.libs[lib_id]
        nums = sorted({n for (u, n) in pins if u in (0, unit)}, key=lambda s: (len(s), s))
        props = [('Reference', ref, ref_off, ref.startswith('#')), ('Value', value, val_off, not show_value),
                 ('Footprint', '', (0, 0), True), ('Datasheet', '', (0, 0), True), ('Description', '', (0, 0), True)]
        for k, v in (fields or {}).items():
            props.append((k, v, (0, 0), True))
        s = ['(symbol (lib_id "%s") (at %.2f %.2f %d) (unit %d) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)'
             % (lib_id, x, y, rot, unit)]
        s.append('(uuid "%s")' % uid('sym', ref, unit))
        for k, v, (ox, oy), hide in props:
            s.append('(property "%s" "%s" (at %.2f %.2f %d) (effects (font (size 1.27 1.27))%s))'
                     % (k, v, x + ox, y + oy, rot if rot in (90, 270) and not lib_id.startswith('power:') else 0, ' (hide yes)' if hide else ''))
        for n in nums:
            s.append('(pin "%s" (uuid "%s"))' % (n, uid('pin', ref, unit, n)))
        s.append('(instances (project "%s" (path "/%s" (reference "%s") (unit %d))))' % (PROJECT, ROOT_UUID, ref, unit))
        s.append(')')
        self.items.append('\n'.join(s))
        return {'lib_id': lib_id, 'x': x, 'y': y, 'rot': rot, 'unit': unit, 'ref': ref}

    def wire(self, x1, y1, x2, y2):
        self.items.append('(wire (pts (xy %.2f %.2f) (xy %.2f %.2f)) (stroke (width 0) (type default)) (uuid "%s"))'
                          % (x1, y1, x2, y2, uid('w', x1, y1, x2, y2)))

    def label(self, name, x, y, d):
        # 線の端に置くラベル。文字は外向きに
        ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[d]
        just = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[ang]
        self.items.append('(label "%s" (at %.2f %.2f %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s"))'
                          % (name, x, y, ang, just, uid('l', name, x, y)))

    def power(self, net, x, y, d):
        self.npwr += 1
        lib = 'power:' + net
        if net == '+3V3':
            rot = {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[d]
        else:  # GND: 記号は下向き
            rot = {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[d]
        self.symbol(lib, '#PWR%02d' % self.npwr, net, x, y, rot, ref_off=(0, 6.35), val_off=(0, 3.81) if net == 'GND' else (0, -3.81))

    def pp(self, comp, num):
        x, y, _ = self.pin_point(comp, comp['unit'], num)
        return (x, y)

    def wires(self, *pts):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if (x1, y1) != (x2, y2):
                self.wire(x1, y1, x2, y2)

    def junction(self, x, y):
        self.items.append('(junction (at %.2f %.2f) (diameter 0) (color 0 0 0 0) (uuid "%s"))' % (x, y, uid('j', x, y)))

    def nc(self, x, y):
        self.items.append('(no_connect (at %.2f %.2f) (uuid "%s"))' % (x, y, uid('nc', x, y)))

    def text(self, s, x, y, size=1.27):
        s = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        self.items.append('(text "%s" (exclude_from_sim no) (at %.2f %.2f 0) (effects (font (size %.2f %.2f)) (justify left top)) (uuid "%s"))'
                          % (s, x, y, size, size, uid('t', x, y)))

    def connect_elbow(self, comp, num, net):
        x, y, d = self.pin_point(comp, comp['unit'], num)
        ex = round(x + d[0] * 2.54, 2)
        up = (0, -1) if net == '+3V3' else (0, 1)
        ey = round(y + up[1] * 2.54, 2)
        self.wires((x, y), (ex, y), (ex, ey))
        self.power(net, ex, ey, up)

    def connect(self, comp, num, net, stub=5.08, unit=None):
        """ピンから外向きに短い線を出し、その先にラベルか電源記号を置く。net=None は未接続。"""
        x, y, d = self.pin_point(comp, unit or comp['unit'], num)
        if net is None:
            self.nc(x, y)
            return
        ex, ey = round(x + d[0] * stub, 2), round(y + d[1] * stub, 2)
        self.wire(x, y, ex, ey)
        if net in ('+3V3', 'GND'):
            self.power(net, ex, ey, d)
        else:
            self.label(net, ex, ey, d)

    def write(self, path, title, comment):
        hdr = ['(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")',
               '(uuid "%s")' % ROOT_UUID, '(paper "A4")',
               '(title_block (title "%s") (date "2026-10-06") (rev "1") (company "情報通信実験第5")%s)'
               % (title, ' (comment 1 "%s")' % comment if comment else ''),
               '(lib_symbols']
        hdr += [blk for blk, _ in self.libs.values()]
        hdr.append(')')
        body = hdr + self.items + ['(sheet_instances (path "/" (page "1")))', ')']
        open(path, 'w', encoding='utf-8').write('\n'.join(body) + '\n')


def main():
    s = Sch()
    for lib, name, new in [('Device', 'R', None), ('Device', 'R_Potentiometer', None), ('Device', 'R_Variable', None),
                           ('Amplifier_Operational', 'LM2902', None), ('Motor', 'Motor_DC', None),
                           ('power', '+3V3', None), ('power', 'GND', None), ('power', 'PWR_FLAG', None)]:
        s.add_lib(*lib_symbol(lib, name, new))
    s.add_lib(*box_symbol('ESP32-DevKitC', 'U', 'ESP32-DevKitC', ESP_L, ESP_R, width=25.4,
                          desc='Espressif ESP32-DevKitC (ESP32-WROOM-32)'))
    s.add_lib(*box_symbol('TB6612FNG_Breakout', 'U', 'TB6612FNG Breakout', TB_L, TB_R, width=17.78,
                          desc='SparkFun TB6612FNG motor driver breakout'))
    W, J, P = s.wires, s.junction, s.pp

    # ---------------------------------------------------------------- ESP32(左)
    esp = s.symbol('ICTEx5:ESP32-DevKitC', 'U3', 'ESP32-DevKitC', 60.96, 101.6, ref_off=(0, -29.21), val_off=(0, 29.21))
    used = {'1': '+3V3', '14': 'GND', '5': 'ADC_OUT', '29': 'AIN1', '30': 'AIN2', '31': 'PWMA', '20': 'GND', '26': 'GND'}
    for num, _, _ in ESP_L + ESP_R:
        if used.get(num) in ('+3V3', 'GND'):
            s.connect_elbow(esp, num, used[num])
        else:
            s.connect(esp, num, used.get(num))

    # ---------------------------------------------------------------- センサアンプ(中央上)
    opa = 'Amplifier_Operational:LM2902'
    ud = s.symbol(opa, 'U1', 'NJU7044D', 167.64, 58.42, unit=4, ref_off=(2.54, -6.35), val_off=(2.54, -3.81))
    pin_p, pin_n, pout = P(ud, '12'), P(ud, '13'), P(ud, '14')
    # VREF 分圧(R1・R2)→ +入力
    nx, ny = pin_p[0] - 30.48, pin_p[1]
    r1 = s.symbol('Device:R', 'R1', '1k', nx, ny - 7.62, ref_off=(2.54, -1.27), val_off=(2.54, 1.27))
    r2 = s.symbol('Device:R', 'R2', '1k', nx, ny + 7.62, ref_off=(2.54, -1.27), val_off=(2.54, 1.27))
    W(P(r1, '2'), (nx, ny)); W(P(r2, '1'), (nx, ny)); W((nx, ny), pin_p); J(nx, ny)
    s.label('VREF', nx + 5.08, ny, (1, 0))
    s.connect(r1, '1', '+3V3', stub=2.54)
    s.connect(r2, '2', 'GND', stub=2.54)
    # −入力の節点: FSR(R4)を GND へ、RV1 を出力へ(帰還)
    mx, my = pin_n[0] - 7.62, pin_n[1]
    W(pin_n, (mx, my)); J(mx, my)
    fx = mx - 10.16                                  # FSR は節点の左に吊るす
    fsr = s.symbol('Device:R_Variable', 'R4', 'FSR400', fx, my + 7.62, ref_off=(-6.35, -1.27), val_off=(-6.35, 1.27))
    W((mx, my), (fx, my), P(fsr, '1'))
    s.connect(fsr, '2', 'GND', stub=2.54)
    fy = my + 12.7                                   # 帰還経路の高さ(アンプの下)
    rv = s.symbol('Device:R_Potentiometer', 'RV1', '10k (T103)', pin_n[0] + 10.16, fy, rot=90, ref_off=(0, 5.08), val_off=(0, 7.62))
    a, b, w = P(rv, '1'), P(rv, '3'), P(rv, '2')
    left, right = (a, b) if a[0] < b[0] else (b, a)
    ox = pout[0] + 5.08                              # 出力の節点
    W((mx, my), (mx, fy), left)                      # −入力の節点 → RV1 の左端
    W(right, (ox, right[1]), (ox, pout[1]), pout)    # RV1 の右端 → 出力
    wy = w[1] + 2.54 if w[1] > fy else w[1] - 2.54   # ワイパーを右端(出力)につなぐ
    W(w, (w[0], wy), (ox, wy), (ox, right[1]))
    J(ox, right[1]); J(ox, pout[1])
    W((ox, pout[1]), (ox + 7.62, pout[1])); s.label('ADC_OUT', ox + 7.62, pout[1], (1, 0))
    # 電源(E 回路)と未使用の A・B・C 回路(右)
    upw = s.symbol(opa, 'U1', 'NJU7044D', 223.52, 58.42, unit=5, ref_off=(3.81, -1.27), val_off=(3.81, 1.27))
    s.connect(upw, '4', '+3V3', stub=2.54)
    s.connect(upw, '11', 'GND', stub=2.54)
    for i, (u, ins, out) in enumerate([(1, ('3', '2'), '1'), (2, ('5', '6'), '7'), (3, ('10', '9'), '8')]):
        c = s.symbol(opa, 'U1', 'NJU7044D', 254.0, 50.8 + i * 15.24, unit=u, ref_off=(0, -6.35), val_off=(0, 6.35), show_value=False)
        for n in ins + (out,):
            s.connect(c, n, None)

    # ---------------------------------------------------------------- モータードライバ(中央下)
    tb = s.symbol('ICTEx5:TB6612FNG_Breakout', 'U2', 'TB6612FNG Breakout', 162.56, 137.16, ref_off=(0, -13.97), val_off=(0, 13.97))
    for num, net in {'1': 'PWMA', '2': 'AIN2', '3': 'AIN1', '5': None, '6': None, '7': None, '14': None, '15': None}.items():
        s.connect(tb, num, net)
    # STBY → +3V3、左下の GND
    s.connect_elbow(tb, '4', '+3V3')
    s.connect_elbow(tb, '8', 'GND')
    # VM・VCC をまとめて +3V3
    vm, vcc = P(tb, '9'), P(tb, '10')
    bx = vm[0] + 5.08
    W(vm, (bx, vm[1])); W(vcc, (bx, vcc[1])); W((bx, vcc[1]), (bx, vm[1])); J(bx, vm[1])
    W((bx, vm[1]), (bx, vm[1] - 5.08)); s.power('+3V3', bx, vm[1] - 5.08, (0, -1))
    # 右下の GND 2本をまとめて GND
    g1, g2 = P(tb, '11'), P(tb, '16')
    W(g1, (bx, g1[1])); W(g2, (bx, g2[1])); W((bx, g1[1]), (bx, g2[1])); J(bx, g2[1])
    W((bx, g2[1]), (bx, g2[1] + 5.08)); s.power('GND', bx, g2[1] + 5.08, (0, 1))
    # AO1 → R3(4.7 Ω)→ M1 → AO2
    ao1, ao2 = P(tb, '12'), P(tb, '13')
    r3 = s.symbol('Device:R', 'R3', '4.7', ao1[0] + 17.78, ao1[1], rot=90, ref_off=(0, -3.81), val_off=(0, -1.905 + 4.445))
    W(ao1, P(r3, '1' if P(r3, '1')[0] < P(r3, '2')[0] else '2'))
    r3r = max(P(r3, '1'), P(r3, '2'))
    mxm = r3r[0] + 7.62
    m1 = s.symbol('Motor:Motor_DC', 'M1', 'Motor_DC', mxm, ao1[1] + 10.16, ref_off=(5.08, -1.27), val_off=(5.08, 1.27))
    m_top, m_bot = sorted([P(m1, '1'), P(m1, '2')], key=lambda p: p[1])
    W(r3r, (mxm, r3r[1])); W((mxm, r3r[1]), m_top)
    rx = ao2[0] + 10.16
    W(m_bot, (mxm, m_bot[1] + 2.54)); W((mxm, m_bot[1] + 2.54), (rx, m_bot[1] + 2.54))
    W((rx, m_bot[1] + 2.54), (rx, ao2[1])); W((rx, ao2[1]), ao2)

    # 電源フラグ(ESP32 の 3V3 出力と GND を電源として扱う)
    for i, net in enumerate(['+3V3', 'GND']):
        x0, y0 = 101.6 + i * 20.32, 154.94
        s.power(net, x0, y0, (0, -1) if net == '+3V3' else (0, 1))
        s.wires((x0, y0), (x0 + 7.62, y0))
        s.symbol('power:PWR_FLAG', '#FLG%02d' % (i + 1), 'PWR_FLAG', x0 + 7.62, y0, ref_off=(0, -6.35), val_off=(0, -3.81))

    # ---------------------------------------------------------------- 注記
    s.text('触覚提示実験の回路(入出力部)\n'
           'ESP32 の 3V3 出力(USB から)で全体を動かす。+3V3 と GND はブレッドボードの + / − 列。', 20.32, 15.24, 2.0)
    s.text('センサアンプ(U1 の D 回路)\n'
           'VREF = 3.3 V × R2/(R1+R2) = 1.65 V\n'
           'ADC_OUT = VREF × (1 + RV1/R4)\n'
           '押していない(R4 = FSR ≒ ∞)とき ADC_OUT ≒ 1.65 V(ADC 値 1600〜2000)。\n'
           '押すと FSR の抵抗が下がって ADC_OUT が上がる。\n'
           'RV1 で感度を調整(押したとき約 2500)。RV1 は可変抵抗として使用。', 101.6, 88.9, 1.27)
    s.text('モータ駆動(U2)\n'
           'IO5 → AIN1、IO17 → AIN2 に 50 kHz の PWM(bdc_motor)。\n'
           'IO16 → PWMA は常に High。STBY・VM・VCC は 3.3 V。\n'
           'モータと直列の 4.7 Ω(R3)で電流を制限する。', 101.6, 114.3, 1.27)
    s.text('補足\n'
           '・JTAG デバッガ(FT232H、緑の基板)の配線は省略。ESP32 の IO12=TDI、IO13=TCK、IO14=TMS、IO15=TDO と GND につながる。\n'
           '・U1 の A・B・C 回路は使わない。', 20.32, 167.64, 1.27)

    s.write(os.path.join(HERE, PROJECT + '.kicad_sch'), '触覚提示実験 回路図(ActiveHaptic / SoftHaptics)', '')
    own = [blk.replace('(symbol "ICTEx5:', '(symbol "', 1) for lid, (blk, _) in s.libs.items() if lid.startswith('ICTEx5:')]
    open(os.path.join(HERE, 'ICTEx5.kicad_sym'), 'w', encoding='utf-8').write(
        '(kicad_symbol_lib (version 20231120) (generator "make_sch.py")\n' + '\n'.join(own) + '\n)\n')
    open(os.path.join(HERE, 'sym-lib-table'), 'w').write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "ICTEx5")(type "KiCad")(uri "${KIPRJMOD}/ICTEx5.kicad_sym")(options "")(descr "情報通信実験第5 の独自記号"))\n)\n')
    open(os.path.join(HERE, PROJECT + '.kicad_pro'), 'w').write('{\n  "meta": {\n    "filename": "%s.kicad_pro",\n    "version": 1\n  }\n}\n' % PROJECT)


if __name__ == '__main__':
    main()
