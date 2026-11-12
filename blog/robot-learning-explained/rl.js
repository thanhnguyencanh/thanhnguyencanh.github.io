// "Robot learning, explained": the PPO clipping plot, behavior cloning vs DAgger (dagger-core.js), the flow-matching figure
// and the title trends (data.js, window.FAMILY.trend).
(function () {
  "use strict";
  var doc = document.documentElement;
  var vi = function () { return doc.dataset.lang === "vi"; };
  var L = function (en, v) { return vi() ? v : en; };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var num = function (n, d) { return Number(n).toLocaleString(vi() ? "vi-VN" : "en-US", { maximumFractionDigits: d || 0, minimumFractionDigits: d || 0 }); };
  var $ = function (id) { return document.getElementById(id); };
  var f1 = function (v) { return v.toFixed(1); };
  var minus = function (s) { return String(s).replace(/-/g, "−"); };

  // ---- PPO: the clipped surrogate objective as a function of the probability ratio ----
  function ppo() {
    var box = $("rl-ppo"), sl = $("rl-eps");
    if (!box || !sl) return;
    function panel(x0, A) {
      var W = 300, H = 210, P = 34, T = 26, B = 34, eps = +sl.value;
      var X = function (r) { return x0 + P + r / 2 * (W - P - 12); }, lo = A > 0 ? -0.1 : -2.1, hi = A > 0 ? 2.1 : 0.1;
      var Y = function (v) { return T + (hi - v) / (hi - lo) * (H - T - B); };
      var clip = function (r) { return Math.max(1 - eps, Math.min(1 + eps, r)); }, Lc = function (r) { return Math.min(r * A, clip(r) * A); };
      var s = "", flat = A > 0 ? [1 + eps, 2] : [0, 1 - eps];
      s += '<rect class="rl-flat" x="' + f1(X(flat[0])) + '" y="' + T + '" width="' + f1(X(flat[1]) - X(flat[0])) + '" height="' + (H - T - B) + '"></rect>';
      s += '<text class="rl-flat-t" x="' + f1((X(flat[0]) + X(flat[1])) / 2) + '" y="' + (T + 16) + '" text-anchor="middle">' + esc(L("no gradient", "không có gradient")) + "</text>";
      (A > 0 ? [0, 1, 2] : [-2, -1, 0]).forEach(function (v) {
        s += '<line class="grid" x1="' + X(0) + '" x2="' + X(2) + '" y1="' + f1(Y(v)) + '" y2="' + f1(Y(v)) + '"></line><text x="' + (X(0) - 6) + '" y="' + f1(Y(v) + 4) + '" text-anchor="end">' + minus(v) + "</text>";
      });
      [0, 1 - eps, 1, 1 + eps, 2].forEach(function (r, i) {
        s += '<line class="' + (i === 0 || i === 4 ? "grid" : "rl-tick") + '" x1="' + f1(X(r)) + '" x2="' + f1(X(r)) + '" y1="' + T + '" y2="' + (H - B) + '"></line>';
      });
      s += '<text x="' + f1(X(1 - eps)) + '" y="' + (H - B + 16) + '" text-anchor="middle">1−ε</text><text x="' + f1(X(1 + eps)) + '" y="' + (H - B + 16) + '" text-anchor="middle">1+ε</text>' +
        '<text x="' + f1(X(0)) + '" y="' + (H - B + 16) + '" text-anchor="middle">0</text><text x="' + f1(X(2)) + '" y="' + (H - B + 16) + '" text-anchor="middle">2</text>';
      var un = "", cl = "";
      for (var k = 0; k <= 200; k++) { var r = k / 100; un += (k ? "L" : "M") + f1(X(r)) + " " + f1(Y(r * A)); cl += (k ? "L" : "M") + f1(X(r)) + " " + f1(Y(Lc(r))); }
      s += '<path class="rl-unclip" d="' + un + '"></path><path class="rl-clip" d="' + cl + '"></path>';
      s += '<text class="lab" x="' + (x0 + P) + '" y="14">' + esc(A > 0 ? L("Â > 0: the action was better than expected", "Â > 0: hành động tốt hơn kỳ vọng") : L("Â < 0: the action was worse than expected", "Â < 0: hành động tệ hơn kỳ vọng")) + "</text>";
      s += '<text x="' + (x0 + W - 10) + '" y="' + (H - 2) + '" text-anchor="end">' + esc(L("ratio ρ = π", "tỉ số ρ = π")) + '<tspan dy="3" font-size="9">θ</tspan><tspan dy="-3"> / π</tspan><tspan dy="3" font-size="9">' + esc(L("old", "cũ")) + "</tspan></text>";
      return s;
    }
    function draw() {
      $("rl-eps-v").textContent = "ε = " + num(+sl.value, 2);
      box.innerHTML = '<div class="ba-scroll"><svg viewBox="0 0 620 210" role="img" aria-label="' + esc(L("PPO clipped objective", "Hàm mục tiêu có cắt ngưỡng của PPO")) + '">' + panel(0, 1) + panel(320, -1) + "</svg></div>" +
        '<div class="ft-legend"><span><i class="rl-sw-clip"></i>' + esc(L("clipped objective (PPO)", "hàm mục tiêu có cắt ngưỡng (PPO)")) + '</span><span><i class="rl-sw-unclip"></i>' +
        esc(L("unclipped ρ·Â (plain policy gradient)", "ρ·Â không cắt ngưỡng (gradient chính sách thường)")) + "</span></div>";
    }
    sl.addEventListener("input", draw);
    document.addEventListener("langchange", draw);
    draw();
  }

  // ---- behavior cloning vs DAgger on the lane-keeping toy ----
  function dagger() {
    var box = $("rl-dagger"), D = window.DaggerDemo;
    if (!box || !D) return;
    var E, seed = 0, busy = false;
    var R0 = D.road(), ang = Math.atan2(R0[R0.length - 1].y - R0[0].y, R0[R0.length - 1].x - R0[0].x), ca = Math.cos(ang), sa = Math.sin(ang);
    var rot = function (p) { return { x: ca * p.x + sa * p.y, y: -sa * p.x + ca * p.y }; };  // the road's chord along +x
    var R = R0.map(function (p) { var q = rot(p); return { x: q.x, y: q.y, phi: p.phi - ang }; });
    var xs = R.map(function (p) { return p.x; }), ys = R.map(function (p) { return p.y; });
    var x0 = Math.min.apply(null, xs) - 1.5, x1 = Math.max.apply(null, xs) + 1.5, y0 = Math.min.apply(null, ys) - 1.5, y1 = Math.max.apply(null, ys) + 1.5;
    var W = 640, k = W / (x1 - x0), H = Math.round((y1 - y0) * k);
    $("rl-road-svg").setAttribute("viewBox", "0 0 " + W + " " + H);
    var X = function (x) { return f1((x - x0) * k); }, Y = function (y) { return f1((y1 - y) * k); };
    function edge(side) {
      return R.filter(function (p, i) { return i % 4 === 0; }).map(function (p, i) {
        var ex = p.x - Math.sin(p.phi) * side * D.HALF, ey = p.y + Math.cos(p.phi) * side * D.HALF;
        return (i ? "L" : "M") + X(ex) + " " + Y(ey);
      }).join("");
    }
    var roadSvg = '<path class="rl-road-edge" d="' + edge(1) + '"></path><path class="rl-road-edge" d="' + edge(-1) + '"></path>' +
      '<path class="rl-road-mid" d="' + R.filter(function (p, i) { return i % 4 === 0; }).map(function (p, i) { return (i ? "L" : "M") + X(p.x) + " " + Y(p.y); }).join("") + '"></path>';
    function runs(list, cls) {
      return list.map(function (r) {
        var pts = r.path.map(rot);
        var d = pts.filter(function (p, i) { return i % 3 === 0 || i === pts.length - 1; }).map(function (p, i) { return (i ? "L" : "M") + X(p.x) + " " + Y(p.y); }).join("");
        var end = pts[pts.length - 1], mark = r.off ? '<path class="' + cls + '-x" d="M' + (+X(end.x) - 5) + " " + (+Y(end.y) - 5) + "l10 10m0 -10l-10 10" + '"></path>' : "";
        return '<path class="' + cls + '" d="' + d + '"></path>' + mark;
      }).join("");
    }
    function curve() {
      var Wc = 320, Hc = 180, P = 36, n = Math.max(6, E.round), s = "";
      var Xc = function (i) { return P + i / n * (Wc - P - 10); }, Yc = function (v) { return Hc - 26 - v * (Hc - 46); };
      [0, 0.5, 1].forEach(function (v) { s += '<line class="grid" x1="' + P + '" x2="' + (Wc - 10) + '" y1="' + f1(Yc(v)) + '" y2="' + f1(Yc(v)) + '"></line><text x="' + (P - 6) + '" y="' + f1(Yc(v) + 4) + '" text-anchor="end">' + num(100 * v) + "%</text>"; });
      for (var i = 0; i <= n; i++) if (i % Math.max(1, Math.round(n / 6)) === 0) s += '<text x="' + f1(Xc(i)) + '" y="' + (Hc - 8) + '" text-anchor="middle">' + i + "</text>";
      [["bc", "rl-bc"], ["dagger", "rl-dg"]].forEach(function (m) {
        s += '<path class="' + m[1] + '-line" d="' + E.hist.map(function (h, i) { return (i ? "L" : "M") + f1(Xc(h.round)) + " " + f1(Yc(h[m[0]])); }).join("") + '"></path>';
        E.hist.forEach(function (h) { s += '<circle class="' + m[1] + '-dot" cx="' + f1(Xc(h.round)) + '" cy="' + f1(Yc(h[m[0]])) + '" r="3.5"><title>' + esc(L("round ", "vòng ") + h.round + ": " + num(100 * h[m[0]]) + "%") + "</title></circle>"; });
      });
      s += '<text class="lab" x="' + P + '" y="12">' + esc(L("share of the road completed", "phần đường đi hết")) + "</text>";
      s += '<text x="' + (Wc - 10) + '" y="' + (Hc - 8 + 0) + '" text-anchor="end" dy="-12">' + esc(L("round", "vòng")) + "</text>";
      $("rl-curve").innerHTML = s;
    }
    function data() {
      var Wd = 320, Hd = 180, P = 36, lim = 0.6, s = "";
      var Xd = function (v) { return P + (Math.max(-lim, Math.min(lim, v)) + lim) / (2 * lim) * (Wd - P - 10); }, Yd = function (v) { return Hd - 26 - (Math.max(-lim, Math.min(lim, v)) + lim) / (2 * lim) * (Hd - 46); };
      [-0.6, 0, 0.6].forEach(function (v) {
        s += '<line class="grid" x1="' + f1(Xd(v)) + '" x2="' + f1(Xd(v)) + '" y1="20" y2="' + (Hd - 26) + '"></line><text x="' + f1(Xd(v)) + '" y="' + (Hd - 10) + '" text-anchor="middle">' + minus(num(v, 1)) + "</text>";
        s += '<text x="' + (P - 6) + '" y="' + f1(Yd(v) + 4) + '" text-anchor="end">' + minus(num(v, 1)) + "</text>";
      });
      function pts(list, cls) { var step = Math.max(1, Math.floor(list.length / 700)), o = ""; for (var i = 0; i < list.length; i += step) o += '<circle class="' + cls + '" cx="' + f1(Xd(list[i].o[0])) + '" cy="' + f1(Yd(list[i].o[1])) + '" r="1.6"></circle>'; return o; }
      s += pts(E.dg, "rl-dg-pt") + pts(E.bc, "rl-bc-pt");
      s += '<text class="lab" x="' + P + '" y="12">' + esc(L("training states: lateral offset (m) × heading error (rad)", "trạng thái huấn luyện: độ lệch ngang (m) × sai số hướng (rad)")) + "</text>";
      $("rl-data").innerHTML = s;
    }
    function draw() {
      var h = E.hist[E.hist.length - 1];
      $("rl-road").innerHTML = roadSvg + runs(h.runsDG, "rl-dg-run") + runs(h.runsBC, "rl-bc-run");
      curve(); data();
      $("rl-dg-stats").innerHTML = "<p><b>" + esc(L("Round ", "Vòng ")) + E.round + "</b> · " + esc(L("labels: ", "số nhãn: ")) + num(h.nbc) + " / " + num(h.ndg) + "</p>" +
        '<p><span class="rl-key rl-key-bc"></span>' + esc(L("Behavior cloning: ", "Behavior cloning: ")) + "<b>" + num(100 * h.bc) + "%</b> " + esc(L("of the road", "quãng đường")) + "</p>" +
        '<p><span class="rl-key rl-key-dg"></span>DAgger: <b>' + num(100 * h.dagger) + "%</b> " + esc(L("of the road", "quãng đường")) + "</p>" +
        (E.round === 0 ? '<p class="ba-small">' + esc(L("Round 0: both students have the same data, so their drives coincide.", "Vòng 0: hai người trò có cùng dữ liệu, nên các lượt lái trùng nhau.")) + "</p>" : "") +
        '<p class="ba-small">' + esc(L("Average over 6 test drives that start slightly off the centre line. × marks where a student left the road.",
          "Trung bình trên 6 lượt chạy thử bắt đầu hơi lệch khỏi tim đường. Dấu × là nơi người trò rời khỏi đường.")) + "</p>";
    }
    function reset() { E = D.create(seed, 6); draw(); }
    function step() { D.advance(E); draw(); }
    box.addEventListener("click", function (e) {
      var b = e.target.closest("[data-rl]");
      if (!b || busy) return;
      if (b.dataset.rl === "round") step();
      else if (b.dataset.rl === "reset") reset();
      else if (b.dataset.rl === "noise") { seed++; reset(); }
      else if (b.dataset.rl === "run") {
        busy = true;
        var left = 6;
        (function next() { if (left-- <= 0) { busy = false; return; } step(); setTimeout(next, 60); })();
      }
    });
    document.addEventListener("langchange", function () { if (E) draw(); });
    reset();
  }

  // ---- flow matching on a two-mode action distribution, against regression ----
  function flow() {
    var box = $("rl-flow");
    if (!box) return;
    var MU = [-1, 1], S = 0.12, seed = 5;
    function vel(x, t) {  // the exact marginal velocity for x_t = t x1 + (1 - t) x0, x0 ~ N(0, 1), x1 ~ two Gaussians
      var n = 0, d = 0;
      MU.forEach(function (m) {
        var v = t * t * S * S + (1 - t) * (1 - t), p = Math.exp(-Math.pow(x - t * m, 2) / (2 * v)) / Math.sqrt(v);
        n += p * (m + t * S * S / v * (x - t * m)); d += p;
      });
      return (n / d - x) / (1 - t);
    }
    function draw() {
      var W = 620, H = 260, P = 40, T = 24, B = 30, lim = 2.6, s = "", r = (function (z) { return function () { z = (Math.imul(z, 1664525) + 1013904223) >>> 0; return z / 4294967296; }; })(seed);
      var X = function (t) { return P + t * (W - P - 120); }, Y = function (a) { return T + (lim - a) / (2 * lim) * (H - T - B); };
      [-2, -1, 0, 1, 2].forEach(function (a) { s += '<line class="grid" x1="' + P + '" x2="' + f1(X(1)) + '" y1="' + f1(Y(a)) + '" y2="' + f1(Y(a)) + '"></line><text x="' + (P - 6) + '" y="' + f1(Y(a) + 4) + '" text-anchor="end">' + minus(a) + "</text>"; });
      [0, 0.5, 1].forEach(function (t) { s += '<text x="' + f1(X(t)) + '" y="' + (H - 10) + '" text-anchor="middle">' + num(t, 1) + "</text>"; });
      for (var n = 0; n < 60; n++) {
        var x = Math.sqrt(-2 * Math.log(Math.max(1e-12, r()))) * Math.cos(2 * Math.PI * r()), d = "M" + f1(X(0)) + " " + f1(Y(Math.max(-lim, Math.min(lim, x))));
        for (var i = 0; i < 100; i++) { var t = i / 100; x += vel(x, t) / 100; d += "L" + f1(X((i + 1) / 100)) + " " + f1(Y(Math.max(-lim, Math.min(lim, x)))); }
        s += '<path class="' + (x < 0 ? "rl-flow-a" : "rl-flow-b") + '" d="' + d + '"></path>';
      }
      s += '<line class="rl-mse" x1="' + P + '" x2="' + f1(X(1) + 6) + '" y1="' + f1(Y(0)) + '" y2="' + f1(Y(0)) + '"></line>';
      s += '<rect class="rl-obstacle" x="' + f1(X(1) + 14) + '" y="' + f1(Y(0.35)) + '" width="22" height="' + f1(Y(-0.35) - Y(0.35)) + '" rx="3"></rect>';
      s += '<text class="lab" x="' + f1(X(1) + 42) + '" y="' + f1(Y(0) + 4) + '">' + esc(L("obstacle", "vật cản")) + "</text>";
      s += '<text x="' + f1(X(1) + 14) + '" y="' + f1(Y(1) + 4) + '">' + esc(L("go left", "rẽ trái")) + '</text><text x="' + f1(X(1) + 14) + '" y="' + f1(Y(-1) + 4) + '">' + esc(L("go right", "rẽ phải")) + "</text>";
      s += '<text class="lab" x="' + P + '" y="14">' + esc(L("action a (steering), from noise at τ = 0 to an action at τ = 1", "hành động a (lái), từ nhiễu ở τ = 0 đến hành động ở τ = 1")) + "</text>";
      s += '<text class="rl-mse-t" x="' + f1(X(0.52)) + '" y="' + f1(Y(0) - 6) + '" text-anchor="middle">' + esc(L("regression (MSE) predicts the average: straight ahead", "hồi quy (MSE) dự đoán trung bình: đi thẳng")) + "</text>";
      box.innerHTML = '<div class="ba-scroll"><svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + esc(L("Flow matching splits noise into the two demonstrated actions", "Flow matching tách nhiễu thành hai hành động đã trình diễn")) + '">' + s + "</svg></div>";
    }
    document.querySelectorAll("[data-rl-flow]").forEach(function (b) { b.addEventListener("click", function () { seed++; draw(); }); });
    document.addEventListener("langchange", draw);
    draw();
  }

  // ---- title trends in robotics venues: small multiples on one shared axis ----
  function trend() {
    var box = $("rl-trend"), T = window.FAMILY && window.FAMILY.trend;
    if (!box || !T) return;
    function draw() {
      var mx = 0;
      T.topics.forEach(function (t) { t.rate.forEach(function (v) { mx = Math.max(mx, v); }); });
      mx = Math.ceil(mx / 10) * 10;
      var n = T.years.length, last = T.years[n - 1];
      box.innerHTML = T.topics.map(function (tp) {
        var W = 300, H = 150, P = 30, Tp = 22, B = 20, bw = (W - P - 6) / n, s = "";
        var Y = function (v) { return H - B - v / mx * (H - B - Tp); };
        [0, mx / 2, mx].forEach(function (v) { s += '<line class="grid" x1="' + P + '" x2="' + W + '" y1="' + f1(Y(v)) + '" y2="' + f1(Y(v)) + '"></line><text x="' + (P - 5) + '" y="' + f1(Y(v) + 4) + '" text-anchor="end">' + num(v) + "</text>"; });
        tp.rate.forEach(function (v, i) {
          var x = P + i * bw + 1.5, w = bw - 3, tip = T.years[i] + (T.years[i] === last ? L(" (so far)", " (đến nay)") : "") + ": " + num(tp.count[i]) + L(" titles, ", " tiêu đề, ") + num(v, 1) + L(" per 1,000 papers", " trên 1.000 bài");
          s += '<rect class="rl-bar" x="' + f1(x) + '" y="' + f1(Y(v)) + '" width="' + f1(w) + '" height="' + f1(Y(0) - Y(v)) + '" rx="1.5"><title>' + esc(tip) + "</title></rect>";
        });
        s += '<text x="' + (P + 2) + '" y="' + (H - 5) + '">' + T.years[0] + '</text><text x="' + W + '" y="' + (H - 5) + '" text-anchor="end">' + last + "*</text>";
        s += '<text class="lab" x="' + f1(P + (n - 1) * bw + bw / 2) + '" y="' + f1(Y(tp.rate[n - 1]) - 5) + '" text-anchor="end">' + num(tp.rate[n - 1], 0) + "</text>";
        return '<figure class="rl-mini"><figcaption>' + esc(L(tp.en, tp.vi)) + '</figcaption><svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + esc(L(tp.en, tp.vi)) + '">' + s + "</svg></figure>";
      }).join("");
      var note = $("rl-trend-note");
      if (note) note.textContent = L("Titles per 1,000 papers in " + T.venues.join(", ") + ", from keyword rules on titles; * " + last + " so far. Topics overlap, and “distillation” also counts perception models.",
        "Số tiêu đề trên 1.000 bài ở " + T.venues.join(", ") + ", theo quy tắc từ khóa trên tiêu đề; * " + last + " tính đến nay. Các chủ đề có thể trùng nhau, và “chưng cất” cũng tính cả mô hình tri giác.");
    }
    document.addEventListener("langchange", draw);
    draw();
  }

  function math() {  // KaTeX renders the TeX equations of the post (loaded with defer from cdnjs)
    if (window.renderMathInElement) renderMathInElement(document.querySelector(".post-body"), {
      delimiters: [{ left: "$$", right: "$$", display: true }, { left: "\\(", right: "\\)", display: false }], throwOnError: false });
  }
  function start() { math(); ppo(); dagger(); flow(); trend(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
