// Bundle adjustment in 2D, small enough to run in the browser (used by ba.js; testable with node).
// Cameras have a position (x, y) and a heading th; a point p is seen at u = f x / z, where x is its lateral offset
// and z its depth in the camera. Levenberg-Marquardt solves for cameras and points with an explicit Schur complement.
(function (root) {
  "use strict";
  var F = 300, TAN = Math.tan(30 * Math.PI / 180), SIGMA = 0.5, HUBER = 3;

  function rng(seed) { return function () { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; }; }
  function normal(r) { var a = Math.max(1e-12, r()), b = r(); return Math.sqrt(-2 * Math.log(a)) * Math.cos(2 * Math.PI * b); }

  function project(c, p) {
    var vx = p.x - c.x, vy = p.y - c.y, dx = Math.cos(c.th), dy = Math.sin(c.th);
    var z = vx * dx + vy * dy, x = -vx * dy + vy * dx;  // depth along the heading, lateral offset to the left
    return { u: F * x / z, x: x, z: z, dx: dx, dy: dy };
  }
  // derivatives of u with respect to the point (px, py) and the camera (cx, cy, th)
  function jac(c, p) {
    var q = project(c, p), lx = -q.dy, ly = q.dx;
    var dpx = F / q.z * lx - F * q.x / (q.z * q.z) * q.dx, dpy = F / q.z * ly - F * q.x / (q.z * q.z) * q.dy;
    return { u: q.u, z: q.z, p: [dpx, dpy], c: [-dpx, -dpy, -F * (1 + q.x * q.x / (q.z * q.z))] };
  }

  // a scene: cameras on an arc looking at points in the middle; measurements with pixel noise and optional outliers
  function scene(o) {
    var r = rng(o.seed || 3), cams = [], pts = [], obs = [], m = 6, n = 30;
    for (var i = 0; i < m; i++) {
      var a = (-90 + 36 * i) * Math.PI / 180, R = 4.5;
      cams.push({ x: R * Math.sin(a), y: -R * Math.cos(a), th: Math.atan2(Math.cos(a), -Math.sin(a)) + (r() - 0.5) * 0.1 });
    }
    for (var j = 0; j < n; j++) pts.push({ x: (r() - 0.5) * 7, y: (r() - 0.5) * 5 });
    cams.forEach(function (c, ci) {
      pts.forEach(function (p, pj) {
        var q = project(c, p);
        if (q.z > 0.5 && Math.abs(q.x / q.z) < TAN) obs.push({ c: ci, p: pj, u: q.u + SIGMA * normal(r), out: false });
      });
    });
    if (o.outliers) {
      var ro = rng(99);
      obs.forEach(function (ob) { if (ro() < 0.1) { ob.u = (ro() * 2 - 1) * F * TAN; ob.out = true; } });
    }
    return { cams: cams, pts: pts, obs: obs };
  }
  // starting guess: everything perturbed, except the first camera and the position of the second (they fix the gauge:
  // position, heading and scale cannot be observed from images alone)
  function start(S, seed, size) {
    var r = rng(seed || 17), k = size || 1;
    var cams = S.cams.map(function (c, i) {
      if (i === 0) return { x: c.x, y: c.y, th: c.th };
      if (i === 1) return { x: c.x, y: c.y, th: c.th + 0.04 * k * normal(r) };
      return { x: c.x + 0.2 * k * normal(r), y: c.y + 0.2 * k * normal(r), th: c.th + 0.04 * k * normal(r) };
    });
    var pts = S.pts.map(function (p) { return { x: p.x + 0.3 * k * normal(r), y: p.y + 0.3 * k * normal(r) }; });
    return { cams: cams, pts: pts, lambda: 1e-3, history: [] };
  }
  function layout(S) {  // free camera parameters first, then 2 per point
    var cols = [];
    S.cams.forEach(function (c, i) { (i === 0 ? [] : i === 1 ? ["th"] : ["x", "y", "th"]).forEach(function (k) { cols.push({ cam: i, k: k }); }); });
    var nc = cols.length;
    S.pts.forEach(function (p, j) { cols.push({ pt: j, k: "x" }); cols.push({ pt: j, k: "y" }); });
    return { cols: cols, nc: nc, camCol: function (i, k) { for (var q = 0; q < nc; q++) if (cols[q].cam === i && cols[q].k === k) return q; return -1; } };
  }
  function residuals(S, E, robust) {
    var out = [], cost = 0;
    S.obs.forEach(function (ob) {
      var q = project(E.cams[ob.c], E.pts[ob.p]), r = ob.u - q.u, a = Math.abs(r);
      if (!(q.z > 1e-3)) r = 1e3, a = 1e3;  // behind the camera: a large, finite penalty
      var w = 1, rho = r * r, d2 = HUBER * HUBER;
      if (robust === "huber" && a > HUBER) { w = HUBER / a; rho = 2 * HUBER * a - d2; }
      if (robust === "cauchy") { w = 1 / (1 + r * r / d2); rho = d2 * Math.log(1 + r * r / d2); }
      cost += rho;
      out.push({ r: r, w: w });
    });
    return { list: out, cost: 0.5 * cost };
  }
  function cholSolve(A, b) {  // A symmetric positive definite (dense, small)
    var n = b.length, L = A.map(function (row) { return row.slice(); }), x = b.slice();
    for (var j = 0; j < n; j++) {
      for (var k = 0; k < j; k++) L[j][j] -= L[j][k] * L[j][k];
      if (!(L[j][j] > 1e-12)) return null;
      L[j][j] = Math.sqrt(L[j][j]);
      for (var i = j + 1; i < n; i++) { for (k = 0; k < j; k++) L[i][j] -= L[i][k] * L[j][k]; L[i][j] /= L[j][j]; }
    }
    for (i = 0; i < n; i++) { for (k = 0; k < i; k++) x[i] -= L[i][k] * x[k]; x[i] /= L[i][i]; }
    for (i = n - 1; i >= 0; i--) { for (k = i + 1; k < n; k++) x[i] -= L[k][i] * x[k]; x[i] /= L[i][i]; }
    return x;
  }
  function zeros(r, c) { var a = []; for (var i = 0; i < r; i++) { a.push(new Array(c).fill(0)); } return a; }

  // normal equations H = J^T W J and g = J^T W r, kept in camera / point blocks
  function system(S, E, robust) {
    var Lt = layout(S), N = Lt.cols.length, nc = Lt.nc, H = zeros(N, N), g = new Array(N).fill(0), R = residuals(S, E, robust), J = [];
    S.obs.forEach(function (ob, k) {
      var d = jac(E.cams[ob.c], E.pts[ob.p]), row = [], w = R.list[k].w, r = R.list[k].r;
      ["x", "y", "th"].forEach(function (key, t) { var q = Lt.camCol(ob.c, key); if (q >= 0) row.push([q, d.c[t]]); });
      row.push([nc + 2 * ob.p, d.p[0]], [nc + 2 * ob.p + 1, d.p[1]]);
      J.push(row.map(function (e) { return e[0]; }));
      row.forEach(function (a) { g[a[0]] += w * a[1] * r; row.forEach(function (b) { H[a[0]][b[0]] += w * a[1] * b[1]; }); });
    });
    return { H: H, g: g, J: J, nc: nc, N: N, cost: R.cost };
  }
  // one damped Gauss-Newton step through the Schur complement: S = B - E C^-1 E^T
  function solve(sys, lambda) {
    var nc = sys.nc, N = sys.N, H = sys.H, g = sys.g, np = (N - nc) / 2;
    var B = zeros(nc, nc), Cinv = [], rhs = g.slice(0, nc);
    for (var i = 0; i < nc; i++) for (var j = 0; j < nc; j++) B[i][j] = H[i][j] + (i === j ? lambda * (H[i][i] + 1e-9) : 0);
    for (var p = 0; p < np; p++) {
      var a = nc + 2 * p, c00 = H[a][a] * (1 + lambda) + 1e-9, c11 = H[a + 1][a + 1] * (1 + lambda) + 1e-9, c01 = H[a][a + 1], det = c00 * c11 - c01 * c01;
      var ci = [[c11 / det, -c01 / det], [-c01 / det, c00 / det]];
      Cinv.push(ci);
      // S -= E_p C_p^-1 E_p^T, rhs -= E_p C_p^-1 g_p
      for (i = 0; i < nc; i++) {
        var e0 = H[i][a], e1 = H[i][a + 1];
        if (!e0 && !e1) continue;
        var t0 = e0 * ci[0][0] + e1 * ci[1][0], t1 = e0 * ci[0][1] + e1 * ci[1][1];
        rhs[i] -= t0 * g[a] + t1 * g[a + 1];
        for (j = 0; j < nc; j++) { var f0 = H[j][a], f1 = H[j][a + 1]; if (f0 || f1) B[i][j] -= t0 * f0 + t1 * f1; }
      }
    }
    var dc = cholSolve(B, rhs);
    if (!dc) return null;
    var d = dc.slice();
    for (p = 0; p < np; p++) {  // back-substitution: d_p = C_p^-1 (g_p - E_p^T d_c)
      a = nc + 2 * p;
      var b0 = g[a], b1 = g[a + 1];
      for (i = 0; i < nc; i++) { b0 -= H[i][a] * dc[i]; b1 -= H[i][a + 1] * dc[i]; }
      d.push(Cinv[p][0][0] * b0 + Cinv[p][0][1] * b1, Cinv[p][1][0] * b0 + Cinv[p][1][1] * b1);
    }
    return { d: d, S: B };
  }
  function apply(S, E, d) {
    var Lt = layout(S), cams = E.cams.map(function (c) { return { x: c.x, y: c.y, th: c.th }; }), pts = E.pts.map(function (p) { return { x: p.x, y: p.y }; });
    Lt.cols.forEach(function (col, q) { if (col.cam !== undefined) cams[col.cam][col.k] += d[q]; else pts[col.pt][col.k] += d[q]; });
    return { cams: cams, pts: pts };
  }
  // one Levenberg-Marquardt iteration: try a step; keep it if the cost drops (smaller lambda), otherwise damp more and retry
  function step(S, E, robust) {
    var sys = system(S, E, robust), tries = 0;
    if (!E.history.length) E.history.push(sys.cost);
    while (tries++ < 12) {
      var sol = solve(sys, E.lambda);
      if (sol) {
        var cand = apply(S, E, sol.d), cost = residuals(S, cand, robust).cost;
        if (cost < sys.cost) {
          E.cams = cand.cams; E.pts = cand.pts; E.lambda = Math.max(1e-7, E.lambda / 3); E.history.push(cost);
          return { accepted: true, cost: cost, sys: sys, S: sol.S };
        }
      }
      E.lambda *= 4;
    }
    E.history.push(sys.cost);
    return { accepted: false, cost: sys.cost, sys: sys, S: sol ? sol.S : null };
  }
  function errors(S, E) {
    var se = 0, si = 0, ni = 0;
    S.obs.forEach(function (ob) { var r = ob.u - project(E.cams[ob.c], E.pts[ob.p]).u; se += r * r; if (!ob.out) { si += r * r; ni++; } });
    var pe = 0; S.pts.forEach(function (p, j) { pe += Math.pow(E.pts[j].x - p.x, 2) + Math.pow(E.pts[j].y - p.y, 2); });
    return { rms: Math.sqrt(se / S.obs.length), rmsInliers: Math.sqrt(si / Math.max(1, ni)), points: Math.sqrt(pe / S.pts.length) };
  }
  var api = { F: F, TAN: TAN, SIGMA: SIGMA, HUBER: HUBER, scene: scene, start: start, step: step, system: system, solve: solve, layout: layout, errors: errors, project: project };
  if (typeof module !== "undefined") module.exports = api; else root.BADemo = api;
})(this);
