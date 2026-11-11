// "Visual SLAM datasets": the comparison table with feature filters (data in data.js) and the trajectory-evaluation demo (eval-core.js).
(function () {
  "use strict";
  var doc = document.documentElement;
  var vi = function () { return doc.dataset.lang === "vi"; };
  var L = function (en, v) { return vi() ? v : en; };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var num = function (n, d) { return Number(n).toLocaleString(vi() ? "vi-VN" : "en-US", { maximumFractionDigits: d || 0, minimumFractionDigits: d || 0 }); };
  var $ = function (id) { return document.getElementById(id); };

  // ---- comparison table ----
  var GROUPS = [
    ["sensors", "Sensors", "Cảm biến", [["mono", "Monocular", "Đơn camera"], ["stereo", "Stereo", "Stereo"], ["rgbd", "RGB-D", "RGB-D"], ["imu", "IMU", "IMU"], ["lidar", "LiDAR", "LiDAR"]]],
    ["setting", "Setting", "Bối cảnh", [["indoor", "Indoor", "Trong nhà"], ["outdoor", "Outdoor, urban", "Ngoài trời, đô thị"], ["field", "Off-road, mines", "Địa hình, hầm mỏ"], ["synth", "Synthetic", "Tổng hợp"]]],
    ["challenge", "Challenges and labels", "Thách thức và nhãn", [["dyn", "Moving objects", "Vật chuyển động"], ["light", "Low or changing light", "Ánh sáng yếu hoặc thay đổi"],
      ["long", "Long-term change", "Thay đổi dài hạn"], ["large", "Large scale", "Quy mô lớn"], ["sem", "Semantic or other labels", "Nhãn ngữ nghĩa hoặc nhãn khác"]]]
  ];
  function table() {
    var box = $("vd-table"), F = window.FAMILY;
    if (!box || !F) return;
    var need = {}, truth = {};
    F.trees[1].nodes.forEach(function (n) { truth[n.id] = n; });
    function draw() {
      var keys = Object.keys(need).filter(function (k) { return need[k]; }), shown = 0;
      var chips = GROUPS.map(function (g) {
        return '<div class="vd-chips"><span>' + esc(L(g[1], g[2])) + ":</span>" + g[3].map(function (f) {
          return '<button class="filter-chip" type="button" data-vd-f="' + f[0] + '" aria-pressed="' + !!need[f[0]] + '">' + esc(L(f[1], f[2])) + "</button>";
        }).join("") + "</div>";
      }).join("");
      var head1 = '<tr><th rowspan="2">' + esc(L("Dataset", "Bộ dữ liệu")) + '</th><th rowspan="2">' + esc(L("Year", "Năm")) + "</th>" +
        GROUPS.map(function (g) { return '<th colspan="' + g[3].length + '" class="vd-group vd-' + g[0] + '">' + esc(L(g[1], g[2])) + "</th>"; }).join("") +
        '<th rowspan="2">' + esc(L("Ground truth", "Ground truth")) + "</th></tr>";
      var head2 = "<tr>" + GROUPS.map(function (g) { return g[3].map(function (f) { return '<th class="vd-rot"><span>' + esc(L(f[1], f[2])) + "</span></th>"; }).join(""); }).join("") + "</tr>";
      var rows = F.items.map(function (it) {
        var ok = keys.every(function (k) { return it.f.indexOf(k) >= 0; });
        if (ok) shown++;
        var g = truth[it.g], top = truth[g.parent];
        return '<tr' + (ok ? "" : " hidden") + '><td><a href="' + esc(it.site) + '">' + esc(it.name) + '</a></td><td class="vs-num">' + it.year + "</td>" +
          GROUPS.map(function (gr) {
            return gr[3].map(function (f) {
              var has = it.f.indexOf(f[0]) >= 0;
              return '<td class="vd-dot vd-' + gr[0] + '">' + (has ? '<i title="' + esc(L(f[1], f[2])) + '"></i><span class="sr-only">' + esc(L(f[1], f[2])) + "</span>" : "") + "</td>";
            }).join("");
          }).join("") + '<td class="vd-gt">' + esc(L(g.en, g.vi)) + (top ? ' <span>· ' + esc(L(top.en, top.vi)) + "</span>" : "") + "</td></tr>";
      }).join("");
      box.innerHTML = chips + '<p class="vd-count" role="status">' + esc(L(shown + " of " + F.items.length + " datasets", shown + " trên " + F.items.length + " bộ dữ liệu")) +
        (keys.length ? ' <button class="filter-chip" type="button" data-vd-clear>' + esc(L("Clear filters", "Bỏ lọc")) + "</button>" : "") + "</p>" +
        '<div class="vs-table-wrap"><table class="vs-table vd-table"><thead>' + head1 + head2 + "</thead><tbody>" + rows + "</tbody></table></div>";
    }
    box.addEventListener("click", function (e) {
      var b = e.target.closest("[data-vd-f],[data-vd-clear]");
      if (!b) return;
      if (b.hasAttribute("data-vd-clear")) need = {}; else need[b.dataset.vdF] = !need[b.dataset.vdF];
      draw();
    });
    document.addEventListener("langchange", draw);
    draw();
  }

  // ---- trajectory evaluation ----
  var PRESETS = {
    mono: { scale: 0.5 }, sdrift: { scaleDrift: 3 }, ydrift: { yawDrift: 0.3 }, mid: { jump: 10, at: 50 }, end: { jump: 10, at: 90 }, noise: { noise: 2 }
  };
  function evalDemo() {
    var box = $("vd-eval"), D = window.EvalDemo;
    if (!box || !D) return;
    var sliders = ["scale", "scaleDrift", "yawDrift", "jump", "at", "noise"], st = { sim: false };
    var val = function (k) { return +$("vd-" + k).value; };
    var fmt = {
      scale: function (v) { return "×" + num(v, 2); }, scaleDrift: function (v) { return (v > 0 ? "+" : "") + num(v, 1) + " %/10 m"; },
      yawDrift: function (v) { return num(v, 2) + "°/m"; }, jump: function (v) { return num(v) + "°"; }, at: function (v) { return num(v) + " %"; },
      noise: function (v) { return num(v, 1) + " cm"; }
    };
    function opts() {
      return { scale: val("scale"), scaleDrift: val("scaleDrift") / 100, yawDrift: val("yawDrift"), jump: val("jump"), at: val("at") / 100, noise: val("noise") / 100 };
    }
    function plot(r) {
      var xs = r.T.concat(r.E).map(function (p) { return p.x; }), ys = r.T.concat(r.E).map(function (p) { return p.y; });
      var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
      var W = 520, H = 340, pad = 18, k = Math.min((W - 2 * pad) / (x1 - x0 || 1), (H - 2 * pad) / (y1 - y0 || 1));
      var X = function (x) { return (pad + (x - x0) * k + ((W - 2 * pad) - (x1 - x0) * k) / 2).toFixed(1); };
      var Y = function (y) { return (H - pad - (y - y0) * k - ((H - 2 * pad) - (y1 - y0) * k) / 2).toFixed(1); };
      var path = function (P) { return P.map(function (p, i) { return (i ? "L" : "M") + X(p.x) + " " + Y(p.y); }).join(""); };
      var s = "";
      for (var i = 0; i < r.T.length; i += 8) s += '<line class="vd-err" x1="' + X(r.T[i].x) + '" y1="' + Y(r.T[i].y) + '" x2="' + X(r.E[i].x) + '" y2="' + Y(r.E[i].y) + '"></line>';
      s += '<path class="vd-gt-path" d="' + path(r.T) + '"></path><path class="vd-est-path" d="' + path(r.E) + '"></path>';
      s += '<circle class="vd-start" cx="' + X(r.T[0].x) + '" cy="' + Y(r.T[0].y) + '" r="5"></circle>';
      var at = Math.round(val("at") / 100 * (D.N - 1));
      if (val("jump")) s += '<circle class="vd-jump" cx="' + X(r.E[at].x) + '" cy="' + Y(r.E[at].y) + '" r="6"></circle>';
      $("vd-plot").innerHTML = s;
    }
    function draw() {
      var o = opts(), r = D.evaluate(o, st.sim);
      sliders.forEach(function (k) { $("vd-" + k + "-v").textContent = fmt[k](val(k)); });
      document.querySelectorAll("[data-vd-align]").forEach(function (b) { b.setAttribute("aria-pressed", String((b.dataset.vdAlign === "sim") === st.sim)); });
      plot(r);
      $("vd-stats").innerHTML =
        "<p>" + esc(L("ATE (RMSE): ", "ATE (RMSE): ")) + "<b>" + num(r.ate, 2) + " m</b> " + esc(L("on a " + num(r.length) + " m loop", "trên vòng " + num(r.length) + " m")) + "</p>" +
        "<p>" + esc(L("Alignment: ", "Căn chỉnh: ")) + (st.sim ? esc(L("rotation, translation and scale ", "quay, tịnh tiến và tỉ lệ ")) + "<b>s = " + num(r.align.s, 2) + "</b>" : esc(L("rotation and translation", "quay và tịnh tiến"))) + "</p>" +
        "<p>" + esc(L("RPE over 5 m: ", "RPE trên 5 m: ")) + "<b>" + num(r.rpe.trans, 1) + " %</b> · <b>" + num(r.rpe.rot, 2) + " °/m</b></p>";
    }
    box.addEventListener("input", function (e) { if (e.target.matches("input[type=range]")) draw(); });
    box.addEventListener("click", function (e) {
      var b = e.target.closest("[data-vd-preset],[data-vd-align]");
      if (!b) return;
      if (b.hasAttribute("data-vd-align")) st.sim = b.dataset.vdAlign === "sim";
      else {
        var p = PRESETS[b.dataset.vdPreset], base = { scale: 1, scaleDrift: 0, yawDrift: 0, jump: 0, at: 50, noise: 0 };
        sliders.forEach(function (k) { $("vd-" + k).value = p[k] !== undefined ? p[k] : base[k]; });
      }
      draw();
    });
    document.addEventListener("langchange", draw);
    draw();
  }

  function math() {  // KaTeX renders the TeX equations of the post (loaded with defer from cdnjs)
    if (window.renderMathInElement) renderMathInElement(document.querySelector(".post-body"), {
      delimiters: [{ left: "$$", right: "$$", display: true }, { left: "\\(", right: "\\)", display: false }], throwOnError: false });
  }
  function start() { math(); table(); evalDemo(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
