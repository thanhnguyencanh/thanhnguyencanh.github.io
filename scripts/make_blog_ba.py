#!/usr/bin/env python3
"""Data for the blog post "Bundle adjustment, explained" (blog/bundle-adjustment/data.js): a reading map of key papers.

Each paper from 2015 on is looked up by its title in the Paper Explorer data (explorer/data, from dblp), so title, authors,
venue, year and link come from there; earlier papers and out-of-venue journals were checked on Crossref.

It also draws the static figures of the post as inline SVG into data/blog/bundle-adjustment.html, between
<!--fig:NAME--> and <!--/fig:NAME--> (colours come from CSS classes in assets/blog.css, so both themes work).

Run after scripts/make_paper_explorer.py:  python3 scripts/make_blog_ba.py   (then python3 scripts/build_site.py)
Only the figures:                          python3 scripts/make_blog_ba.py --figures
"""
import html
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "explorer" / "data"
OUT = ROOT / "blog" / "bundle-adjustment" / "data.js"

TREE = [
    ("found", "Foundations & sparse solvers", "Nền tảng và bộ giải thưa",
     "BA as sparse nonlinear least squares, and the libraries that solve it on CPUs.",
     "BA như bài toán bình phương tối thiểu phi tuyến thưa, và các thư viện giải nó trên CPU.",
     [("f-theory", "Theory", "Lý thuyết"), ("f-lib", "Sparse solvers & libraries", "Bộ giải và thư viện thưa")]),
    ("large", "Large-scale BA", "BA quy mô lớn",
     "Problems with thousands of cameras and millions of points, and the linear algebra that makes them tractable.",
     "Bài toán với hàng nghìn camera và hàng triệu điểm, cùng phần đại số tuyến tính giúp giải được chúng.",
     [("l-big", "Large problems", "Bài toán lớn"), ("l-linalg", "Better linear algebra", "Đại số tuyến tính tốt hơn")]),
    ("sfm", "Structure from motion", "Cấu trúc từ chuyển động",
     "Full reconstruction pipelines in which BA is the final, most accurate step.",
     "Các hệ tái tạo hoàn chỉnh trong đó BA là bước cuối, chính xác nhất.",
     [("s-pipe", "Incremental & global SfM", "SfM tăng dần và toàn cục")]),
    ("gpu", "GPUs & deep-learning frameworks", "GPU và framework học sâu",
     "Second-order optimization on GPUs, inside PyTorch and other deep-learning frameworks.",
     "Tối ưu bậc hai trên GPU, ngay trong PyTorch và các framework học sâu khác.",
     [("g-dl", "On deep-learning frameworks", "Trên framework học sâu"), ("g-dist", "Distributed GPU", "GPU phân tán")]),
    ("beyond", "Beyond keypoints", "Vượt ra ngoài điểm đặc trưng",
     "BA on pixel intensities or learned feature maps instead of keypoint positions.",
     "BA trên cường độ điểm ảnh hoặc bản đồ đặc trưng học được thay vì vị trí điểm đặc trưng.",
     [("b-photo", "Photometric & featuremetric BA", "BA trắc quang và theo đặc trưng")]),
    ("learn", "BA inside learning", "BA bên trong học sâu",
     "Differentiable BA layers, trained end to end with the networks around them.",
     "Các lớp BA khả vi, huấn luyện đầu-cuối cùng với mạng xung quanh.",
     [("n-layer", "Differentiable BA", "BA khả vi")]),
]
PAPERS = [  # (title as in dblp, or its start; branch; short name; description en; description vi)
    ("Structure-from-Motion Revisited", "s-pipe", "COLMAP",
     "Incremental structure from motion that alternates image registration, triangulation and bundle adjustment; a standard pipeline.",
     "Cấu trúc từ chuyển động tăng dần, xen kẽ đăng ký ảnh, tam giác hóa và tối ưu bó; một hệ thống chuẩn mực."),
    ("Global Structure-from-Motion Revisited", "s-pipe", "GLOMAP",
     "Global structure from motion: positions all cameras and points jointly, then refines them with bundle adjustment.",
     "Cấu trúc từ chuyển động toàn cục: xác định vị trí tất cả camera và điểm cùng lúc, rồi tinh chỉnh bằng tối ưu bó."),
    ("Square Root Bundle Adjustment for Large-Scale Reconstruction", "l-linalg", "√BA",
     "Eliminates the points with a QR-based nullspace projection instead of the Schur complement; stable even in single precision.",
     "Khử các điểm bằng phép chiếu không gian rỗng dựa trên QR thay vì bù Schur; ổn định ngay cả với độ chính xác đơn."),
    ("Power Bundle Adjustment for Large-Scale 3D Reconstruction", "l-linalg", "Power BA",
     "Approximates the inverse of the Schur complement with a power series, for fast solves on very large problems.",
     "Xấp xỉ nghịch đảo của bù Schur bằng chuỗi lũy thừa, giải nhanh các bài toán rất lớn."),
    ("DeepLM", "g-dl", "DeepLM",
     "Large-scale nonlinear least squares on deep-learning frameworks, with stochastic domain decomposition.",
     "Bình phương tối thiểu phi tuyến quy mô lớn trên framework học sâu, với phân rã miền ngẫu nhiên."),
    ("Theseus: A Library for Differentiable Nonlinear Optimization", "g-dl", "Theseus",
     "A PyTorch library for differentiable nonlinear least squares, so optimization layers can sit inside neural networks.",
     "Thư viện PyTorch cho bình phương tối thiểu phi tuyến khả vi, để các lớp tối ưu có thể nằm trong mạng nơ-ron."),
    ("PyPose: A Library for Robot Learning with Physics-based Optimization", "g-dl", "PyPose",
     "A PyTorch library with Lie groups and second-order optimizers such as Levenberg-Marquardt, for robot learning.",
     "Thư viện PyTorch với nhóm Lie và các bộ tối ưu bậc hai như Levenberg-Marquardt, phục vụ học máy cho robot."),
    ("Bundle Adjustment in the Eager Mode", "g-dl", "BAE",
     "Eager-mode BA in PyTorch: sparsity-aware automatic differentiation and GPU sparse operations for second-order optimization.",
     "BA ở chế độ eager trong PyTorch: vi phân tự động biết khai thác tính thưa và phép toán thưa trên GPU cho tối ưu bậc hai."),
    ("MegBA", "g-dist", "MegBA",
     "A GPU-based distributed library that splits very large BA problems across several GPUs.",
     "Thư viện phân tán trên GPU, chia các bài toán BA rất lớn cho nhiều GPU."),
    ("Pixel-Perfect Structure-from-Motion with Featuremetric Refinement", "b-photo", "Pixel-Perfect SfM",
     "Refines keypoints and then the whole reconstruction on dense learned features: featuremetric BA.",
     "Tinh chỉnh điểm đặc trưng rồi toàn bộ phần tái tạo trên đặc trưng dày đặc học được: BA theo đặc trưng."),
    ("BA-Net: Dense Bundle Adjustment Networks", "n-layer", "BA-Net",
     "Dense bundle adjustment as a differentiable network layer, learning the features and depth bases it uses.",
     "Tối ưu bó dày đặc dưới dạng lớp mạng khả vi, học các đặc trưng và cơ sở độ sâu mà nó dùng."),
    ("DROID-SLAM: Deep Visual SLAM", "n-layer", "DROID-SLAM",
     "Recurrent optical-flow updates coupled with a differentiable dense bundle adjustment layer.",
     "Cập nhật lặp dòng quang học kết hợp với một lớp tối ưu bó dày đặc khả vi."),
    ("VGGSfM", "n-layer", "VGGSfM",
     "A fully differentiable structure-from-motion pipeline: learned tracking, initialization and differentiable bundle adjustment.",
     "Một hệ cấu trúc từ chuyển động khả vi hoàn toàn: theo dõi học được, khởi tạo và tối ưu bó khả vi."),
]
MANUAL = [  # checked on Crossref
    {"name": "BA: a modern synthesis", "year": 2000, "node": "f-theory", "authors": "Bill Triggs, Philip F. McLauchlan, Richard I. Hartley, Andrew W. Fitzgibbon",
     "venue": "Vision Algorithms (LNCS) 2000", "title": "Bundle Adjustment — A Modern Synthesis", "url": "https://doi.org/10.1007/3-540-44480-7_21",
     "den": "The reference survey: BA as sparse nonlinear least squares, with error models, robust costs, gauge freedom and sparse solvers.",
     "dvi": "Bài tổng quan kinh điển: BA như bình phương tối thiểu phi tuyến thưa, với mô hình sai số, hàm chi phí bền vững, tự do gauge và bộ giải thưa."},
    {"name": "SBA", "year": 2009, "node": "f-lib", "authors": "Manolis I. A. Lourakis, Antonis A. Argyros", "venue": "ACM TOMS 2009",
     "title": "SBA: A software package for generic sparse bundle adjustment", "url": "https://doi.org/10.1145/1486525.1486527",
     "den": "A widely used package for generic sparse BA, built around Levenberg-Marquardt and the camera-point block structure.",
     "dvi": "Gói phần mềm phổ biến cho BA thưa tổng quát, xây dựng quanh Levenberg-Marquardt và cấu trúc khối camera-điểm."},
    {"name": "g²o", "year": 2011, "node": "f-lib", "authors": "Rainer Kümmerle, Giorgio Grisetti, Hauke Strasdat, Kurt Konolige, Wolfram Burgard", "venue": "ICRA 2011",
     "title": "g2o: A general framework for graph optimization", "url": "https://doi.org/10.1109/ICRA.2011.5979949",
     "den": "A general C++ framework for graph optimization, used for BA and pose graphs with sparse solvers.",
     "dvi": "Khung C++ tổng quát cho tối ưu đồ thị, dùng cho BA và đồ thị tư thế với các bộ giải thưa."},
    {"name": "iSAM2", "year": 2012, "node": "f-lib", "authors": "Michael Kaess, Hordur Johannsson, Richard Roberts, Viorela Ila, John J. Leonard, Frank Dellaert",
     "venue": "IJRR 2012", "title": "iSAM2: Incremental smoothing and mapping using the Bayes tree", "url": "https://doi.org/10.1177/0278364911430419",
     "den": "Incremental smoothing on the Bayes tree, re-solving only what new measurements change; the core of GTSAM.",
     "dvi": "Làm mịn tăng dần trên cây Bayes, chỉ giải lại phần bị phép đo mới làm thay đổi; lõi của GTSAM."},
    {"name": "BAL", "year": 2010, "node": "l-big", "authors": "Sameer Agarwal, Noah Snavely, Steven M. Seitz, Richard Szeliski", "venue": "ECCV 2010",
     "title": "Bundle Adjustment in the Large", "url": "https://doi.org/10.1007/978-3-642-15552-9_3",
     "den": "Introduced the BAL benchmark of large community-photo problems and studied preconditioned conjugate gradients for them.",
     "dvi": "Giới thiệu bộ dữ liệu BAL gồm các bài toán lớn từ ảnh cộng đồng, và nghiên cứu gradient liên hợp có tiền điều kiện cho chúng."},
    {"name": "Multicore BA", "year": 2011, "node": "l-big", "authors": "Changchang Wu, Sameer Agarwal, Brian Curless, Steven M. Seitz", "venue": "CVPR 2011",
     "title": "Multicore bundle adjustment", "url": "https://doi.org/10.1109/CVPR.2011.5995552",
     "den": "Parallel BA on multicore CPUs and GPUs, with conjugate gradients that avoid forming the Schur complement explicitly.",
     "dvi": "BA song song trên CPU đa nhân và GPU, dùng gradient liên hợp mà không cần lập bù Schur một cách tường minh."},
    {"name": "DSO", "year": 2018, "node": "b-photo", "authors": "Jakob Engel, Vladlen Koltun, Daniel Cremers", "venue": "T-PAMI 2018",
     "title": "Direct Sparse Odometry", "url": "https://doi.org/10.1109/TPAMI.2017.2658577",
     "den": "Photometric BA in a sliding window: poses, point depths and brightness parameters optimized on the photometric error.",
     "dvi": "BA trắc quang trong cửa sổ trượt: tối ưu tư thế, độ sâu điểm và tham số độ sáng theo sai số trắc quang."},
]


def expand(link, codes):
    if link.startswith("10."):
        return "https://doi.org/" + link
    for c, t in codes:
        link = link.replace(c, t)
    return link


def main():
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    files = {v["id"]: json.loads((DATA / f'{v["id"]}.json').read_text(encoding="utf-8")) for v in index["venues"]}
    venue = {v["id"]: v for v in index["venues"]}
    nodes = []
    for tid, en, vi, den, dvi, branches in TREE:
        nodes.append({"id": tid, "parent": None, "en": en, "vi": vi, "den": den, "dvi": dvi})
        for bid, ben, bvi in branches:
            nodes.append({"id": bid, "parent": tid, "en": ben, "vi": bvi})
    top = {n["id"]: n["parent"] for n in nodes if n["parent"]}
    items = list(MANUAL)
    for start, node, name, den, dvi in PAPERS:
        hits = [(vid, i) for vid, d in files.items() for i, t in enumerate(d["t"]) if t.lower().startswith(start.lower())]
        assert len(hits) == 1, (start, [(v, files[v]["t"][i]) for v, i in hits])
        vid, i = hits[0]
        d = files[vid]
        items.append({"name": name, "year": d["y"][i], "node": node, "authors": d["a"][i], "venue": f'{venue[vid]["short"]} {d["y"][i]}',
                      "title": d["t"][i], "url": expand(d["l"][i], index["codes"]), "den": den, "dvi": dvi})
    for it in items:
        it["lineage"] = top[it["node"]]
        it["cite"] = f'{it["authors"]}. {it["title"]}. {it["venue"]}.'
    items.sort(key=lambda x: (x["year"], x["name"].lower()))
    for i, it in enumerate(items):
        it["id"] = i
    data = {"root": {"en": "Bundle adjustment", "vi": "Tối ưu bó (bundle adjustment)",
                     "den": f"{len(items)} papers on bundle adjustment, from its theory to GPU solvers and differentiable layers.",
                     "dvi": f"{len(items)} bài báo về tối ưu bó, từ lý thuyết đến bộ giải trên GPU và lớp khả vi."},
            "trees": [{"id": "lineage", "en": "Lineage", "vi": "Dòng", "nodes": nodes, "field": "node"}],
            "items": items, "chart": "dots", "itemWord": {"en": ["paper", "papers"], "vi": ["bài báo", "bài báo"]}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// Bundle adjustment reading map; generated by scripts/make_blog_ba.py.\n"
                   "window.FAMILY = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(OUT, len(items), "papers;", dict(Counter(it["lineage"] for it in items)), items[0]["year"], "-", items[-1]["year"])
    import blog_cover
    blog_cover.tree_cover(nodes, items, "node", OUT.parent / "cover.svg", OUT.parent / "cover-dark.svg")
    blog_cover.png(OUT.parent / "cover.svg", OUT.parent / "cover.png")



# ---------- static figures (inline SVG) ----------
BODY = ROOT / "data" / "blog" / "bundle-adjustment.html"


def _n(v):
    t = f"{v:.1f}"
    return t[:-2] if t.endswith(".0") else t


def _line(a, b, cls):
    return f'<line class="{cls}" x1="{_n(a[0])}" y1="{_n(a[1])}" x2="{_n(b[0])}" y2="{_n(b[1])}"></line>'


def _circle(c, r, cls):
    return f'<circle class="{cls}" cx="{_n(c[0])}" cy="{_n(c[1])}" r="{_n(r)}"></circle>'


def _rect(x, y, w, h, cls):
    return f'<rect class="{cls}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}"></rect>'


def _path(points, cls, close=False):
    return f'<path class="{cls}" d="M' + "L".join(f"{_n(x)} {_n(y)}" for x, y in points) + ("Z" if close else "") + '"></path>'


def _head(tip, frm, cls, size=9.0):
    """A filled arrowhead at tip, pointing away from frm."""
    dx, dy = tip[0] - frm[0], tip[1] - frm[1]
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    bx, by = tip[0] - ux * size, tip[1] - uy * size
    w = size * 0.45
    return _path([tip, (bx - uy * w, by + ux * w), (bx + uy * w, by - ux * w)], cls, close=True)


def _m(src):
    """Maths label as SVG tspans: {X} is a bold vector, _a or _{ab} a subscript, ^a or ^{ab} a superscript."""
    segs, i = [], 0
    while i < len(src):
        ch = src[i]
        if ch in "_^":
            if src[i + 1] == "{":
                j = src.index("}", i)
                part, i = src[i + 2:j], j + 1
            else:
                part, i = src[i + 1], i + 2
            segs.append((part, "sub" if ch == "_" else "sup"))
        elif ch == "{":
            j = src.index("}", i)
            segs.append((src[i + 1:j], "v"))
            i = j + 1
        else:
            j = i
            while j < len(src) and src[j] not in "_^{":
                j += 1
            segs.append((src[i:j], ""))
            i = j
    out, level = "", 0
    for text, kind in segs:
        want = {"sub": 4, "sup": -7}.get(kind, 0)
        dy = f' dy="{want - level}"' if want != level else ""
        cls = {"sub": ' class="s"', "sup": ' class="s"', "v": ' class="v"'}.get(kind, "")
        out += f"<tspan{dy}{cls}>{html.escape(text)}</tspan>"
        level = want
    return out


def _text(x, y, inner, cls="", anchor="start"):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    c = f' class="{cls}"' if cls else ""
    return f'<text x="{_n(x)}" y="{_n(y)}"{a}{c}>{inner}</text>'


def _bi(x, y, en, vi, cls="", anchor="start"):
    return "".join(_text(x, y, html.escape(t), (cls + " t-" + lang).strip(), anchor) for t, lang in ((en, "en"), (vi, "vi")))


def _svg(w, h, en, vi, body):
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(en)} / {html.escape(vi)}">{body}</svg>'


def fig_reproj():
    """Two cameras, the measured and the predicted ray of one point, and the reprojection error on the image of camera i."""
    plane, half = 178.0, 80.0
    cams = [(150.0, 238.0), (530.0, 238.0)]
    est, meet = (340.0, 62.0), (340.0, 118.0)  # the current estimate of the point; where the measured rays meet

    def hit(c, x):
        t = (plane - c[1]) / (x[1] - c[1])
        return (c[0] + t * (x[0] - c[0]), plane)

    s = ""
    for c in cams:
        d = (meet[0] - c[0], meet[1] - c[1])
        k = 40 / math.hypot(*d)
        s += _line(c, (meet[0] + d[0] * k, meet[1] + d[1] * k), "ray-m") + _line(c, est, "ray")
    for idx, c in enumerate(cams):
        u, p = hit(c, meet), hit(c, est)
        s += _path([(c[0] - half, plane), c, (c[0] + half, plane)], "frustum", close=True)
        s += _line((c[0] - half, plane), (c[0] + half, plane), "plane")
        s += _line(u, p, "res") + _circle(p, 4.8, "pred") + _circle(u, 4.4, "meas") + _circle(c, 3.4, "ctr")
        s += _text(c[0], c[1] + 26, _m("{T}_" + "ik"[idx]), "m", "middle")
    s += _circle(est, 6.5, "pt") + _text(est[0] + 13, est[1] - 7, _m("{X}_j"), "m")
    u, p = hit(cams[0], meet), hit(cams[0], est)
    s += _text(p[0] - 10, plane - 11, _m("π({T}_i{X}_j)"), "m", "end")
    s += _text((u[0] + p[0]) / 2 + 9, plane - 11, _m("{r}_{ij}"), "m res-t", "middle")
    s += _text(u[0] + 11, plane + 21, _m("{u}_{ij}"), "m")
    s += _bi(cams[1][0] + half + 8, plane + 5, "image", "ảnh", "lab")
    return _svg(680, 280, "Reprojection error of one point in two cameras", "Sai số chiếu lại của một điểm trong hai camera", s)


def fig_manifold():
    """The pose group as a curve, its tangent line at T, the step and the exponential map back onto the group."""
    cx, cy, rad = 280.0, 400.0, 300.0

    def on(a):
        return (cx + rad * math.sin(a), cy - rad * math.cos(a))

    a_t, step = math.radians(-20), 180.0
    t_pt, tan = on(a_t), (math.cos(a_t), math.sin(a_t))
    tip = (t_pt[0] + tan[0] * step, t_pt[1] + tan[1] * step)
    a_e = a_t + step / rad
    e_pt = on(a_e)
    lo, hi = math.radians(-40), math.radians(40)
    s = _path([on(lo + (hi - lo) * k / 80) for k in range(81)], "mani")
    s += _line((t_pt[0] - tan[0] * 110, t_pt[1] - tan[1] * 110), (t_pt[0] + tan[0] * 230, t_pt[1] + tan[1] * 230), "tan")
    s += _path([on(a_t + (a_e - a_t) * k / 30) for k in range(31)], "mani-step")
    s += _line(t_pt, (tip[0] - tan[0] * 6, tip[1] - tan[1] * 6), "step") + _head(tip, t_pt, "step-h")
    start, end = (tip[0] + 3, tip[1] + 7), (e_pt[0] + 3, e_pt[1] - 9)
    ctrl = (tip[0] + 30, (tip[1] + e_pt[1]) / 2)
    s += f'<path class="exp" d="M{_n(start[0])} {_n(start[1])}Q{_n(ctrl[0])} {_n(ctrl[1])} {_n(end[0])} {_n(end[1])}"></path>' + _head((e_pt[0] + 1.5, e_pt[1] - 6), ctrl, "exp-h", 8)
    s += _circle(t_pt, 5, "pt") + _circle(e_pt, 5, "pt") + _circle(tip, 4.5, "off")
    s += _text(t_pt[0] + 6, t_pt[1] + 26, _m("{T}"), "m", "middle")
    s += _text(t_pt[0] + tan[0] * 92 - 5, t_pt[1] + tan[1] * 92 - 13, _m("{δξ}"), "m", "middle")
    s += "".join(_text(tip[0] - 10, tip[1] - 12, _m("{T} + {δ}") + f'<tspan class="w">{html.escape(w)}</tspan>', "m t-" + lang, "end")
                 for w, lang in ((": not a pose", "en"), (": không phải tư thế", "vi")))
    s += _text(ctrl[0] - 2, (tip[1] + e_pt[1]) / 2 + 5, _m("Exp"), "m", "start")
    s += _text(e_pt[0] - 4, e_pt[1] + 41, _m("Exp({δξ}){T}"), "m", "middle")
    s += _text(on(hi)[0] - 4, on(hi)[1] + 22, _m("SE(3)"), "m", "end")
    end_t = (t_pt[0] + tan[0] * 230, t_pt[1] + tan[1] * 230)
    s += _bi(end_t[0] + 6, end_t[1] + 2, "tangent space", "không gian tiếp tuyến", "lab")
    s += _bi(end_t[0] + 6, end_t[1] + 18, "at T, 6-D", "tại T, 6 chiều", "lab")
    return _svg(560, 200, "Pose update on the manifold", "Cập nhật tư thế trên đa tạp", s)


def fig_blocks():
    """J, H and S of a small problem: four cameras in a row and five points, each seen by neighbouring cameras."""
    seen = {0: [0, 1], 1: [0, 1, 2], 2: [1, 2, 3, 4], 3: [2, 3, 4]}  # the points each camera sees
    obs = sorted((j, i) for i, js in seen.items() for j in js)        # rows ordered by point
    m, n, u = 4, 5, 4.5
    cw, pw, nc = 6 * u, 3 * u, 4 * 6 * u
    size = nc + n * pw
    tops = 48.0
    xj, xh, xs = 22.0, 252.0, 508.0
    s = ""
    # J
    s += _rect(xj, tops, size, len(obs) * 2 * u, "frame")
    for r, (j, i) in enumerate(obs):
        y = tops + r * 2 * u
        s += _rect(xj + i * cw + 0.5, y + 0.5, cw - 1, 2 * u - 1, "ba-mc") + _rect(xj + nc + j * pw + 0.5, y + 0.5, pw - 1, 2 * u - 1, "ba-mp")
    s += _line((xj + nc, tops), (xj + nc, tops + len(obs) * 2 * u), "sep")
    s += _text(xj + size / 2, tops - 14, _m("{J}"), "m", "middle")
    s += _bi(xj + nc / 2, tops + len(obs) * 2 * u + 18, "cameras", "camera", "", "middle")
    s += _bi(xj + nc + n * pw / 2, tops + len(obs) * 2 * u + 18, "points", "điểm", "", "middle")
    # H
    s += _rect(xh, tops, size, size, "frame")
    for i in range(m):
        s += _rect(xh + i * cw + 0.5, tops + i * cw + 0.5, cw - 1, cw - 1, "ba-mc")
    for j in range(n):
        s += _rect(xh + nc + j * pw + 0.5, tops + nc + j * pw + 0.5, pw - 1, pw - 1, "ba-mp")
    for j, i in obs:
        s += _rect(xh + nc + j * pw + 0.5, tops + i * cw + 0.5, pw - 1, cw - 1, "ba-me") + _rect(xh + i * cw + 0.5, tops + nc + j * pw + 0.5, cw - 1, pw - 1, "ba-me")
    s += _line((xh + nc, tops), (xh + nc, tops + size), "sep") + _line((xh, tops + nc), (xh + size, tops + nc), "sep")
    s += _text(xh + size / 2, tops - 14, _m("{H} = {J}^T{J}"), "m", "middle")
    for lab, x, y in (("B", xh + cw / 2, tops + 3.5 * cw + 6), ("E", xh + nc + 3.5 * pw + 4, tops + cw / 2 + 6),
                      ("E^T", xh + cw / 2, tops + nc + 3.5 * pw + 6), ("C", xh + nc + 3.6 * pw + 4, tops + nc + pw / 2 + 6)):
        s += _text(x, y, _m("{" + lab[0] + "}" + lab[1:]), "m q", "middle")
    # S
    share = lambda a, b: a == b or bool(set(seen[a]) & set(seen[b]))
    s += _rect(xs, tops, m * cw, m * cw, "frame")
    for a in range(m):
        for b in range(m):
            if share(a, b):
                s += _rect(xs + b * cw + 0.5, tops + a * cw + 0.5, cw - 1, cw - 1, "ba-mc")
            else:
                s += _text(xs + b * cw + cw / 2, tops + a * cw + cw / 2 + 5, "0", "", "middle")
    s += _text(xs + m * cw / 2, tops - 14, _m("{S} = {B} − {E}{C}^{−1}{E}^T"), "m", "middle")
    s += _bi(xs + m * cw / 2, tops + m * cw + 18, "cameras only", "chỉ còn camera", "", "middle")
    return _svg(680, 236, "Block structure of J, H and the Schur complement S", "Cấu trúc khối của J, H và phần bù Schur S", s)


def fig_gauge():
    """The same reconstruction before and after a similarity transform: identical images."""
    pts = [(-1.0, 1.25), (-0.15, 1.7), (0.9, 1.4), (0.35, 0.85), (-0.55, 0.8)]
    cams = [(-1.25, -0.55), (0.25, -0.8), (1.45, -0.3)]
    mid = (0.1, 0.45)
    cen = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    def scene(scale, rot, at):
        c, si = math.cos(rot), math.sin(rot)
        tf = lambda p: (mid[0] + scale * (c * (p[0] - mid[0]) - si * (p[1] - mid[1])), mid[1] + scale * (si * (p[0] - mid[0]) + c * (p[1] - mid[1])))
        px = lambda p: (at[0] + 44 * (p[0] - mid[0]), at[1] - 44 * (p[1] - mid[1]))
        out = ""
        for q in cams:
            for p in pts:
                out += _line(px(tf(q)), px(tf(p)), "ray")
        for q in cams:
            h = math.atan2(cen[1] - q[1], cen[0] - q[0]) + rot
            apex, ln = tf(q), 0.42 * scale
            out += _path([px(apex), px((apex[0] + ln * math.cos(h + 0.42), apex[1] + ln * math.sin(h + 0.42))),
                          px((apex[0] + ln * math.cos(h - 0.42), apex[1] + ln * math.sin(h - 0.42)))], "wedge", close=True)
        for p in pts:
            out += _circle(px(tf(p)), 3.6, "pt")
        return out

    s = scene(1.0, 0.0, (150.0, 118.0)) + scene(1.35, math.radians(32), (505.0, 112.0))
    s += _line((262, 112), (372, 112), "arrow") + _head((382, 112), (262, 112), "arrow-h")
    s += _bi(322, 100, "move, turn, scale", "dịch, xoay, co giãn", "lab", "middle")
    s += _bi(322, 134, "same images", "ảnh không đổi", "", "middle")
    s += _bi(150, 222, "one solution", "một nghiệm", "", "middle") + _bi(505, 222, "another one, just as good", "một nghiệm khác, tốt như vậy", "", "middle")
    return _svg(680, 232, "Gauge freedom: a similarity transform does not change the images", "Bậc tự do gauge: phép đồng dạng không làm ảnh thay đổi", s)


def fig_bae():
    """A dense Jacobian next to the blocks and indices that BAE keeps."""
    obs = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 3)]  # (camera, point)
    cams, pts, cu, rh = 3, 4, 5.0, 12.0
    nc, ncol = 9 * cams, 9 * cams + 3 * pts
    x0, y0 = 16.0, 46.0
    hgt = len(obs) * rh
    s = _rect(x0, y0, ncol * cu, hgt, "frame")
    for k in range(1, ncol):
        s += _line((x0 + k * cu, y0), (x0 + k * cu, y0 + hgt), "cell")
    for k in range(1, 2 * len(obs)):
        s += _line((x0, y0 + k * rh / 2), (x0 + ncol * cu, y0 + k * rh / 2), "cell")
    for r, (c, p) in enumerate(obs):
        y = y0 + r * rh
        s += _rect(x0 + c * 9 * cu, y, 9 * cu, rh, "ba-mc") + _rect(x0 + (nc + 3 * p) * cu, y, 3 * cu, rh, "ba-mp")
    s += _line((x0 + nc * cu, y0), (x0 + nc * cu, y0 + hgt), "sep")
    s += _bi(x0, y0 - 14, "generic autograd: dense", "vi phân tự động tổng quát: dày đặc", "lab")
    s += _bi(x0 + nc * cu / 2, y0 + hgt + 18, "cameras", "camera", "", "middle") + _bi(x0 + (nc + 6) * cu, y0 + hgt + 18, "points", "điểm", "", "middle")
    ax = x0 + ncol * cu
    s += _line((ax + 14, y0 + hgt / 2), (ax + 50, y0 + hgt / 2), "arrow") + _head((ax + 60, y0 + hgt / 2), (ax + 14, y0 + hgt / 2), "arrow-h")
    tx = ax + 82
    cols = (tx, tx + 40, tx + 78, tx + 140)
    s += _bi(tx - 12, y0 - 14, "BAE: blocks and indices", "BAE: các khối và chỉ số", "lab")
    s += _text(cols[0], y0 - 2, "cidx", "mono", "middle") + _text(cols[1], y0 - 2, "pidx", "mono", "middle")
    s += _bi(cols[2] + 22, y0 - 2, "2×9", "2×9", "", "middle") + _bi(cols[3] - 1, y0 - 2, "2×3", "2×3", "", "middle")
    for r, (c, p) in enumerate(obs):
        y = y0 + r * rh + 3
        s += _text(cols[0], y + 8.5, str(c), "mono", "middle") + _text(cols[1], y + 8.5, str(p), "mono", "middle")
        s += _rect(cols[2], y, 9 * cu, rh - 2, "ba-mc") + _rect(cols[3] - 7.5, y, 3 * cu, rh - 2, "ba-mp")
    return _svg(520, 186, "Dense Jacobian versus the blocks that BAE stores", "Jacobian dày đặc so với các khối mà BAE lưu", s)


FIGURES = {"reproj": fig_reproj, "manifold": fig_manifold, "blocks": fig_blocks, "gauge": fig_gauge, "bae": fig_bae}


def figures():
    body = BODY.read_text(encoding="utf-8")
    for name, draw in FIGURES.items():
        pat = re.compile(f"<!--fig:{name}-->.*?<!--/fig:{name}-->", re.S)
        assert len(pat.findall(body)) == 1, name
        body = pat.sub(lambda _m_: f'<!--fig:{name}--><!-- prettier-ignore --><div class="ba-scroll">{draw()}</div><!--/fig:{name}-->', body)  # keep the tspans together
    BODY.write_text(body, encoding="utf-8")
    print(BODY, "figures:", ", ".join(FIGURES))


if __name__ == "__main__":
    if "--figures" not in sys.argv:
        main()
    figures()
