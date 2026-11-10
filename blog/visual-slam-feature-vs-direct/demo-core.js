// Toy 1-D model of the two front-ends, used by demo.js (browser) and testable with node.
// A row of pixels plays the image; frame 2 is frame 1 moved by the camera and made brighter or darker.
(function (root) {
  "use strict";
  var N = 320, PAD = 90, RANGE = 60, STEP = 0.25;
  var BLUR = [0.7, 2, 4, 8];  // pixel blur of each "pyramid level"

  var TEX = [[7.3, 0.03, 0], [12.7, 0.03, 1], [21.1, 0.035, 2.1], [35.3, 0.04, 0.4], [58.9, 0.045, 1.7], [97, 0.05, 2.9]];  // period, amplitude, phase
  function rng(seed) { return function () { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; }; }
  // textured: sharp edges and small blobs over fine texture; smooth: slow shading without corners.
  // Intensities stay in 0.05-0.75, so a brighter exposure (gain up to 1.3) does not saturate.
  function scene(kind) {
    var r = rng(kind === "texture" ? 12 : 5), parts = [];
    for (var i = 0; i < 10; i++) parts.push({ c: -90 + r() * 500, w: 0.8 + r() * 1.2, a: (r() < 0.5 ? -1 : 1) * (0.06 + r() * 0.06), step: true });
    for (i = 0; i < 30; i++) parts.push({ c: -90 + r() * 500, w: 1 + r() * 2.5, a: (r() - 0.5) * 0.16, step: false });
    return function (x) {
      var v = 0.4;
      if (kind === "texture") {
        parts.forEach(function (p) { v += p.step ? p.a * (1 / (1 + Math.exp(-(x - p.c) / p.w)) - 0.5) : p.a * Math.exp(-Math.pow((x - p.c) / p.w, 2)); });
        TEX.forEach(function (w) { v += w[1] * Math.sin(2 * Math.PI * x / w[0] + w[2]); });  // texture at several scales
      } else v += 0.15 * Math.sin(2 * Math.PI * x / 210) + 0.05 * Math.sin(2 * Math.PI * x / 87 + 1.3);
      return Math.min(0.75, Math.max(0.05, v));
    };
  }
  function blur(a, s) {
    var rad = Math.ceil(3 * s), k = [], sum = 0, out = new Float64Array(a.length);
    for (var i = -rad; i <= rad; i++) { var w = Math.exp(-i * i / (2 * s * s)); k.push(w); sum += w; }
    for (var x = 0; x < a.length; x++) {
      var v = 0;
      for (var j = -rad; j <= rad; j++) v += k[j + rad] * a[Math.min(a.length - 1, Math.max(0, x + j))];
      out[x] = v / sum;
    }
    return out;
  }
  // rows cover pixels -PAD .. N+PAD; frame 2 sees the scene moved by `motion` px, times `gain`, plus `bias`
  function frames(o) {
    var f = scene(o.scene), a = new Float64Array(N + 2 * PAD), b = new Float64Array(N + 2 * PAD);
    for (var i = 0; i < a.length; i++) { var x = i - PAD; a[i] = f(x); b[i] = Math.min(1, Math.max(0, o.gain * f(x - o.motion) + (o.bias || 0))); }
    return { raw1: a, raw2: b, img1: blur(a, BLUR[o.level]), img2: blur(b, BLUR[o.level]), sharp1: blur(a, 1), sharp2: blur(b, 1) };
  }
  function at(row, x) {  // linear interpolation at pixel x (x = 0 is row index PAD)
    var u = x + PAD, i = Math.floor(u), t = u - i;
    if (i < 0 || i + 1 >= row.length) return NaN;
    return row[i] * (1 - t) + row[i + 1] * t;
  }

  // ---- direct: photometric error over all pixels, optionally with affine brightness a*I + b ----
  function photometric(F, affine) {
    var ts = [], es = [];
    for (var t = -RANGE; t <= RANGE + 1e-9; t += STEP) {
      var xs = [], ys = [];
      for (var x = 0; x < N; x++) { xs.push(at(F.img1, x)); ys.push(at(F.img2, x + t)); }
      var a = 1, b = 0;
      if (affine) {
        var mx = 0, my = 0, n = xs.length;
        for (var i = 0; i < n; i++) { mx += xs[i]; my += ys[i]; }
        mx /= n; my /= n;
        var sxy = 0, sxx = 0;
        for (i = 0; i < n; i++) { sxy += (xs[i] - mx) * (ys[i] - my); sxx += (xs[i] - mx) * (xs[i] - mx); }
        a = sxx > 1e-12 ? sxy / sxx : 1; b = my - a * mx;
      }
      var e = 0;
      for (i = 0; i < xs.length; i++) { var r = ys[i] - (a * xs[i] + b); e += r * r; }
      ts.push(t); es.push(e / xs.length);
    }
    return { t: ts, e: es };
  }

  // ---- feature-based: keypoints at strong gradient maxima, brightness-invariant patch descriptors, mutual matches ----
  // like ORB: keep the strongest responses (here, gradient maxima), so a darker or brighter image gives the same keypoints;
  // a small floor removes responses that are too weak to be corners at all
  function keypoints(row) {
    var g = [], kp = [];
    for (var x = 0; x < N; x++) g.push((at(row, x + 1) - at(row, x - 1)) / 2);
    for (x = 8; x < N - 8; x++) if (Math.abs(g[x]) > 0.012 && Math.abs(g[x]) >= Math.abs(g[x - 1]) && Math.abs(g[x]) > Math.abs(g[x + 1])) kp.push(x);
    kp.sort(function (a, b) { return Math.abs(g[b]) - Math.abs(g[a]); });
    return kp.slice(0, 16).sort(function (a, b) { return a - b; });
  }
  function descriptor(row, x) {
    var p = [], m = 0, s = 0;
    for (var i = -7; i <= 7; i++) p.push(at(row, x + i));
    p.forEach(function (v) { m += v; }); m /= p.length;
    p = p.map(function (v) { return v - m; });
    p.forEach(function (v) { s += v * v; }); s = Math.sqrt(s) || 1;
    return p.map(function (v) { return v / s; });
  }
  function dot(a, b) { var s = 0; for (var i = 0; i < a.length; i++) s += a[i] * b[i]; return s; }
  function matches(F) {
    var k1 = keypoints(F.sharp1), k2 = keypoints(F.sharp2);
    var d1 = k1.map(function (x) { return descriptor(F.sharp1, x); }), d2 = k2.map(function (x) { return descriptor(F.sharp2, x); });
    var best12 = d1.map(function (d) { var b = -1, s = -2; d2.forEach(function (e, j) { var c = dot(d, e); if (c > s) { s = c; b = j; } }); return [b, s]; });
    var best21 = d2.map(function (e) { var b = -1, s = -2; d1.forEach(function (d, i) { var c = dot(d, e); if (c > s) { s = c; b = i; } }); return b; });
    var out = [];
    best12.forEach(function (m, i) { if (m[0] >= 0 && best21[m[0]] === i && m[1] > 0.85) out.push({ x1: k1[i], x2: k2[m[0]], d: k2[m[0]] - k1[i] }); });
    return { k1: k1, k2: k2, m: out };
  }
  function reprojection(M) {  // robust (Huber) error of the matched displacements against a guessed motion
    var ts = [], es = [];
    for (var t = -RANGE; t <= RANGE + 1e-9; t += STEP) {
      var e = 0;
      M.m.forEach(function (m) { var r = Math.abs(m.d - t); e += r <= 2 ? 0.5 * r * r : 2 * (r - 1); });
      ts.push(t); es.push(M.m.length ? e / M.m.length : 0);
    }
    return { t: ts, e: es };
  }
  // gradient descent on the sampled curve, starting from zero motion
  function descend(c) {
    var i = Math.round(RANGE / STEP);
    while (true) {
      var l = i > 0 ? c.e[i - 1] : Infinity, r = i < c.e.length - 1 ? c.e[i + 1] : Infinity;
      if (l < c.e[i] && l <= r) i--; else if (r < c.e[i]) i++; else break;
    }
    return c.t[i];
  }
  function run(o) {
    var F = frames(o), M = matches(F), P = photometric(F, o.affine), R = reprojection(M);
    return { F: F, M: M, P: P, R: R, endP: descend(P), endR: M.m.length >= 3 ? descend(R) : null };
  }
  var api = { run: run, N: N, PAD: PAD, RANGE: RANGE, BLUR: BLUR };
  if (typeof module !== "undefined") module.exports = api; else root.VSDemo = api;
})(this);
