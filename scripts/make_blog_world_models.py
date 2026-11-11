#!/usr/bin/env python3
"""Data for the blog post "World models and SLAM" (blog/world-models-slam/data.js).

1. A reading map of key papers. Each paper is looked up by its title in the Paper Explorer data (explorer/data, from dblp),
   so title, authors, venue, year and link come from there; three earlier or out-of-venue papers were checked on Crossref.
2. The growth of world-model research: papers with "world model" in the title, per year, in the 14 Paper Explorer venues,
   and how many of them are about 3D or spatial worlds (keywords below).

Run after scripts/make_paper_explorer.py:  python3 scripts/make_blog_world_models.py   (then python3 scripts/build_site.py)
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "explorer" / "data"
OUT = ROOT / "blog" / "world-models-slam" / "data.js"

TREE = [
    ("slam", "Probabilistic SLAM", "SLAM xác suất",
     "SLAM written as inference: a motion model, an observation model and a posterior over the path and the map.",
     "SLAM viết dưới dạng suy luận: mô hình chuyển động, mô hình quan sát và phân phối hậu nghiệm của quỹ đạo và bản đồ.",
     [("s-found", "Foundations", "Nền tảng")]),
    ("latent", "Latent world models", "Mô hình thế giới tiềm ẩn",
     "Learn a compact state, its dynamics and a decoder from pixels, and act by imagining the future in that state.",
     "Học một trạng thái nén, động lực học của nó và bộ giải mã từ điểm ảnh, rồi hành động bằng cách tưởng tượng tương lai trong trạng thái đó.",
     [("l-pixels", "Dynamics from pixels", "Động lực học từ điểm ảnh"), ("l-robot", "World models for robot control", "Mô hình thế giới cho điều khiển robot")]),
    ("video", "Generative world models", "Mô hình thế giới sinh",
     "Predict future images or video conditioned on actions; recent ones add an explicit 3D memory to stay consistent.",
     "Dự đoán ảnh hoặc video tương lai theo hành động; các mô hình gần đây thêm bộ nhớ 3D tường minh để giữ nhất quán.",
     [("v-sim", "Interactive simulators", "Bộ mô phỏng tương tác"), ("v-drive", "Driving video", "Video lái xe"),
      ("v-mem", "Video with 3D memory", "Video có bộ nhớ 3D")]),
    ("occ", "3D occupancy world models", "Mô hình thế giới chiếm chỗ 3D",
     "Forecast how 3D occupancy or point clouds will evolve, mostly for autonomous driving.",
     "Dự báo trạng thái chiếm chỗ 3D hoặc đám mây điểm sẽ thay đổi thế nào, chủ yếu cho lái xe tự hành.",
     [("o-fore", "4D forecasting from sensors", "Dự báo 4D từ cảm biến"), ("o-wm", "Occupancy world models", "Mô hình thế giới chiếm chỗ")]),
    ("geo", "Geometry foundation models", "Mô hình nền tảng hình học",
     "Feed-forward networks that predict 3D structure and cameras from images, now used inside SLAM.",
     "Mạng truyền thẳng dự đoán cấu trúc 3D và camera từ ảnh, nay được dùng ngay trong SLAM.",
     [("g-ff", "Feed-forward 3D", "3D truyền thẳng"), ("g-slam", "SLAM on 3D priors", "SLAM trên tiền nghiệm 3D")]),
    ("mem", "Maps as memory for agents", "Bản đồ làm bộ nhớ cho tác tử",
     "Maps and scene graphs that embodied agents use to explore, reason and plan.",
     "Bản đồ và đồ thị cảnh mà tác tử hiện thân dùng để khám phá, suy luận và lập kế hoạch.",
     [("m-nav", "Learned maps for navigation", "Bản đồ học được cho điều hướng"), ("m-graph", "3D scene graphs & memory", "Đồ thị cảnh 3D và bộ nhớ")]),
]

# (title as in dblp, or its start; branch; short name; description en; description vi)
PAPERS = [
    ("Past, Present, and Future of Simultaneous Localization and Mapping", "s-found", "SLAM: past, present, future",
     "Survey of SLAM and its open problems toward robust perception: long-term operation, dynamic scenes, semantics and new representations.",
     "Tổng quan SLAM và các vấn đề mở hướng tới tri giác bền vững: vận hành dài hạn, cảnh động, ngữ nghĩa và cách biểu diễn mới."),
    ("Recurrent World Models Facilitate Policy Evolution", "l-pixels", "World Models",
     "A VAE compresses frames and a recurrent network predicts the next latent state; a small controller is trained inside the learned model.",
     "Một VAE nén khung hình và một mạng hồi quy dự đoán trạng thái ẩn kế tiếp; một bộ điều khiển nhỏ được huấn luyện ngay trong mô hình đã học."),
    ("Learning Latent Dynamics for Planning from Pixels", "l-pixels", "PlaNet",
     "Learns latent dynamics from pixels with a recurrent state-space model (RSSM) and plans in that latent space.",
     "Học động lực học ẩn từ điểm ảnh bằng mô hình không gian trạng thái hồi quy (RSSM) và lập kế hoạch trong không gian ẩn đó."),
    ("Dream to Control", "l-pixels", "Dreamer",
     "Learns behaviours by backpropagating through trajectories imagined by the world model.",
     "Học hành vi bằng cách lan truyền ngược qua các quỹ đạo do mô hình thế giới tưởng tượng ra."),
    ("Mastering Atari with Discrete World Models", "l-pixels", "DreamerV2",
     "Discrete latent states; the first agent to reach human-level performance on 55 Atari games by learning inside a separately trained world model.",
     "Trạng thái ẩn rời rạc; tác tử đầu tiên đạt mức con người trên 55 trò Atari bằng cách học bên trong một mô hình thế giới huấn luyện riêng."),
    ("DayDreamer", "l-robot", "DayDreamer",
     "Trains Dreamer directly on physical robots, for example a quadruped that learns to walk in about an hour.",
     "Huấn luyện Dreamer trực tiếp trên robot thật, ví dụ robot bốn chân học đi trong khoảng một giờ."),
    ("TD-MPC2", "l-robot", "TD-MPC2",
     "A scalable world model without an observation decoder, used with model-predictive control; one agent for many continuous-control tasks.",
     "Mô hình thế giới có thể mở rộng, không có bộ giải mã quan sát, dùng với điều khiển dự báo; một tác tử cho nhiều tác vụ điều khiển liên tục."),
    ("Genie: Generative Interactive Environments", "v-sim", "Genie",
     "Learns playable 2D environments from unlabeled internet videos, with latent actions inferred without action labels.",
     "Học các môi trường 2D chơi được từ video internet không nhãn, với hành động tiềm ẩn suy ra mà không cần nhãn hành động."),
    ("Learning Interactive Real-World Simulators", "v-sim", "UniSim",
     "Learns an interactive simulator of the real world from diverse video, responding to actions such as language instructions or robot motions.",
     "Học một bộ mô phỏng thế giới thực có tương tác từ video đa dạng, phản hồi theo hành động như chỉ dẫn ngôn ngữ hay chuyển động robot."),
    ("DriveDreamer: Towards Real-World-Drive World Models", "v-drive", "DriveDreamer",
     "A driving world model learned from real driving data that generates controllable future driving video.",
     "Mô hình thế giới lái xe học từ dữ liệu lái thực tế, sinh video lái xe tương lai có thể điều khiển."),
    ("Vista: A Generalizable Driving World Model", "v-drive", "Vista",
     "A driving world model that generalizes across scenes, with high-fidelity prediction and several kinds of action control.",
     "Mô hình thế giới lái xe tổng quát hóa qua nhiều cảnh, dự đoán chân thực và điều khiển được bằng nhiều kiểu hành động."),
    ("ReconDreamer: Crafting World Models for Driving Scene Reconstruction", "v-drive", "ReconDreamer",
     "Uses a driving world model to repair renderings of a reconstructed scene, so that large maneuvers can be rendered.",
     "Dùng mô hình thế giới lái xe để sửa ảnh kết xuất từ cảnh đã tái tạo, nhờ đó kết xuất được cả các thao tác lái lớn."),
    ("WorldMem", "v-mem", "WorldMem",
     "Adds a memory of past frames with their poses and times, so that a generated world stays consistent over long horizons.",
     "Thêm bộ nhớ các khung hình cũ kèm tư thế và thời điểm, để thế giới được sinh ra giữ nhất quán trong thời gian dài."),
    ("VMem", "v-mem", "VMem",
     "Indexes past views by the 3D surfels they saw and retrieves the relevant ones, keeping generated scenes consistent.",
     "Đánh chỉ mục các góc nhìn cũ theo các surfel 3D chúng đã thấy và truy xuất những góc nhìn liên quan, giữ cảnh sinh ra nhất quán."),
    ("Video World Models with Long-term Spatial Memory", "v-mem", "Long-term spatial memory",
     "Gives a video world model a geometry-grounded long-term spatial memory, next to short-term working memory.",
     "Cho mô hình thế giới video một bộ nhớ không gian dài hạn gắn với hình học, bên cạnh bộ nhớ làm việc ngắn hạn."),
    ("Spatia: Video Generation with Updatable Spatial Memory", "v-mem", "Spatia",
     "Generates video while keeping an explicit spatial memory of the scene that is updated as new frames are made.",
     "Sinh video trong khi duy trì một bộ nhớ không gian tường minh của cảnh, được cập nhật khi có khung hình mới."),
    ("WorldStereo", "v-mem", "WorldStereo",
     "Couples camera-guided video generation with scene reconstruction through 3D geometric memories.",
     "Gắn sinh video theo camera với tái tạo cảnh thông qua các bộ nhớ hình học 3D."),
    ("Point Cloud Forecasting as a Proxy for 4D Occupancy Forecasting", "o-fore", "4D occupancy forecasting",
     "Forecasts future LiDAR point clouds through a 4D occupancy representation, learned from unlabeled sensor sequences.",
     "Dự báo đám mây điểm LiDAR tương lai thông qua biểu diễn chiếm chỗ 4D, học từ chuỗi cảm biến không nhãn."),
    ("Copilot4D", "o-fore", "Copilot4D",
     "An unsupervised world model for driving that tokenizes LiDAR observations and predicts the future with discrete diffusion.",
     "Mô hình thế giới không giám sát cho lái xe: mã hóa quan sát LiDAR thành token và dự đoán tương lai bằng khuếch tán rời rạc."),
    ("UnO: Unsupervised Occupancy Fields", "o-fore", "UnO",
     "Learns a continuous 4D occupancy field from unlabeled LiDAR and uses it for both perception and forecasting.",
     "Học một trường chiếm chỗ 4D liên tục từ LiDAR không nhãn và dùng nó cho cả tri giác lẫn dự báo."),
    ("OccWorld", "o-wm", "OccWorld",
     "A world model in 3D semantic-occupancy space that predicts how the scene and the ego vehicle will move.",
     "Mô hình thế giới trong không gian chiếm chỗ ngữ nghĩa 3D, dự đoán cảnh và xe tự hành sẽ di chuyển thế nào."),
    ("GaussianWorld", "o-wm", "GaussianWorld",
     "Turns 3D occupancy prediction into forecasting with Gaussians that move with the ego vehicle and the objects, and fill newly seen areas.",
     "Biến dự đoán chiếm chỗ 3D thành dự báo với các Gaussian dịch chuyển theo xe và vật thể, đồng thời lấp các vùng mới thấy."),
    ("SparseWorld-TC", "o-wm", "SparseWorld-TC",
     "A world model that forecasts sparse occupancy conditioned on the planned ego trajectory.",
     "Mô hình thế giới dự báo trạng thái chiếm chỗ thưa theo quỹ đạo dự kiến của xe."),
    ("Vision-Centric 4D Occupancy Forecasting and Planning", "o-wm", "Implicit residual world model",
     "Forecasts 4D occupancy from cameras with an implicit residual world model and plans with it.",
     "Dự báo trạng thái chiếm chỗ 4D từ camera bằng một mô hình thế giới phần dư ngầm định và dùng nó để lập kế hoạch."),
    ("DUSt3R", "g-ff", "DUSt3R",
     "Predicts pointmaps of two images in one frame without known cameras; poses and intrinsics can be recovered from them.",
     "Dự đoán pointmap của hai ảnh trong cùng hệ tọa độ mà không cần biết camera; tư thế và thông số nội có thể suy ra từ đó."),
    ("Grounding Image Matching in 3D with MASt3R", "g-ff", "MASt3R",
     "Extends DUSt3R with dense local features, grounding 2D matching in 3D.",
     "Mở rộng DUSt3R với đặc trưng cục bộ dày đặc, gắn việc so khớp 2D với hình học 3D."),
    ("VGGT: Visual Geometry Grounded Transformer", "g-ff", "VGGT",
     "A feed-forward transformer that predicts cameras, depth maps, pointmaps and point tracks from one to hundreds of views.",
     "Transformer truyền thẳng dự đoán camera, bản đồ độ sâu, pointmap và vết điểm từ một đến hàng trăm góc nhìn."),
    ("MASt3R-SLAM", "g-slam", "MASt3R-SLAM",
     "Dense real-time SLAM built on MASt3R's two-view 3D reconstruction priors.",
     "SLAM dày đặc thời gian thực xây dựng trên tiền nghiệm tái tạo 3D hai góc nhìn của MASt3R."),
    ("VGGT-SLAM", "g-slam", "VGGT-SLAM",
     "Dense RGB SLAM that aligns VGGT reconstructions of sub-maps by optimizing on the SL(4) manifold.",
     "SLAM RGB dày đặc ghép các tái tạo VGGT của từng bản đồ con bằng tối ưu trên đa tạp SL(4)."),
    ("Learning To Explore Using Active Neural SLAM", "m-nav", "Active Neural SLAM",
     "Modular exploration: a learned neural SLAM module builds a top-down map that global and local policies use.",
     "Khám phá theo mô-đun: một mô-đun SLAM nơ-ron học được xây bản đồ nhìn từ trên xuống cho các chính sách toàn cục và cục bộ."),
    ("Neural Topological SLAM for Visual Navigation", "m-nav", "Neural Topological SLAM",
     "Builds a topological map of image nodes and navigates to image goals with learned semantic predictions.",
     "Xây bản đồ tô-pô gồm các nút ảnh và điều hướng tới mục tiêu dạng ảnh nhờ dự đoán ngữ nghĩa học được."),
    ("Hydra: A Real-time Spatial Perception System", "m-graph", "Hydra",
     "Builds and optimizes a layered 3D scene graph of objects, places and rooms in real time.",
     "Xây dựng và tối ưu đồ thị cảnh 3D nhiều tầng gồm vật thể, địa điểm và phòng theo thời gian thực."),
    ("ConceptGraphs", "m-graph", "ConceptGraphs",
     "Open-vocabulary 3D scene graphs from foundation-model features, which language models can use for planning.",
     "Đồ thị cảnh 3D từ vựng mở từ đặc trưng của mô hình nền tảng, mà mô hình ngôn ngữ có thể dùng để lập kế hoạch."),
    ("3D-Mem", "m-graph", "3D-Mem",
     "A compact 3D scene memory of informative snapshots that a vision-language model uses to explore and reason.",
     "Bộ nhớ cảnh 3D gọn gồm các ảnh chụp giàu thông tin, được mô hình thị giác-ngôn ngữ dùng để khám phá và suy luận."),
]
# papers outside the Explorer venues or years, checked on Crossref
MANUAL = [
    {"name": "SLAM tutorial, part I", "year": 2006, "node": "s-found", "authors": "Hugh Durrant-Whyte, Tim Bailey", "venue": "IEEE RAM 2006",
     "title": "Simultaneous localization and mapping: part I", "url": "https://doi.org/10.1109/MRA.2006.1638022",
     "den": "Tutorial that writes SLAM as a probabilistic problem: a motion model, an observation model and the joint posterior over path and map.",
     "dvi": "Bài hướng dẫn viết SLAM thành bài toán xác suất: mô hình chuyển động, mô hình quan sát và hậu nghiệm đồng thời của quỹ đạo và bản đồ."},
    {"name": "iSAM2", "year": 2012, "node": "s-found", "authors": "Michael Kaess, Hordur Johannsson, Richard Roberts, Viorela Ila, John J. Leonard, Frank Dellaert",
     "venue": "IJRR 2012", "title": "iSAM2: Incremental smoothing and mapping using the Bayes tree", "url": "https://doi.org/10.1177/0278364911430419",
     "den": "Incremental smoothing on the Bayes tree: updates the factor-graph solution as measurements arrive, re-solving only what changed.",
     "dvi": "Làm mịn tăng dần trên cây Bayes: cập nhật lời giải đồ thị nhân tử khi có phép đo mới, chỉ giải lại phần thay đổi."},
    {"name": "DreamerV3", "year": 2025, "node": "l-pixels", "authors": "Danijar Hafner, Jurgis Pasukonis, Jimmy Ba, Timothy Lillicrap", "venue": "Nature 2025",
     "title": "Mastering diverse control tasks through world models", "url": "https://doi.org/10.1038/s41586-025-08744-2",
     "den": "One configuration that works across many domains without tuning, including collecting diamonds in Minecraft from scratch.",
     "dvi": "Một cấu hình duy nhất dùng được cho nhiều miền mà không cần tinh chỉnh, kể cả tự thu thập kim cương trong Minecraft từ đầu."},
]

WORLD = re.compile(r"(?i)\bworld[- ]models?\b")
SPATIAL = re.compile(r"(?i)\b(3d|4d|occupancy|scene|map|mapping|slam|gaussian|point cloud|spatial|memory|reconstruction|geometr|lidar|bev|navigation|driving)")


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
    # 1. reading map
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
        assert it["node"] in top, it["name"]
        it["lineage"] = top[it["node"]]
        it["cite"] = f'{it["authors"]}. {it["title"]}. {it["venue"]}.'
    items.sort(key=lambda x: (x["year"], x["name"].lower()))
    for i, it in enumerate(items):
        it["id"] = i
    # 2. growth of world-model papers
    y0, y1 = index["years"]
    count, spatial, total, field = Counter(), Counter(), Counter(), Counter()
    for vid, d in files.items():
        for t, y in zip(d["t"], d["y"]):
            total[y] += 1
            if WORLD.search(t):
                count[y] += 1
                field[(y, venue[vid]["field"])] += 1
                spatial[y] += bool(SPATIAL.search(t))
    years = list(range(y0, y1 + 1))
    trend = {"years": years, "spatial": [spatial[y] for y in years], "other": [count[y] - spatial[y] for y in years],
             "rate": [round(1e4 * count[y] / total[y], 1) if total[y] else 0 for y in years],
             "rob": [field[(y, "rob")] for y in years], "cv": [field[(y, "cv")] for y in years], "ml": [field[(y, "ml")] for y in years],
             "partial": [v["short"] for v in index["venues"] if not v["years"].get(str(y1)) and v["id"] not in ("iccv", "eccv")]}  # ICCV, ECCV: every other year
    a, b = 2020, y1 - 1
    share = lambda y: round(100 * spatial[y] / count[y]) if count[y] else 0
    fe = lambda n: f"{n:,}"
    facts = {
        "growth": {"en": f"Papers with “world model” in the title went from **{count[a]}** in {a} to **{count[b]}** in {b}, across the {len(files)} Paper Explorer venues.",
                   "vi": f"Số bài có “world model” trong tiêu đề tăng từ **{count[a]}** năm {a} lên **{count[b]}** năm {b}, trên {len(files)} hội nghị và tạp chí của Paper Explorer."},
        "rate": {"en": f"Relative to all papers, that is **{trend['rate'][years.index(a)]}** per 10,000 in {a} and **{trend['rate'][years.index(b)]}** per 10,000 in {b}, about {round(trend['rate'][years.index(b)] / trend['rate'][years.index(a)])} times more.",
                 "vi": f"So với tổng số bài, đó là **{str(trend['rate'][years.index(a)]).replace('.', ',')}** trên 10.000 bài năm {a} và **{str(trend['rate'][years.index(b)]).replace('.', ',')}** trên 10.000 bài năm {b}, gấp khoảng {round(trend['rate'][years.index(b)] / trend['rate'][years.index(a)])} lần."},
        "spatial": {"en": f"The 3D and spatial share rose from **{share(2023)}%** in 2023 to **{share(b)}%** in {b}: occupancy, scenes, maps, memory and driving.",
                    "vi": f"Tỷ lệ về 3D và không gian tăng từ **{share(2023)}%** năm 2023 lên **{share(b)}%** năm {b}: chiếm chỗ, cảnh, bản đồ, bộ nhớ và lái xe."},
    }
    data = {"root": {"en": "World models and SLAM", "vi": "Mô hình thế giới và SLAM",
                     "den": f"{len(items)} papers that connect world models with SLAM, mapping and spatial memory.",
                     "dvi": f"{len(items)} bài báo kết nối mô hình thế giới với SLAM, lập bản đồ và bộ nhớ không gian."},
            "facts": facts, "trees": [{"id": "lineage", "en": "Lineage", "vi": "Dòng", "nodes": nodes, "field": "node"}],
            "items": items, "chart": "dots", "itemWord": {"en": ["paper", "papers"], "vi": ["bài báo", "bài báo"]}, "trend": trend}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// World models and SLAM: reading map and growth of world-model papers; generated by scripts/make_blog_world_models.py.\n"
                   "window.FAMILY = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(OUT, len(items), "papers;", dict(Counter(it["lineage"] for it in items)))
    for y in years:
        print(y, count[y], "spatial", spatial[y], "per10k", trend["rate"][years.index(y)])
    print("not indexed for", y1, ":", trend["partial"])
    for k, v in facts.items():
        print(k, "|", v["en"])
    import blog_cover
    blog_cover.tree_cover(nodes, items, "node", OUT.parent / "cover.svg", OUT.parent / "cover-dark.svg")
    blog_cover.png(OUT.parent / "cover.svg", OUT.parent / "cover.png")


if __name__ == "__main__":
    main()
