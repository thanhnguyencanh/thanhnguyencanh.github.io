#!/usr/bin/env python3
"""Data for the blog post "A family tree of visual SLAM" (blog/slam-family-tree/data.js).

Source: the systems compared in our four SLAM surveys, read from the data files of their project pages
(local copies in ../pairslab.github.io/publications/; they are not in this repository, so the generated data.js is committed).
Run: python3 scripts/make_blog_slam_tree.py   (then python3 scripts/build_site.py)
Each system is placed once, in a seven-lineage tree whose branches follow the surveys' own groupings.

Rules (also stated in the post):
  * The same paper in two surveys is merged when the names match and the two references share an author name;
    the earlier of the cited years is kept.
  * Placement follows the most specific survey that covers the system: collaborative survey, then open-world survey,
    then semantic survey, then the colonoscopy survey.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT.parent / "pairslab.github.io" / "publications"  # project-page sources, kept next to this repository
OUT = ROOT / "blog" / "slam-family-tree" / "data.js"

SOURCES = {
    "gs": {"dir": "3D Collab GS Survey/assets/data.js", "url": "https://thanhnguyencanh.github.io/3DCollabGS-SLAM-Survey/",
           "en": "Collaborative SLAM in the era of 3D Gaussian splatting (survey, preprint)",
           "vi": "SLAM cộng tác trong kỷ nguyên 3D Gaussian Splatting (khảo sát, bản preprint)"},
    "ow": {"dir": "OpenSemanticSLAM/site/assets/data.js", "url": "https://thanhnguyencanh.github.io/open-semanticSLAM-survey/",
           "en": "Open-world semantic SLAM (survey, preprint)", "vi": "SLAM ngữ nghĩa thế giới mở (khảo sát, bản preprint)"},
    "sem": {"dir": "Seman SLAM Survey/assets/data.js", "url": "https://thanhnguyencanh.github.io/Semantic-Slam-survey/",
            "en": "Semantic visual SLAM (survey, Robotics and Autonomous Systems 2026)",
            "vi": "SLAM thị giác ngữ nghĩa (khảo sát, Robotics and Autonomous Systems 2026)"},
    "col": {"dir": "MonovSLAM 4 Colon Survey/assets/data.js", "url": "https://thanhnguyencanh.github.io/MonovSLAM4Colon/",
            "en": "Monocular vSLAM for colonoscopy (survey, preprint)", "vi": "vSLAM một camera cho nội soi đại tràng (khảo sát, bản preprint)"},
}
PRIORITY = ["gs", "ow", "sem", "col"]

# lineage -> branches: (id, en, vi, description en, description vi)
TREE = [
    ("semantic", "Semantic & object SLAM", "SLAM ngữ nghĩa và đối tượng",
     "Maps that carry meaning on top of geometry: object instances, semantic labels and 3D scene graphs.",
     "Bản đồ mang ý nghĩa trên nền hình học: các đối tượng, nhãn ngữ nghĩa và đồ thị cảnh 3D.",
     [("objects", "Objects & closed-set semantics", "Đối tượng và ngữ nghĩa tập đóng",
       "Semantic labels from a fixed class list, fused into dense maps or object-level landmarks.",
       "Nhãn ngữ nghĩa từ một danh sách lớp cố định, được hợp nhất vào bản đồ dày đặc hoặc mốc ở mức đối tượng."),
      ("scene-graphs", "3D scene graphs & scene understanding", "Đồ thị cảnh 3D và hiểu cảnh",
       "Layered graphs of places, rooms and objects built from metric-semantic maps.",
       "Đồ thị nhiều tầng gồm địa điểm, phòng và đối tượng, xây dựng từ bản đồ hình học–ngữ nghĩa.")]),
    ("neural", "Neural & Gaussian maps", "Bản đồ nơ-ron và Gaussian",
     "Differentiable scene representations optimized together with the camera poses by rendering.",
     "Biểu diễn cảnh khả vi, được tối ưu cùng tư thế camera thông qua kết xuất (rendering).",
     [("nerf", "Neural implicit fields (NeRF-style)", "Trường ẩn nơ-ron (kiểu NeRF)",
       "Global MLPs, feature grids, tri-planes and neural points that store geometry and appearance implicitly.",
       "MLP toàn cục, lưới đặc trưng, tri-plane và điểm nơ-ron lưu hình học và diện mạo một cách ẩn."),
      ("gaussian", "3D Gaussian splatting", "3D Gaussian Splatting",
       "Explicit Gaussian primitives that render in real time and can be edited one by one.",
       "Các phần tử Gaussian tường minh, kết xuất theo thời gian thực và có thể chỉnh sửa từng phần tử.")]),
    ("foundation", "Foundation models & open vocabulary", "Mô hình nền tảng và từ vựng mở",
     "Vision–language models such as CLIP, DINO and SAM let a map answer free-form language queries.",
     "Các mô hình thị giác–ngôn ngữ như CLIP, DINO và SAM giúp bản đồ trả lời truy vấn ngôn ngữ tự do.",
     [("open-vocab", "Open-vocabulary maps", "Bản đồ từ vựng mở",
       "Per-element language features or labels from foundation models, queried without a fixed class list.",
       "Đặc trưng ngôn ngữ hoặc nhãn từ mô hình nền tảng cho từng phần tử, truy vấn mà không cần danh sách lớp cố định."),
      ("fm-slam", "Foundation-model SLAM & language", "SLAM dùng mô hình nền tảng và ngôn ngữ",
       "SLAM pipelines that fuse foundation-model features or language into the map itself.",
       "Các hệ SLAM hợp nhất đặc trưng của mô hình nền tảng hoặc ngôn ngữ vào chính bản đồ.")]),
    ("uncertainty", "Uncertainty-aware SLAM", "SLAM nhận biết độ bất định",
     "Calibrated beliefs about geometry and meaning, not only point estimates.",
     "Niềm tin được hiệu chỉnh về hình học và ngữ nghĩa, không chỉ là ước lượng điểm.",
     [("geo-unc", "Geometric uncertainty", "Độ bất định hình học",
       "Depth and pose uncertainty inside neural SLAM.", "Độ bất định của độ sâu và tư thế trong SLAM nơ-ron."),
      ("sem-unc", "Semantic uncertainty", "Độ bất định ngữ nghĩa",
       "Bayesian kernel inference and evidential learning for calibrated semantic labels.",
       "Suy luận kernel Bayes và học bằng chứng (evidential learning) cho nhãn ngữ nghĩa được hiệu chỉnh.")]),
    ("lifelong", "Lifelong & dynamic SLAM", "SLAM dài hạn và môi trường động",
     "Maps that stay useful as the world changes, within a session and across sessions.",
     "Bản đồ vẫn hữu ích khi thế giới thay đổi, trong một phiên và qua nhiều phiên.",
     [("submaps", "Submaps & multi-session", "Bản đồ con và nhiều phiên",
       "Independently optimizable submaps, loop closure and maps reused across visits.",
       "Bản đồ con tối ưu độc lập, đóng vòng lặp và bản đồ dùng lại qua nhiều lần ghé thăm."),
      ("dynamic", "Dynamic scenes", "Cảnh động",
       "Tracking and mapping among moving people and objects.", "Định vị và lập bản đồ giữa người và vật thể chuyển động.")]),
    ("collaborative", "Collaborative & multi-robot SLAM", "SLAM cộng tác và đa robot",
     "Several agents build one map together, from shared keyframes to shared neural and Gaussian maps.",
     "Nhiều tác tử cùng xây dựng một bản đồ, từ chia sẻ keyframe đến chia sẻ bản đồ nơ-ron và Gaussian.",
     [("co-classic", "Classic collaborative SLAM", "SLAM cộng tác cổ điển",
       "Centralized and distributed visual and visual-inertial SLAM with sparse maps.",
       "SLAM thị giác và thị giác–quán tính tập trung hoặc phân tán với bản đồ thưa."),
      ("co-implicit", "Collaborative neural implicit", "Cộng tác với trường ẩn nơ-ron",
       "Agents that train and share neural implicit maps.", "Các tác tử huấn luyện và chia sẻ bản đồ trường ẩn nơ-ron."),
      ("co-gs", "Collaborative Gaussian splatting", "Cộng tác với Gaussian Splatting",
       "Agents that exchange and merge Gaussian submaps.", "Các tác tử trao đổi và hợp nhất bản đồ con Gaussian."),
      ("co-semantic", "Multi-robot semantic SLAM", "SLAM ngữ nghĩa đa robot",
       "Teams that share semantic maps of objects and places.", "Các nhóm robot chia sẻ bản đồ ngữ nghĩa về đối tượng và địa điểm.")]),
    ("endoscopic", "Endoscopic & deformable SLAM", "SLAM nội soi và môi trường biến dạng",
     "Monocular SLAM inside the body, where low texture, specular highlights and moving tissue break the usual "
     "assumptions. It includes general systems that the survey benchmarks on colonoscopy.",
     "SLAM một camera bên trong cơ thể, nơi bề mặt ít kết cấu, phản xạ gương và mô chuyển động phá vỡ các giả thiết "
     "thông thường. Nhánh này gồm cả các hệ tổng quát được khảo sát đánh giá trên dữ liệu nội soi đại tràng.",
     [("endo-feature", "Feature-based", "Dựa trên đặc trưng", "Keypoint tracking and mapping.", "Theo dõi và lập bản đồ bằng điểm đặc trưng."),
      ("endo-direct", "Direct", "Phương pháp trực tiếp", "Photometric alignment of image intensities.", "Căn chỉnh trắc quang theo cường độ ảnh."),
      ("endo-dl", "Deep learning", "Học sâu", "Learned depth, flow or neural and Gaussian maps.", "Độ sâu, dòng quang học học được hoặc bản đồ nơ-ron và Gaussian."),
      ("endo-nonrigid", "Non-rigid (deformable)", "Không cứng (biến dạng)",
       "Models that let the scene deform while the camera moves.", "Mô hình cho phép cảnh biến dạng trong khi camera di chuyển.")]),
]

# names that only one survey lists inside a coarse family: their branch, fixed by hand
SEM_CONTINUOUS = {"H2-Mapping": "nerf", "H3-Mapping": "nerf"}


def load(path):
    t = (PUB / path).read_text(encoding="utf-8")
    return json.loads(t[t.index("{"):t.rstrip().rindex(";")])


def branch_of(src, s):
    if src == "gs":
        return {"classic": "co-classic", "implicit": "co-implicit", "gs": "co-gs"}[s["family"]]
    if src == "ow":
        p, g = s["pillar"], s["group"]
        if p == "P1":
            return "nerf" if g.startswith("NeRF") else "gaussian"
        if p == "P2":
            return "objects" if g.startswith("Closed") else "open-vocab"
        if p == "P3":
            return "geo-unc" if g.startswith("Geometric") else "sem-unc"
        if p == "P4":
            return "submaps" if g.startswith("Submaps") else "dynamic"
        return "scene-graphs"
    if src == "sem":
        f = s["family"]
        if f == "classic":
            return "scene-graphs" if s["name"] in ("Kimera", "Hydra") else "objects"
        if f == "continuous":
            return SEM_CONTINUOUS.get(s["name"])  # the others are also in the open-world survey, whose placement wins
        if f == "foundation":
            return "fm-slam"
        return "co-semantic"
    return {"feature": "endo-feature", "direct": "endo-direct", "dl": "endo-dl", "nonrigid": "endo-nonrigid"}[s["family"]]


norm = lambda n: re.sub(r"[^a-z0-9+]", "", n.lower())
STOP = {"and", "the", "for", "with", "slam", "visual", "dense", "neural", "gaussian", "splatting", "real", "time", "semantic", "mapping",
        "implicit", "multi", "robot", "agent", "collaborative", "online", "scene", "graph", "graphs", "learning", "monocular", "map", "maps"}
authors = lambda c: {w.lower() for w in re.findall(r"[A-Za-zÀ-ž]{3,}", c[:45])} - STOP


def make_facts(items, nodes):
    """Sentences for the post, computed from the data (both languages)."""
    from collections import Counter
    name = {n["id"]: n for n in nodes}
    lin = Counter(i["lineage"] for i in items)
    br = Counter(i["node"] for i in items)
    big, nbig = lin.most_common(1)[0]
    bbr, nbbr = br.most_common(1)[0]
    first_b = min(i["year"] for i in items if i["node"] == bbr)
    old = items[0]
    recent = sum(1 for i in items if i["year"] >= 2023)
    multi = sum(1 for i in items if len(i["sources"]) > 1)
    L = lambda k, l: name[k][l]
    return {
        "biggest": {"en": f"**{L(big, 'en')}** is the largest lineage, with **{nbig}** systems; its branch **{L(bbr, 'en')}** alone has **{nbbr}**, all from {first_b} on.",
                    "vi": f"**{L(big, 'vi')}** là dòng lớn nhất, với **{nbig}** hệ thống; riêng nhánh **{L(bbr, 'vi')}** có **{nbbr}** hệ thống, tất cả từ năm {first_b} trở đi."},
        "oldest": {"en": f"The oldest system in the tree is **{old['name']}** ({old['year']}), in **{L(old['lineage'], 'en')}**.",
                   "vi": f"Hệ thống lâu đời nhất trên cây là **{old['name']}** ({old['year']}), thuộc dòng **{L(old['lineage'], 'vi')}**."},
        "recent": {"en": f"**{recent}** of the {len(items)} systems ({round(100 * recent / len(items))}%) appeared in 2023 or later.",
                   "vi": f"**{recent}** trên {len(items)} hệ thống ({round(100 * recent / len(items))}%) ra đời từ năm 2023 trở đi."},
        "multi": {"en": f"**{multi}** systems are compared in more than one of our surveys.",
                  "vi": f"**{multi}** hệ thống được so sánh trong nhiều hơn một bài khảo sát của chúng tôi."},
    }


def main():
    entries = []
    for src in PRIORITY:
        for s in load(SOURCES[src]["dir"])["systems"]:
            entries.append({"src": src, "name": s["name"], "year": int(s["year"]), "cite": s["cite"], "branch": branch_of(src, s)})
    merged = []
    for e in entries:  # entries arrive in priority order, so the first match is the primary placement
        twin = next((m for m in merged if norm(m["name"]) == norm(e["name"]) and e["src"] not in m["sources"]
                     and abs(m["year"] - e["year"]) <= 2 and authors(m["cite"]) & authors(e["cite"])), None)
        if twin:
            twin["sources"].append(e["src"])
            twin["year"] = min(twin["year"], e["year"])
            twin["merged_from"].append((e["src"], e["name"], e["year"]))
        else:
            merged.append({**e, "sources": [e["src"]], "merged_from": []})
    for m in merged:
        if m["merged_from"]:
            print("merged:", m["name"], m["src"], "<-", m["merged_from"])
    branch_ids = {b[0] for l in TREE for b in l[5]}
    assert all(m["branch"] in branch_ids for m in merged), [m["name"] for m in merged if m["branch"] not in branch_ids]
    lineage_of = {b[0]: l[0] for l in TREE for b in l[5]}
    nodes = []
    for lid, en, vi, den, dvi, branches in TREE:
        nodes.append({"id": lid, "parent": None, "en": en, "vi": vi, "den": den, "dvi": dvi})
        for bid, ben, bvi, bden, bdvi in branches:
            nodes.append({"id": bid, "parent": lid, "en": ben, "vi": bvi, "den": bden, "dvi": bdvi})
    sources = {k: {"en": v["en"], "vi": v["vi"], "url": v["url"]} for k, v in SOURCES.items()}
    items = sorted(({"name": m["name"], "year": m["year"], "node": m["branch"], "lineage": lineage_of[m["branch"]], "cite": m["cite"],
                     "sources": m["sources"]} for m in merged), key=lambda x: (x["year"], x["name"].lower()))
    for i, it in enumerate(items):
        it["id"] = i
    facts = make_facts(items, nodes)
    data = {"root": {"en": "Visual SLAM", "vi": "SLAM thị giác",
                     "den": "All systems compared in our four SLAM surveys, in seven lineages.",
                     "dvi": "Tất cả hệ thống được so sánh trong bốn bài khảo sát SLAM của chúng tôi, chia thành bảy dòng."},
            "facts": facts, "levels": {"en": ["Lineage", "Branch", "System"], "vi": ["Dòng", "Nhánh", "Hệ thống"]},
            "trees": [{"id": "lineage", "en": "Lineage", "vi": "Dòng", "nodes": nodes, "field": "node"}],
            "items": items, "sources": sources, "chart": "dots"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// Systems from our four SLAM surveys, placed in one family tree; generated by scripts/make_blog_slam_tree.py.\n"
                   "window.FAMILY = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    import blog_cover  # cover pictures from the same data (light, dark, and a PNG for link previews)
    blog_cover.tree_cover(nodes, items, "node", OUT.parent / "cover.svg", OUT.parent / "cover-dark.svg")
    blog_cover.png(OUT.parent / "cover.svg", OUT.parent / "cover.png")
    from collections import Counter
    print(OUT, len(items), "systems;", dict(Counter(i["lineage"] for i in items)), "years", items[0]["year"], "-", items[-1]["year"])


if __name__ == "__main__":
    main()
