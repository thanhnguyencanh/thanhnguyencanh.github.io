// Research Trends: one card per venue, a trend view for the selected venue, and topics across venues (data: trends/data.json).
(function () {
  "use strict";
  var root = document.getElementById("tr");
  if (!root) return;
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var num = function (n) { return Number(n).toLocaleString("en-US"); };
  var pct = function (v) { return (100 * v).toFixed(100 * v < 10 ? 1 : 0) + "%"; };
  var pp = function (v) { return (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(100 * v).toFixed(1) + " pp"; };
  var f1 = function (v) { return v.toFixed(1); };
  var span = function (w) { return w[0] === w[1] ? String(w[0]) : w[0] + "–" + w[1]; };
  var explorer = function (q) { return "../explorer/?" + Object.keys(q).filter(function (k) { return q[k] !== "" && q[k] !== undefined; }).map(function (k) { return k + "=" + encodeURIComponent(q[k]); }).join("&"); };
  var GROUPS = [
    ["Robotics conferences", function (v) { return v.field === "rob" && v.kind === "conference"; }],
    ["Robotics journals", function (v) { return v.field === "rob" && v.kind === "journal"; }],
    ["Computer vision", function (v) { return v.field === "cv"; }],
    ["Machine learning", function (v) { return v.field === "ml"; }]
  ];

  fetch(root.dataset.src).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(init).catch(function () {
    root.insertAdjacentHTML("afterbegin", '<p class="tr-error">The trend data could not be loaded. Please reload the page.</p>');
  });

  function init(D) {
    var T = D.topics, V = D.venues, by = {}, st = { show: "all", all: false };
    V.forEach(function (v) {
      by[v.id] = v;
      var sum = function (w) { return v.years.reduce(function (s, y, i) { return w.indexOf(y) >= 0 ? s + v.n[i] : s; }, 0); };
      var share = function (w, i) { var n = sum(w); return n ? v.years.reduce(function (s, y, k) { return w.indexOf(y) >= 0 ? s + v.topics[i][k] : s; }, 0) / n : 0; };
      v.total = v.n.reduce(function (a, b) { return a + b; }, 0);
      v.shareR = T.map(function (t, i) { return share(v.recent, i); });
      v.shareE = T.map(function (t, i) { return share(v.early, i); });
      v.shift = T.map(function (t, i) { return v.shareR[i] - v.shareE[i]; });
      var last = v.years.length - 1 - (v.partial ? 1 : 0), back = -1;  // a journal's current year is still growing
      v.last = last;
      v.years.forEach(function (y, i) { if (y <= v.years[last] - 5) back = i; });
      v.growth = back >= 0 && v.n[back] ? { x: v.n[last] / v.n[back], y: v.years[back] } : null;
      v.topTopic = v.shareR.indexOf(Math.max.apply(null, v.shareR));
    });
    var sel = by[location.hash.slice(1)] ? location.hash.slice(1) : V[0].id;

    var soFar = function (v, i) { return v.partial && i === v.years.length - 1; };
    function spark(v, W, H) {
      var mx = Math.max.apply(null, v.n), bw = W / v.n.length, s = "";
      v.n.forEach(function (n, i) { var h = Math.max(1, n / mx * (H - 2)); s += '<rect' + (soFar(v, i) ? ' class="is-partial"' : "") + ' x="' + f1(i * bw + 0.5) + '" y="' + f1(H - h) + '" width="' + f1(bw - 1) + '" height="' + f1(h) + '" rx="1"><title>' + v.years[i] + (soFar(v, i) ? " so far" : "") + ": " + num(n) + " papers</title></rect>"; });
      return '<svg class="tr-spark" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Papers per year">' + s + "</svg>";
    }
    function card(v) {
      var last = v.last, rising = v.rising.slice(0, 3).map(function (x) { return esc(x.t); }).join(", ");
      return '<article class="tr-card' + (v.id === sel ? " is-on" : "") + '" data-v="' + v.id + '">' +
        '<div class="tr-card-top"><h3>' + esc(v.short) + '</h3><span class="tr-kind">' + (v.kind === "journal" ? "Journal" : "Conference") + "</span></div>" +
        '<p class="tr-full">' + esc(v.name) + "</p>" +
        '<p class="tr-big"><b>' + num(v.n[last]) + "</b> papers in " + v.years[last] + (v.growth ? ' <span class="tr-growth">×' + v.growth.x.toFixed(1) + " since " + v.growth.y + "</span>" : "") + "</p>" +
        spark(v, 240, 34) +
        '<p class="tr-line"><span>Rising terms</span>' + rising + "</p>" +
        '<p class="tr-line"><span>Largest topic</span>' + esc(T[v.topTopic].name) + " · " + pct(v.shareR[v.topTopic]) + "</p>" +
        '<div class="tr-actions"><button class="filter-chip" type="button" data-sel="' + v.id + '" aria-pressed="' + (v.id === sel) + '">Trends</button>' +
        '<a class="resource-link" href="' + esc(explorer({ venues: v.id })) + '">Papers ↗</a><a class="resource-link" href="' + esc(v.site) + '">Website ↗</a></div></article>';
    }
    function cards() {
      var f = document.getElementById("tr-filter");
      f.innerHTML = [["all", "All venues"], ["conference", "Conferences"], ["journal", "Journals"]].map(function (o) {
        return '<button class="filter-chip" type="button" data-show="' + o[0] + '" aria-pressed="' + (st.show === o[0]) + '">' + o[1] + "</button>";
      }).join("");
      document.getElementById("tr-cards").innerHTML = GROUPS.map(function (g) {
        var list = V.filter(g[1]).filter(function (v) { return st.show === "all" || v.kind === st.show; });
        return list.length ? '<h2 class="tr-group">' + g[0] + '</h2><div class="tr-grid">' + list.map(card).join("") + "</div>" : "";
      }).join("");
    }

    // ---- the selected venue ----
    function bars(v) {
      var W = 460, H = 200, P = 44, B = 24, Tp = 14, mx = Math.max.apply(null, v.n), bw = (W - P - 4) / v.n.length, s = "";
      var nice = Math.pow(10, Math.floor(Math.log10(mx))), top = Math.ceil(mx / nice) * nice, Y = function (n) { return H - B - n / top * (H - B - Tp); };
      [0, top / 2, top].forEach(function (t) { s += '<line class="tr-grid-l" x1="' + P + '" x2="' + W + '" y1="' + f1(Y(t)) + '" y2="' + f1(Y(t)) + '"></line><text x="' + (P - 6) + '" y="' + f1(Y(t) + 4) + '" text-anchor="end">' + num(t) + "</text>"; });
      v.n.forEach(function (n, i) {
        var x = P + i * bw + 2, w = bw - 4;
        s += '<rect class="tr-bar' + (soFar(v, i) ? " is-partial" : "") + '" x="' + f1(x) + '" y="' + f1(Y(n)) + '" width="' + f1(w) + '" height="' + f1(Y(0) - Y(n)) + '" rx="2"><title>' + v.years[i] + (soFar(v, i) ? " so far" : "") + ": " + num(n) + " papers</title></rect>";
        if (i === 0 || i === v.n.length - 1 || v.n.length <= 8) s += '<text x="' + f1(x + w / 2) + '" y="' + (H - 7) + '" text-anchor="middle">' + v.years[i] + (soFar(v, i) ? "*" : "") + "</text>";
      });
      return '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Papers per year">' + s + "</svg>";
    }
    function shifts(v) {
      var idx = T.map(function (t, i) { return i; }), up = idx.slice().sort(function (a, b) { return v.shift[b] - v.shift[a]; }).filter(function (i) { return v.shift[i] > 0.002; }).slice(0, 6);
      var down = idx.slice().sort(function (a, b) { return v.shift[a] - v.shift[b]; }).filter(function (i) { return v.shift[i] < -0.002; }).slice(0, 4), rows = up.concat(down);
      var W = 500, L = 236, R = 64, G = 58, rh = 22, H = rows.length * rh + 8, mx = Math.max.apply(null, rows.map(function (i) { return Math.abs(v.shift[i]); }).concat([0.01]));
      var mid = L + G + (W - L - G - R) * (down.length ? 0.3 : 0), X = function (d) { return mid + d / mx * (d > 0 ? W - R - mid : mid - L - G); }, s = "";
      s += '<line class="tr-axis" x1="' + f1(mid) + '" x2="' + f1(mid) + '" y1="0" y2="' + H + '"></line>';
      rows.forEach(function (i, k) {
        var y = 4 + k * rh, d = v.shift[i], x0 = Math.min(X(0), X(d)), w = Math.abs(X(d) - X(0));
        s += '<a href="' + esc(explorer({ venues: v.id, topics: T[i].id, from: v.recent[0], to: v.recent[1] })) + '"><text class="tr-lab" x="' + (L - 8) + '" y="' + (y + 14) + '" text-anchor="end">' + esc(T[i].name) + "</text>" +
          '<rect class="' + (d > 0 ? "tr-up" : "tr-down") + '" x="' + f1(x0) + '" y="' + (y + 3) + '" width="' + f1(Math.max(1, w)) + '" height="' + (rh - 8) + '" rx="2"><title>' + esc(T[i].name) + ": " + pct(v.shareE[i]) + " → " + pct(v.shareR[i]) + " of papers</title></rect>" +
          '<text x="' + f1(d > 0 ? X(d) + 5 : X(d) - 5) + '" y="' + (y + 14) + '" text-anchor="' + (d > 0 ? "start" : "end") + '">' + pp(d) + "</text></a>";
      });
      return '<div class="tr-scroll"><svg viewBox="0 0 ' + W + " " + H + '" style="min-width:440px" role="img" aria-label="Topics with the largest change in share">' + s + "</svg></div>";
    }
    function heat(v) {
      var order = T.map(function (t, i) { return i; }).sort(function (a, b) { return v.shareR[b] - v.shareR[a]; });
      var rows = st.all ? order : order.slice(0, 14), ny = v.years.length, L = 232, R = 86, cw = Math.max(26, Math.min(48, Math.floor(620 / ny))), rh = 22;
      var W = L + ny * cw + R, H = rows.length * rh + 26, s = "", mx = 0;
      rows.forEach(function (i) { v.years.forEach(function (y, k) { if (v.n[k]) mx = Math.max(mx, v.topics[i][k] / v.n[k]); }); });
      v.years.forEach(function (y, k) { if (k === 0 || k === ny - 1 || k % 2 === (ny - 1) % 2) s += '<text x="' + (L + k * cw + cw / 2) + '" y="14" text-anchor="middle">' + y + "</text>"; });
      s += '<text x="' + (L + ny * cw + 8) + '" y="14">' + esc(span(v.recent)) + "</text>";
      rows.forEach(function (i, r) {
        var y = 22 + r * rh;
        s += '<text class="tr-lab" x="' + (L - 8) + '" y="' + (y + 15) + '" text-anchor="end">' + esc(T[i].name) + "</text>";
        v.years.forEach(function (yr, k) {
          var sh = v.n[k] ? v.topics[i][k] / v.n[k] : 0, op = sh > 0 ? 0.06 + 0.94 * sh / (mx || 1) : 0;
          s += '<a href="' + esc(explorer({ venues: v.id, topics: T[i].id, from: yr, to: yr })) + '"><rect class="tr-cell" x="' + (L + k * cw + 1) + '" y="' + (y + 1) + '" width="' + (cw - 2) + '" height="' + (rh - 2) + '" rx="2" style="fill-opacity:' + op.toFixed(3) + '"><title>' +
            esc(T[i].name) + ", " + yr + ": " + num(v.topics[i][k]) + " of " + num(v.n[k]) + " papers (" + pct(sh) + ")</title></rect></a>";
        });
        s += '<text x="' + (L + ny * cw + 8) + '" y="' + (y + 15) + '">' + pct(v.shareR[i]) + "</text>";
      });
      return '<svg viewBox="0 0 ' + W + " " + H + '" style="width:' + W + 'px;max-width:none" role="img" aria-label="Share of papers per topic and year">' + s + "</svg>" + legend(mx);
    }
    function legend(mx) {
      return '<p class="tr-legend"><span>0%</span><i class="tr-ramp" aria-hidden="true"></i><span>' + pct(mx) + "</span> of a year's papers</p>";
    }
    function termSpark(v, c) {
      var W = 72, H = 18, sh = c.map(function (x, k) { return v.n[k] ? x / v.n[k] : 0; }), mx = Math.max.apply(null, sh.concat([1e-9]));
      return '<svg class="tr-tspark" viewBox="0 0 ' + W + " " + H + '" aria-hidden="true"><path d="' + sh.map(function (x, k) { return (k ? "L" : "M") + f1(k / Math.max(1, sh.length - 1) * (W - 2) + 1) + " " + f1(H - 2 - x / mx * (H - 4)); }).join("") + '"></path></svg>';
    }
    function terms(v, list, up) {
      if (!list.length) return '<p class="tr-empty">No term passes the minimum count.</p>';
      return '<ol class="tr-terms">' + list.map(function (x) {
        var q = /\s/.test(x.t) ? '"' + x.t + '"' : x.t;
        return '<li><a href="' + esc(explorer({ q: q, venues: v.id })) + '"><span class="tr-term">' + esc(x.t) + "</span>" + termSpark(v, x.c) +
          '<span class="tr-val ' + (up ? "is-up" : "is-down") + '">' + pct(x.e) + " → " + pct(x.r) + "</span></a></li>";
      }).join("") + "</ol>";
    }
    function detail() {
      var v = by[sel], box = document.getElementById("tr-detail"), w = span(v.early) + " → " + span(v.recent);
      box.innerHTML = '<div class="tr-dhead"><div><p class="eyebrow">' + (v.kind === "journal" ? "Journal" : "Conference") + " · " + esc(D.fields.filter(function (f) { return f.id === v.field; })[0].name) + "</p>" +
        "<h2>" + esc(v.short) + ' <span class="tr-dname">' + esc(v.name) + "</span></h2>" +
        '<p class="tr-dmeta">' + v.years[0] + "–" + v.years[v.years.length - 1] + " in dblp · " + num(v.total) + ' papers · topic shifts compare <b>' + esc(span(v.early)) + "</b> with <b>" + esc(span(v.recent)) + "</b></p></div>" +
        '<div class="tr-actions"><a class="resource-link" href="' + esc(explorer({ venues: v.id })) + '">Search its papers ↗</a><a class="resource-link" href="' + esc(v.site) + '">Website ↗</a></div></div>' +
        '<div class="tr-dgrid">' +
        '<figure class="tr-panel"><figcaption>Papers per year</figcaption>' + bars(v) + "</figure>" +
        '<figure class="tr-panel"><figcaption>Biggest topic shifts, ' + esc(w) + ' <span>(share of papers)</span></figcaption>' + shifts(v) + "</figure>" +
        '<figure class="tr-panel tr-wide"><figcaption>Topics over time <span>(share of each year\'s papers; select a cell to see its papers)</span></figcaption><div class="tr-scroll">' + heat(v) + "</div>" +
        '<button class="filter-chip" type="button" data-all aria-pressed="' + st.all + '">' + (st.all ? "Show the top 14 topics" : "Show all " + T.length + " topics") + "</button></figure>" +
        '<figure class="tr-panel"><figcaption>Rising title terms, ' + esc(w) + "</figcaption>" + terms(v, v.rising, true) + "</figure>" +
        '<figure class="tr-panel"><figcaption>Fading title terms, ' + esc(w) + "</figcaption>" + terms(v, v.falling, false) + "</figure></div>";
    }

    // ---- topics across venues ----
    function compare() {
      var cols = [];
      GROUPS.forEach(function (g) { V.filter(g[1]).forEach(function (v) { cols.push(v); }); });
      var L = 236, cw = 46, rh = 21, W = L + cols.length * cw + 4, groups = ["Robotics", "Learning", "Vision"], s = "", y = 30, mx = 0;
      cols.forEach(function (v) { v.shareR.forEach(function (x) { mx = Math.max(mx, x); }); });
      cols.forEach(function (v, k) {
        s += '<a href="#' + v.id + '" data-jump="' + v.id + '"><text class="tr-col" x="' + (L + k * cw + cw / 2) + '" y="18" text-anchor="middle">' + esc(v.short.replace("Sci. Robotics", "SciRob")) + "</text></a>";
      });
      groups.forEach(function (g) {
        s += '<text class="tr-ghead" x="4" y="' + (y + 14) + '">' + g + "</text>";
        y += rh;
        T.forEach(function (t, i) {
          if (t.group !== g) return;
          s += '<text class="tr-lab" x="' + (L - 8) + '" y="' + (y + 14) + '" text-anchor="end">' + esc(t.name) + "</text>";
          cols.forEach(function (v, k) {
            var sh = v.shareR[i], op = sh > 0 ? 0.05 + 0.95 * sh / mx : 0;
            s += '<a href="#' + v.id + '" data-jump="' + v.id + '"><rect class="tr-cell" x="' + (L + k * cw + 1) + '" y="' + (y + 1) + '" width="' + (cw - 2) + '" height="' + (rh - 2) + '" rx="2" style="fill-opacity:' + op.toFixed(3) + '"><title>' +
              esc(v.short + ", " + t.name + ": " + pct(sh) + " of papers in " + span(v.recent)) + "</title></rect></a>";
          });
          y += rh;
        });
      });
      document.getElementById("tr-compare").innerHTML = '<svg viewBox="0 0 ' + W + " " + (y + 6) + '" style="width:' + W + 'px;max-width:none" role="img" aria-label="Share of papers per topic and venue">' + s + "</svg>" +
        legend(mx).replace(" of a year's papers", " of a venue's papers in its last two editions");
    }

    function select(id, scroll) {
      if (!by[id]) return;
      sel = id;
      document.querySelectorAll(".tr-card").forEach(function (c) { c.classList.toggle("is-on", c.dataset.v === id); });
      document.querySelectorAll("[data-sel]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.sel === id)); });
      detail();
      if (location.hash.slice(1) !== id) history.replaceState(null, "", "#" + id);
      if (scroll) document.getElementById("tr-detail").scrollIntoView({ behavior: "smooth", block: "start" });
    }
    root.addEventListener("click", function (e) {
      var b = e.target.closest("[data-sel],[data-show],[data-all],[data-jump]");
      if (!b) return;
      if (b.hasAttribute("data-sel")) select(b.dataset.sel, true);
      else if (b.hasAttribute("data-jump")) { e.preventDefault(); select(b.dataset.jump, true); }
      else if (b.hasAttribute("data-show")) { st.show = b.dataset.show; cards(); }
      else if (b.hasAttribute("data-all")) { st.all = !st.all; detail(); }
    });
    window.addEventListener("hashchange", function () { if (by[location.hash.slice(1)] && location.hash.slice(1) !== sel) select(location.hash.slice(1), true); });
    cards(); detail(); compare();
    var status = document.getElementById("tr-status");
    if (status) status.hidden = true;
  }
})();
