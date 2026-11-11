// "World models and SLAM": the SLAM / world-model switch and the growth chart (data in data.js, window.FAMILY.trend).
(function () {
  "use strict";
  var doc = document.documentElement;
  var vi = function () { return doc.dataset.lang === "vi"; };
  var L = function (en, v) { return vi() ? v : en; };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var num = function (n, d) { return Number(n).toLocaleString(vi() ? "vi-VN" : "en-US", { maximumFractionDigits: d || 0, minimumFractionDigits: d || 0 }); };

  function loop() {
    var box = document.getElementById("wm-loop");
    if (!box) return;
    document.querySelectorAll("[data-wm-mode]").forEach(function (b) {
      b.addEventListener("click", function () {
        box.dataset.mode = b.dataset.wmMode;
        document.querySelectorAll("[data-wm-mode]").forEach(function (c) { c.setAttribute("aria-pressed", String(c === b)); });
      });
    });
  }

  function trend() {
    var box = document.getElementById("wm-trend"), T = window.FAMILY && window.FAMILY.trend;
    if (!box || !T) return;
    function nice(v) { var p = Math.pow(10, Math.floor(Math.log10(v))), m = v / p; return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 5 ? 5 : 10) * p; }
    function draw() {
      var n = T.years.length, W = 1000, H = 300, Lm = 44, B = 30, Tm = 22, bw = (W - Lm - 10) / n;
      var tot = T.years.map(function (y, i) { return T.spatial[i] + T.other[i]; }), mx = nice(Math.max.apply(null, tot) || 1);
      var Y = function (v) { return H - B - v / mx * (H - B - Tm); }, last = T.years[n - 1], svg = "";
      [0, 0.5, 1].forEach(function (f) {
        svg += '<line class="grid" x1="' + Lm + '" x2="' + W + '" y1="' + Y(f * mx) + '" y2="' + Y(f * mx) + '"></line><text x="' + (Lm - 6) + '" y="' + (Y(f * mx) + 4) + '" text-anchor="end">' + num(f * mx) + "</text>";
      });
      T.years.forEach(function (y, i) {
        var x = Lm + i * bw + 4, w = bw - 8, s = T.spatial[i], o = T.other[i];
        var tip = y + (y === last ? L(" (so far)", " (đến nay)") : "") + ": " + num(s + o) + L(" papers", " bài") + " · " + num(s) + L(" about 3D or space", " về 3D hoặc không gian") +
          " · " + num(T.rate[i], 1) + L(" per 10,000 papers", " trên 10.000 bài") + " · " + L("robotics ", "robot ") + T.rob[i] + L(", vision ", ", thị giác ") + T.cv[i] + L(", ML ", ", học máy ") + T.ml[i];
        if (s) svg += '<rect class="wm-sp" x="' + x.toFixed(1) + '" y="' + Y(s).toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + (Y(0) - Y(s)).toFixed(1) + '" rx="2"><title>' + esc(tip) + "</title></rect>";
        if (o) svg += '<rect class="wm-ot" x="' + x.toFixed(1) + '" y="' + Y(s + o).toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + (Y(s) - Y(s + o)).toFixed(1) + '" rx="2"><title>' + esc(tip) + "</title></rect>";
        if (s + o >= 10) svg += '<text class="lab" x="' + (x + w / 2).toFixed(1) + '" y="' + (Y(s + o) - 6).toFixed(1) + '" text-anchor="middle">' + num(s + o) + "</text>";
        svg += '<text x="' + (x + w / 2).toFixed(1) + '" y="' + (H - 10) + '" text-anchor="middle">' + y + (y === last ? "*" : "") + "</text>";
      });
      box.innerHTML = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + esc(L("World-model papers per year", "Số bài về mô hình thế giới theo năm")) + '">' + svg + "</svg>" +
        '<div class="ft-legend"><span><i class="wm-sp"></i>' + esc(L("About a 3D or spatial world (occupancy, scenes, maps, memory, driving)", "Về thế giới 3D hoặc không gian (chiếm chỗ, cảnh, bản đồ, bộ nhớ, lái xe)")) +
        '</span><span><i class="wm-ot"></i>' + esc(L("Other world-model papers", "Các bài về mô hình thế giới khác")) + "</span></div>";
      var note = document.getElementById("wm-trend-note");
      if (note) note.textContent = L("* " + last + " so far: " + T.partial.join(", ") + " " + last + " are not in dblp yet. 3D or spatial means the title also names occupancy, scenes, maps, SLAM, memory, Gaussians, point clouds, LiDAR or driving.",
        "* " + last + " tính đến nay: " + T.partial.join(", ") + " " + last + " chưa có trong dblp. “3D hoặc không gian” nghĩa là tiêu đề còn nhắc đến chiếm chỗ, cảnh, bản đồ, SLAM, bộ nhớ, Gaussian, đám mây điểm, LiDAR hoặc lái xe.");
    }
    document.addEventListener("langchange", draw);
    draw();
  }

  function start() { loop(); trend(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
