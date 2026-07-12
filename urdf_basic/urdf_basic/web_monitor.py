import json
import os
import subprocess
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

CART_JOINT = 'slider_joint'
POLE_JOINT = 'pole_joint'
BUFFER_LEN = 2000
DECIMATION = 10  # gazebo publishes at ~1 kHz; keep every 10th sample

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cart-Pole Web Monitor</title>
<style>
  :root {
    --surface-1: #fcfcfb;
    --page: #f9f9f7;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --text-muted: #898781;
    --grid: #e1e0d9;
    --axis: #c3c2b7;
    --border: rgba(11,11,11,0.10);
    --cart: #2a78d6;
    --pole: #e34948;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --surface-1: #1a1a19;
      --page: #0d0d0d;
      --text-primary: #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted: #898781;
      --grid: #2c2c2a;
      --axis: #383835;
      --border: rgba(255,255,255,0.10);
      --cart: #3987e5;
      --pole: #e66767;
    }
  }
  * { box-sizing: border-box; margin: 0; }
  body {
    background: var(--page);
    color: var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 16px;
  }
  header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px; }
  header h1 { font-size: 18px; font-weight: 600; }
  #status { font-size: 13px; color: var(--text-muted); }
  #reset-btn {
    margin-left: auto;
    font: 600 13px system-ui, -apple-system, "Segoe UI", sans-serif;
    color: var(--text-primary);
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 5px 14px;
    cursor: pointer;
  }
  #reset-btn:hover { border-color: var(--text-muted); }
  #reset-btn:disabled { opacity: 0.5; cursor: wait; }
  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    max-width: 1100px;
  }
  @media (max-width: 760px) {
    .grid { grid-template-columns: 1fr; }
  }
  .card {
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 12px 6px;
  }
  .card-head { display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }
  .chip { width: 10px; height: 10px; border-radius: 3px; flex: none; align-self: center; }
  .card-title { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
  .readout {
    margin-left: auto;
    font-size: 13px;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
  }
  canvas { width: 100%; height: 180px; display: block; cursor: crosshair; }
  .scene-card { grid-column: 1 / -1; }
  #scene { height: 300px; cursor: default; }
</style>
</head>
<body>
<header>
  <h1>Cart-Pole Web Monitor</h1>
  <span id="status">waiting for /joint_states&hellip;</span>
  <button id="reset-btn" title="Respawn the cart-pole at its initial pose">Reset</button>
</header>
<div class="grid" id="charts">
  <div class="card scene-card">
    <div class="card-head">
      <span class="card-title">Cart-Pole 2D View (x&ndash;z plane)</span>
      <span class="readout" id="scene-readout">&ndash;</span>
    </div>
    <canvas id="scene"></canvas>
  </div>
</div>

<script>
'use strict';

const SERIES = [
  {key: 'cart_pos', title: 'Cart Position [m]',            entity: 'cart', unit: 'm'},
  {key: 'cart_vel', title: 'Cart Velocity [m/s]',          entity: 'cart', unit: 'm/s'},
  {key: 'pole_pos', title: 'Pole Angle [rad]',             entity: 'pole', unit: 'rad'},
  {key: 'pole_vel', title: 'Pole Angular Velocity [rad/s]', entity: 'pole', unit: 'rad/s'},
];
const MARGIN = {top: 8, right: 12, bottom: 22, left: 48};

// scene geometry mirrors cartpole.urdf (metres)
const SCENE = {
  railY: 1.0, railHalf: 1.0,
  cartW: 0.2, cartH: 0.15,
  pivotDy: 0.075, poleLen: 0.5, poleR: 0.02,
  poleTilt: 0.2618,  // initial tilt baked into the pole_joint origin
  xMin: -1.55, xMax: 1.55, zMin: 0.25, zMax: 1.85,
};
const RENDER_LAG = 0.35;  // s behind the newest sample, so we interpolate not extrapolate

let data = {t: [], cart_pos: [], cart_vel: [], pole_pos: [], pole_vel: []};
let hoverT = null;  // sim time under the cursor, shared by all charts
let lastPollWall = 0;  // performance.now() when the newest sample arrived
const charts = [];

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function makeCard(series) {
  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML =
    '<div class="card-head">' +
    '  <span class="chip"></span>' +
    '  <span class="card-title"></span>' +
    '  <span class="readout">&ndash;</span>' +
    '</div>';
  card.querySelector('.card-title').textContent = series.title;
  const canvas = document.createElement('canvas');
  card.appendChild(canvas);
  document.getElementById('charts').appendChild(card);

  canvas.addEventListener('mousemove', (ev) => {
    const rect = canvas.getBoundingClientRect();
    const chart = charts.find((c) => c.canvas === canvas);
    hoverT = chart ? chart.xFromPixel(ev.clientX - rect.left) : null;
    drawAll();
  });
  canvas.addEventListener('mouseleave', () => { hoverT = null; drawAll(); });

  return {
    series: series,
    canvas: canvas,
    chip: card.querySelector('.chip'),
    readout: card.querySelector('.readout'),
    scale: null,
    xFromPixel(px) {
      if (!this.scale) return null;
      const s = this.scale;
      return s.t0 + (px - MARGIN.left) / s.xs;
    },
  };
}

function niceTicks(lo, hi, n) {
  if (!(hi > lo)) { hi = lo + 1; }
  const span = hi - lo;
  const step0 = span / Math.max(1, n);
  const mag = Math.pow(10, Math.floor(Math.log10(step0)));
  let step = mag;
  for (const m of [1, 2, 5, 10]) {
    if (step0 <= m * mag) { step = m * mag; break; }
  }
  const ticks = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-6; v += step) {
    ticks.push(v);
  }
  return ticks;
}

function fmt(v) {
  const a = Math.abs(v);
  if (a >= 100) return v.toFixed(0);
  if (a >= 1) return v.toFixed(2);
  return v.toFixed(3);
}

function drawChart(chart) {
  const canvas = chart.canvas;
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
    canvas.width = w * dpr;
    canvas.height = h * dpr;
  }
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);

  const color = cssVar(chart.series.entity === 'cart' ? '--cart' : '--pole');
  chart.chip.style.background = color;

  const t = data.t;
  const y = data[chart.series.key];
  const plotW = w - MARGIN.left - MARGIN.right;
  const plotH = h - MARGIN.top - MARGIN.bottom;
  ctx.font = '11px system-ui, sans-serif';

  if (t.length < 2) {
    ctx.fillStyle = cssVar('--text-muted');
    ctx.textAlign = 'center';
    ctx.fillText('no data', w / 2, h / 2);
    chart.scale = null;
    return;
  }

  const t0 = t[0], t1 = t[t.length - 1];
  let yLo = Math.min(...y), yHi = Math.max(...y);
  const pad = (yHi - yLo) * 0.1 || 0.1;
  yLo -= pad; yHi += pad;
  const xs = plotW / Math.max(t1 - t0, 1e-9);
  const ys = plotH / (yHi - yLo);
  chart.scale = {t0: t0, xs: xs};
  const X = (tv) => MARGIN.left + (tv - t0) * xs;
  const Y = (yv) => MARGIN.top + (yHi - yv) * ys;

  // hairline grid + tick labels (muted ink)
  ctx.lineWidth = 1;
  ctx.strokeStyle = cssVar('--grid');
  ctx.fillStyle = cssVar('--text-muted');
  for (const ty of niceTicks(yLo, yHi, 4)) {
    ctx.beginPath();
    ctx.moveTo(MARGIN.left, Y(ty));
    ctx.lineTo(w - MARGIN.right, Y(ty));
    ctx.stroke();
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(fmt(ty), MARGIN.left - 6, Y(ty));
  }
  for (const tx of niceTicks(t0, t1, 5)) {
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(fmt(tx), X(tx), h - MARGIN.bottom + 6);
  }

  // baseline axis
  ctx.strokeStyle = cssVar('--axis');
  ctx.beginPath();
  ctx.moveTo(MARGIN.left, h - MARGIN.bottom);
  ctx.lineTo(w - MARGIN.right, h - MARGIN.bottom);
  ctx.stroke();

  // 2px data line
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  for (let i = 0; i < t.length; i++) {
    if (i === 0) ctx.moveTo(X(t[i]), Y(y[i]));
    else ctx.lineTo(X(t[i]), Y(y[i]));
  }
  ctx.stroke();

  // crosshair synced across charts + hovered value in the readout
  let shownIdx = t.length - 1;
  if (hoverT !== null && hoverT >= t0 && hoverT <= t1) {
    let idx = t.findIndex((tv) => tv >= hoverT);
    if (idx < 0) idx = t.length - 1;
    shownIdx = idx;
    ctx.strokeStyle = cssVar('--axis');
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(X(t[idx]), MARGIN.top);
    ctx.lineTo(X(t[idx]), h - MARGIN.bottom);
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(X(t[idx]), Y(y[idx]), 4, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = cssVar('--surface-1');
    ctx.lineWidth = 2;
    ctx.stroke();
  }
  chart.readout.textContent =
    fmt(y[shownIdx]) + ' ' + chart.series.unit + ' @ ' + t[shownIdx].toFixed(2) + ' s';
}

function drawAll() {
  for (const chart of charts) drawChart(chart);
}

// --- 2D scene animation ---------------------------------------------------

const sceneCanvas = document.getElementById('scene');
const sceneReadout = document.getElementById('scene-readout');

function sampleAt(tq) {
  const t = data.t;
  if (!t.length) return null;
  if (tq <= t[0]) return {cart: data.cart_pos[0], pole: data.pole_pos[0]};
  const n = t.length - 1;
  if (tq >= t[n]) return {cart: data.cart_pos[n], pole: data.pole_pos[n]};
  let lo = 0, hi = n;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (t[mid] <= tq) lo = mid; else hi = mid;
  }
  const a = (tq - t[lo]) / (t[hi] - t[lo] || 1e-9);
  return {
    cart: data.cart_pos[lo] + a * (data.cart_pos[hi] - data.cart_pos[lo]),
    pole: data.pole_pos[lo] + a * (data.pole_pos[hi] - data.pole_pos[lo]),
  };
}

function drawScene(sample) {
  const dpr = window.devicePixelRatio || 1;
  const w = sceneCanvas.clientWidth;
  const h = sceneCanvas.clientHeight;
  if (sceneCanvas.width !== w * dpr || sceneCanvas.height !== h * dpr) {
    sceneCanvas.width = w * dpr;
    sceneCanvas.height = h * dpr;
  }
  const ctx = sceneCanvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);

  // metre -> pixel, aspect preserved, y flipped
  const s = Math.min(w / (SCENE.xMax - SCENE.xMin), h / (SCENE.zMax - SCENE.zMin));
  const ox = (w - s * (SCENE.xMax - SCENE.xMin)) / 2;
  const oy = (h - s * (SCENE.zMax - SCENE.zMin)) / 2;
  const X = (wx) => ox + (wx - SCENE.xMin) * s;
  const Y = (wz) => h - oy - (wz - SCENE.zMin) * s;

  // rail with end stops
  ctx.strokeStyle = cssVar('--axis');
  ctx.lineWidth = Math.max(2, SCENE.poleR * 2 * s);
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(X(-SCENE.railHalf), Y(SCENE.railY));
  ctx.lineTo(X(SCENE.railHalf), Y(SCENE.railY));
  ctx.stroke();
  ctx.lineWidth = 2;
  for (const ex of [-SCENE.railHalf, SCENE.railHalf]) {
    ctx.beginPath();
    ctx.moveTo(X(ex), Y(SCENE.railY - 0.08));
    ctx.lineTo(X(ex), Y(SCENE.railY + 0.08));
    ctx.stroke();
  }

  if (!sample) {
    ctx.fillStyle = cssVar('--text-muted');
    ctx.font = '11px system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('no data', w / 2, Y(SCENE.railY + 0.4));
    sceneReadout.textContent = '–';
    return;
  }

  const cartColor = cssVar('--cart');
  const poleColor = cssVar('--pole');
  const px = sample.cart;                       // cart centre x
  const phi = SCENE.poleTilt + sample.pole;     // pole angle from vertical (+z)
  const pivX = px;
  const pivZ = SCENE.railY + SCENE.pivotDy;
  const tipX = pivX + SCENE.poleLen * Math.sin(phi);
  const tipZ = pivZ + SCENE.poleLen * Math.cos(phi);

  // cart (side view of the cylinder = rounded rectangle)
  ctx.fillStyle = cartColor;
  ctx.beginPath();
  ctx.roundRect(X(px - SCENE.cartW / 2), Y(SCENE.railY + SCENE.cartH / 2),
                SCENE.cartW * s, SCENE.cartH * s, 4);
  ctx.fill();

  // pole with a 2px surface ring so it separates from the cart
  ctx.lineCap = 'round';
  ctx.strokeStyle = cssVar('--surface-1');
  ctx.lineWidth = SCENE.poleR * 2 * s + 4;
  ctx.beginPath();
  ctx.moveTo(X(pivX), Y(pivZ));
  ctx.lineTo(X(tipX), Y(tipZ));
  ctx.stroke();
  ctx.strokeStyle = poleColor;
  ctx.lineWidth = SCENE.poleR * 2 * s;
  ctx.beginPath();
  ctx.moveTo(X(pivX), Y(pivZ));
  ctx.lineTo(X(tipX), Y(tipZ));
  ctx.stroke();

  // pivot
  ctx.fillStyle = cssVar('--text-primary');
  ctx.beginPath();
  ctx.arc(X(pivX), Y(pivZ), 3, 0, 2 * Math.PI);
  ctx.fill();

  const deg = (phi * 180 / Math.PI) % 360;
  sceneReadout.textContent =
    'cart ' + fmt(px) + ' m · pole ' + deg.toFixed(1) + '° from vertical';
}

function animate(now) {
  if (data.t.length >= 2) {
    const tq = data.t[data.t.length - 1] + (now - lastPollWall) / 1000 - RENDER_LAG;
    drawScene(sampleAt(tq));
  } else {
    drawScene(null);
  }
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);

for (const series of SERIES) charts.push(makeCard(series));

async function poll() {
  try {
    const res = await fetch('/data');
    data = await res.json();
    lastPollWall = performance.now();
    document.getElementById('status').textContent = data.t.length
      ? 'sim time ' + data.t[data.t.length - 1].toFixed(2) + ' s (last '
        + (data.t[data.t.length - 1] - data.t[0]).toFixed(0) + ' s shown)'
      : 'waiting for /joint_states…';
  } catch (err) {
    document.getElementById('status').textContent = 'connection lost';
  }
  drawAll();
}

const resetBtn = document.getElementById('reset-btn');
resetBtn.addEventListener('click', async () => {
  resetBtn.disabled = true;
  try {
    const res = await fetch('/reset', {method: 'POST'});
    if (res.ok) {
      data = {t: [], cart_pos: [], cart_vel: [], pole_pos: [], pole_vel: []};
      hoverT = null;
      drawAll();
    } else {
      document.getElementById('status').textContent = 'reset failed';
    }
  } catch (err) {
    document.getElementById('status').textContent = 'reset failed';
  }
  resetBtn.disabled = false;
});

setInterval(poll, 250);
window.addEventListener('resize', drawAll);
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', drawAll);
poll();
</script>
</body>
</html>
"""


class WebMonitor(Node):

    def __init__(self):
        super().__init__('web_monitor')
        self.declare_parameter('port', 8000)
        self.declare_parameter('world', 'empty')
        self.declare_parameter('model', 'cartpole')
        self.world_name = self.get_parameter('world').value
        self.model_name = self.get_parameter('model').value
        self.urdf_path = os.path.join(
            get_package_share_directory('urdf_basic'), 'urdf', 'cartpole.urdf')
        self.lock = threading.Lock()
        self.time = deque(maxlen=BUFFER_LEN)
        self.cart_pos = deque(maxlen=BUFFER_LEN)
        self.cart_vel = deque(maxlen=BUFFER_LEN)
        self.pole_pos = deque(maxlen=BUFFER_LEN)
        self.pole_vel = deque(maxlen=BUFFER_LEN)
        self.msg_count = 0

        self.create_subscription(
            JointState, 'joint_states', self.joint_state_callback, 10)

    def joint_state_callback(self, msg):
        if CART_JOINT not in msg.name or POLE_JOINT not in msg.name:
            return

        self.msg_count += 1
        if self.msg_count % DECIMATION != 0:
            return

        cart_idx = msg.name.index(CART_JOINT)
        pole_idx = msg.name.index(POLE_JOINT)
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        with self.lock:
            self.time.append(stamp)
            self.cart_pos.append(msg.position[cart_idx])
            self.cart_vel.append(msg.velocity[cart_idx])
            self.pole_pos.append(msg.position[pole_idx])
            self.pole_vel.append(msg.velocity[pole_idx])

    def snapshot(self):
        with self.lock:
            return {
                't': list(self.time),
                'cart_pos': list(self.cart_pos),
                'cart_vel': list(self.cart_vel),
                'pole_pos': list(self.pole_pos),
                'pole_vel': list(self.pole_vel),
            }

    def _gz_service(self, service, reqtype, req):
        result = subprocess.run(
            ['gz', 'service', '-s', service, '--reqtype', reqtype,
             '--reptype', 'gz.msgs.Boolean', '--timeout', '3000', '--req', req],
            capture_output=True, text=True, timeout=10)
        if result.returncode != 0 or 'true' not in result.stdout:
            self.get_logger().error(
                f'gz service {service} failed: {result.stdout} {result.stderr}')
            return False
        return True

    def reset_simulation(self):
        # A WorldControl reset kills the model-embedded JointStatePublisher
        # plugin in Harmonic, so respawn the model instead: sim time stays
        # monotonic and the plugin comes back with the fresh model.
        ok = self._gz_service(
            f'/world/{self.world_name}/remove', 'gz.msgs.Entity',
            f'name: "{self.model_name}", type: MODEL')
        if not ok:
            return False
        time.sleep(0.5)
        ok = self._gz_service(
            f'/world/{self.world_name}/create', 'gz.msgs.EntityFactory',
            f'sdf_filename: "{self.urdf_path}", name: "{self.model_name}"')
        if not ok:
            return False

        with self.lock:
            self.time.clear()
            self.cart_pos.clear()
            self.cart_vel.clear()
            self.pole_pos.clear()
            self.pole_vel.clear()
            self.msg_count = 0

        self.get_logger().info(f'{self.model_name} respawned at initial pose')
        return True


def make_handler(node):

    class MonitorHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            if self.path in ('/', '/index.html'):
                body = PAGE.encode('utf-8')
                content_type = 'text/html; charset=utf-8'
            elif self.path == '/data':
                body = json.dumps(node.snapshot()).encode('utf-8')
                content_type = 'application/json'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != '/reset':
                self.send_error(404)
                return
            ok = node.reset_simulation()
            body = json.dumps({'ok': ok}).encode('utf-8')
            self.send_response(200 if ok else 500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass  # keep the ROS console clean

    return MonitorHandler


def main():
    rclpy.init()
    node = WebMonitor()

    port = node.get_parameter('port').value
    server = ThreadingHTTPServer(('0.0.0.0', port), make_handler(node))
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    node.get_logger().info(f'web monitor running at http://localhost:{port}')

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
