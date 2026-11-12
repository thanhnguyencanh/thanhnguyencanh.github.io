#!/usr/bin/env python3
"""Data and figures for the blog post "Robot learning, explained" (blog/robot-learning-explained/).

data.js holds a reading map of key papers and the title-keyword trends. Papers in the Paper Explorer venues are looked up by
title there (dblp), so title, authors, venue, year and link come from it; arXiv-only and AISTATS papers were checked on arXiv
and PMLR, and one dblp author list was corrected from Crossref. The trends count titles in ICRA, RA-L, T-RO, IJRR and
Science Robotics, the robotics venues that dblp covers up to 2026.

The static figures are drawn as inline SVG into data/blog/robot-learning-explained.html, between <!--fig:NAME--> markers,
with the SVG helpers of make_blog_ba.py.

Run after scripts/make_paper_explorer.py:  python3 scripts/make_blog_robot_learning_explained.py   (then build_site.py)
Only the figures:                          python3 scripts/make_blog_robot_learning_explained.py --figures
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_blog_ba import _bi, _head, _line, _m, _path, _rect, _svg, _text  # noqa: E402  (shared SVG helpers)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "explorer" / "data"
OUT = ROOT / "blog" / "robot-learning-explained" / "data.js"
BODY = ROOT / "data" / "blog" / "robot-learning-explained.html"

TREE = [
    ("rl", "Reinforcement learning", "Học tăng cường", "Algorithms that learn a policy from reward.", "Các thuật toán học chính sách từ phần thưởng.",
     [("r-pg", "Policy gradients and trust regions", "Gradient chính sách và vùng tin cậy"), ("r-off", "Off-policy actor-critic", "Actor-critic ngoài chính sách"),
      ("r-wm", "World models", "Mô hình thế giới")]),
    ("sim", "Simulation to reality", "Từ mô phỏng đến thực tế", "Training in simulation and making the policy work on the real robot.",
     "Huấn luyện trong mô phỏng và làm cho chính sách chạy được trên robot thật.",
     [("s-dr", "Domain randomization", "Ngẫu nhiên hóa miền"), ("s-skill", "Skills learned in simulation", "Kỹ năng học trong mô phỏng")]),
    ("ts", "Teacher–student distillation", "Chưng cất thầy–trò", "A teacher with privileged information trains a student that uses only onboard sensors.",
     "Một người thầy có thông tin đặc quyền huấn luyện người trò chỉ dùng cảm biến trên robot.",
     [("t-priv", "Privileged teachers", "Thầy có thông tin đặc quyền"), ("t-adapt", "Adaptation from history", "Thích nghi từ lịch sử"),
      ("t-agile", "Agile skills from vision", "Kỹ năng linh hoạt từ thị giác")]),
    ("il", "Imitation learning", "Học bắt chước", "Learning from demonstrations.", "Học từ các lần trình diễn.",
     [("i-inter", "Interactive imitation", "Bắt chước tương tác"), ("i-expr", "Expressive policies", "Chính sách giàu biểu đạt"),
      ("i-human", "Learning from humans", "Học từ con người")]),
    ("gen", "Generalist policies", "Chính sách tổng quát", "Large models trained on data from many robots and tasks.", "Các mô hình lớn huấn luyện trên dữ liệu từ nhiều robot và nhiệm vụ.",
     [("g-vla", "Vision-language-action models", "Mô hình thị giác-ngôn ngữ-hành động"), ("g-data", "Cross-embodiment data", "Dữ liệu đa thân thể")]),
]

# (leaf, short name, explorer title prefix, description en, description vi)
PAPERS = [
    ("r-pg", "TRPO", "Trust Region Policy Optimization",
     "Policy updates constrained to a trust region in KL divergence, so each step improves the policy reliably.",
     "Cập nhật chính sách bị giới hạn trong một vùng tin cậy theo độ phân kỳ KL, để mỗi bước cải thiện chính sách một cách tin cậy."),
    ("r-off", "SAC", "Soft Actor-Critic: Off-Policy Maximum Entropy",
     "Off-policy actor-critic that maximizes reward plus the policy's entropy and reuses past experience for sample efficiency.",
     "Actor-critic ngoài chính sách, tối đa hóa phần thưởng cộng entropy của chính sách và dùng lại kinh nghiệm cũ để tiết kiệm mẫu."),
    ("r-off", "TD3", "Addressing Function Approximation Error in Actor-Critic",
     "Twin critics, delayed policy updates and target smoothing against overestimation in deterministic actor-critic methods.",
     "Hai critic, cập nhật chính sách trễ và làm trơn mục tiêu để chống ước lượng quá cao trong actor-critic tất định."),
    ("r-wm", "Dreamer", "Dream to Control",
     "Learns a latent world model from pixels and trains the policy on rollouts imagined in that model.",
     "Học một mô hình thế giới tiềm ẩn từ điểm ảnh và huấn luyện chính sách trên các lượt chạy tưởng tượng trong mô hình đó."),
    ("r-wm", "DayDreamer", "DayDreamer: World Models for Physical Robot Learning",
     "Dreamer's world models trained directly on physical robots, without a simulator.",
     "Mô hình thế giới của Dreamer được huấn luyện trực tiếp trên robot thật, không cần trình mô phỏng."),
    ("s-dr", "Domain randomization", "Domain randomization for transferring deep neural networks",
     "Randomizes textures, lighting and cameras in simulation so a network trained only on rendered images works on real ones.",
     "Ngẫu nhiên hóa kết cấu, ánh sáng và camera trong mô phỏng để mạng chỉ học từ ảnh kết xuất vẫn chạy được trên ảnh thật."),
    ("s-dr", "Dynamics randomization", "Sim-to-Real Transfer of Robotic Control with Dynamics Randomization",
     "Randomizes physical parameters such as masses, friction and latency so a policy trained in simulation transfers to a real arm.",
     "Ngẫu nhiên hóa các tham số vật lý như khối lượng, ma sát và độ trễ để chính sách học trong mô phỏng chuyển được sang cánh tay thật."),
    ("s-skill", "ANYmal skills", "Learning agile and dynamic motor skills for legged robots",
     "Trains ANYmal's locomotion in simulation with a learned model of its actuators, and transfers it to the real robot.",
     "Huấn luyện khả năng di chuyển của ANYmal trong mô phỏng với một mô hình học được của bộ truyền động, rồi chuyển sang robot thật."),
    ("s-skill", "Dexterous hand", "Learning dexterous in-hand manipulation",
     "In-hand reorientation of a block with a Shadow hand, learned entirely in heavily randomized simulation.",
     "Xoay khối vật trong bàn tay Shadow, học hoàn toàn trong mô phỏng được ngẫu nhiên hóa mạnh."),
    ("s-skill", "Walking in minutes", "Learning to Walk in Minutes Using Massively Parallel",
     "Thousands of simulated robots on one GPU train a walking policy in under four minutes on flat ground and twenty on rough terrain.",
     "Hàng nghìn robot mô phỏng trên một GPU huấn luyện chính sách đi bộ trong chưa đến bốn phút trên nền phẳng và hai mươi phút trên địa hình gồ ghề."),
    ("s-skill", "DeXtreme", "DeXtreme: Transfer of Agile In-hand Manipulation",
     "Agile in-hand manipulation learned in simulation and transferred to a real robot hand.",
     "Thao tác linh hoạt trong lòng bàn tay, học trong mô phỏng và chuyển sang bàn tay robot thật."),
    ("t-priv", "Learning by Cheating", "Learning by Cheating",
     "A privileged driving agent that sees the ground-truth layout and all traffic participants teaches a purely vision-based student.",
     "Một tác tử lái xe có thông tin đặc quyền, thấy bố cục thật và mọi phương tiện, dạy một người trò chỉ dùng thị giác."),
    ("t-priv", "Proprioceptive ANYmal", "Learning quadrupedal locomotion over challenging terrain",
     "A teacher with privileged terrain information supervises a proprioceptive student (a temporal convolutional network) trained with DAgger.",
     "Một người thầy có thông tin đặc quyền về địa hình giám sát người trò chỉ dùng cảm biến bản thể (mạng tích chập thời gian), huấn luyện bằng DAgger."),
    ("t-priv", "Perceptive ANYmal", "Learning robust perceptive locomotion",
     "A student with a belief encoder fuses proprioception and noisy terrain heights, imitating a teacher trained with PPO on privileged state.",
     "Người trò có bộ mã hóa niềm tin, hợp nhất cảm biến bản thể với độ cao địa hình bị nhiễu, bắt chước người thầy được huấn luyện bằng PPO trên trạng thái đặc quyền."),
    ("t-priv", "Visual dexterity", "Visual dexterity",
     "A teacher trained with RL on privileged state teaches a student that reorients new objects from a single depth camera.",
     "Người thầy được huấn luyện bằng RL trên trạng thái đặc quyền dạy người trò xoay các vật mới chỉ từ một camera độ sâu."),
    ("t-adapt", "RMA", "RMA: Rapid Motor Adaptation for Legged Robots",
     "The teacher encodes environment parameters into a latent z; an adaptation module estimates z from the last 0.5 s of states and actions.",
     "Người thầy mã hóa các tham số môi trường thành biến tiềm ẩn z; một mô-đun thích nghi ước lượng z từ 0,5 giây trạng thái và hành động gần nhất."),
    ("t-adapt", "In-hand RMA", "In-Hand Object Rotation via Rapid Motor Adaptation",
     "The adaptation idea of RMA applied to rotating objects in a multi-fingered hand.",
     "Ý tưởng thích nghi của RMA áp dụng cho việc xoay vật trong bàn tay nhiều ngón."),
    ("t-agile", "Robot parkour", "Robot Parkour Learning",
     "Parkour skills learned with privileged physics information, then distilled into one vision-based policy for low-cost quadrupeds.",
     "Các kỹ năng parkour học với thông tin vật lý đặc quyền, rồi được chưng cất thành một chính sách thị giác duy nhất cho robot bốn chân giá rẻ."),
    ("t-agile", "Extreme parkour", "Extreme Parkour with Legged Robots",
     "A teacher trained on scandots (privileged terrain points) is distilled with DAgger into a student that sees one front depth camera.",
     "Người thầy học trên scandots (các điểm địa hình đặc quyền) được chưng cất bằng DAgger thành người trò chỉ thấy một camera độ sâu phía trước."),
    ("i-expr", "Implicit BC", "Implicit Behavioral Cloning",
     "Energy-based policies that represent multimodal and discontinuous actions better than explicit regression.",
     "Chính sách dựa trên năng lượng, biểu diễn hành động đa mode và gián đoạn tốt hơn hồi quy tường minh."),
    ("i-expr", "ACT", "Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware",
     "Action chunking with transformers: predicts sequences of future actions, which limits compounding errors, on low-cost bimanual arms.",
     "Action chunking với transformer: dự đoán chuỗi hành động tương lai, giúp hạn chế sai số tích lũy, trên hai cánh tay giá rẻ."),
    ("i-expr", "Diffusion Policy", "Diffusion Policy: Visuomotor Policy Learning via Action Diffusion",
     "Denoises action sequences with a diffusion model conditioned on observations, handling multimodal demonstrations.",
     "Khử nhiễu chuỗi hành động bằng mô hình khuếch tán có điều kiện theo quan sát, xử lý được trình diễn đa mode."),
    ("i-human", "HumanPlus", "HumanPlus: Humanoid Shadowing and Imitation from Humans",
     "A humanoid shadows a person from one RGB camera with an RL policy trained on 40 hours of human motion, then learns skills by behavior cloning.",
     "Robot hình người bắt chước tư thế một người qua một camera RGB nhờ chính sách RL học từ 40 giờ chuyển động người, rồi học kỹ năng bằng behavior cloning."),
    ("g-vla", "RT-1", "RT-1: Robotics Transformer for Real-World Control at Scale",
     "A transformer policy trained on a large real-robot dataset that maps images and language instructions to actions.",
     "Chính sách transformer huấn luyện trên bộ dữ liệu robot thật lớn, ánh xạ ảnh và câu lệnh ngôn ngữ thành hành động."),
    ("g-vla", "RT-2", "RT-2: Vision-Language-Action Models Transfer",
     "Co-fine-tunes a vision-language model on robot data by writing actions as text tokens: the paper that named VLA models.",
     "Đồng tinh chỉnh một mô hình thị giác-ngôn ngữ trên dữ liệu robot bằng cách viết hành động thành token văn bản: bài báo đặt tên cho mô hình VLA."),
    ("g-vla", "OpenVLA", "OpenVLA: An Open-Source Vision-Language-Action Model",
     "An open 7B VLA built on Llama 2 with DINOv2 and SigLIP features, trained on 970k real robot demonstrations.",
     "Một VLA mở 7 tỉ tham số dựa trên Llama 2 với đặc trưng DINOv2 và SigLIP, huấn luyện trên 970 nghìn lần trình diễn trên robot thật."),
    ("g-data", "Open X-Embodiment", "Open X-Embodiment: Robotic Learning Datasets",
     "Data from 22 robots and 21 institutions in one format, with RT-X models that show positive transfer across robots.",
     "Dữ liệu từ 22 robot và 21 tổ chức trong cùng một định dạng, cùng các mô hình RT-X cho thấy chuyển giao tích cực giữa các robot."),
    ("g-data", "DROID", "DROID: A Large-Scale In-The-Wild Robot Manipulation Dataset",
     "A large-scale manipulation dataset collected in many real-world scenes.",
     "Bộ dữ liệu thao tác quy mô lớn thu trong nhiều cảnh thật."),
    ("g-data", "Octo", "Octo: An Open-Source Generalist Robot Policy",
     "An open transformer policy trained on 800k Open X-Embodiment trajectories, fine-tunable to new sensors and action spaces in hours.",
     "Chính sách transformer mở, huấn luyện trên 800 nghìn quỹ đạo của Open X-Embodiment, tinh chỉnh được cho cảm biến và không gian hành động mới trong vài giờ."),
]
# checked on arXiv (ids), PMLR or Crossref
MANUAL = [
    ("r-pg", "GAE", {"year": 2015, "venue": "arXiv 2015", "title": "High-Dimensional Continuous Control Using Generalized Advantage Estimation",
                     "authors": "John Schulman, Philipp Moritz, Sergey Levine, Michael Jordan, Pieter Abbeel", "url": "https://arxiv.org/abs/1506.02438"},
     "Generalized advantage estimation: an exponentially weighted sum of TD errors that trades bias against variance through λ.",
     "Ước lượng lợi thế tổng quát: tổng có trọng số mũ của các sai số TD, cân bằng độ chệch và phương sai qua λ."),
    ("r-pg", "PPO", {"year": 2017, "venue": "arXiv 2017", "title": "Proximal Policy Optimization Algorithms",
                     "authors": "John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, Oleg Klimov", "url": "https://arxiv.org/abs/1707.06347"},
     "A clipped surrogate objective that keeps the new policy near the old one with first-order updates; widely used to train locomotion and dexterity in simulation.",
     "Hàm mục tiêu thay thế có cắt ngưỡng, giữ chính sách mới gần chính sách cũ chỉ với cập nhật bậc nhất; được dùng rộng rãi để huấn luyện di chuyển và thao tác khéo léo trong mô phỏng."),
    ("i-inter", "DAgger", {"year": 2011, "venue": "AISTATS 2011", "title": "A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning",
                           "authors": "Stephane Ross, Geoffrey J. Gordon, J. Andrew Bagnell", "url": "https://proceedings.mlr.press/v15/ross11a.html"},
     "Dataset aggregation: run the learner, let the expert label the states it visits, retrain on all data; the error grows linearly with the horizon instead of quadratically.",
     "Gộp dữ liệu: chạy người học, để chuyên gia gán nhãn cho các trạng thái nó đi qua, rồi huấn luyện lại trên toàn bộ dữ liệu; sai số tăng tuyến tính theo độ dài thay vì bậc hai."),
    ("g-vla", "π0", {"year": 2025, "venue": "RSS 2025", "title": "π0: A Vision-Language-Action Flow Model for General Robot Control",
                     "authors": "Kevin Black, Noah Brown, Danny Driess, Adnan Esmail, Michael Equi, Chelsea Finn, Niccolo Fusai, Lachy Groom, +16",
                     "url": "https://arxiv.org/abs/2410.24164"},
     "A VLM backbone with a flow-matching action expert that outputs chunks of 50 actions, at up to 50 Hz for dexterous tasks such as folding laundry.",
     "Một mô hình VLM với bộ phận hành động dùng flow matching, xuất ra từng khối 50 hành động, tới 50 Hz cho các việc khéo léo như gấp quần áo."),
]
AUTHORS_FIX = {"Learning agile and dynamic motor skills for legged robots":  # dblp's record lacks the first author; Crossref has all seven
               "Jemin Hwangbo, Joonho Lee, Alexey Dosovitskiy, Dario Bellicoso, Vassilios Tsounis, Vladlen Koltun, Marco Hutter"}

TREND_VENUES = ["icra", "ral", "tro", "ijrr", "scirob"]
TOPICS = [
    ("rl", "Reinforcement learning", "Học tăng cường", r"reinforcement learning|\bdeep rl\b|\brl\b|actor-critic|policy gradient|policy optimization|q-learning"),
    ("il", "Imitation learning", "Học bắt chước", r"imitation learning|behavio(u)?r(al)? cloning|learning from demonstrations?|from human demonstrations?|\bimitation\b"),
    ("s2r", "Sim-to-real", "Từ mô phỏng đến thực tế", r"sim-to-real|sim2real|simulation-to-real|sim-and-real|domain randomi[sz]ation|real-to-sim"),
    ("ts", "Teacher–student, privileged, distillation", "Thầy–trò, đặc quyền, chưng cất", r"teacher-student|teacher–student|student-teacher|privileged|distill"),
    ("diff", "Diffusion and flow matching", "Khuếch tán và flow matching", r"diffusion|flow matching|flow policy"),
    ("vla", "Language and foundation models", "Mô hình ngôn ngữ và nền tảng",
     r"vision-language-action|\bvlas?\b|foundation models?|large language models?|\bllms?\b|vision-language models?|\bvlms?\b|language models?"),
]


def expand(link, codes):
    if link.startswith("10."):
        return "https://doi.org/" + link
    for c, t in codes:
        link = link.replace(c, t)
    return link


def trend(files, venue):
    years = list(range(2015, 2027))
    total, hits = Counter(), defaultdict(Counter)
    for vid in TREND_VENUES:
        d = files[vid]
        for t, y in zip(d["t"], d["y"]):
            if y not in years:
                continue
            total[y] += 1
            for tid, _, _, pat in TOPICS:
                if re.search(pat, t.lower()):
                    hits[tid][y] += 1
    return {"years": years, "venues": [venue[v]["short"] for v in TREND_VENUES], "total": [total[y] for y in years],
            "topics": [{"id": tid, "en": en, "vi": vi, "count": [hits[tid][y] for y in years],
                        "rate": [round(1000 * hits[tid][y] / total[y], 1) for y in years]} for tid, en, vi, _ in TOPICS]}


def main():
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    files = {v["id"]: json.loads((DATA / f'{v["id"]}.json').read_text(encoding="utf-8")) for v in index["venues"]}
    venue = {v["id"]: v for v in index["venues"]}
    nodes, top = [], {}
    for tid, en, vi, den, dvi, leaves in TREE:
        nodes.append({"id": tid, "parent": None, "en": en, "vi": vi, "den": den, "dvi": dvi})
        for lid, len_, lvi in leaves:
            nodes.append({"id": lid, "parent": tid, "en": len_, "vi": lvi})
            top[lid] = tid
    items = []
    for leaf, name, prefix, den, dvi in PAPERS:
        hits = {d["l"][i]: (vid, i) for vid, d in files.items() for i, t in enumerate(d["t"]) if t.lower().startswith(prefix.lower())}
        exact = {k: v for k, v in hits.items() if files[v[0]]["t"][v[1]].lower() == prefix.lower()}
        hits = exact or hits  # an exact title wins over longer titles that start the same way
        if len(hits) > 1 and len({files[v]["t"][i].lower() for v, i in hits.values()}) == 1:  # a journal version of the same paper:
            first = min(hits.values(), key=lambda h: files[h[0]]["y"][h[1]])                      # cite the original
            hits = {k: v for k, v in hits.items() if v == first}
        assert len(hits) == 1, (name, hits)
        vid, i = next(iter(hits.values()))
        d = files[vid]
        items.append({"name": name, "node": leaf, "year": d["y"][i], "venue": f'{venue[vid]["short"]} {d["y"][i]}', "title": d["t"][i],
                      "authors": AUTHORS_FIX.get(d["t"][i], d["a"][i]), "url": expand(d["l"][i], index["codes"]), "den": den, "dvi": dvi})
    for leaf, name, meta, den, dvi in MANUAL:
        items.append({"name": name, "node": leaf, **meta, "den": den, "dvi": dvi})
    for it in items:
        assert it["node"] in top, it["name"]
        it["lineage"] = top[it["node"]]
        it["cite"] = f'{it["authors"]}. {it["title"]}. {it["venue"]}.'
    items.sort(key=lambda x: (x["year"], x["name"].lower()))
    for i, it in enumerate(items):
        it["id"] = i
    data = {"root": {"en": "Robot learning", "vi": "Học robot",
                     "den": f"{len(items)} key papers, from reinforcement learning and sim-to-real transfer to teacher–student distillation and generalist policies.",
                     "dvi": f"{len(items)} bài báo chính, từ học tăng cường và chuyển từ mô phỏng sang thực tế đến chưng cất thầy–trò và chính sách tổng quát."},
            "trees": [{"id": "lineage", "en": "Lineage", "vi": "Dòng", "nodes": nodes, "field": "node"}],
            "items": items, "chart": "dots", "itemWord": {"en": ["paper", "papers"], "vi": ["bài báo", "bài báo"]}, "trend": trend(files, venue)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// Robot learning, explained: reading map and title trends; generated by scripts/make_blog_robot_learning_explained.py.\n"
                   "window.FAMILY = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(OUT, len(items), "papers;", dict(Counter(it["lineage"] for it in items)), items[0]["year"], "-", items[-1]["year"])
    for t in data["trend"]["topics"]:
        print(f'  {t["id"]:5}', " ".join(f"{r:5.1f}" for r in t["rate"]))
    import blog_cover
    blog_cover.tree_cover(nodes, items, "node", OUT.parent / "cover.svg", OUT.parent / "cover-dark.svg")
    blog_cover.png(OUT.parent / "cover.svg", OUT.parent / "cover.png")


# ---------- static figures ----------
def _box(x, y, w, h, cls="node"):
    return f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"></rect>'


def _arrow(a, b, cls="arrow"):
    return _line(a, b, cls) + _head(b, a, cls + "-h")


def fig_loop():
    """The reinforcement-learning loop: the policy acts, the environment returns the next state and a reward."""
    s = _box(40, 55, 210, 96) + _box(390, 55, 210, 96)
    s += _bi(145, 86, "Policy", "Chính sách", "lab big", "middle") + _text(145, 114, _m("π_θ(a | s)"), "m", "middle")
    s += _bi(145, 138, "the robot's controller", "bộ điều khiển của robot", "", "middle")
    s += _bi(495, 86, "Environment", "Môi trường", "lab big", "middle") + _bi(495, 112, "simulator or real world", "trình mô phỏng hoặc thế giới thật", "", "middle")
    s += _bi(495, 134, "with a reward function", "với một hàm phần thưởng", "", "middle")
    s += _arrow((250, 78), (388, 78)) + _arrow((390, 128), (252, 128))
    s += _text(319, 68, _m("action a_t"), "m small", "middle") + _text(319, 150, _m("state s_{t+1}, reward r_t"), "m small", "middle")
    s += f'<path class="loopback" d="M110 55 C 110 18, 180 18, 180 53"></path>' + _head((180, 53), (180, 30), "arrow-h")
    s += _bi(145, 15, "update θ to raise the return", "cập nhật θ để tăng tổng phần thưởng", "", "middle")
    return _svg(640, 170, "The reinforcement-learning loop", "Vòng lặp học tăng cường", s)


def fig_teacher():
    """Teacher-student distillation in three phases."""
    cols = [(14, "1. Teacher, in simulation", "1. Thầy, trong mô phỏng"), (252, "2. Student, in simulation", "2. Trò, trong mô phỏng"),
            (490, "3. Student, on the robot", "3. Trò, trên robot")]
    s = ""
    for x, en, vi in cols:
        s += _rect(x, 8, 216, 210, "panel") + _bi(x + 108, 30, en, vi, "lab", "middle")
    # teacher
    s += _box(34, 92, 176, 48) + _text(122, 122, _m("π_T(a | o_t, x_t^{priv})"), "m", "middle")
    s += _bi(122, 56, "privileged state:", "trạng thái đặc quyền:", "", "middle") + _bi(122, 72, "terrain, friction, contacts, object pose", "địa hình, ma sát, tiếp xúc, tư thế vật", "small", "middle")
    s += _arrow((122, 78), (122, 90))
    s += _bi(122, 176, "trained by RL (e.g. PPO)", "huấn luyện bằng RL (ví dụ PPO)", "", "middle") + _bi(122, 194, "on a reward", "theo một hàm phần thưởng", "", "middle")
    s += _arrow((122, 160), (122, 142))
    # student in simulation
    s += _box(272, 92, 176, 48) + _text(360, 122, _m("π_S(a | o_{t−H:t})"), "m", "middle")
    s += _bi(360, 56, "onboard sensors only:", "chỉ cảm biến trên robot:", "", "middle") + _bi(360, 72, "joints, IMU, camera history", "khớp, IMU, lịch sử camera", "small", "middle")
    s += _arrow((360, 78), (360, 90))
    s += _bi(360, 166, "copies the teacher's actions", "chép hành động của thầy", "", "middle") + _bi(360, 184, "on its own states (DAgger)", "trên trạng thái của chính nó (DAgger)", "", "middle")
    s += _arrow((210, 116), (270, 116)) + _bi(240, 108, "labels", "nhãn", "small", "middle")
    # deployment
    s += _box(510, 92, 176, 48) + _text(598, 122, _m("π_S(a | o_{t−H:t})"), "m", "middle")
    s += _bi(598, 166, "no privileged information", "không cần thông tin đặc quyền", "", "middle") + _bi(598, 184, "is needed at run time", "khi chạy thật", "", "middle")
    s += _arrow((448, 116), (508, 116)) + _bi(478, 108, "deploy", "triển khai", "small", "middle")
    return _svg(720, 226, "Teacher-student distillation in three phases", "Chưng cất thầy–trò qua ba giai đoạn", s)


def fig_vla():
    """A generalist policy: a vision-language model with an action expert that outputs a chunk of actions."""
    s = ""
    ins = [(30, "camera images", "ảnh camera"), (82, "instruction: “fold the shirt”", "câu lệnh: “gấp áo”"), (134, "robot state (joint angles)", "trạng thái robot (góc khớp)")]
    for y, en, vi in ins:
        s += _box(10, y, 168, 38, "node in") + _bi(94, y + 24, en, vi, "small", "middle") + _arrow((178, y + 19), (226, 101))
    s += _box(228, 54, 190, 96) + _bi(323, 92, "Vision-language model", "Mô hình thị giác-ngôn ngữ", "lab", "middle") + _bi(323, 114, "pretrained on web data", "học trước trên dữ liệu web", "small", "middle")
    s += _box(458, 54, 150, 96, "node act") + _bi(533, 92, "Action expert", "Bộ phận hành động", "lab", "middle") + _bi(533, 114, "diffusion or flow", "khuếch tán hoặc flow", "small", "middle")
    s += _arrow((418, 102), (456, 102)) + _arrow((533, 196), (533, 152)) + _bi(533, 212, "noise ε", "nhiễu ε", "small", "middle")
    s += _arrow((608, 102), (646, 102)) + _bi(680, 92, "action chunk", "khối hành động", "small", "middle") + _text(680, 114, _m("[a_t, …, a_{t+H−1}]"), "m small", "middle")
    return _svg(720, 222, "A generalist robot policy", "Một chính sách robot tổng quát", s)


FIGURES = {"loop": fig_loop, "teacher": fig_teacher, "vla": fig_vla}


def figures():
    body = BODY.read_text(encoding="utf-8")
    for name, draw in FIGURES.items():
        pat = re.compile(f"<!--fig:{name}-->.*?<!--/fig:{name}-->", re.S)
        assert len(pat.findall(body)) == 1, name
        body = pat.sub(lambda _m_: f'<!--fig:{name}--><!-- prettier-ignore --><div class="ba-scroll">{draw()}</div><!--/fig:{name}-->', body)
    BODY.write_text(body, encoding="utf-8")
    print(BODY, "figures:", ", ".join(FIGURES))


if __name__ == "__main__":
    if "--figures" not in sys.argv:
        main()
    if BODY.is_file():
        figures()
