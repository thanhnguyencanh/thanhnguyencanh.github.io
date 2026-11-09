// Paper Explorer: search and filter papers of robotics, vision and machine learning venues (data: dblp, CC0).
// Data: explorer/data/index.json (venues, topics) + one columnar file per venue {t, a, y, l, g}.
(function () {
  "use strict";
  var root = document.getElementById("px");
  if (!root) return;
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var fold = function (s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); };
  var num = function (n) { return Number(n).toLocaleString("en-US"); };
  var base = root.getAttribute("data-base") || "data/";
  var META = null, P = [], loaded = 0;
  var params = new URLSearchParams(location.search);
  var list = function (k) { return (params.get(k) || "").split(",").filter(Boolean); };
  var st = { q: params.get("q") || "", field: params.get("field") || "", venues: new Set(list("venues")), topics: new Set(list("topics")),
             from: +params.get("from") || 0, to: +params.get("to") || 0, sort: params.get("sort") || "year-desc", show: 50 };

  // ---- query: words must all appear (title or authors); "quoted phrases" stay together ----
  function terms(q) {
    var out = [], re = /"([^"]+)"|(\S+)/g, m;
    while ((m = re.exec(fold(q)))) out.push((m[1] || m[2]).trim());
    return out.filter(Boolean);
  }
  function highlight(text, ts, wordStart) {
    var out = esc(text);
    if (!ts.length) return out;
    var folded = fold(text), marks = [];
    ts.forEach(function (w) {
      var i = 0;
      while ((i = folded.indexOf(w, i)) >= 0) {
        if (!wordStart || i === 0 || !/[a-z0-9]/.test(folded[i - 1])) marks.push([i, i + w.length]);
        i += w.length;
      }
    });
    if (!marks.length) return out;
    marks.sort(function (a, b) { return a[0] - b[0]; });
    var res = "", pos = 0;
    marks.forEach(function (m) { if (m[0] < pos) return; res += esc(text.slice(pos, m[0])) + "<mark>" + esc(text.slice(m[0], m[1])) + "</mark>"; pos = m[1]; });
    return res + esc(text.slice(pos));
  }

  // ---- filters ----
  var venueIdx = {}, topicBit = {};
  function passes(p, ts, skip) {
    var v = META.venues[p.v];
    if (skip !== "field" && st.field && v.field !== st.field) return false;
    if (skip !== "venue" && st.venues.size && !st.venues.has(v.id)) return false;
    if (skip !== "year" && ((st.from && p.y < st.from) || (st.to && p.y > st.to))) return false;
    if (skip !== "topic" && st.topics.size) { for (var t of st.topics) if (!(p.g >> topicBit[t] & 1)) return false; }
    for (var i = 0; i < ts.length; i++) if (p.ht.indexOf(ts[i]) < 0 && p.ha.indexOf(" " + ts[i]) < 0) return false;
    return true;
  }
  function sorted(rows, ts) {
    var by = {
      "year-desc": function (a, b) { return b.y - a.y || a.t.localeCompare(b.t); },
      "year-asc": function (a, b) { return a.y - b.y || a.t.localeCompare(b.t); },
      "title": function (a, b) { return a.t.localeCompare(b.t); },
      "match": function (a, b) { return score(b) - score(a) || b.y - a.y; }
    };
    function score(p) { var s = 0; ts.forEach(function (w) { s += p.ht.indexOf(w) >= 0 ? 2 : 1; }); return s; }
    return rows.sort(by[st.sort] || by["year-desc"]);
  }

  // ---- controls ----
  function chip(attr, value, label, count, on, extra) {
    return '<button type="button" class="filter-chip' + (extra || "") + '" ' + attr + '="' + esc(value) + '" aria-pressed="' + on + '">' + esc(label) +
      (count === null ? "" : ' <span class="px-n">' + num(count) + "</span>") + "</button>";
  }
  function renderControls(ts) {
    var fc = {}, vc = {}, tc = {};
    P.forEach(function (p) {
      var v = META.venues[p.v];
      if (passes(p, ts, "field")) fc[v.field] = (fc[v.field] || 0) + 1;
      if (passes(p, ts, "venue")) vc[v.id] = (vc[v.id] || 0) + 1;
      if (passes(p, ts, "topic")) {
        var ok = true;
        for (var t of st.topics) if (!(p.g >> topicBit[t] & 1)) { ok = false; break; }
        if (ok) for (var i = 0; i < META.topics.length; i++) if (p.g >> i & 1) tc[i] = (tc[i] || 0) + 1;
      }
    });
    var allF = Object.keys(fc).reduce(function (a, k) { return a + fc[k]; }, 0);
    $("px-fields").innerHTML = chip("data-field", "", "All fields", allF, !st.field) +
      META.fields.map(function (f) { return chip("data-field", f.id, f.name, fc[f.id] || 0, st.field === f.id, " px-f-" + f.id); }).join("");
    $("px-venues").innerHTML = META.fields.map(function (f) {
      return '<span class="px-group">' + META.venues.filter(function (v) { return v.field === f.id; }).map(function (v) {
        return chip("data-venue", v.id, v.short, vc[v.id] || 0, st.venues.has(v.id), " px-f-" + v.field);
      }).join("") + "</span>";
    }).join("");
    var groups = [];
    META.topics.forEach(function (t) { if (groups.indexOf(t.group) < 0) groups.push(t.group); });
    $("px-topic-chips").innerHTML = groups.map(function (g) {
      return '<div class="px-topic-group"><span class="px-sub">' + esc(g) + "</span>" + META.topics.map(function (t, i) {
        return t.group === g ? chip("data-topic", t.id, t.name, tc[i] || 0, st.topics.has(t.id)) : "";
      }).join("") + "</div>";
    }).join("");
    $("px-topic-count").textContent = st.topics.size ? "(" + st.topics.size + " selected, papers must match all)" : "";
  }

  // ---- overview: share of papers per year, and where they are published ----
  function renderOverview(rows, ts) {
    var y0 = META.years[0], y1 = META.years[1], hit = {}, all = {}, byV = {}, filtering = ts.length || st.topics.size;
    rows.forEach(function (p) { hit[p.y] = (hit[p.y] || 0) + 1; byV[p.v] = (byV[p.v] || 0) + 1; });
    P.forEach(function (p) {
      var v = META.venues[p.v];
      if ((st.field && v.field !== st.field) || (st.venues.size && !st.venues.has(v.id))) return;
      all[p.y] = (all[p.y] || 0) + 1;
    });
    var W = 620, H = 190, L = 44, B = 24, n = y1 - y0 + 1, bw = (W - L - 8) / n, vals = [], mx = 0;
    for (var y = y0; y <= y1; y++) { var v = filtering ? (all[y] ? (hit[y] || 0) / all[y] * 100 : 0) : (hit[y] || 0); vals.push(v); mx = Math.max(mx, v); }
    mx = mx || 1;
    var nice = niceMax(mx), svg = "";
    [0, 0.5, 1].forEach(function (f) {
      var yy = H - B - f * (H - B - 12);
      svg += '<line class="px-grid" x1="' + L + '" x2="' + W + '" y1="' + yy + '" y2="' + yy + '"></line><text x="' + (L - 6) + '" y="' + (yy + 4) + '" text-anchor="end">' +
        (filtering ? pctLabel(f * nice, nice) + "%" : num(Math.round(f * nice))) + "</text>";
    });
    vals.forEach(function (v, i) {
      var yr = y0 + i, h = v / nice * (H - B - 12), x = L + i * bw + 3;
      var tip = filtering ? yr + ": " + num(hit[yr] || 0) + " of " + num(all[yr] || 0) + " papers (" + (all[yr] ? (100 * (hit[yr] || 0) / all[yr]).toFixed(2) : 0) + "%)"
                          : yr + ": " + num(hit[yr] || 0) + " papers";
      svg += '<rect class="px-bar" x="' + x.toFixed(1) + '" y="' + (H - B - h).toFixed(1) + '" width="' + (bw - 6).toFixed(1) + '" height="' + Math.max(0, h).toFixed(1) + '" rx="2"><title>' + esc(tip) + "</title></rect>";
      if (n <= 12 || i % 2 === 0) svg += '<text x="' + (x + (bw - 6) / 2).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle">' + yr + "</text>";
    });
    $("px-trend").innerHTML = '<p class="px-sub">' + (filtering ? "Share of all papers in the selected venues, per year" : "Papers per year in the selected venues") + "</p>" +
      '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Papers per year">' + svg + "</svg>";
    var top = Object.keys(byV).map(function (k) { return [+k, byV[k]]; }).sort(function (a, b) { return b[1] - a[1]; }).slice(0, 8);
    var tm = top.length ? top[0][1] : 1;
    $("px-venuebars").innerHTML = '<p class="px-sub">Where these papers are published</p>' + (top.length ? top.map(function (r) {
      var v = META.venues[r[0]];
      return '<div class="px-vrow"><span class="px-vname">' + esc(v.short) + '</span><span class="px-vbar"><i class="px-f-' + v.field + '" style="width:' + (100 * r[1] / tm).toFixed(1) + '%"></i></span><span class="px-vn">' + num(r[1]) + "</span></div>";
    }).join("") : '<p class="px-sub">No papers.</p>');
  }
  function pctLabel(v, top) { var d = top >= 2 ? 0 : top >= 0.2 ? 1 : top >= 0.02 ? 2 : 3; return v.toFixed(d); }
  function niceMax(v) { var p = Math.pow(10, Math.floor(Math.log10(v))), m = v / p; return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 5 ? 5 : 10) * p; }

  // ---- results ----
  function link(l) {
    if (/^10\./.test(l)) return "https://doi.org/" + l;
    (META.codes || []).forEach(function (c) { l = l.split(c[0]).join(c[1]); });
    return l;
  }
  function renderResults(rows, ts) {
    var shown = rows.slice(0, st.show);
    $("px-results").innerHTML = shown.map(function (p) {
      var v = META.venues[p.v], tags = [];
      for (var i = 0; i < META.topics.length; i++) if (p.g >> i & 1) tags.push('<span class="tag">' + esc(META.topics[i].name) + "</span>");
      return '<li class="px-item"><a class="px-title" href="' + esc(link(p.l)) + '">' + highlight(p.t, ts) + '</a><p class="px-meta"><span class="px-venue px-f-' + v.field + '" title="' + esc(v.name) + '">' + esc(v.short) +
        "</span> " + p.y + ' · <span class="px-authors">' + highlight(p.a, ts, true) + "</span></p>" + (tags.length ? '<p class="px-tags">' + tags.join("") + "</p>" : "") + "</li>";
    }).join("") || '<li class="px-empty">No papers match. Try fewer words or remove a filter.</li>';
    var more = $("px-more");
    more.hidden = rows.length <= st.show;
    more.textContent = "Show more (" + num(rows.length - st.show) + " left)";
    $("px-status").textContent = (loaded < META.venues.length ? "Loading " + loaded + " of " + META.venues.length + " venues… " : "") +
      num(rows.length) + " of " + num(P.length) + " papers" + (rows.length > st.show ? ", showing " + num(Math.min(st.show, rows.length)) : "");
  }

  // ---- state <-> URL ----
  function saveURL() {
    var q = new URLSearchParams();
    if (st.q) q.set("q", st.q);
    if (st.field) q.set("field", st.field);
    if (st.venues.size) q.set("venues", Array.from(st.venues).join(","));
    if (st.topics.size) q.set("topics", Array.from(st.topics).join(","));
    if (st.from && st.from !== META.years[0]) q.set("from", st.from);
    if (st.to && st.to !== META.years[1]) q.set("to", st.to);
    if (st.sort !== "year-desc") q.set("sort", st.sort);
    var s = q.toString();
    history.replaceState(null, "", location.pathname + (s ? "?" + s : ""));
  }
  var pending = 0;
  function render() {
    cancelAnimationFrame(pending);
    pending = requestAnimationFrame(function () {
      var ts = terms(st.q), rows = sorted(P.filter(function (p) { return passes(p, ts); }), ts);
      renderControls(ts); renderOverview(rows, ts); renderResults(rows, ts); saveURL();
    });
  }

  // ---- events ----
  var timer = 0, qi = $("px-q");
  qi.value = st.q;
  qi.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(function () { st.q = qi.value.trim(); st.show = 50; render(); }, 140); });
  root.addEventListener("click", function (e) {
    var b = e.target.closest("[data-field],[data-venue],[data-topic],#px-more,#px-clear");
    if (!b) return;
    if (b.id === "px-more") { st.show += 50; return render(); }
    if (b.id === "px-clear") {
      st.q = ""; qi.value = ""; st.field = ""; st.venues.clear(); st.topics.clear(); st.from = META.years[0]; st.to = META.years[1]; st.sort = "year-desc";
      $("px-from").value = st.from; $("px-to").value = st.to; $("px-sort").value = st.sort;
    } else if (b.hasAttribute("data-field")) { st.field = b.getAttribute("data-field"); st.venues.clear(); }
    else if (b.hasAttribute("data-venue")) { var v = b.getAttribute("data-venue"); if (st.venues.has(v)) st.venues.delete(v); else st.venues.add(v); }
    else if (b.hasAttribute("data-topic")) { var t = b.getAttribute("data-topic"); if (st.topics.has(t)) st.topics.delete(t); else st.topics.add(t); }
    st.show = 50; render();
  });
  ["px-from", "px-to", "px-sort"].forEach(function (id) {
    $(id).addEventListener("change", function () {
      st.from = +$("px-from").value; st.to = +$("px-to").value; st.sort = $("px-sort").value;
      if (st.from > st.to) { var x = st.from; st.from = st.to; st.to = x; $("px-from").value = st.from; $("px-to").value = st.to; }
      st.show = 50; render();
    });
  });

  // ---- load ----
  fetch(base + "index.json").then(function (r) { return r.json(); }).then(function (meta) {
    META = meta;
    META.venues.forEach(function (v, i) { venueIdx[v.id] = i; });
    META.topics.forEach(function (t, i) { topicBit[t.id] = i; });
    st.venues = new Set(Array.from(st.venues).filter(function (v) { return v in venueIdx; }));
    st.topics = new Set(Array.from(st.topics).filter(function (t) { return t in topicBit; }));
    var opts = "";
    for (var y = META.years[0]; y <= META.years[1]; y++) opts += "<option>" + y + "</option>";
    $("px-from").innerHTML = opts; $("px-to").innerHTML = opts;
    st.from = Math.max(META.years[0], Math.min(META.years[1], st.from || META.years[0]));
    st.to = Math.max(st.from, Math.min(META.years[1], st.to || META.years[1]));
    $("px-from").value = st.from; $("px-to").value = st.to; $("px-sort").value = st.sort;
    document.querySelectorAll("[data-px=total]").forEach(function (el) { el.textContent = num(META.total); });
    document.querySelectorAll("[data-px=date]").forEach(function (el) { el.textContent = META.generated; });
    var late = META.venues.map(function (v) {  // venues whose newest papers are not in dblp yet
      var ys = Object.keys(v.years).filter(function (y) { return v.years[y] > 0; }).map(Number);
      return [v.short, Math.max.apply(null, ys)];
    }).filter(function (r) { return r[1] < META.years[1] - 1 || (r[1] < META.years[1] && ["ICCV"].indexOf(r[0]) < 0); });
    var cov = $("px-coverage");
    if (cov && late.length) cov.textContent = " Newest year in dblp so far: " + late.map(function (r) { return r[0] + " " + r[1]; }).join(", ") + ".";
    $("px-status").textContent = "Loading papers…";
    return Promise.all(META.venues.map(function (v, vi) {
      return fetch(base + v.id + ".json").then(function (r) { return r.json(); }).then(function (d) {
        for (var i = 0; i < d.t.length; i++) P.push({ t: d.t[i], a: d.a[i], y: d.y[i], l: d.l[i], g: d.g[i], v: vi, ht: fold(d.t[i]), ha: " " + fold(d.a[i]).replace(/[^a-z0-9]+/g, " ") });
        loaded++; render();
      });
    }));
  }).catch(function (err) { $("px-status").textContent = "Could not load the paper list (" + err + "). Please reload the page."; });
})();
