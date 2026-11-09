// Paper Explorer: search and filter papers of robotics, vision and machine learning venues (data: dblp, CC0).
// Data: explorer/data/index.json (venues, topics) + one columnar file per venue {t, a, y, l, g}
// + optional explorer/data/nn/<venue>.bin: 10 similar papers per paper (scripts/make_paper_neighbors.py).
(function () {
  "use strict";
  var root = document.getElementById("px");
  if (!root) return;
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  // case, accents, hyphens and apostrophes are ignored; one character in gives one out, so positions still map to the original text
  var fold = function (s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[-‐-―_'’]/g, " "); };
  var num = function (n) { return Number(n).toLocaleString("en-US"); };
  var base = root.getAttribute("data-base") || "data/";
  var META = null, P = [], byGi = [], loaded = 0, NN = {}, K = 10;
  var params = new URLSearchParams(location.search);
  var list = function (k) { return (params.get(k) || "").split(",").filter(Boolean); };
  var st = { q: params.get("q") || "", field: params.get("field") || "", venues: new Set(list("venues")), topics: new Set(list("topics")),
             from: +params.get("from") || 0, to: +params.get("to") || 0, sort: params.get("sort") || "year-desc", show: 50, sim: new Set() };

  // ---- query ----
  // Every word must appear, in the title or the authors; "quoted phrases" stay together; small words are ignored.
  // A word also finds its synonyms and UK/US spellings; words of up to 3 letters must match whole words ("rl" is not "world").
  var STOP = new Set(["a", "an", "the", "of", "for", "and", "or", "with", "in", "on", "to", "via", "using", "by", "from", "at", "towards", "toward", "into", "is", "are"]);
  var SYN = [
    ["llm", "large language model"], ["vlm", "vision-language model"], ["mllm", "multimodal large language model", "multimodal llm"],
    ["vla", "vision-language-action"], ["foundation model", "foundation models"], ["rl", "reinforcement learning"],
    ["irl", "inverse reinforcement learning"], ["marl", "multi agent reinforcement learning"], ["rlhf", "reinforcement learning from human feedback"],
    ["il", "imitation learning"], ["bc", "behavior cloning", "behavioral cloning"], ["lfd", "learning from demonstration"],
    ["gs", "3dgs", "gaussian splatting"], ["nerf", "neural radiance field"], ["slam", "simultaneous localization and mapping"],
    ["vo", "visual odometry"], ["vio", "visual inertial odometry"], ["lio", "lidar inertial odometry"], ["sfm", "structure from motion"],
    ["mvs", "multi view stereo"], ["vpr", "visual place recognition"], ["icp", "iterative closest point"], ["ekf", "extended kalman filter"],
    ["mpc", "model predictive control"], ["tamp", "task and motion planning"], ["hri", "human robot interaction"],
    ["uav", "unmanned aerial vehicle", "drone"], ["auv", "autonomous underwater vehicle"], ["bev", "bird's-eye view", "birds-eye view", "bird-eye view"],
    ["gnn", "graph neural network"], ["cnn", "convolutional neural network"], ["vit", "vision transformer"],
    ["gan", "generative adversarial network"], ["vae", "variational autoencoder"], ["sam", "segment anything"], ["ood", "out of distribution"],
    ["sim2real", "sim to real"], ["6dof", "6 dof", "6d pose"], ["moe", "mixture of experts"], ["vqa", "visual question answering"],
    ["vln", "vision and language navigation", "vision language navigation"], ["ssl", "self supervised learning"], ["ocr", "optical character recognition"]
  ];
  var shown = {};  // folded form -> form to show in the hint
  SYN = SYN.map(function (g) { return g.map(function (w) { var f = fold(w); shown[f] = w; return f; }); });
  var synOf = {};
  SYN.forEach(function (g) { g.forEach(function (w) { synOf[w] = g; }); });
  var SPELL = [["centre", "center"], ["metre", "meter"], ["fibre", "fiber"], ["manoeuvre", "maneuver"], ["grey", "gray"], ["analys", "analyz"],
               ["aluminium", "aluminum"], ["defence", "defense"], ["licence", "license"], ["catalog", "catalogue"]];
  function spellings(w) {  // UK and US spellings of one word
    var out = [w], m;
    if ((m = w.match(/^(.{3,}?)i([sz])(e|ed|es|ing|er|ers|ation|ations|able|ability)$/))) out.push(m[1] + "i" + (m[2] === "s" ? "z" : "s") + m[3]);
    if ((m = w.match(/^(behavio|colo|neighbo|favo|labo|harbo|humo|vapo|flavo|rumo|endeavo)(u?)r(s|al|ally|ed|ing|hood)?$/))) out.push(m[1] + (m[2] ? "" : "u") + "r" + (m[3] || ""));
    if ((m = w.match(/^(model|label|travel|signal|cancel|fuel|tunnel|channel|level|marshal)(l?)(ing|ed|er|ers)$/))) out.push(m[1] + (m[2] ? "" : "l") + m[3]);
    SPELL.forEach(function (p) { if (w.indexOf(p[0]) === 0) out.push(p[1] + w.slice(p[0].length)); else if (w.indexOf(p[1]) === 0) out.push(p[0] + w.slice(p[1].length)); });
    return out;
  }
  function variants(phrase) {  // spellings of every word of a phrase (at most 8 combinations)
    var outs = [""];
    phrase.split(" ").forEach(function (w) {
      var next = [];
      spellings(w).forEach(function (s) { outs.forEach(function (o) { if (next.length < 8) next.push(o ? o + " " + s : s); }); });
      outs = next;
    });
    return outs;
  }
  function alt(s) {
    var whole = s.length <= 3 && s.indexOf(" ") < 0;
    return { s: s, whole: whole, rx: whole ? new RegExp("(^|[^a-z0-9])" + s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "(s|es)?(?![a-z0-9])") : null };
  }
  function term(text) {
    var group = synOf[text] || [text], seen = {}, alts = [];
    group.forEach(function (g) { variants(g).forEach(function (v) { if (!seen[v]) { seen[v] = 1; alts.push(alt(v)); } }); });
    return { src: text, alts: alts, fixed: null };
  }
  function parse(q) {
    var out = [], phrases = [], rest = q.replace(/"([^"]+)"/g, function (m, p) { phrases.push(fold(p).trim()); return " "; });
    var words = fold(rest).split(/\s+/).filter(Boolean);
    for (var i = 0; i < words.length; i++) {  // a known multi-word name typed without quotes ("reinforcement learning") stays one term
      var hit = null;
      for (var n = Math.min(6, words.length - i); n >= 2 && !hit; n--) { var ph = words.slice(i, i + n).join(" "); if (synOf[ph]) hit = [ph, n]; }
      if (hit) { phrases.push(hit[0]); i += hit[1] - 1; } else phrases.push(words[i]);
    }
    var content = phrases.filter(function (w) { return !STOP.has(w); });
    (content.length ? content : phrases).forEach(function (w) { if (w) out.push(term(w)); });
    return out;
  }
  function altHit(a, p) {
    if (a.whole ? a.rx.test(p.ht) : p.ht.indexOf(a.s) >= 0) return 2;
    return p.ha.indexOf(" " + a.s + (a.whole ? " " : "")) >= 0 ? 1 : 0;  // authors: from the start of a name part
  }
  function termHit(t, p) { var best = 0; for (var i = 0; i < t.alts.length && best < 2; i++) best = Math.max(best, altHit(t.alts[i], p)); return best; }

  // ---- typo tolerance: a word that no paper contains is replaced by the closest word of the titles ----
  var VOCAB = null;
  function vocab() {
    if (VOCAB) return VOCAB;
    var c = new Map();
    P.forEach(function (p) { p.ht.split(/[^a-z0-9]+/).forEach(function (w) { if (w.length >= 4) c.set(w, (c.get(w) || 0) + 1); }); });
    VOCAB = Array.from(c.entries());
    return VOCAB;
  }
  function distance(a, b, max) {  // Levenshtein distance, or max + 1 once it is clearly larger
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var prev = [], cur;
    for (var j = 0; j <= b.length; j++) prev.push(j);
    for (var i = 1; i <= a.length; i++) {
      cur = [i]; var low = i;
      for (var k = 1; k <= b.length; k++) { cur.push(Math.min(prev[k] + 1, cur[k - 1] + 1, prev[k - 1] + (a[i - 1] === b[k - 1] ? 0 : 1))); low = Math.min(low, cur[k]); }
      if (low > max) return max + 1;
      prev = cur;
    }
    return prev[b.length];
  }
  function correct(t) {
    var w = t.src, max = w.length >= 8 ? 2 : 1, best = null;
    if (t.fixed || w.length < 4 || w.indexOf(" ") >= 0 || /[0-9]/.test(w)) return false;
    vocab().forEach(function (e) {
      var d = distance(w, e[0], max);
      if (d <= max && (!best || d < best[1] || (d === best[1] && e[1] > best[2]))) best = [e[0], d, e[1]];
    });
    if (!best) return false;
    var fixed = term(best[0]);
    t.fixed = best[0]; t.alts = fixed.alts;
    return true;
  }

  // ---- highlight ----
  function highlight(text, ts, author) {
    var out = esc(text);
    if (!ts.length) return out;
    var folded = fold(text), marks = [];
    ts.forEach(function (t) {
      t.alts.forEach(function (a) {
        var i = 0;
        while ((i = folded.indexOf(a.s, i)) >= 0) {
          var before = i === 0 || !/[a-z0-9]/.test(folded[i - 1]), after = !/[a-z0-9]/.test(folded[i + a.s.length] || " ");
          if ((!author && !a.whole) || (before && (!a.whole || after || /^(s|es)(?![a-z0-9])/.test(folded.slice(i + a.s.length))))) marks.push([i, i + a.s.length]);
          i += a.s.length;
        }
      });
    });
    if (!marks.length) return out;
    marks.sort(function (a, b) { return a[0] - b[0] || b[1] - a[1]; });
    var res = "", pos = 0;
    marks.forEach(function (m) { if (m[0] < pos) return; res += esc(text.slice(pos, m[0])) + "<mark>" + esc(text.slice(m[0], m[1])) + "</mark>"; pos = m[1]; });
    return res + esc(text.slice(pos));
  }

  // ---- filters ----
  var venueIdx = {}, topicBit = {}, QOK = null, QSCORE = null;
  function passes(p, skip) {
    var v = META.venues[p.v];
    if (skip !== "field" && st.field && v.field !== st.field) return false;
    if (skip !== "venue" && st.venues.size && !st.venues.has(v.id)) return false;
    if (skip !== "year" && ((st.from && p.y < st.from) || (st.to && p.y > st.to))) return false;
    if (skip !== "topic" && st.topics.size) { for (var t of st.topics) if (!(p.g >> topicBit[t] & 1)) return false; }
    return !QOK || QOK[p.idx] === 1;
  }
  function matchQuery(ts) {  // one pass over all papers; a word that matches nothing gets a typo correction
    if (!ts.length) { QOK = null; QSCORE = null; return; }
    var hits = ts.map(function () { return 0; });
    QOK = new Uint8Array(P.length); QSCORE = new Uint8Array(P.length);
    P.forEach(function (p) {
      var ok = 1, sc = 0;
      for (var i = 0; i < ts.length; i++) { var h = termHit(ts[i], p); if (h) { hits[i]++; sc += h; } else ok = 0; }
      QOK[p.idx] = ok; QSCORE[p.idx] = sc;
    });
    var changed = false;
    if (loaded === META.venues.length) ts.forEach(function (t, i) { if (!hits[i] && correct(t)) changed = true; });
    if (changed) matchQuery(ts);
  }
  function sorted(rows) {
    var by = {
      "year-desc": function (a, b) { return b.y - a.y || a.t.localeCompare(b.t); },
      "year-asc": function (a, b) { return a.y - b.y || a.t.localeCompare(b.t); },
      "title": function (a, b) { return a.t.localeCompare(b.t); },
      "match": function (a, b) { return (QSCORE ? QSCORE[b.idx] - QSCORE[a.idx] : 0) || b.y - a.y; }
    };
    return rows.sort(by[st.sort] || by["year-desc"]);
  }
  function renderHint(ts) {
    var notes = [];
    ts.forEach(function (t) {
      if (t.fixed) notes.push("Showing results for <b>" + esc(t.fixed) + "</b>: no paper contains “" + esc(t.src) + "”.");
      var extra = t.alts.map(function (a) { return shown[a.s] || a.s; }).filter(function (s) { return fold(s) !== (t.fixed || t.src); });
      if (extra.length) notes.push("“" + esc(shown[t.fixed || t.src] || t.fixed || t.src) + "” also finds: " + extra.slice(0, 5).map(esc).join(", ") + ".");
    });
    var h = $("px-hint");
    h.innerHTML = notes.join(" ");
    h.hidden = !notes.length;
  }

  // ---- controls ----
  function chip(attr, value, label, count, on, extra) {
    return '<button type="button" class="filter-chip' + (extra || "") + '" ' + attr + '="' + esc(value) + '" aria-pressed="' + on + '">' + esc(label) +
      (count === null ? "" : ' <span class="px-n">' + num(count) + "</span>") + "</button>";
  }
  function renderControls() {
    var fc = {}, vc = {}, tc = {};
    P.forEach(function (p) {
      var v = META.venues[p.v];
      if (passes(p, "field")) fc[v.field] = (fc[v.field] || 0) + 1;
      if (passes(p, "venue")) vc[v.id] = (vc[v.id] || 0) + 1;
      if (passes(p, "topic")) {
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

  // ---- similar papers (10 nearest titles by meaning, computed offline) ----
  function loadNN(vi) {
    var v = META.venues[vi];
    if (!NN[v.id]) NN[v.id] = fetch(base + "nn/" + v.id + ".bin").then(function (r) { if (!r.ok) throw r.status; return r.arrayBuffer(); }).then(function (b) {
      var a = new Uint8Array(b);
      if (a.length !== v.count * K * 4) throw "size";
      NN[v.id] = a;
      return a;
    });
    return NN[v.id];
  }
  function similarHTML(p) {
    var a = NN[META.venues[p.v].id];
    if (!a || typeof a.then === "function" || loaded < META.venues.length) return '<p class="px-sub">Loading similar papers…</p>';
    var rows = [];
    for (var k = 0; k < K; k++) {
      var o = (p.i * K + k) * 4, q = byGi[a[o] | a[o + 1] << 8 | a[o + 2] << 16];
      if (!q) continue;
      var v = META.venues[q.v];
      rows.push('<li><a href="' + esc(link(q.l)) + '">' + esc(q.t) + '</a> <span class="px-venue px-f-' + v.field + '" title="' + esc(v.name) + '">' + esc(v.short) + "</span> " + q.y + "</li>");
    }
    return '<p class="px-sub">Papers with the most similar titles, from all venues:</p><ol>' + rows.join("") + "</ol>";
  }

  // ---- results ----
  function link(l) {
    if (/^10\./.test(l)) return "https://doi.org/" + l;
    (META.codes || []).forEach(function (c) { l = l.split(c[0]).join(c[1]); });
    return l;
  }
  function renderResults(rows, ts) {
    var shown = rows.slice(0, st.show), withNN = !!META.neighbors;
    $("px-results").innerHTML = shown.map(function (p) {
      var v = META.venues[p.v], tags = [], open = st.sim.has(p.gi);
      for (var i = 0; i < META.topics.length; i++) if (p.g >> i & 1) tags.push('<span class="tag">' + esc(META.topics[i].name) + "</span>");
      return '<li class="px-item"><a class="px-title" href="' + esc(link(p.l)) + '">' + highlight(p.t, ts) + '</a><p class="px-meta"><span class="px-venue px-f-' + v.field + '" title="' + esc(v.name) + '">' + esc(v.short) +
        "</span> " + p.y + ' · <span class="px-authors">' + highlight(p.a, ts, true) + "</span></p>" +
        '<p class="px-tags">' + tags.join("") + (withNN ? '<button type="button" class="px-simbtn" data-sim="' + p.gi + '" aria-expanded="' + open + '">' + (open ? "Hide similar papers" : "Similar papers") + "</button>" : "") + "</p>" +
        (open ? '<div class="px-sim">' + similarHTML(p) + "</div>" : "") + "</li>";
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
      var ts = parse(st.q);
      matchQuery(ts);
      var rows = sorted(P.filter(function (p) { return passes(p); }));
      renderHint(ts); renderControls(); renderOverview(rows, ts); renderResults(rows, ts); saveURL();
    });
  }

  // ---- events ----
  var timer = 0, qi = $("px-q");
  qi.value = st.q;
  qi.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(function () { st.q = qi.value.trim(); st.show = 50; render(); }, 160); });
  root.addEventListener("click", function (e) {
    var b = e.target.closest("[data-field],[data-venue],[data-topic],[data-sim],#px-more,#px-clear");
    if (!b) return;
    if (b.hasAttribute("data-sim")) {
      var gi = +b.getAttribute("data-sim"), p = byGi[gi];
      if (st.sim.has(gi)) st.sim.delete(gi); else { st.sim.add(gi); loadNN(p.v).then(render, function () { b.textContent = "Similar papers are not available"; }); }
      return render();
    }
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
    if (META.neighbors) K = META.neighbors.k;
    var offset = 0;
    META.venues.forEach(function (v, i) { venueIdx[v.id] = i; v.offset = offset; offset += v.count; });
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
        for (var i = 0; i < d.t.length; i++) {
          var p = { t: d.t[i], a: d.a[i], y: d.y[i], l: d.l[i], g: d.g[i], v: vi, i: i, gi: v.offset + i, idx: P.length,
                    ht: fold(d.t[i]), ha: " " + fold(d.a[i]).replace(/[^a-z0-9]+/g, " ") + " " };
          P.push(p); byGi[p.gi] = p;
        }
        loaded++; VOCAB = null; render();
      });
    }));
  }).catch(function (err) { $("px-status").textContent = "Could not load the paper list (" + err + "). Please reload the page."; });
})();
