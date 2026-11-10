// Interactive parts of the post: pipeline switch, the two-errors demo (model in demo-core.js) and the citation table.
(function () {
  "use strict";
  var doc = document.documentElement;
  var vi = function () { return doc.dataset.lang === "vi"; };
  var L = function (en, v) { return vi() ? v : en; };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var num = function (n, d) { return Number(n).toLocaleString(vi() ? "vi-VN" : "en-US", { maximumFractionDigits: d || 0, minimumFractionDigits: d || 0 }); };

  // ---- pipeline: switch the text of each block between the two families ----
  function pipeline() {
    var pipe = document.getElementById("vs-pipe");
    if (!pipe) return;
    document.querySelectorAll("[data-vs-mode]").forEach(function (b) {
      b.addEventListener("click", function () {
        pipe.dataset.mode = b.dataset.vsMode;
        document.querySelectorAll("[data-vs-mode]").forEach(function (c) { c.setAttribute("aria-pressed", String(c === b)); });
      });
    });
  }

  // ---- the two-errors demo ----
  function demo() {
    var box = document.getElementById("vs-demo");
    if (!box || !window.VSDemo) return;
    var D = window.VSDemo, $ = function (id) { return document.getElementById(id); };
    var st = { scene: "texture" }, pending = 0;
    function color(name) { return getComputedStyle(box).getPropertyValue(name).trim() || "#0072b2"; }
    function read() {
      return { scene: st.scene, motion: +$("vs-motion").value, level: +$("vs-level").value, gain: +$("vs-gain").value, affine: $("vs-affine").checked };
    }
    function strip(r, o) {
      var c = $("vs-strip"), g = c.getContext("2d"), W = c.width, H = c.height, s = W / D.N, top = 4, h = 30, bot = H - 4 - h;
      g.clearRect(0, 0, W, H);
      [[r.F.img1, top], [r.F.img2, bot]].forEach(function (pair) {
        for (var x = 0; x < D.N; x++) {
          var v = Math.round(255 * Math.min(1, Math.max(0, pair[0][x + D.PAD])));
          g.fillStyle = "rgb(" + v + "," + v + "," + v + ")";
          g.fillRect(x * s, pair[1], Math.ceil(s), h);
        }
      });
      var feat = color("--vs-feat"), bad = color("--vs-bad");
      g.lineWidth = 1.5;
      r.M.m.forEach(function (m) {
        g.strokeStyle = Math.abs(m.d - o.motion) > 2 ? bad : feat;
        g.beginPath(); g.moveTo(m.x1 * s, top + h); g.lineTo(m.x2 * s, bot); g.stroke();
      });
      g.fillStyle = feat;
      r.M.k1.forEach(function (x) { g.fillRect(x * s - 1.5, top + h - 7, 3, 7); });
      r.M.k2.forEach(function (x) { g.fillRect(x * s - 1.5, bot, 3, 7); });
    }
    function plot(id, curve, end, truth, cls, title, note) {
      var W = 600, H = 190, L0 = 34, R0 = 10, T = 26, B = 34, mx = Math.max.apply(null, curve.e) || 1;
      var X = function (t) { return L0 + (t + D.RANGE) / (2 * D.RANGE) * (W - L0 - R0); };
      var Y = function (e) { return H - B - e / mx * (H - B - T); };
      var path = curve.t.map(function (t, i) { return (i ? "L" : "M") + X(t).toFixed(1) + " " + Y(curve.e[i]).toFixed(1); }).join("");
      var svg = '<line class="vs-axis" x1="' + L0 + '" x2="' + (W - R0) + '" y1="' + (H - B) + '" y2="' + (H - B) + '"></line>';
      [-60, -30, 0, 30, 60].forEach(function (t) { svg += '<text x="' + X(t) + '" y="' + (H - B + 16) + '" text-anchor="middle">' + t + "</text>"; });
      svg += '<text x="' + (W - R0) + '" y="' + (H - 4) + '" text-anchor="end">' + esc(L("guessed motion (px)", "chuyển động phỏng đoán (px)")) + "</text>";
      svg += '<line class="vs-truth" x1="' + X(truth) + '" x2="' + X(truth) + '" y1="' + T + '" y2="' + (H - B) + '"></line><text class="vs-lab" x="' + X(truth) + '" y="' + (T - 8) + '" text-anchor="middle">' + esc(L("true", "đúng")) + "</text>";
      if (curve.e.some(function (e) { return e > 0; })) svg += '<path class="vs-curve ' + cls + '" d="' + path + '"></path>';
      svg += '<circle class="vs-start" cx="' + X(0) + '" cy="' + Y(curve.e[Math.round(D.RANGE / 0.25)]) + '" r="4"></circle>';
      if (end !== null) svg += '<circle class="vs-end ' + cls + '" cx="' + X(end) + '" cy="' + Y(curve.e[curve.t.indexOf(end)]) + '" r="6"></circle>';
      $(id).innerHTML = '<p class="vs-plot-title">' + title + '</p><svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + esc(title.replace(/<[^>]+>/g, "")) + '">' + svg + '</svg><p class="vs-result">' + note + "</p>";
    }
    function verdict(end, truth) {
      var ok = Math.abs(end - truth) < 1;
      return (ok ? '<b class="vs-ok">✓ ' : '<b class="vs-no">✗ ') + esc(L(ok ? "found the motion" : "stuck in a local minimum", ok ? "tìm đúng chuyển động" : "kẹt ở cực tiểu cục bộ")) + "</b> · " +
        esc(L("descent from 0 ends at ", "xuất phát từ 0, dừng ở ")) + num(end, 2) + " px (" + esc(L("true ", "đúng: ")) + o_truth(truth) + " px)";
    }
    function o_truth(t) { return num(t); }
    function draw() {
      var o = read(), r = D.run(o);
      $("vs-motion-v").textContent = o.motion + " px";
      $("vs-level-v").textContent = L("level ", "mức ") + o.level + " (" + L("blur ", "làm mờ ") + D.BLUR[o.level] + " px)";
      $("vs-gain-v").textContent = "× " + num(o.gain, 2);
      document.querySelectorAll("[data-vs-scene]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.vsScene === st.scene)); });
      strip(r, o);
      var outl = r.M.m.filter(function (m) { return Math.abs(m.d - o.motion) > 2; }).length;
      var fnote = r.M.m.length < 3 ? '<b class="vs-no">✗ ' + esc(L("too few keypoints: tracking is lost", "quá ít điểm đặc trưng: mất dấu")) + "</b> (" + r.M.k1.length + " / " + r.M.k2.length + ")"
                                   : verdict(r.endR, o.motion) + " · " + r.M.m.length + esc(L(" matches", " cặp khớp")) + (outl ? ", " + outl + esc(L(" wrong", " sai")) : "");
      plot("vs-plot-f", r.R, r.endR, o.motion, "vs-f", esc(L("Feature-based: reprojection error of matched keypoints", "Dựa trên đặc trưng: sai số chiếu lại của các điểm đã khớp")), fnote);
      var floor = Math.min.apply(null, r.P.e), dnote = verdict(r.endP, o.motion);
      if (floor > 1e-6) dnote += " · " + esc(L("the error cannot reach zero: the brightness changed", "sai số không thể về 0: độ sáng đã thay đổi"));
      plot("vs-plot-d", r.P, r.endP, o.motion, "vs-d", esc(L("Direct: photometric error over all pixels", "Trực tiếp: sai số trắc quang trên mọi điểm ảnh")) +
        (o.affine ? esc(L(", with brightness a·I + b", ", có mô hình độ sáng a·I + b")) : ""), dnote);
    }
    function later() { cancelAnimationFrame(pending); pending = requestAnimationFrame(draw); }
    box.addEventListener("input", later);
    box.addEventListener("change", later);
    box.addEventListener("click", function (e) {
      var b = e.target.closest("[data-vs-scene]");
      if (b) { st.scene = b.dataset.vsScene; later(); }
      var p = e.target.closest("[data-vs-preset]");
      if (p) {
        var v = p.dataset.vsPreset.split(",");
        st.scene = v[0]; $("vs-motion").value = v[1]; $("vs-level").value = v[2]; $("vs-gain").value = v[3]; $("vs-affine").checked = v[4] === "1";
        later();
      }
    });
    document.addEventListener("langchange", later);
    var mq = window.matchMedia ? matchMedia("(prefers-color-scheme: dark)") : null;
    new MutationObserver(later).observe(doc, { attributes: true, attributeFilter: ["data-theme"] });
    if (mq && mq.addEventListener) mq.addEventListener("change", later);
    draw();
  }

  // ---- most cited recent systems in the robotics journals ----
  function sota() {
    var box = document.getElementById("vs-sota"), D = window.FAMILY && window.FAMILY.sota;
    if (!box || !D) return;
    function draw() {
      var rows = D.rows.map(function (r, i) {
        return "<tr><td>" + (i + 1) + '</td><td><a href="' + esc(r.url) + '" title="' + esc(r.title) + '">' + esc(r.name) + "</a></td><td class=\"vs-nowrap\">" + esc(r.venue) + " " + r.year +
          "</td><td>" + esc(vi() ? r.vi : r.en) + '</td><td class="vs-num">' + num(r.cites) + '</td><td class="vs-num">' + num(r.rate) + "</td></tr>";
      }).join("");
      box.innerHTML = "<thead><tr><th>#</th><th>" + esc(L("System", "Hệ thống")) + "</th><th>" + esc(L("Journal", "Tạp chí")) + "</th><th>" + esc(L("Family", "Họ")) +
        '</th><th class="vs-num">' + esc(L("Citations", "Trích dẫn")) + '</th><th class="vs-num">' + esc(L("per year", "mỗi năm")) + "</th></tr></thead><tbody>" + rows + "</tbody>";
      var c = document.getElementById("vs-sota-note");
      if (c) c.textContent = L("Citations from OpenAlex on " + D.date + "; ranked by citations per year among " + D.candidates +
        " visual SLAM and odometry papers published in T-RO, RA-L and IJRR since 2019. Citations measure how widely a system is used, not how accurate it is.",
        "Số trích dẫn từ OpenAlex ngày " + D.date + "; xếp hạng theo số trích dẫn mỗi năm trong " + D.candidates +
        " bài về SLAM thị giác và đo hành trình đăng trên T-RO, RA-L và IJRR từ năm 2019. Số trích dẫn cho biết một hệ thống được dùng rộng rãi đến đâu, không phải nó chính xác đến đâu.");
    }
    document.addEventListener("langchange", draw);
    draw();
  }

  function start() { pipeline(); demo(); sota(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
