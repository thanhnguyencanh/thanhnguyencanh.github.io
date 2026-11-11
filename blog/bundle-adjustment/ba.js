// "Bundle adjustment, explained": the interactive 2D bundle adjustment (model in ba-core.js), its matrices, and the robust-kernel plot.
(function () {
  "use strict";
  var doc = document.documentElement;
  var vi = function () { return doc.dataset.lang === "vi"; };
  var L = function (en, v) { return vi() ? v : en; };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var num = function (n, d) { return Number(n).toLocaleString(vi() ? "vi-VN" : "en-US", { maximumFractionDigits: d || 0, minimumFractionDigits: d || 0 }); };
  var $ = function (id) { return document.getElementById(id); };
  var sci = function (v) {  // 3.3 × 10^-4, with the reader's decimal mark
    var e = Math.floor(Math.log10(v) + 1e-9), m = v / Math.pow(10, e);
    return num(m, 1) + " × 10<sup>" + String(e).replace("-", "−") + "</sup>";
  };

  // ---- robust kernels: rho(r) and the weight w(r) = rho'(s), for delta = 3 px ----
  function kernels() {
    var box = $("ba-kernels");
    if (!box) return;
    function draw() {
      var d = 3, W = 300, H = 170, P = 34, R = 10;
      var defs = [["ls", L("Least squares", "Bình phương tối thiểu"), function (r) { return r * r; }, function () { return 1; }],
                  ["hu", "Huber", function (r) { var a = Math.abs(r); return a <= d ? r * r : 2 * d * a - d * d; }, function (r) { var a = Math.abs(r); return a <= d ? 1 : d / a; }],
                  ["ca", "Cauchy", function (r) { return d * d * Math.log(1 + r * r / (d * d)); }, function (r) { return 1 / (1 + r * r / (d * d)); }]];
      function panel(x0, title, pick, ymax, ticks) {
        var X = function (r) { return x0 + P + (r + R) / (2 * R) * (W - P - 12); }, Y = function (v) { return H - 26 - Math.min(v, ymax) / ymax * (H - 50); }, s = "";
        s += '<text class="lab" x="' + (x0 + P) + '" y="14">' + esc(title) + "</text>";
        ticks.forEach(function (t) { s += '<line class="grid" x1="' + (x0 + P) + '" x2="' + (x0 + W - 12) + '" y1="' + Y(t) + '" y2="' + Y(t) + '"></line><text x="' + (x0 + P - 5) + '" y="' + (Y(t) + 4) + '" text-anchor="end">' + num(t, ymax < 2 ? 1 : 0) + "</text>"; });
        [-10, -3, 0, 3, 10].forEach(function (t) { s += '<text x="' + X(t) + '" y="' + (H - 10) + '" text-anchor="middle">' + String(t).replace("-", "−") + "</text>"; });
        defs.forEach(function (k) {
          var path = "";
          for (var r = -R; r <= R + 1e-9; r += 0.1) path += (path ? "L" : "M") + X(r).toFixed(1) + " " + Y(pick(k)(r)).toFixed(1);
          s += '<path class="ba-k ba-k-' + k[0] + '" d="' + path + '"></path>';
        });
        return s;
      }
      var svg = panel(0, L("cost ρ for a residual r (px)", "chi phí ρ theo phần dư r (px)"), function (k) { return k[2]; }, 100, [0, 50, 100]) +
                panel(W + 20, L("weight w = ρ′ in the normal equations", "trọng số w = ρ′ trong phương trình chuẩn"), function (k) { return k[3]; }, 1, [0, 0.5, 1]);
      box.innerHTML = '<div class="ba-scroll"><svg viewBox="0 0 ' + (2 * W + 20) + " " + H + '" role="img" aria-label="' + esc(L("Robust kernels", "Các hàm bền vững")) + '">' + svg + "</svg></div>" +
        '<div class="ft-legend">' + defs.map(function (k) { return '<span><i class="ba-k-' + k[0] + '"></i>' + esc(k[1]) + "</span>"; }).join("") + "</div>";
    }
    document.addEventListener("langchange", draw);
    draw();
  }

  // ---- the 2D bundle adjustment ----
  function demo() {
    var box = $("ba-demo"), B = window.BADemo;
    if (!box || !B) return;
    var st = { outliers: false, kernel: null, seed: 17, timer: 0 }, S, E, last;
    function reset() {
      stop();
      S = B.scene({ seed: 3, outliers: st.outliers });
      E = B.start(S, st.seed);
      var sys = B.system(S, E, st.kernel);
      E.history = [sys.cost];
      last = { sys: sys, S: (B.solve(sys, E.lambda) || {}).S, accepted: null };
      draw();
    }
    function converged() { var h = E.history; return h.length > 2 && Math.abs(h[h.length - 2] - h[h.length - 1]) <= 1e-7 * h[h.length - 1]; }
    function step() { last = B.step(S, E, st.kernel); draw(); }
    function stop() { clearInterval(st.timer); st.timer = 0; }
    function run() {
      stop();
      st.timer = setInterval(function () { if (converged() || E.history.length > 60) return stop(); step(); }, 320);
    }
    // the scene window, in metres: x from -5.6 to 5.6, y from -5.3 to 3.3 (the svg is 500 x 384)
    var K = 500 / 11.2, X = function (x) { return ((x + 5.6) * K).toFixed(1); }, Y = function (y) { return ((3.3 - y) * K).toFixed(1); };
    function wedge(c, cls) {
      var len = 0.75, a = 30 * Math.PI / 180, p1 = [c.x + len * Math.cos(c.th + a), c.y + len * Math.sin(c.th + a)], p2 = [c.x + len * Math.cos(c.th - a), c.y + len * Math.sin(c.th - a)];
      return '<path class="' + cls + '" d="M' + X(c.x) + " " + Y(c.y) + "L" + X(p1[0]) + " " + Y(p1[1]) + "L" + X(p2[0]) + " " + Y(p2[1]) + 'Z"></path>';
    }
    function scene() {
      var s = "";
      S.obs.forEach(function (ob) {  // the bundles of rays; outliers are drawn along their (wrong) measured direction
        var c = E.cams[ob.c];
        if (ob.out) {
          var ang = c.th + Math.atan(ob.u / B.F);
          s += '<line class="ba-ray-out" x1="' + X(c.x) + '" y1="' + Y(c.y) + '" x2="' + X(c.x + 7 * Math.cos(ang)) + '" y2="' + Y(c.y + 7 * Math.sin(ang)) + '"></line>';
        } else s += '<line class="ba-ray" x1="' + X(c.x) + '" y1="' + Y(c.y) + '" x2="' + X(E.pts[ob.p].x) + '" y2="' + Y(E.pts[ob.p].y) + '"></line>';
      });
      S.pts.forEach(function (p, j) {
        var q = E.pts[j];
        s += '<line class="ba-err" x1="' + X(p.x) + '" y1="' + Y(p.y) + '" x2="' + X(q.x) + '" y2="' + Y(q.y) + '"></line>';
        s += '<circle class="ba-pt-true" cx="' + X(p.x) + '" cy="' + Y(p.y) + '" r="4.5"></circle><circle class="ba-pt" cx="' + X(q.x) + '" cy="' + Y(q.y) + '" r="3.6"></circle>';
      });
      S.cams.forEach(function (c, i) {
        s += wedge(c, "ba-cam-true") + wedge(E.cams[i], "ba-cam");
        if (i < 2) s += '<circle class="ba-fixed" cx="' + X(c.x) + '" cy="' + Y(c.y) + '" r="9"></circle>';
        s += '<text class="ba-lab" x="' + (+X(c.x) + (c.x < 0 ? -12 : 12)) + '" y="' + (+Y(c.y) + 16) + '" text-anchor="' + (c.x < 0 ? "end" : "start") + '">' + (i + 1) + "</text>";
      });
      $("ba-scene").innerHTML = s;
    }
    function cost() {
      var h = E.history, Wc = 360, Hc = 170, P = 44, n = Math.max(8, h.length - 1);
      var lo = Math.floor(Math.log10(Math.min.apply(null, h))), hi = Math.ceil(Math.log10(Math.max.apply(null, h)));
      if (hi === lo) hi = lo + 1;
      var Xc = function (i) { return P + i / n * (Wc - P - 10); }, Yc = function (v) { return Hc - 24 - (Math.log10(v) - lo) / (hi - lo) * (Hc - 40); }, s = "";
      for (var e = lo; e <= hi; e++) s += '<line class="grid" x1="' + P + '" x2="' + (Wc - 10) + '" y1="' + Yc(Math.pow(10, e)) + '" y2="' + Yc(Math.pow(10, e)) + '"></line><text x="' + (P - 6) + '" y="' + (Yc(Math.pow(10, e)) + 4) + '" text-anchor="end">10' + "<tspan dy='-5' font-size='9'>" + e + "</tspan></text>";
      s += '<path class="ba-cost" d="' + h.map(function (v, i) { return (i ? "L" : "M") + Xc(i).toFixed(1) + " " + Yc(v).toFixed(1); }).join("") + '"></path>';
      h.forEach(function (v, i) { s += '<circle class="ba-cost-dot" cx="' + Xc(i).toFixed(1) + '" cy="' + Yc(v).toFixed(1) + '" r="3"></circle>'; });
      s += '<text x="' + (Wc - 10) + '" y="' + (Hc - 6) + '" text-anchor="end">' + esc(L("iteration", "vòng lặp")) + "</text>";
      s += '<text class="lab" x="' + P + '" y="10">' + esc(L("cost F (log scale)", "chi phí F (thang log)")) + "</text>";
      $("ba-cost").innerHTML = s;
    }
    function matrices() {
      var sys = last.sys, nc = sys.nc, N = sys.N, rows = sys.J.length, cw = 3, ch = 1.5, s = "";
      // J: one row per measurement; each touches one camera block and one point block
      sys.J.forEach(function (cols, r) { cols.forEach(function (c) { s += '<rect class="' + (c < nc ? "ba-mc" : "ba-mp") + '" x="' + c * cw + '" y="' + r * ch + '" width="' + cw + '" height="' + ch + '"></rect>'; }); });
      $("ba-J").setAttribute("viewBox", "0 0 " + N * cw + " " + rows * ch); $("ba-J").innerHTML = s;
      s = ""; var c2 = 3;
      for (var i = 0; i < N; i++) for (var j = 0; j < N; j++) {
        if (Math.abs(sys.H[i][j]) < 1e-12) continue;
        var cls = i < nc && j < nc ? "ba-mc" : i >= nc && j >= nc ? "ba-mp" : "ba-me";
        s += '<rect class="' + cls + '" x="' + j * c2 + '" y="' + i * c2 + '" width="' + c2 + '" height="' + c2 + '"></rect>';
      }
      s += '<line class="ba-split" x1="' + nc * c2 + '" x2="' + nc * c2 + '" y1="0" y2="' + N * c2 + '"></line><line class="ba-split" y1="' + nc * c2 + '" y2="' + nc * c2 + '" x1="0" x2="' + N * c2 + '"></line>';
      $("ba-H").setAttribute("viewBox", "0 0 " + N * c2 + " " + N * c2); $("ba-H").innerHTML = s;
      s = ""; var c3 = 10, Sm = last.S, mx = 0;
      if (Sm) {
        Sm.forEach(function (row) { row.forEach(function (v) { mx = Math.max(mx, Math.abs(v)); }); });
        Sm.forEach(function (row, a) { row.forEach(function (v, b) { if (Math.abs(v) > 1e-12) s += '<rect class="ba-mc" x="' + b * c3 + '" y="' + a * c3 + '" width="' + (c3 - 1) + '" height="' + (c3 - 1) + '" opacity="' + (0.2 + 0.8 * Math.log(1 + Math.abs(v)) / Math.log(1 + mx)).toFixed(2) + '"></rect>'; }); });
      }
      $("ba-S").setAttribute("viewBox", "0 0 " + nc * c3 + " " + nc * c3); $("ba-S").innerHTML = s;
      $("ba-J-cap").textContent = "J · " + rows + " × " + N;
      $("ba-H-cap").textContent = "H = JᵀWJ · " + N + " × " + N;
      $("ba-S-cap").textContent = "S = B − E C⁻¹ Eᵀ · " + nc + " × " + nc;
    }
    function stats() {
      var e = B.errors(S, E), it = E.history.length - 1, done = converged();
      $("ba-stats").innerHTML = "<p><b>" + esc(L("Iteration", "Vòng lặp")) + " " + it + "</b>" + (done ? " · " + esc(L("converged", "đã hội tụ")) : "") + "</p>" +
        "<p>" + esc(L("Reprojection error (RMS): ", "Sai số chiếu lại (RMS): ")) + "<b>" + num(e.rms, 2) + " px</b>" + (st.outliers ? " · " + esc(L("inliers ", "điểm đúng ")) + "<b>" + num(e.rmsInliers, 2) + " px</b>" : "") + "</p>" +
        "<p>" + esc(L("Point error vs. truth: ", "Sai số điểm so với thực: ")) + "<b>" + num(e.points, 3) + " m</b></p>" +
        "<p>" + esc(L("Damping λ: ", "Hệ số giảm chấn λ: ")) + sci(E.lambda) + (last.accepted === false ? " · " + esc(L("step rejected", "bước bị loại")) : "") + "</p>" +
        '<p class="ba-small">' + esc(L(S.obs.length + " measurements, " + S.obs.filter(function (o) { return o.out; }).length + " of them outliers; noise " + num(B.SIGMA, 1) + " px",
                                       S.obs.length + " phép đo, trong đó " + S.obs.filter(function (o) { return o.out; }).length + " điểm ngoại lai; nhiễu " + num(B.SIGMA, 1) + " px")) + "</p>";
      document.querySelectorAll("[data-ba-kernel]").forEach(function (b) { b.setAttribute("aria-pressed", String((b.dataset.baKernel || "") === (st.kernel || ""))); });
    }
    function draw() { scene(); cost(); matrices(); stats(); }
    box.addEventListener("click", function (e) {
      var b = e.target.closest("[data-ba],[data-ba-kernel]");
      if (!b) return;
      if (b.dataset.ba === "step") { stop(); step(); }
      else if (b.dataset.ba === "run") run();
      else if (b.dataset.ba === "reset") { st.seed += 1; reset(); }
      else if (b.hasAttribute("data-ba-kernel")) { st.kernel = b.dataset.baKernel || null; reset(); }
    });
    $("ba-out").addEventListener("change", function () { st.outliers = $("ba-out").checked; reset(); });
    document.addEventListener("langchange", function () { if (S) stats(); });
    reset();
  }

  function math() {  // KaTeX renders the TeX equations of the post (loaded with defer from cdnjs)
    if (window.renderMathInElement) renderMathInElement(document.querySelector(".post-body"), {
      delimiters: [{ left: "$$", right: "$$", display: true }, { left: "\\(", right: "\\)", display: false }], throwOnError: false });
  }
  function start() { math(); kernels(); demo(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
