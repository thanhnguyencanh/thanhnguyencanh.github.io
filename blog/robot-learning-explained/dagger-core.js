// Teacher-student distillation on a toy lane-keeping task, small enough to run in the browser (used by rl.js; testable with node).
// The teacher steers with privileged information: the true lateral offset, heading error and road curvature, known only in
// simulation. The student sees noisy estimates of them, as a lane detector would give, and copies the teacher's steering by
// nearest neighbours. Behavior cloning trains it on the teacher's own drives; DAgger also labels the states the student visits.
(function (root) {
  "use strict";
  var V = 2, DT = 0.05, HALF = 0.6, DS = 0.05, LEN = 80, U_MAX = 2.5, K = 4, NOISE = 0.03;

  function rng(seed) { return function () { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; }; }
  function normal(r) { var a = Math.max(1e-12, r()), b = r(); return Math.sqrt(-2 * Math.log(a)) * Math.cos(2 * Math.PI * b); }
  function wrap(a) { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; }

  // the road: a centerline with smoothly varying curvature, sampled every DS metres
  function road() {
    var n = Math.round(LEN / DS) + 1, pts = [], x = 0, y = 0, phi = 0;
    for (var i = 0; i < n; i++) {
      var s = i * DS, k = 0.32 * Math.sin(2 * Math.PI * s / 22) + 0.18 * Math.sin(2 * Math.PI * s / 9 + 1);
      pts.push({ x: x, y: y, phi: phi, k: k, s: s });
      phi += k * DS; x += Math.cos(phi) * DS; y += Math.sin(phi) * DS;
    }
    return pts;
  }
  // where the car is relative to the road: nearest centerline point (searched near the last one), lateral offset, heading error
  function locate(R, car, hint) {
    var best = hint, bd = Infinity;
    for (var i = Math.max(0, hint - 40); i < Math.min(R.length, hint + 40); i++) {
      var dx = car.x - R[i].x, dy = car.y - R[i].y, d2 = dx * dx + dy * dy;
      if (d2 < bd) { bd = d2; best = i; }
    }
    var c = R[best], nx = -Math.sin(c.phi), ny = Math.cos(c.phi);
    return { i: best, d: (car.x - c.x) * nx + (car.y - c.y) * ny, psi: wrap(car.th - c.phi), k: c.k };
  }
  // the teacher: a lane-keeping law on the privileged state (curvature feed-forward, feedback on heading and offset)
  function teacher(loc) { return Math.max(-U_MAX, Math.min(U_MAX, V * loc.k - 3.6 * loc.psi - 2 * loc.d)); }
  // the student's observation: the same three quantities, with noise
  function observe(loc, r) { return [loc.d + NOISE * normal(r), loc.psi + NOISE * normal(r), loc.k + NOISE * normal(r)]; }
  function knn(data, o) {  // mean steering of the K nearest stored observations
    var bd = [Infinity, Infinity, Infinity, Infinity], bu = [0, 0, 0, 0], n = 0;
    for (var j = 0; j < data.length; j++) {
      var e = data[j].o, a = e[0] - o[0], b = e[1] - o[1], c = e[2] - o[2], d = a * a + b * b + c * c;
      if (d >= bd[K - 1]) continue;
      var q = K - 1;
      while (q > 0 && bd[q - 1] > d) { bd[q] = bd[q - 1]; bu[q] = bu[q - 1]; q--; }
      bd[q] = d; bu[q] = data[j].u; n++;
    }
    var m = Math.min(K, n), s = 0;
    for (j = 0; j < m; j++) s += bu[j];
    return m ? s / m : 0;
  }
  // one drive. who = "teacher" or a dataset (the student); label = also return teacher-labelled samples of the visited states
  function drive(R, who, start, seed, label) {
    var r = rng(seed), car = { x: R[0].x - Math.sin(R[0].phi) * start.d, y: R[0].y + Math.cos(R[0].phi) * start.d, th: R[0].phi + start.psi }, hint = 0;
    var path = [], samples = [], off = false, steps = Math.round(LEN / (V * DT)) - 5;
    for (var t = 0; t < steps; t++) {
      var loc = locate(R, car, hint); hint = loc.i;
      path.push({ x: car.x, y: car.y });
      if (Math.abs(loc.d) > HALF) { off = true; break; }
      if (loc.i >= R.length - Math.round(2 / DS) - 1) break;
      var o = observe(loc, r), ut = teacher(loc);
      if (label && t % 2 === 0) samples.push({ o: o, u: ut });  // every second step is enough
      var u = who === "teacher" ? ut : Math.max(-U_MAX, Math.min(U_MAX, knn(who, o)));
      car.th += u * DT; car.x += V * Math.cos(car.th) * DT; car.y += V * Math.sin(car.th) * DT;
    }
    var end = locate(R, car, hint);
    return { path: path, samples: samples, off: off, done: off ? R[end.i].s / LEN : 1 };
  }
  // test starts: small offsets and heading errors, like an imperfect start or a push
  function starts(seed, n) {
    var r = rng(seed), out = [];
    for (var i = 0; i < n; i++) out.push({ d: (r() - 0.5) * 0.3, psi: (r() - 0.5) * 0.12 });
    return out;
  }
  // an experiment: both students start from one teacher drive along the centre of the road (a nominal expert demonstration).
  // Each round, behavior cloning gets one more such drive; DAgger gets its own student's drive, labelled by the teacher.
  function create(seed, nTests) {
    var R = road(), first = drive(R, "teacher", { d: 0, psi: 0 }, 50 + seed, true).samples;
    var E = { R: R, seed: seed, tests: starts(1000 + seed, nTests || 6), bc: first.slice(), dg: first.slice(), round: 0, hist: [] };
    score(E);
    return E;
  }
  function score(E) {
    var row = { round: E.round, nbc: E.bc.length, ndg: E.dg.length, runsBC: [], runsDG: [], bc: 0, dagger: 0 };
    E.tests.forEach(function (st, i) {
      var a = drive(E.R, E.bc, st, 70 + E.seed + 31 * i, false), b = drive(E.R, E.dg, st, 70 + E.seed + 31 * i, false);
      row.runsBC.push(a); row.runsDG.push(b); row.bc += a.done / E.tests.length; row.dagger += b.done / E.tests.length;
    });
    E.hist.push(row);
    return row;
  }
  function advance(E) {
    E.round++;
    var k = E.round;
    E.bc = E.bc.concat(drive(E.R, "teacher", { d: 0, psi: 0 }, 50 + k + E.seed, true).samples);
    E.dg = E.dg.concat(drive(E.R, E.dg, E.tests[(k - 1) % E.tests.length], 50 + k + E.seed, true).samples);
    return score(E);
  }
  function experiment(o) {
    var E = create(o.seed || 0, o.tests);
    for (var k = 0; k < (o.rounds || 6); k++) advance(E);
    return E;
  }
  var api = { V: V, HALF: HALF, LEN: LEN, NOISE: NOISE, road: road, drive: drive, starts: starts, create: create, advance: advance, experiment: experiment, teacher: teacher, locate: locate };
  if (typeof module !== "undefined") module.exports = api; else root.DaggerDemo = api;
})(this);
