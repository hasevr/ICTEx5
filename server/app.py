"""協調動作実験の Web サーバ(Raspberry Pi で動かす)。

ESP32(HttpHaptic)から送られてくる値を受け取って記録し、ブラウザでグラフ表示する。
ブラウザから振動の周波数を指定すると、ESP32 への応答に入れて送り返す。

  python3 app.py            → http://<Raspberry Pi の IP アドレス>:50000/ をブラウザで開く

URL:
  /getadc?ADC=1975&TIME=12.3   ESP32 が値を送ってくる先。応答は JSON {"adc": 1975, "freq": 0}
  /                            グラフと周波数の入力欄
  /data.json                   記録した値(最新 N 件)
  /data.csv                    記録した値の全件(CSV。Colab での解析用)
  /freq                        周波数の取得(GET)・設定(POST freq=200)
"""
import collections
import csv
import io
import time

from flask import Flask, Response, jsonify, request

PORT = 50000
KEEP = 5000                     # メモリに残す件数

app = Flask(__name__)
records = collections.deque(maxlen=KEEP)   # (受信した時刻 [s], ESP32 の時刻 [s], ADC の値)
freq = 0.0                                  # ESP32 に送る周波数 [Hz]。0 は「押すたびに切り替える」
t_start = time.time()
total = 0                                   # 受け取った件数の合計


@app.route('/getadc')
def getadc():
    global total
    adc = request.args.get('ADC', type=int)
    t_dev = request.args.get('TIME', type=float)
    t_srv = time.time() - t_start
    records.append((t_srv, t_dev, adc))
    total += 1
    print(f'{t_srv:8.3f} s  from {request.remote_addr}  ADC={adc}  TIME={t_dev}')
    return jsonify(adc=adc, freq=freq)


@app.route('/data.json')
def data_json():
    n = request.args.get('n', default=500, type=int)
    last = list(records)[-n:]
    return jsonify(t_server=[r[0] for r in last], t_device=[r[1] for r in last],
                   adc=[r[2] for r in last], count=total, freq=freq)


@app.route('/data.csv')
def data_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['t_server', 't_device', 'adc'])
    w.writerows(records)
    return Response(buf.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=data.csv'})


@app.route('/freq', methods=['GET', 'POST'])
def set_freq():
    global freq
    if request.method == 'POST':
        freq = float(request.form.get('freq', 0) or 0)
        print(f'freq = {freq} Hz')
    return jsonify(freq=freq)


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
  await fetch('/freq', {method: 'POST', body: new FormData(e.target)});
  update();
};
</script>
</body></html>"""


@app.route('/')
def index():
    return PAGE


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, threaded=True)
