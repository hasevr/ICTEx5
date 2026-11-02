"""協調動作実験の Web サーバ(Raspberry Pi で動かす)。

ESP32(HttpHaptic)から送られてくる値を受け取って記録し、ブラウザでグラフ表示する。
ブラウザから振動の周波数を指定すると、ESP32 への応答に入れて送り返す。
Python の標準ライブラリだけで動く(Flask などのインストールは不要)。

  python3 app.py            → http://<Raspberry Pi の名前か IP アドレス>:50000/ をブラウザで開く

URL:
  /getadc?ADC=1975&TIME=12.3   ESP32 が値を送ってくる先。応答は JSON {"adc": 1975, "freq": 0.0}
  /                            グラフと周波数の入力欄
  /data.json                   記録した値(最新 N 件。?n=500)
  /data.csv                    記録した値の全件(CSV。Colab での解析用)
  /freq                        周波数の取得(GET)・設定(POST freq=200)
"""
import collections
import csv
import io
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 50000
KEEP = 5000                     # メモリに残す件数

records = collections.deque(maxlen=KEEP)   # (受信した時刻 [s], ESP32 の時刻 [s], ADC の値)
freq = 0.0                                  # ESP32 に送る周波数 [Hz]。0 は「押すたびに切り替える」
total = 0                                   # 受け取った件数の合計
t_start = time.time()
lock = threading.Lock()


def number(params, name, kind):
    """クエリのパラメータ name を kind(int か float)に変換する。無ければ None。"""
    try:
        return kind(params[name][0])
    except (KeyError, ValueError):
        return None


def getadc(params, client):
    global total
    adc = number(params, 'ADC', int)
    t_dev = number(params, 'TIME', float)
    t_srv = time.time() - t_start
    with lock:
        records.append((t_srv, t_dev, adc))
        total += 1
    print(f'{t_srv:8.3f} s  from {client}  ADC={adc}  TIME={t_dev}', flush=True)
    return {'adc': adc, 'freq': freq}


def data_json(params):
    n = number(params, 'n', int) or 500
    with lock:
        last = list(records)[-n:]
        count = total
    return {'t_server': [r[0] for r in last], 't_device': [r[1] for r in last],
            'adc': [r[2] for r in last], 'count': count, 'freq': freq}


def data_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['t_server', 't_device', 'adc'])
    with lock:
        w.writerows(records)
    return buf.getvalue()


PAGE = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>協調動作実験</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>body{font-family:sans-serif;margin:16px;max-width:900px} #st{color:#555} canvas{max-height:360px}</style>
</head><body>
<h2>ESP32 から届いた力センサの値</h2>
<p id="st">待っています…</p>
<canvas id="c"></canvas>
<h3>振動の周波数を ESP32 に送る</h3>
<form id="f">周波数 <input name="freq" size="6" value="0"> Hz <button>送る</button>
 (0 は「押すたびに切り替える」)  現在: <b id="cur">-</b> Hz</form>
<p><a href="/data.csv">記録した値を CSV でダウンロード</a></p>
<script>
const chart = new Chart(document.getElementById('c'), {type: 'line',
  data: {labels: [], datasets: [{label: 'ADC', data: [], pointRadius: 0, borderWidth: 1}]},
  options: {animation: false, scales: {x: {title: {display: true, text: '受信した時刻 [s]'}}, y: {min: 0, max: 4095}}}});
let prev = null;
async function update() {
  try {
    const d = await (await fetch('/data.json?n=500')).json();
    chart.data.labels = d.t_server.map(t => t.toFixed(1));
    chart.data.datasets[0].data = d.adc;
    chart.update();
    const now = performance.now();
    const rate = prev ? ((d.count - prev.count) / ((now - prev.t) / 1000)).toFixed(1) : '-';
    prev = {count: d.count, t: now};
    document.getElementById('st').textContent = `受信 ${d.count} 件、毎秒 ${rate} 件、最新の値 ${d.adc.at(-1) ?? '-'}`;
    document.getElementById('cur').textContent = d.freq;
  } catch (e) { document.getElementById('st').textContent = 'サーバにつながりません'; }
}
setInterval(update, 1000); update();
document.getElementById('f').onsubmit = async e => {
  e.preventDefault();
  await fetch('/freq', {method: 'POST', body: new URLSearchParams(new FormData(e.target))});
  update();
};
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'       # 接続を使い回せるようにする(keep-alive)

    def reply(self, body, ctype='application/json', extra=None):
        if not isinstance(body, (bytes, str)):
            body = json.dumps(body)
        if isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', ctype + ('; charset=utf-8' if ctype.startswith('text') else ''))
        self.send_header('Content-Length', str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        params = parse_qs(url.query)
        if url.path == '/getadc':
            self.reply(getadc(params, self.client_address[0]))
        elif url.path == '/data.json':
            self.reply(data_json(params))
        elif url.path == '/data.csv':
            self.reply(data_csv(), 'text/csv', {'Content-Disposition': 'attachment; filename=data.csv'})
        elif url.path == '/freq':
            self.reply({'freq': freq})
        elif url.path == '/':
            self.reply(PAGE, 'text/html')
        else:
            self.send_error(404)

    def do_POST(self):
        global freq
        url = urlparse(self.path)
        length = int(self.headers.get('Content-Length') or 0)
        form = parse_qs(self.rfile.read(length).decode('utf-8'))
        if url.path == '/freq':
            freq = number(form, 'freq', float) or 0.0
            print(f'freq = {freq} Hz', flush=True)
            self.reply({'freq': freq})
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        pass                            # 1 件ごとのアクセスログは出さない(getadc で表示している)


if __name__ == '__main__':
    print(f'Running on http://0.0.0.0:{PORT}/  (Ctrl+C で止める)', flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
