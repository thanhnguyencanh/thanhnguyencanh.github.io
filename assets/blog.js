// PAIRS Lab blog: language switch (English / Vietnamese) and the "family tree" explorer used by data posts.
// A post provides window.FAMILY = {root, trees:[{id, en, vi, field, nodes:[{id, parent, en, vi, den, dvi}]}], items:[...], ...}.
(function () {
  "use strict";
  var doc = document.documentElement;
  var lang = function () { return doc.dataset.lang === "vi" ? "vi" : "en"; };
  var params = new URLSearchParams(location.search);
  function setParam(k, v) {
    if (v === null || v === undefined || v === "") params.delete(k); else params.set(k, v);
    var s = params.toString();
    history.replaceState(null, "", location.pathname + (s ? "?" + s : "") + location.hash);
  }
  var switches = [].slice.call(document.querySelectorAll("[data-set-lang]"));
  function applyLang(l, save) {
    doc.dataset.lang = l; doc.lang = l;
    switches.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.setLang === l)); });
    if (save) { try { localStorage.setItem("blog-lang", l); } catch (e) {} setParam("lang", l === "vi" ? "vi" : null); }
    document.dispatchEvent(new CustomEvent("langchange"));
  }
  switches.forEach(function (b) { b.addEventListener("click", function () { applyLang(b.dataset.setLang, true); }); });
  applyLang(lang(), false);

  var host = document.getElementById("ft");
  if (!window.FAMILY || !host) return;
  if (window.FAMILY.shards) loadShards(window.FAMILY).then(start, function (e) {
    var p = document.getElementById("ft-panel"); if (p) p.textContent = "Could not load the papers (" + e + "). Please reload the page.";
  }); else start(window.FAMILY);

  // Papers kept in the Paper Explorer files: the post brings one branch label per paper, in file order.
  function loadShards(F) {
    var S0 = F.shards, wait = document.getElementById("ft-panel");
    if (wait) wait.textContent = "Loading papers…";
    var get = function (name) { return fetch(S0.base + name).then(function (r) { if (!r.ok) throw r.status; return r.json(); }); };
    return get("index.json").then(function (index) {
      var codes = index.codes || [];
      var expand = function (l) { if (/^10\./.test(l)) return "https://doi.org/" + l; codes.forEach(function (c) { l = l.split(c[0]).join(c[1]); }); return l; };
      return Promise.all(S0.venues.map(function (v) { return get(v + ".json"); })).then(function (files) {
        var items = [];
        files.forEach(function (d, k) {
          var v = S0.venues[k], lab = S0.labels[v];
          if (d.t.length !== S0.counts[v] || lab.length !== d.t.length) throw "the paper list changed; run scripts/make_blog_robotics_tree.py again";
          for (var i = 0; i < d.t.length; i++) {
            items.push({ title: d.t[i], authors: d.a[i], year: d.y[i], venue: S0.names[v] + " " + d.y[i], url: expand(d.l[i]), n: S0.leaves[S0.alphabet.indexOf(lab[i])] });
          }
        });
        items.sort(function (a, b) { return a.year - b.year || a.title.localeCompare(b.title); });
        items.forEach(function (it, i) { it.id = i; });
        F.items = items;
        return F;
      });
    });
  }

  function start(D) {
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#8C7B00", "#7E57C2", "#5D7087"];
  var S = {
    en: { search: "Search", all: "All", more: "Show more", covered: "Covered in", ref: "Reference", none: "Nothing matches this search.", years: "years",
          share: "Share", count: "Count", of: "of", shown: "shown", in: "in", authors: "Authors", open: "Open paper", method: "Method", task: "Task",
          clear: "Clear filter", cell: "Filtered by", subtree: "Inside" },
    vi: { search: "Tìm kiếm", all: "Tất cả", more: "Xem thêm", covered: "Có trong", ref: "Tài liệu", none: "Không có kết quả phù hợp.", years: "năm",
          share: "Tỷ lệ", count: "Số lượng", of: "trên", shown: "đang hiển thị", in: "trong", authors: "Tác giả", open: "Mở bài báo", method: "Phương pháp", task: "Nhiệm vụ",
          clear: "Bỏ lọc", cell: "Lọc theo", subtree: "Bên trong" }
  };
  var t = function (k) { return S[lang()][k]; };
  var num = function (n) { return Number(n).toLocaleString(lang() === "vi" ? "vi-VN" : "en-US"); };  // 1,490 / 1.490 (not for years)
  var word = function (n) { var w = (D.itemWord || { en: ["system", "systems"], vi: ["hệ thống", "hệ thống"] })[lang()]; return n === 1 ? w[0] : w[1]; };
  var label = function (o) { return o ? (o[lang()] || o.en) : ""; };
  var desc = function (o) { return o ? (lang() === "vi" ? o.dvi : o.den) || "" : ""; };
  var title = function (it) { return it.name || it.title; };
  var tipAttr = function (h) { return ' data-tip="' + esc(h) + '"'; };

  // ---- index the trees ----
  var trees = D.trees.map(function (tr, ti) {
    var byId = {}, kids = { "": [] };
    tr.nodes.forEach(function (n) { byId[n.id] = n; (kids[n.parent || ""] = kids[n.parent || ""] || []).push(n); });
    kids[""].forEach(function (n, i) { n.color = n.color || COLORS[i % COLORS.length]; });  // a node may bring its own colour (grey for "Other")
    tr.nodes.forEach(function (n) { if (n.parent) n.color = byId[n.parent].color; });
    return { def: tr, byId: byId, kids: kids, top: kids[""], ti: ti };
  });
  var years = D.items.map(function (i) { return i.year; });
  var Y0 = Math.min.apply(null, years), Y1 = Math.max.apply(null, years);
  var leafInTree = D.items.length <= 400;
  var st = { ti: Math.max(0, trees.findIndex(function (x) { return x.def.id === params.get("tree"); })), node: null, item: null,
             q: params.get("q") || "", cell: null, open: {}, show: 12, chartMode: "share" };
  var T = function () { return trees[st.ti]; };
  var leafOf = function (it, tr) { return tr.byId[it[tr.def.field]]; };
  var topOf = function (it, tr) { var n = leafOf(it, tr); return n && n.parent ? tr.byId[n.parent] : n; };
  function inNode(it, tr, node) { if (!node) return true; var l = leafOf(it, tr); return !!l && (l.id === node.id || l.parent === node.id); }
  function matches(it) {
    if (st.cell) { if (topOf(it, trees[0]).id !== st.cell[0] || topOf(it, trees[1]).id !== st.cell[1]) return false; }
    if (!st.q) return true;
    var hay = (title(it) + " " + (it.authors || "") + " " + (it.cite || "")).toLowerCase();
    return st.q.toLowerCase().split(/\s+/).filter(Boolean).every(function (w) { return hay.indexOf(w) >= 0; });
  }
  var filtered = function () { return D.items.filter(matches); };
  function mark(s) {
    var out = esc(s);
    st.q.split(/\s+/).filter(function (w) { return w.length > 1; }).forEach(function (w) {
      out = out.replace(new RegExp("(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig"), "<mark>$1</mark>");
    });
    return out;
  }

  // ---- tooltip ----
  var tip = document.createElement("div"); tip.className = "ft-tip"; tip.hidden = true; document.body.appendChild(tip);
  host.addEventListener("mousemove", function (e) {
    var el = e.target.closest("[data-tip]");
    if (!el) { tip.hidden = true; return; }
    tip.innerHTML = el.getAttribute("data-tip"); tip.hidden = false;
    tip.style.left = Math.min(innerWidth - tip.offsetWidth - 10, e.clientX + 14) + "px";
    tip.style.top = Math.min(innerHeight - tip.offsetHeight - 10, e.clientY + 14) + "px";
  });
  host.addEventListener("mouseleave", function () { tip.hidden = true; });

  // ---- stats ----
  function stats() {
    var tr = trees[0];
    var set = { items: num(D.items.length), lineages: tr.top.filter(function (n) { return !n.other; }).length, branches: tr.def.nodes.length - tr.top.length, span: Y0 + "–" + Y1,
                sources: D.sources ? Object.keys(D.sources).length : 0, editions: new Set(years).size };
    document.querySelectorAll("[data-stat]").forEach(function (el) { el.textContent = set[el.dataset.stat]; });
    document.querySelectorAll("[data-fact]").forEach(function (el) { var f = (D.facts || {})[el.dataset.fact]; if (f) el.innerHTML = esc(label(f)).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>"); });
  }

  // ---- tree ----
  function countIn(node, tr, list) { return list.filter(function (it) { return inNode(it, tr, node); }).length; }
  function treeHTML() {
    var tr = T(), list = filtered();
    function row(node, depth) {
      var kids = tr.kids[node.id] || [], n = countIn(node, tr, list), open = !!st.open[node.id];
      var items = leafInTree && !kids.length ? list.filter(function (it) { return leafOf(it, tr) === node; }).sort(function (a, b) { return a.year - b.year; }) : [];
      var expandable = kids.length || items.length;
      var h = '<li><button type="button" class="ft-row' + (n ? "" : " is-empty") + '" data-node="' + esc(node.id) + '" aria-current="' + (st.node === node.id && st.item === null) + '"' +
        (expandable ? ' aria-expanded="' + open + '"' : "") + '><span class="ft-caret">' + (expandable ? (open ? "▾" : "▸") : "") + '</span><span class="ft-dot" style="background:' + node.color +
        '"></span><span class="ft-name">' + esc(label(node)) + '</span><span class="ft-n">' + num(n) + "</span></button>";
      if (open && kids.length) h += "<ul>" + kids.map(function (k) { return row(k, depth + 1); }).join("") + "</ul>";
      if (open && items.length) h += "<ul>" + items.map(function (it) {
        return '<li><button type="button" class="ft-row is-leaf" data-item="' + it.id + '" aria-current="' + (st.item === it.id) + '"><span class="ft-caret"></span><span class="ft-name">' +
          mark(title(it)) + '</span><span class="ft-y">' + it.year + "</span></button></li>";
      }).join("") + "</ul>";
      return h + "</li>";
    }
    var all = list.length;
    return '<ul><li><button type="button" class="ft-row" data-node="" aria-current="' + (st.node === null && st.item === null) + '"><span class="ft-caret">▾</span>' +
      '<span class="ft-name"><b>' + esc(label(D.root)) + '</b></span><span class="ft-n">' + num(all) + "</span></button><ul>" +
      tr.top.map(function (n) { return row(n, 1); }).join("") + "</ul></li></ul>";
  }

  // ---- panel ----
  function spark(list) {
    var W = 600, H = 70, n = Y1 - Y0 + 1, bw = W / n, by = {};
    list.forEach(function (it) { by[it.year] = (by[it.year] || 0) + 1; });
    var mx = Math.max.apply(null, Object.keys(by).map(function (k) { return by[k]; }).concat([1]));
    var bars = "";
    for (var y = Y0; y <= Y1; y++) {
      var v = by[y] || 0, h = v ? Math.max(2, (H - 16) * v / mx) : 0;
      bars += '<rect x="' + ((y - Y0) * bw + 1).toFixed(1) + '" y="' + (H - 14 - h).toFixed(1) + '" width="' + Math.max(1, bw - 2).toFixed(1) + '" height="' + h.toFixed(1) +
        '" rx="2"' + tipAttr(y + ": " + v + " " + esc(word(v))) + "></rect>";
    }
    return '<svg class="ft-spark" viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="none" role="img" aria-label="' + esc(word(2)) + ' per year">' + bars +
      '<text x="0" y="' + (H - 2) + '">' + Y0 + '</text><text x="' + W + '" y="' + (H - 2) + '" text-anchor="end">' + Y1 + "</text></svg>";
  }
  function crumbs(node) {
    var tr = T(), chain = [];
    for (var n = node; n; n = n.parent ? tr.byId[n.parent] : null) chain.unshift(n);
    return '<nav class="ft-crumbs"><button type="button" data-node="">' + esc(label(D.root)) + "</button>" +
      chain.map(function (n) { return '<span>›</span><button type="button" data-node="' + esc(n.id) + '">' + esc(label(n)) + "</button>"; }).join("") + "</nav>";
  }
  function itemSub(it) {
    if (it.authors) return esc(it.authors.length > 110 ? it.authors.slice(0, 107) + "…" : it.authors) + (it.venue ? " · " + esc(it.venue) : "");
    return (it.sources || []).map(function (s) { return esc(label(D.sources[s]).split(" (")[0]); }).join(" · ");
  }
  function panelHTML() {
    var tr = T(), list = filtered();
    if (st.item !== null) {
      var it = D.items[st.item], node = leafOf(it, tr), h = crumbs(node);
      h += "<h3>" + esc(title(it)) + "</h3><div class=\"ft-metrics\"><span><b>" + it.year + "</b></span><span>" + esc(label(node)) + "</span></div>";
      if (it.den) h += '<p class="ft-desc">' + esc(lang() === "vi" ? it.dvi || it.den : it.den) + "</p>";  // a short description, when the post gives one
      if (it.authors) h += '<p class="ft-desc"><b>' + t("authors") + ":</b> " + esc(it.authors) + (it.venue ? " · " + esc(it.venue) : "") + "</p>";
      if (trees.length > 1) h += '<p class="ft-desc">' + trees.map(function (x) { var l = leafOf(it, x); return "<b>" + esc(label(x.def)) + ":</b> " + (l.parent ? esc(label(x.byId[l.parent])) + " › " : "") + esc(label(l)); }).join("<br>") + "</p>";
      if (it.cite) h += '<p class="ft-desc"><b>' + t("ref") + ':</b></p><p class="ft-cite">' + esc(it.cite) + "</p>";
      if (it.sources) h += '<p class="ft-desc"><b>' + t("covered") + ':</b></p><div class="ft-src">' + it.sources.map(function (s) { return '<a class="resource-link" href="' + esc(D.sources[s].url) + '">' + esc(label(D.sources[s])) + " ↗</a>"; }).join("") + "</div>";
      if (it.url) h += '<div class="ft-src"><a class="resource-link" href="' + esc(it.url) + '">' + t("open") + " ↗</a></div>";
      return h;
    }
    var nd = st.node ? tr.byId[st.node] : null, inside = list.filter(function (x) { return inNode(x, tr, nd); });
    var h2 = nd ? crumbs(nd) : "", ys = inside.map(function (x) { return x.year; });
    h2 += "<h3>" + esc(nd ? label(nd) : label(D.root)) + '</h3><p class="ft-desc">' + esc(nd ? desc(nd) : desc(D.root)) + "</p>";
    h2 += '<div class="ft-metrics"><span><b>' + num(inside.length) + "</b> " + esc(word(inside.length)) + (inside.length !== D.items.length && !nd ? " " + t("of") + " " + num(D.items.length) : "") + "</span>" +
      (ys.length ? "<span><b>" + Math.min.apply(null, ys) + "–" + Math.max.apply(null, ys) + "</b></span>" : "") +
      (st.cell ? '<span>' + t("cell") + ": <b>" + esc(label(trees[0].byId[st.cell[0]])) + " × " + esc(label(trees[1].byId[st.cell[1]])) + '</b> <button type="button" class="filter-chip" data-clearcell>' + t("clear") + "</button></span>" : "") + "</div>";
    if (inside.length) h2 += spark(inside);
    var kids = tr.kids[nd ? nd.id : ""] || [];
    if (kids.length) h2 += '<div class="ft-children">' + kids.map(function (k) {
      return '<button type="button" class="filter-chip" data-node="' + esc(k.id) + '"><span class="ft-dot" style="background:' + k.color + '"></span>' + esc(label(k)) + " <b>" + num(countIn(k, tr, list)) + "</b></button>";
    }).join("") + "</div>";
    if (!inside.length) return h2 + '<p class="ft-desc">' + t("none") + "</p>";
    var sorted = inside.slice().sort(function (a, b) { return b.year - a.year || title(a).localeCompare(title(b)); });
    h2 += '<ul class="ft-list">' + sorted.slice(0, st.show).map(function (x) {
      return '<li><button type="button" class="ft-item" data-item="' + x.id + '"><span class="yr">' + x.year + "</span><span><strong>" + mark(title(x)) + "</strong><small>" + itemSub(x) + "</small></span></button></li>";
    }).join("") + "</ul>";
    if (sorted.length > st.show) h2 += '<div class="ft-more"><button type="button" class="filter-chip" data-more>' + t("more") + " (" + num(sorted.length - st.show) + ")</button></div>";
    return h2;
  }

  // ---- charts ----
  function dotsChart() {
    var tr = T(), list = filtered(), ids = {}, W = 1000, L = 210, R = 20, n = Y1 - Y0 + 1, cw = (W - L - R) / n;
    list.forEach(function (it) { ids[it.id] = 1; });
    var rows = tr.top.map(function (top) {
      var cells = {};
      D.items.forEach(function (it) { if (inNode(it, tr, top)) (cells[it.year] = cells[it.year] || []).push(it); });
      var mx = Math.max.apply(null, Object.keys(cells).map(function (k) { return cells[k].length; }).concat([1]));
      return { top: top, cells: cells, h: Math.max(44, Math.ceil(mx / 3) * 10 + 22) };
    });
    var H = rows.reduce(function (a, r) { return a + r.h; }, 0) + 34, y = 6, svg = "";
    for (var yr = Y0; yr <= Y1; yr++) {
      var x = L + (yr - Y0 + 0.5) * cw;
      svg += '<line class="grid" x1="' + x.toFixed(1) + '" y1="4" x2="' + x.toFixed(1) + '" y2="' + (H - 26) + '"></line>';
      if ((yr - Y0) % 2 === 0 || n < 14) svg += '<text x="' + x.toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle">' + yr + "</text>";
    }
    rows.forEach(function (r) {
      svg += '<text class="lab" x="0" y="' + (y + r.h / 2 + 4) + '">' + esc(label(r.top)) + "</text>";
      Object.keys(r.cells).forEach(function (k) {
        var cx0 = L + (k - Y0 + 0.5) * cw;
        r.cells[k].forEach(function (it, i) {
          var col = i % 3, rowi = Math.floor(i / 3), cnt = r.cells[k].length, ncol = Math.min(3, cnt - rowi * 3);
          var cy = y + r.h / 2 + (rowi - (Math.ceil(cnt / 3) - 1) / 2) * 10, cx = cx0 + (col - (ncol - 1) / 2) * 10;
          var dim = !ids[it.id] || (st.node && !inNode(it, tr, tr.byId[st.node]));
          svg += '<circle r="4.6" cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" fill="' + r.top.color + '" class="' + (dim ? "dim" : "") + '" data-item="' + it.id + '"' +
            tipAttr("<b>" + esc(title(it)) + "</b> (" + it.year + ")<br>" + esc(label(leafOf(it, tr)))) + "></circle>";
        });
      });
      y += r.h;
      svg += '<line class="grid" x1="0" y1="' + y + '" x2="' + W + '" y2="' + y + '" stroke-dasharray="2 4"></line>';
    });
    return '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + esc(label(D.root)) + ' timeline">' + svg + "</svg>";
  }
  function stackChart() {
    var tr = T(), list = filtered(), W = 1000, H = 300, L = 40, B = 26, n = Y1 - Y0 + 1, bw = (W - L - 10) / n, svg = "";
    var share = st.chartMode === "share", tot = {}, by = {};
    list.forEach(function (it) { var tp = topOf(it, tr).id; tot[it.year] = (tot[it.year] || 0) + 1; by[it.year + "|" + tp] = (by[it.year + "|" + tp] || 0) + 1; });
    var mx = share ? 1 : Math.max.apply(null, Object.keys(tot).map(function (k) { return tot[k]; }).concat([1]));
    [0, 0.25, 0.5, 0.75, 1].forEach(function (f) {
      var yy = H - B - f * (H - B - 10);
      svg += '<line class="grid" x1="' + L + '" y1="' + yy + '" x2="' + W + '" y2="' + yy + '"></line><text x="' + (L - 6) + '" y="' + (yy + 4) + '" text-anchor="end">' + (share ? Math.round(f * 100) + "%" : Math.round(f * mx)) + "</text>";
    });
    for (var yr = Y0; yr <= Y1; yr++) {
      var x = L + (yr - Y0) * bw + 3, acc = 0, total = tot[yr] || 0;
      tr.top.forEach(function (tp) {
        var v = by[yr + "|" + tp.id] || 0; if (!v) return;
        var h = (share ? v / total : v / mx) * (H - B - 10), y0 = H - B - acc - h; acc += h;
        svg += '<rect class="bar" x="' + x.toFixed(1) + '" y="' + y0.toFixed(1) + '" width="' + (bw - 6).toFixed(1) + '" height="' + h.toFixed(1) + '" fill="' + tp.color + '" opacity="' + (st.node && T().byId[st.node] && (T().byId[st.node].id !== tp.id && T().byId[st.node].parent !== tp.id) ? 0.25 : 1) +
          '" data-node="' + esc(tp.id) + '"' + tipAttr("<b>" + yr + " · " + esc(label(tp)) + "</b><br>" + v + " " + esc(word(v)) + " (" + Math.round(100 * v / total) + "%)") + "></rect>";
      });
      svg += '<text x="' + (x + (bw - 6) / 2).toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle">' + yr + "</text>";
    }
    return '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="share per year">' + svg + "</svg>";
  }
  function legend() {
    return '<div class="ft-legend">' + T().top.map(function (tp) { return '<span><i style="background:' + tp.color + '"></i>' + esc(label(tp)) + "</span>"; }).join("") + "</div>";
  }
  function matrixHTML() {
    if (trees.length < 2) return "";
    var A = trees[0], Bt = trees[1], q = st.cell; st.cell = null; var list = filtered(); st.cell = q;
    var cnt = {}, mx = 1;
    list.forEach(function (it) { var k = topOf(it, A).id + "|" + topOf(it, Bt).id; cnt[k] = (cnt[k] || 0) + 1; mx = Math.max(mx, cnt[k]); });
    var h = '<table class="ft-matrix"><thead><tr><th>' + esc(label(A.def)) + " \\ " + esc(label(Bt.def)) + "</th>" + Bt.top.map(function (c) { return "<th>" + esc(label(c)) + "</th>"; }).join("") + "</tr></thead><tbody>";
    A.top.forEach(function (r) {
      h += "<tr><th>" + esc(label(r)) + "</th>" + Bt.top.map(function (c) {
        var v = cnt[r.id + "|" + c.id] || 0, f = v / mx, on = st.cell && st.cell[0] === r.id && st.cell[1] === c.id;
        var a = v ? 0.08 + 0.85 * Math.sqrt(f) : 0;
        return '<td><button type="button" data-cell="' + esc(r.id + "|" + c.id) + '" aria-pressed="' + !!on + '" style="--f:' + a.toFixed(3) + '"' + (a > 0.5 ? ' class="is-strong"' : "") +
          tipAttr("<b>" + esc(label(r)) + " × " + esc(label(c)) + "</b><br>" + v + " " + esc(word(v))) + "><span>" + v + "</span></button></td>";
      }).join("") + "</tr>";
    });
    return h + "</tbody></table>";
  }

  // ---- render + events ----
  function render() {
    $("#ft-tree").innerHTML = treeHTML();
    $("#ft-panel").innerHTML = panelHTML();
    var list = filtered();
    $("#ft-count").textContent = (st.q || st.cell) ? num(list.length) + " " + t("of") + " " + num(D.items.length) + " " + word(D.items.length) : num(D.items.length) + " " + word(D.items.length);
    var ch = $("#ft-chart");
    if (ch) ch.innerHTML = (D.chart === "stack" ? stackChart() : dotsChart()) + legend();
    var mt = $("#ft-matrix");
    if (mt) mt.innerHTML = matrixHTML();
    document.querySelectorAll("[data-tree]").forEach(function (b) { b.setAttribute("aria-pressed", String(+b.dataset.tree === st.ti)); b.textContent = label(trees[+b.dataset.tree].def); });
    document.querySelectorAll("[data-chartmode]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.chartmode === st.chartMode)); b.textContent = t(b.dataset.chartmode); });
    var inp = $("#ft-q"); if (inp) inp.placeholder = t("search") + "…";
    setParam("path", st.item !== null ? "item-" + st.item : st.node);
    setParam("tree", st.ti ? T().def.id : null);
    setParam("q", st.q || null);
  }
  function selectNode(id) {
    st.item = null; st.show = 12; st.node = id || null;
    var tr = T();
    for (var n = id ? tr.byId[id] : null; n; n = n.parent ? tr.byId[n.parent] : null) st.open[n.id] = true;
    render();
  }
  function selectItem(i) {
    st.item = i; var l = leafOf(D.items[i], T());
    for (var n = l; n; n = n.parent ? T().byId[n.parent] : null) st.open[n.id] = true;
    st.node = l.id; render();
    var p = $("#ft-panel"); if (p.getBoundingClientRect().top < 0) p.scrollIntoView({ block: "start", behavior: "smooth" });
  }
  host.addEventListener("click", function (e) {
    var b = e.target.closest("[data-node],[data-item],[data-more],[data-cell],[data-clearcell],[data-tree],[data-chartmode]");
    if (!b) return;
    if (b.hasAttribute("data-item")) return selectItem(+b.dataset.item);
    if (b.hasAttribute("data-more")) { st.show += 30; return render(); }
    if (b.hasAttribute("data-tree")) { st.ti = +b.dataset.tree; st.node = null; st.item = null; return render(); }
    if (b.hasAttribute("data-chartmode")) { st.chartMode = b.dataset.chartmode; return render(); }
    if (b.hasAttribute("data-clearcell")) { st.cell = null; return render(); }
    if (b.hasAttribute("data-cell")) { var c = b.dataset.cell.split("|"); st.cell = st.cell && st.cell[0] === c[0] && st.cell[1] === c[1] ? null : c; st.item = null; return render(); }
    var id = b.dataset.node;
    if (b.classList.contains("ft-row") && id && st.node === id && st.item === null) { st.open[id] = !st.open[id]; return render(); }
    if (b.classList.contains("ft-row") && id) st.open[id] = true;
    selectNode(id);
  });
  var qi = $("#ft-q"), qt = 0;
  if (qi) { qi.value = st.q; qi.addEventListener("input", function () { clearTimeout(qt); qt = setTimeout(function () { st.q = qi.value.trim(); st.item = null; st.show = 12; render(); }, D.items.length > 3000 ? 160 : 0); }); }
  document.addEventListener("langchange", function () { render(); stats(); });
  // initial selection from ?path=
  var p0 = params.get("path");
  if (p0 && /^item-\d+$/.test(p0) && D.items[+p0.slice(5)]) selectItem(+p0.slice(5));
  else if (p0 && T().byId[p0]) selectNode(p0);
  else { T().top.forEach(function (n) { st.open[n.id] = true; }); render(); }
  stats();
  }
})();
