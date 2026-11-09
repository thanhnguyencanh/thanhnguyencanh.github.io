#!/usr/bin/env python3
"""Data for the blog post "Foundation models and world models for SLAM" (blog/fm-world-models-slam/data.js).

Source: the Paper Explorer data (explorer/data/*.json, 14 venues, from the dblp dump). A paper is kept when its title
names SLAM or mapping AND a foundation model or world model; it is then placed in one branch by keyword rules.

Run after scripts/make_paper_explorer.py:  python3 scripts/make_blog_fm_slam.py [--list]   (then python3 scripts/build_site.py)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "explorer" / "data"
OUT = ROOT / "blog" / "fm-world-models-slam" / "data.js"

SLAM_WORDS = ["slam", "odometry", "place recognition", "loop closure", "loop closing", "relocalization", "relocalisation", "visual localization",
              "camera localization", "global localization", "robot localization", "localization and mapping", "structure from motion",
              "structure-from-motion", "sfm", "bundle adjustment", "3d reconstruction", "scene reconstruction", "dense reconstruction",
              "3d mapping", "semantic mapping", "online mapping", "mapping", "semantic map", "3d map", "neural map", "scene graph",
              "occupancy", "spatial memory", "camera pose estimation", "pose estimation of camera", "visual-inertial", "lidar-inertial"]
# In vision and machine-learning venues, "scene graph", "mapping" and "3D reconstruction" usually mean image scene graphs,
# function mappings and single objects, so there only these unambiguous SLAM terms count:
STRICT_SLAM = ["slam", "odometry", "place recognition", "loop closure", "loop closing", "relocalization", "relocalisation", "visual localization",
               "camera localization", "global localization", "localization and mapping", "structure from motion", "structure-from-motion",
               "bundle adjustment", "3d scene graph", "3d mapping", "online mapping", "scene reconstruction",
               "dense reconstruction", "3d occupancy", "occupancy world", "occupancy forecasting", "visual-inertial", "lidar-inertial", "spatial memory"]
NOT_SLAM = ["visual-semantic mapping", "tone mapping", "mapping network", "style mapping", "texture mapping", "uv mapping"]
# the title must name one of these: a foundation model or a world model (the branch keywords below only pick the branch)
STRONG = ["foundation model", "clip", "dino", "dinov2", "segment anything", "sam2", "sam 2", "sam-based", "sam-guided", "sam-assisted", "llm", "large language model", "language model",
          "vision-language", "vision language", "vlm", "mllm", "multimodal large language", "gpt", "chatgpt", "open-vocabulary", "open vocabulary",
          "open-set", "language-embedded", "language field", "language-guided", "language-driven", "text-queryable", "dust3r", "mast3r", "vggt",
          "pointmap", "depth anything", "metric3d", "unidepth", "world model", "diffusion", "generative", "video generation", "zero-shot", "large model"]

# (id, en, vi, den, dvi, [(leaf id, en, vi, den, dvi, keywords)])
TREE = [
    ("lang", "Language & open-vocabulary maps", "Bản đồ ngôn ngữ và từ vựng mở",
     "Maps that store vision-language features, so a robot can find things by name, or let a language model reason over them.",
     "Bản đồ lưu đặc trưng thị giác-ngôn ngữ, để robot tìm đồ vật theo tên, hoặc để mô hình ngôn ngữ suy luận trên bản đồ.",
     [("l-ov", "Open-vocabulary 3D maps", "Bản đồ 3D từ vựng mở", "CLIP-style features fused into 3D maps and queried with free text.",
       "Đặc trưng kiểu CLIP được hợp nhất vào bản đồ 3D và truy vấn bằng văn bản tự do.",
       ["open-vocabulary", "open vocabulary", "open-set", "clip", "language-embedded", "language field", "language-guided", "language-driven",
        "text-queryable", "language", "vision-language feature"]),
      ("l-llm", "LLMs and VLMs on maps", "LLM và VLM trên bản đồ", "Language models that plan, answer questions or act using a map.",
       "Mô hình ngôn ngữ lập kế hoạch, trả lời câu hỏi hoặc hành động dựa trên bản đồ.",
       ["large language model", "llm", "vision-language model", "vlm", "mllm", "multimodal large language", "gpt", "chatgpt", "language agent",
        "reasoning", "question answering"]),
      ("l-graph", "Scene graphs with foundation models", "Đồ thị cảnh với mô hình nền tảng", "3D scene graphs whose nodes and relations come from foundation models.",
       "Đồ thị cảnh 3D có nút và quan hệ đến từ mô hình nền tảng.", ["scene graph", "3d scene graph"])]),
    ("geo", "Geometry & vision foundation models", "Mô hình nền tảng hình học và thị giác",
     "Large pretrained models that give SLAM depth, correspondences, features or masks without task-specific training.",
     "Các mô hình tiền huấn luyện lớn cung cấp độ sâu, tương ứng điểm, đặc trưng hoặc mặt nạ cho SLAM mà không cần huấn luyện riêng.",
     [("g-3r", "Pointmap & feed-forward reconstruction", "Pointmap và tái tạo một lượt", "DUSt3R, MASt3R, VGGT and similar models that predict 3D points from images.",
       "DUSt3R, MASt3R, VGGT và các mô hình tương tự dự đoán điểm 3D trực tiếp từ ảnh.",
       ["dust3r", "mast3r", "vggt", "pointmap", "feed-forward", "feedforward", "3r", "reconstruction foundation", "3d foundation model", "geometric foundation"]),
      ("g-depth", "Depth foundation models", "Mô hình nền tảng độ sâu", "Depth Anything, Metric3D, UniDepth and other zero-shot depth priors.",
       "Depth Anything, Metric3D, UniDepth và các mô hình độ sâu zero-shot khác.",
       ["depth anything", "metric3d", "unidepth", "depth foundation", "foundation depth", "zero-shot depth", "metric depth"]),
      ("g-feat", "Pretrained features", "Đặc trưng tiền huấn luyện", "DINO and other foundation features for matching, place recognition and loop closure.",
       "DINO và các đặc trưng nền tảng khác cho so khớp, nhận dạng địa điểm và đóng vòng.",
       ["dino", "dinov2", "foundation feature", "anyloc", "pretrained feature", "pre-trained feature", "foundation model feature",
        "vision foundation model", "visual foundation model"]),
      ("g-sam", "Segment Anything priors", "Tiền nghiệm Segment Anything", "SAM masks for dynamic objects, instances and semantics in SLAM.",
       "Mặt nạ SAM cho vật thể động, thực thể và ngữ nghĩa trong SLAM.",
       ["segment anything", "sam2", "sam 2", "sam-based", "sam-guided", "sam-assisted"])]),
    ("world", "World models & generative priors", "Mô hình thế giới và tiền nghiệm sinh",
     "Models that predict or imagine how a scene looks or evolves, used to complete, forecast or simulate maps.",
     "Các mô hình dự đoán hoặc hình dung cảnh trông ra sao và thay đổi thế nào, dùng để hoàn thiện, dự báo hoặc mô phỏng bản đồ.",
     [("w-wm", "World models", "Mô hình thế giới", "Learned models of how the world changes, used for prediction and planning.",
       "Mô hình học được về cách thế giới thay đổi, dùng để dự đoán và lập kế hoạch.", ["world model"]),
      ("w-gen", "Diffusion & generative scene priors", "Tiền nghiệm cảnh từ mô hình khuếch tán và mô hình sinh",
       "Diffusion and other generative models that complete, denoise or create maps and views.",
       "Mô hình khuếch tán và các mô hình sinh khác dùng để hoàn thiện, khử nhiễu hoặc tạo bản đồ và góc nhìn.",
       ["diffusion", "generative", "gan", "video generation", "inpainting", "flow matching"]),
      ("w-occ", "Occupancy & scene forecasting", "Dự báo chiếm chỗ và cảnh", "Predicting future occupancy and scenes, mostly for driving.",
       "Dự đoán trạng thái chiếm chỗ và cảnh trong tương lai, chủ yếu cho lái xe tự hành.",
       ["occupancy forecasting", "occupancy prediction", "forecasting", "future occupancy", "4d occupancy", "occupancy world"])]),
    ("generic", "Foundation models, other uses", "Mô hình nền tảng, cách dùng khác",
     "Papers that use a foundation model in SLAM or mapping in another way.", "Các bài dùng mô hình nền tảng cho SLAM hoặc lập bản đồ theo cách khác.",
     [("f-other", "Other foundation-model uses", "Cách dùng mô hình nền tảng khác", "Foundation models used in other parts of the pipeline.",
       "Mô hình nền tảng được dùng ở các phần khác của hệ thống.", ["foundation model", "zero-shot", "pretrained", "pre-trained", "large model"])]),
]
ORDER = ["g-3r", "g-depth", "g-sam", "g-feat", "w-wm", "l-graph", "l-llm", "l-ov", "w-occ", "w-gen", "f-other"]


def pattern(word):
    return re.compile(r"(?<![a-z0-9])" + re.escape(word) + r"(?:s|es)?(?![a-z0-9])")


SLAM_RX = [pattern(w) for w in SLAM_WORDS]
STRICT_RX = [pattern(w) for w in STRICT_SLAM]
STRONG_RX = [pattern(w) for w in STRONG]
NOT_RX = [pattern(w) for w in NOT_SLAM]
PAIRS = sorted(((pattern(w), leaf[0], len(w)) for top in TREE for leaf in top[5] for w in leaf[5]), key=lambda x: -x[2])
assert set(ORDER) == {leaf[0] for top in TREE for leaf in top[5]}


def is_slam(t, field):
    for rx in NOT_RX:
        t = rx.sub(" ", t)
    return any(rx.search(t) for rx in (SLAM_RX if field == "rob" else STRICT_RX))


def classify(title):
    t, score = title.lower(), Counter()
    for rx, lid, _ in PAIRS:
        if rx.search(t):
            score[lid] += 1
            t = rx.sub(lambda m: "#" * len(m.group(0)), t)
    if not score:
        return None
    return max(score, key=lambda lid: (score[lid], -ORDER.index(lid)))


def main():
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    codes = index.get("codes", [])
    def expand(l):
        if l.startswith("10."):
            return "https://doi.org/" + l
        for c, text in codes:
            l = l.replace(c, text)
        return l
    picked = []
    for v in index["venues"]:
        d = json.loads((DATA / f'{v["id"]}.json').read_text(encoding="utf-8"))
        for t, a, y, l in zip(d["t"], d["a"], d["y"], d["l"]):
            low = t.lower()
            if not is_slam(low, v["field"]) or not any(rx.search(low) for rx in STRONG_RX):
                continue
            leaf = classify(t)
            if leaf:
                picked.append({"title": t, "authors": a, "year": y, "venue": f'{v["short"]} {y}', "url": expand(l), "node": leaf, "field": v["field"]})
    picked.sort(key=lambda x: (x["year"], x["title"].lower()))
    if "--list" in sys.argv:
        for p in picked:
            print(f'{p["node"]:8} {p["venue"]:13} {p["title"][:110]}')
    nodes = []
    for tid, en, vi, den, dvi, leaves in TREE:
        nodes.append({"id": tid, "parent": None, "en": en, "vi": vi, "den": den, "dvi": dvi})
        for lid, len_, lvi, lden, ldvi, _ in leaves:
            nodes.append({"id": lid, "parent": tid, "en": len_, "vi": lvi, "den": lden, "dvi": ldvi})
    top = {n["id"]: (n["parent"] or n["id"]) for n in nodes}
    name = {n["id"]: n for n in nodes}
    for i, p in enumerate(picked):
        p["id"] = i
        p["lineage"] = top[p["node"]]
    by_top = Counter(p["lineage"] for p in picked)
    by_leaf = Counter(p["node"] for p in picked)
    by_year = Counter(p["year"] for p in picked)
    venues = Counter(p["venue"].rsplit(" ", 1)[0] for p in picked)
    first = {lid: min((p for p in picked if p["node"] == lid), key=lambda p: (p["year"], p["title"])) for lid in by_leaf}
    recent = sum(n for y, n in by_year.items() if y >= 2024)
    rob = sum(1 for p in picked if p["field"] == "rob")
    fmt_vi = lambda n: f"{n:,}".replace(",", ".")
    bl, nbl = by_leaf.most_common(1)[0]
    v1, nv1 = venues.most_common(1)[0]
    n3r = by_leaf.get("g-3r", 0)
    y3r = min((p["year"] for p in picked if p["node"] == "g-3r"), default=None)
    facts = {
        "recent": {"en": f"**{recent}** of the {len(picked)} papers ({round(100 * recent / len(picked))}%) appeared in 2024 or later.",
                   "vi": f"**{recent}** trên {len(picked)} bài báo ({round(100 * recent / len(picked))}%) ra đời từ năm 2024 trở đi."},
        "biggest": {"en": f"The largest branch is **{name[bl]['en']}**, with **{nbl}** papers.",
                    "vi": f"Nhánh lớn nhất là **{name[bl]['vi']}**, với **{nbl}** bài báo."},
        "venue": {"en": f"**{v1}** published the most of them (**{nv1}**); **{round(100 * rob / len(picked))}%** appeared in robotics venues.",
                  "vi": f"**{v1}** công bố nhiều nhất (**{nv1}** bài); **{round(100 * rob / len(picked))}%** xuất hiện ở các hội nghị và tạp chí robot."},
    }
    if n3r:
        facts["pointmap"] = {"en": f"**{n3r}** papers build on pointmap or 3D foundation models such as DUSt3R, MASt3R and VGGT, all from **{y3r}** on.",
                             "vi": f"**{n3r}** bài báo dựa trên mô hình pointmap hoặc mô hình nền tảng 3D như DUSt3R, MASt3R và VGGT, tất cả từ năm **{y3r}** trở đi."}
    data = {"root": {"en": "Foundation & world models for SLAM", "vi": "Mô hình nền tảng và mô hình thế giới cho SLAM",
                     "den": f"{len(picked)} papers from the Paper Explorer venues whose titles combine SLAM or mapping with a foundation or world model.",
                     "dvi": f"{len(picked)} bài báo từ các hội nghị và tạp chí của Paper Explorer có tiêu đề kết hợp SLAM hoặc lập bản đồ với mô hình nền tảng hay mô hình thế giới."},
            "facts": facts, "trees": [{"id": "lineage", "en": "Lineage", "vi": "Dòng", "nodes": nodes, "field": "node"}],
            "items": [{k: p[k] for k in ("title", "authors", "year", "venue", "url", "node", "lineage", "id")} for p in picked],
            "chart": "dots", "itemWord": {"en": ["paper", "papers"], "vi": ["bài báo", "bài báo"]}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// SLAM and mapping papers that use foundation or world models; generated by scripts/make_blog_fm_slam.py.\n"
                   "window.FAMILY = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(OUT, len(picked), "papers; by lineage", dict(by_top.most_common()), "; by year", dict(sorted(by_year.items())))
    for k, v in facts.items():
        print(k, "|", v["en"])
    import blog_cover
    blog_cover.tree_cover(nodes, [p for p in picked], "node", OUT.parent / "cover.svg", OUT.parent / "cover-dark.svg")
    blog_cover.png(OUT.parent / "cover.svg", OUT.parent / "cover.png")


if __name__ == "__main__":
    main()
