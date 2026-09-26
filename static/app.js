const wsProto = location.protocol === "https:" ? "wss" : "ws";
const ws = new WebSocket(`${wsProto}://${location.host}/ws`);

const $ = id => document.getElementById(id);
const ctx = $("chart").getContext("2d");
const chart = new Chart(ctx, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      { label: "joins/s",  data: [], borderColor: "#8f8", backgroundColor: "rgba(136,255,136,.15)", tension: .3 },
      { label: "leaves/s", data: [], borderColor: "#fc8", backgroundColor: "rgba(255,204,136,.15)", tension: .3 },
    ]
  },
  options: { animation: false, plugins: { legend: { labels: { color:"#ccc" } } } }
});

let lastJoin = 0, lastLeave = 0;

ws.onmessage = ev => {
  const d = JSON.parse(ev.data);
  $("state").textContent   = d.running ? "RUNNING" : "idle";
  $("state").style.color   = d.running ? "#8f8" : "#888";
  $("cycles").textContent  = d.stats.cycles;
  $("join").textContent    = d.stats.join;
  $("leave").textContent   = d.stats.leave;
  $("errors").textContent  = d.stats.errors;
  $("media").textContent   = d.stats.media_sessions;
  $("workers").textContent = d.stats.workers;

  const map = {jitter_ms:"jitter_ms", cycles:"cycles_in", cooldown_sec:"cooldown_sec", rtp_hold_sec:"rtp_hold_sec"};
  for (const k in map) {
    const inp = $(map[k]);
    if (inp && document.activeElement !== inp) inp.value = d.params[k];
  }

  const dj = d.stats.join  - lastJoin;
  const dl = d.stats.leave - lastLeave;
  lastJoin = d.stats.join; lastLeave = d.stats.leave;
  chart.data.labels.push(new Date().toLocaleTimeString().slice(-8));
  chart.data.datasets[0].data.push(dj * 2);
  chart.data.datasets[1].data.push(dl * 2);
  if (chart.data.labels.length > 60) {
    chart.data.labels.shift();
    chart.data.datasets.forEach(s => s.data.shift());
  }
  chart.update("none");

  $("log").innerHTML = d.log_tail.map(e =>
    `<div class="k-${e.kind}">[${new Date(e.ts*1000).toLocaleTimeString()}] `
    + `<span style="color:#666">${e.worker}</span> ${e.msg}</div>`
  ).join("");
};

async function ctl(a) { await fetch(`/api/${a}`, { method: "POST" }); }

async function applyParams() {
  await fetch("/api/params", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jitter_ms:    parseInt($("jitter_ms").value, 10),
      cycles:       parseInt($("cycles_in").value, 10),
      cooldown_sec: parseInt($("cooldown_sec").value, 10),
      rtp_hold_sec: parseInt($("rtp_hold_sec").value, 10),
    }),
  });
}
