// Trajectory evaluation in 2D, small enough to run in the browser (used by vd.js; testable with node):
// a ground-truth loop, an estimate built from its relative motions with chosen errors, Umeyama alignment
// with or without scale, the absolute trajectory error (ATE) and the relative pose error (RPE).
(function (root) {
  "use strict";
  var N = 400;

  function rng(seed) { return function () { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; }; }
  function normal(r) { var a = Math.max(1e-12, r()), b = r(); return Math.sqrt(-2 * Math.log(a)) * Math.cos(2 * Math.PI * b); }
  function wrap(a) { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; }

  // ground truth: a closed loop of about 60 m, headings along the path, s = distance travelled
  function truth() {
    var T = [], s = 0;
    for (var i = 0; i < N; i++) {
      var t = 2 * Math.PI * i / (N - 1);
      T.push({ x: 9 * Math.cos(t) + 2.2 * Math.cos(2 * t) - 2.2, y: 5.5 * Math.sin(t) + 1.8 * Math.sin(3 * t) });
    }
    for (i = 0; i < N; i++) {
      var a = T[Math.max(0, i - 1)], b = T[Math.min(N - 1, i + 1)];
      T[i].th = Math.atan2(b.y - a.y, b.x - a.x);
      if (i) s += Math.hypot(T[i].x - T[i - 1].x, T[i].y - T[i - 1].y);
      T[i].s = s;
    }
    return T;
  }

  // the estimate: the true relative motions, with a global scale, a scale drift (fraction per 10 m),
  // a heading drift (degrees per metre), one rotation error (degrees, at a fraction of the path) and noise (m per step)
  function estimate(T, o) {
    var E = [{ x: T[0].x, y: T[0].y, th: T[0].th }], sc = o.scale, r = rng(o.seed || 7), at = Math.round((o.at || 0) * (N - 1));
    for (var i = 1; i < N; i++) {
      var a = T[i - 1], b = T[i], dx = b.x - a.x, dy = b.y - a.y, c = Math.cos(a.th), sn = Math.sin(a.th);
      var lx = c * dx + sn * dy, ly = -sn * dx + c * dy, ds = Math.hypot(dx, dy), e = E[i - 1];
      sc *= 1 + (o.scaleDrift || 0) * ds / 10;
      var ce = Math.cos(e.th), se = Math.sin(e.th), nx = (o.noise || 0) * normal(r), ny = (o.noise || 0) * normal(r);
      var th = e.th + wrap(b.th - a.th) + (o.yawDrift || 0) * Math.PI / 180 * ds + (i === at && o.jump ? o.jump * Math.PI / 180 : 0);
      E.push({ x: e.x + sc * (ce * lx - se * ly) + nx, y: e.y + sc * (se * lx + ce * ly) + ny, th: th });
    }
    return E;
  }

  // Umeyama: the rotation, translation (and scale) that best map the estimate Q onto the truth P
  function align(P, Q, withScale) {
    var n = P.length, mp = { x: 0, y: 0 }, mq = { x: 0, y: 0 }, a = 0, b = 0, qq = 0, i;
    for (i = 0; i < n; i++) { mp.x += P[i].x / n; mp.y += P[i].y / n; mq.x += Q[i].x / n; mq.y += Q[i].y / n; }
    for (i = 0; i < n; i++) {
      var px = P[i].x - mp.x, py = P[i].y - mp.y, qx = Q[i].x - mq.x, qy = Q[i].y - mq.y;
      a += qx * px + qy * py; b += qx * py - qy * px; qq += qx * qx + qy * qy;
    }
    var th = Math.atan2(b, a), s = withScale ? Math.hypot(a, b) / qq : 1, c = Math.cos(th), sn = Math.sin(th);
    return { s: s, th: th, t: { x: mp.x - s * (c * mq.x - sn * mq.y), y: mp.y - s * (sn * mq.x + c * mq.y) } };
  }
  function apply(A, Q) {
    var c = Math.cos(A.th), sn = Math.sin(A.th);
    return Q.map(function (q) { return { x: A.s * (c * q.x - sn * q.y) + A.t.x, y: A.s * (sn * q.x + c * q.y) + A.t.y, th: q.th + A.th }; });
  }
  function ate(P, Q) {
    var e = 0;
    for (var i = 0; i < P.length; i++) e += Math.pow(P[i].x - Q[i].x, 2) + Math.pow(P[i].y - Q[i].y, 2);
    return Math.sqrt(e / P.length);
  }
  // relative pose error over a distance d along the true path: translation in % of d, rotation in degrees per metre
  function rpe(T, E, d, s) {
    var et = 0, er = 0, k = 0, j = 0;
    for (var i = 0; i < N; i++) {
      while (j < N && T[j].s - T[i].s < d) j++;
      if (j >= N) break;
      var ci = Math.cos(T[i].th), si = Math.sin(T[i].th), gx = ci * (T[j].x - T[i].x) + si * (T[j].y - T[i].y), gy = -si * (T[j].x - T[i].x) + ci * (T[j].y - T[i].y);
      var cj = Math.cos(E[i].th), sj = Math.sin(E[i].th), ex = s * (cj * (E[j].x - E[i].x) + sj * (E[j].y - E[i].y)), ey = s * (-sj * (E[j].x - E[i].x) + cj * (E[j].y - E[i].y));
      et += Math.pow(gx - ex, 2) + Math.pow(gy - ey, 2);
      er += Math.pow(wrap((T[j].th - T[i].th) - (E[j].th - E[i].th)), 2);
      k++;
    }
    return { trans: 100 * Math.sqrt(et / k) / d, rot: Math.sqrt(er / k) * 180 / Math.PI / d, pairs: k };
  }
  function evaluate(o, withScale) {
    var T = truth(), E = estimate(T, o), A = align(T, E, withScale), Ea = apply(A, E);
    return { T: T, E: Ea, align: A, ate: ate(T, Ea), rpe: rpe(T, E, 5, A.s), length: T[N - 1].s };
  }
  var api = { N: N, truth: truth, estimate: estimate, align: align, apply: apply, ate: ate, rpe: rpe, evaluate: evaluate };
  if (typeof module !== "undefined") module.exports = api; else root.EvalDemo = api;
})(this);
