#!/usr/bin/env python3
"""Data for the blog post "A family tree of robot learning" (blog/robot-learning-family-tree/data.js).

Source: every paper in the Conference on Robot Learning (CoRL) proceedings, 2017-2025, from the PMLR volume
BibTeX files (title, authors, link, abstract). Each paper gets one method and one task from keyword rules on
its title (weight 2) and abstract (weight 1); abstracts are used only for this and are not published.

Run: python3 scripts/make_blog_robot_learning.py [--bib-dir DIR]   (then python3 scripts/build_site.py)
Without --bib-dir the nine BibTeX files are downloaded to a temporary folder.
"""
import argparse
import json
import random
import re
import tempfile
import time
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "blog" / "robot-learning-family-tree" / "data.js"
VOLUMES = {78: 2017, 87: 2018, 100: 2019, 155: 2020, 164: 2021, 205: 2022, 229: 2023, 270: 2024, 305: 2025}

# (id, en, vi, description en, description vi, [(leaf id, en, vi, den, dvi, keywords)])
METHODS = [
    ("rl", "Reinforcement learning", "Học tăng cường",
     "Policies learned from reward, by trial and error.", "Chính sách học từ phần thưởng, qua thử và sai.",
     [("rl-free", "Model-free RL", "RL không mô hình", "Policy-gradient, actor-critic and Q-learning methods.",
       "Các phương pháp policy gradient, actor-critic và Q-learning.",
       ["reinforcement learning", "deep reinforcement", "deep rl", "rl", "policy gradient", "actor-critic", "q-learning", "reward shaping",
        "exploration bonus", "curriculum", "trial and error", "ppo", "sac"]),
      ("rl-model", "Model-based RL & world models", "RL dựa trên mô hình và mô hình thế giới",
       "Learned dynamics or world models, used to plan or to train in imagination.",
       "Mô hình động lực học hoặc mô hình thế giới học được, dùng để lập kế hoạch hoặc huấn luyện trong tưởng tượng.",
       ["model-based reinforcement learning", "model-based reinforcement", "model-based rl", "world model", "dynamics model", "learned dynamics", "learning dynamics", "dreamer",
        "video prediction model", "predictive model", "forward dynamics", "dynamics learning", "physics model"]),
      ("rl-offline", "Offline, multi-task & meta RL", "RL ngoại tuyến, đa nhiệm và meta",
       "Learning from fixed datasets, across many tasks, or learning to adapt fast.",
       "Học từ bộ dữ liệu cố định, trên nhiều nhiệm vụ, hoặc học cách thích nghi nhanh.",
       ["offline reinforcement learning", "offline reinforcement", "offline rl", "batch reinforcement learning", "batch reinforcement",
        "multi-task reinforcement learning", "multi-task", "meta-reinforcement learning", "meta reinforcement learning", "meta-learning",
        "meta-reinforcement", "meta learning", "offline-to-online", "offline pre-training", "offline data",
        "lifelong", "continual", "skill discovery", "unsupervised skill"])]),
    ("il", "Imitation learning", "Học bắt chước",
     "Policies learned from demonstrations instead of reward.", "Chính sách học từ các lần minh họa thay vì từ phần thưởng.",
     [("il-bc", "Behavior cloning & policy architectures", "Nhân bản hành vi và kiến trúc chính sách",
       "Supervised policies from demonstrations, including diffusion and transformer policies.",
       "Chính sách học có giám sát từ minh họa, gồm cả chính sách diffusion và transformer.",
       ["imitation learning", "behavior cloning", "behavioral cloning", "behaviour cloning", "demonstration", "diffusion policy",
        "diffusion policies", "learning from demonstration", "imitation", "visuomotor policy", "visuomotor policies", "policy learning",
        "dagger", "interactive imitation", "action chunking", "flow matching", "consistency flow", "flow policy", "flow policies",
        "transformer policy", "transformer policies"]),
      ("il-reward", "Inverse RL & reward learning", "RL ngược và học phần thưởng",
       "Rewards or preferences inferred from demonstrations, corrections or feedback.",
       "Phần thưởng hoặc sở thích được suy ra từ minh họa, sự điều chỉnh hoặc phản hồi.",
       ["inverse reinforcement learning", "inverse reinforcement", "inverse rl", "reward learning", "learning rewards", "learning reward", "reward function", "preference learning", "preference-based", "human preferences", "learning from preferences", "rankings", "human feedback",
        "reward model", "corrections"]),
      ("il-human", "Learning from human video", "Học từ video của con người",
       "Skills transferred from videos or play of people.", "Kỹ năng được chuyển từ video hoặc hoạt động của con người.",
       ["human video", "videos of humans", "human videos", "youtube", "egocentric", "watching humans", "from humans", "human hand",
        "in-the-wild video", "internet video", "play data"])]),
    ("fm", "Foundation models", "Mô hình nền tảng",
     "Large pretrained models: language, vision-language and robot foundation models.",
     "Các mô hình tiền huấn luyện lớn: mô hình ngôn ngữ, thị giác-ngôn ngữ và mô hình nền tảng cho robot.",
     [("fm-llm", "Language & vision-language models", "Mô hình ngôn ngữ và thị giác-ngôn ngữ",
       "LLMs and VLMs that plan, reason, write code or give rewards.", "LLM và VLM dùng để lập kế hoạch, suy luận, viết mã hoặc cho phần thưởng.",
       ["large language model", "language model", "llm", "gpt", "chatgpt", "gpt-4", "gpt-4v", "vision-language model",
        "vision language model", "vlm", "mllm", "multimodal llm", "multimodal large language", "foundation model", "prompting",
        "code generation", "multimodal large", "large pretrained model", "large pre-trained model"]),
      ("fm-vla", "Vision-language-action & generalist policies", "Thị giác-ngôn ngữ-hành động và chính sách tổng quát",
       "Large policies trained on many robots, tasks and scenes.", "Các chính sách lớn được huấn luyện trên nhiều robot, nhiệm vụ và bối cảnh.",
       ["vision-language-action", "vla", "generalist policy", "generalist policies", "generalist robot", "robot foundation model",
        "cross-embodiment", "open x-embodiment", "rt-1", "rt-2", "openvla", "large-scale robot", "embodiment-agnostic"]),
      ("fm-rep", "Pretrained visual representations", "Biểu diễn thị giác tiền huấn luyện",
       "Self-supervised or pretrained features that robot policies build on.", "Đặc trưng tự giám sát hoặc tiền huấn luyện làm nền cho chính sách robot.",
       ["pretrained representation", "pre-trained representation", "visual representation", "pretrained visual", "pre-trained visual",
        "visual pre-training", "visual pretraining", "masked visual", "sensorimotor pre-training", "universal visual", "self-supervised visual",
        "pretrained vision", "pre-trained vision", "large-scale pre-training", "web-scale"])]),
    ("sim", "Simulation, data & sim-to-real", "Mô phỏng, dữ liệu và sim-to-real",
     "Where training data comes from, and how skills move from simulation to real robots.",
     "Dữ liệu huấn luyện đến từ đâu, và kỹ năng được chuyển từ mô phỏng sang robot thật như thế nào.",
     [("sim-real", "Sim-to-real transfer", "Chuyển giao từ mô phỏng sang thực tế",
       "Domain randomization and adaptation to cross the reality gap.", "Ngẫu nhiên hóa miền và thích nghi để vượt qua khoảng cách thực tế.",
       ["sim-to-real", "sim2real", "simulation-to-reality", "domain randomization", "reality gap", "real-to-sim", "domain adaptation",
        "sim-to-real transfer", "transfer to the real"]),
      ("sim-data", "Datasets, benchmarks & data collection", "Bộ dữ liệu, chuẩn đánh giá và thu thập dữ liệu",
       "Simulators, benchmarks, teleoperation systems and large datasets.", "Bộ mô phỏng, chuẩn đánh giá, hệ thống điều khiển từ xa và bộ dữ liệu lớn.",
       ["^benchmark", "^dataset", "^simulator", "simulation platform", "simulation benchmark", "large-scale dataset", "teleoperation", "data collection", "data generation", "large-scale data",
        "data augmentation", "synthetic data"])]),
    ("perc", "Perception & representation", "Tri giác và biểu diễn",
     "How robots see and model the world around them.", "Cách robot nhìn và mô hình hóa thế giới xung quanh.",
     [("perc-3d", "3D scenes & mapping", "Cảnh 3D và lập bản đồ",
       "Point clouds, implicit fields, NeRF, Gaussian splatting and maps for robots.", "Đám mây điểm, trường ẩn, NeRF, Gaussian Splatting và bản đồ cho robot.",
       ["nerf", "neural radiance", "gaussian splatting", "feature splatting", "^splatting", "point cloud", "3d representation", "implicit neural", "implicit representation",
        "neural implicit", "implicit function", "occupancy", "mapping", "slam",
        "scene representation", "voxel", "signed distance", "3d scene", "scene graph", "depth estimation", "depth sensing", "depth completion", "monocular depth", "depth learning"]),
      ("perc-obj", "Objects, pose & affordances", "Đối tượng, tư thế và khả năng tương tác",
       "Detection, segmentation, pose estimation and where to act on objects.", "Phát hiện, phân đoạn, ước lượng tư thế và vị trí tác động lên đối tượng.",
       ["pose estimation", "6d pose", "6-dof pose", "affordance", "object detection", "grasp detection", "grasp pose", "grasp generation", "grasp synthesis", "^detection", "^detect", "segmentation", "keypoint",
        "object-centric", "correspondence", "articulated object", "category-level", "object discovery", "^recognition"]),
      ("perc-touch", "Touch & multimodal sensing", "Xúc giác và cảm biến đa phương thức",
       "Tactile, force, audio and other senses beyond vision.", "Xúc giác, lực, âm thanh và các giác quan khác ngoài thị giác.",
       ["tactile", "touch", "haptic", "force sensing", "force/torque", "audio", "sound", "acoustic", "multisensory", "event camera",
        "visuotactile", "vision and touch"]),
      ("perc-rep", "Learned state representations", "Biểu diễn trạng thái học được",
       "Latent spaces, embeddings and self-supervised features learned for control.",
       "Không gian ẩn, phép nhúng và đặc trưng tự giám sát được học cho điều khiển.",
       ["representation learning", "state representation", "latent space", "latent representation", "self-supervised", "embedding",
        "contrastive", "disentangled", "latent dynamics"]),
      ("perc-pred", "Prediction & state estimation", "Dự đoán và ước lượng trạng thái",
       "Forecasting how people and vehicles move, tracking and localization.", "Dự báo chuyển động của người và phương tiện, theo dõi và định vị.",
       ["trajectory prediction", "motion prediction", "motion forecasting", "trajectory forecasting", "forecasting", "behavior prediction",
        "pedestrian prediction", "vehicle trajectories", "predicting trajectories", "tracking", "localization", "state estimation", "odometry", "visual-inertial", "vio"])]),
    ("plan", "Planning & control", "Lập kế hoạch và điều khiển",
     "Learning combined with planners and controllers.", "Kết hợp học với bộ lập kế hoạch và bộ điều khiển.",
     [("plan-motion", "Motion planning & trajectory optimization", "Lập kế hoạch chuyển động và tối ưu quỹ đạo",
       "Collision-free paths and optimized trajectories, learned or assisted by learning.",
       "Đường đi không va chạm và quỹ đạo tối ưu, được học hoặc được hỗ trợ bởi học máy.",
       ["motion planning", "trajectory optimization", "trajectory optimisation", "motion optimization", "motion optimisation", "path planning", "collision avoidance", "planner", "sampling-based", "motion planner",
        "trajectory generation"]),
      ("plan-control", "Learning-based control & MPC", "Điều khiển dựa trên học và MPC",
       "Controllers, model-predictive control and optimal control with learned parts.",
       "Bộ điều khiển, điều khiển dự báo theo mô hình và điều khiển tối ưu có thành phần học.",
       ["model predictive control", "model-predictive control", "mpc", "optimal control", "controller", "impedance", "feedback control",
        "adaptive control", "lyapunov", "dynamical system"]),
      ("plan-task", "Task & motion planning", "Lập kế hoạch nhiệm vụ và chuyển động",
       "Long-horizon problems split into symbolic and geometric steps.", "Bài toán dài hạn được chia thành các bước ký hiệu và hình học.",
       ["task and motion planning", "tamp", "long-horizon", "symbolic", "task planning", "planning domain", "pddl"])]),
    ("safe", "Safety, uncertainty & robustness", "An toàn, độ bất định và độ bền vững",
     "Guarantees, calibrated uncertainty and behaviour under change.", "Bảo đảm, độ bất định được hiệu chỉnh và hành vi khi điều kiện thay đổi.",
     [("safe-safety", "Safe learning & verification", "Học an toàn và kiểm chứng",
       "Constraints, barrier functions and formal checks on learned behaviour.", "Ràng buộc, hàm rào chắn và kiểm chứng hình thức cho hành vi học được.",
       ["safe reinforcement learning", "safe rl", "^safe", "^safety", "safety-critical", "safety constraint", "verification", "barrier function",
        "constrained", "formal", "shielding", "^risk", "risk-aware", "risk-sensitive"]),
      ("safe-unc", "Uncertainty & robustness", "Độ bất định và độ bền vững",
       "Bayesian methods, out-of-distribution detection and robustness to change.", "Phương pháp Bayes, phát hiện ngoài phân phối và độ bền vững trước thay đổi.",
       ["uncertainty", "bayesian", "^robustness", "out-of-distribution", "conformal", "calibration", "^probabilistic", "distribution shift",
        "adversarial", "failure detection", "anomaly"])]),
]
TASKS = [
    ("manip", "Manipulation", "Thao tác", "Robots that change the world with arms and hands.", "Robot thay đổi thế giới bằng cánh tay và bàn tay.",
     [("t-grasp", "Grasping & pick-and-place", "Gắp và gắp-đặt", "Picking up objects and putting them somewhere else.",
       "Nhặt đồ vật và đặt chúng ở nơi khác.", ["grasp", "grasping", "grasps", "pick-and-place", "pick and place", "bin picking", "picking"]),
      ("t-dex", "Dexterous & in-hand", "Khéo léo và trong lòng bàn tay", "Multi-fingered hands and in-hand reorientation.",
       "Bàn tay nhiều ngón và xoay đồ vật trong lòng bàn tay.",
       ["dexterous", "in-hand", "multi-fingered", "multi-finger", "dexterity", "allegro", "shadow hand", "anthropomorphic hand", "robotic hand"]),
      ("t-deform", "Deformable objects", "Vật thể biến dạng", "Cloth, rope, cables, dough and liquids.", "Vải, dây, cáp, bột và chất lỏng.",
       ["deformable", "cloth", "fabric", "garment", "rope", "cable", "dough", "liquid", "pouring", "folding", "granular", "elasto"]),
      ("t-contact", "Contact-rich, tools & assembly", "Tiếp xúc nhiều, công cụ và lắp ráp", "Insertion, assembly, tool use and forceful tasks.",
       "Lắp chèn, lắp ráp, dùng công cụ và các nhiệm vụ cần lực.",
       ["insertion", "assembly", "peg", "tool use", "tool-use", "tool manipulation", "contact-rich", "screw", "wiping", "cutting", "tool",
        "non-prehensile"]),
      ("t-mobile", "Mobile & bimanual", "Di động và hai tay", "Manipulators on mobile bases, and two-arm tasks.", "Tay máy trên đế di động và nhiệm vụ hai tay.",
       ["mobile manipulation", "mobile manipulator", "loco-manipulation", "bimanual", "dual-arm", "two-arm", "bi-manual"]),
      ("t-general", "General manipulation", "Thao tác tổng quát", "Tabletop and household manipulation without a narrower focus.",
       "Thao tác trên bàn và trong gia đình, không thuộc nhóm hẹp hơn.",
       ["manipulation", "manipulate", "manipulating", "pushing", "rearrangement", "tabletop", "household", "kitchen", "articulated", "drawer",
        "door", "stacking", "robot arm", "robotic arm"])]),
    ("loco", "Locomotion", "Vận động di chuyển", "Robots that walk, run and jump.", "Robot đi, chạy và nhảy.",
     [("t-legged", "Legged & quadruped", "Có chân và bốn chân", "Quadrupeds and other legged robots.", "Robot bốn chân và các robot có chân khác.",
       ["legged", "quadruped", "quadrupedal", "locomotion", "walking", "gait", "parkour", "anymal", "unitree", "a1 robot", "legs"]),
      ("t-humanoid", "Humanoids & whole-body", "Hình người và toàn thân", "Bipeds, humanoids and whole-body control.", "Robot hai chân, hình người và điều khiển toàn thân.",
       ["humanoid locomotion", "humanoid robot", "bipedal locomotion", "humanoid", "whole-body", "biped", "bipedal", "cassie"])]),
    ("nav", "Navigation & driving", "Điều hướng và lái xe", "Robots and vehicles that move through the world.", "Robot và phương tiện di chuyển trong thế giới.",
     [("t-drive", "Autonomous driving", "Lái xe tự hành", "Self-driving cars, traffic and road users.", "Xe tự lái, giao thông và người tham gia giao thông.",
       ["autonomous driving", "self-driving", "driving", "vehicle", "traffic", "lane", "pedestrian", "car", "intersection"]),
      ("t-nav", "Indoor & visual navigation", "Điều hướng trong nhà và bằng thị giác", "Reaching goals in buildings and unknown places.",
       "Đi đến mục tiêu trong tòa nhà và nơi chưa biết.",
       ["navigation", "navigate", "^exploration", "point-goal", "object-goal", "objectnav", "social navigation", "path following", "wayfinding"]),
      ("t-aerial", "Aerial & field robots", "Robot bay và robot hiện trường", "Drones, boats and off-road or outdoor robots.",
       "Drone, tàu thuyền và robot địa hình hoặc ngoài trời.",
       ["drone", "quadrotor", "quadcopter", "aerial", "uav", "flight", "flying", "underwater", "marine", "off-road", "field robot", "agricultur",
        "outdoor", "terrain"])]),
    ("hri", "Human-robot interaction", "Tương tác người-robot", "Robots that work with, assist or adapt to the people around them.",
     "Robot làm việc cùng, hỗ trợ hoặc thích nghi với những người xung quanh.", []),
    ("multi", "Multi-robot & multi-agent", "Đa robot và đa tác tử", "Teams of robots, swarms and multi-agent settings.",
     "Nhóm robot, bầy robot và bối cảnh đa tác tử.", []),
    ("t-other", "General or other tasks", "Nhiệm vụ chung hoặc khác", "Papers whose task does not fall in the groups above.",
     "Bài báo có nhiệm vụ không thuộc các nhóm trên.", []),
]
MULTI_WORDS = ["multi-robot", "multi-agent", "swarm", "fleet", "multiple robots", "team of robots", "decentralized"]
HRI_WORDS = ["human-robot interaction", "hri", "human-robot collaboration", "collaborative manipulation", "collaborat", "assistive",
             "handover", "shared autonomy", "human partner", "social", "co-robot", "with humans", "exoskeleton", "prosthe", "wheelchair"]
OTHER_METHOD = ("m-other", "Other methods", "Phương pháp khác", "Papers whose method does not fall in the groups above.",
                "Bài báo có phương pháp không thuộc các nhóm trên.")

ACCENTS = {"'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303", "=": "\u0304", ".": "\u0307", "c": "\u0327", "v": "\u030c",
           "u": "\u0306", "H": "\u030b", "k": "\u0328", "r": "\u030a"}
LETTERS = {"o": "ø", "O": "Ø", "ss": "ß", "aa": "å", "AA": "Å", "ae": "æ", "AE": "Æ", "l": "ł", "L": "Ł", "i": "ı", "oe": "œ"}


def detex(s):
    import unicodedata
    s = re.sub(r"\\([`'^\"~=.])\s*\{?\\?([A-Za-z])\}?", lambda m: m.group(2) + ACCENTS[m.group(1)], s)
    s = re.sub(r"\\([cvuHkr])\s*\{\\?([A-Za-z])\}", lambda m: m.group(2) + ACCENTS[m.group(1)], s)
    s = re.sub(r"\\([cvuHkr]) ([A-Za-z])", lambda m: m.group(2) + ACCENTS[m.group(1)], s)
    s = re.sub(r"\{?\\(ss|aa|AA|ae|AE|oe|o|O|l|L|i)\}?(?![A-Za-z])", lambda m: LETTERS[m.group(1)], s)
    s = re.sub(r"\\(emph|textit|textbf|textsc|mathrm|mathbf|text)\{([^{}]*)\}", r"\2", s)
    s = s.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_").replace("--", "–").replace("~", " ")
    s = re.sub(r"\$([^$]*)\$", r"\1", s)
    s = s.replace("{", "").replace("}", "").replace("\\", "")
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", s)).strip()


def fields(entry):
    out, i = {}, 0
    for m in re.finditer(r"(\w+)\s*=\s*\{", entry):
        if m.start() < i:
            continue
        depth, j = 1, m.end()
        while depth and j < len(entry):
            depth += {"{": 1, "}": -1}.get(entry[j], 0)
            j += 1
        out[m.group(1).lower()] = entry[m.end():j - 1]
        i = j
    return out


def authors(raw):
    names = []
    for a in re.split(r"\s+and\s+", raw):
        a = detex(a)
        if "," in a:
            last, first = a.split(",", 1)
            a = first.strip() + " " + last.strip()
        names.append(a.strip())
    return ", ".join(n for n in names if n)


def load(bib_dir):
    papers = []
    for vol, year in VOLUMES.items():
        text = (bib_dir / f"v{vol}.bib").read_text(encoding="utf-8")
        for entry in re.split(r"\n@", text):
            if not entry.lower().startswith("inproceedings"):
                continue
            f = fields(entry)
            papers.append({"title": detex(f["title"]), "authors": authors(f.get("author", "")), "year": year, "url": f.get("url", ""),
                           "abstract": detex(f.get("abstract", ""))})
    return papers


STEMS = ("collaborat", "agricultur", "elasto", "prosthe")
WEIGHT = {"hri": 1.5}  # who the robot works with decides the task even when the paper is also about manipulation
PRIORITY = ["fm-vla", "fm-llm", "fm-rep", "il-human", "il-reward", "il-bc", "rl-offline", "rl-model", "rl-free", "sim-real", "sim-data",
            "perc-touch", "perc-obj", "perc-3d", "perc-rep", "perc-pred", "plan-task", "plan-motion", "plan-control", "safe-safety", "safe-unc",
            "hri", "multi", "t-dex", "t-deform", "t-contact", "t-mobile", "t-grasp", "t-humanoid", "t-legged", "t-drive", "t-aerial", "t-nav",
            "t-general"]


def pattern(word):
    tail = r"" if word in STEMS else r"(?:s|es)?(?![a-z0-9])"
    return re.compile(r"(?<![a-z0-9])" + re.escape(word) + tail)


def pick(tree, title, abstract, extra=()):
    """Leaf with the most keyword hits (title x2, abstract x1). Longer phrases are matched first and blanked out,
    so "inverse reinforcement learning" counts for reward learning only, not also for "reinforcement learning"."""
    pairs = [(w, leaf[0]) for top in tree for leaf in top[5] for w in leaf[5]] + [(w, lid) for lid, words in extra for w in words]
    pairs.sort(key=lambda x: -len(x[0].lstrip("^")))
    score = Counter()
    for text, weight in ((title, 2), (abstract, 1)):
        for w, lid in pairs:
            if w.startswith("^") and weight == 1:
                continue
            rx = pattern(w.lstrip("^"))
            if rx.search(text):
                score[lid] += weight * WEIGHT.get(lid, 1)
                text = rx.sub(lambda m: "#" * len(m.group(0)), text)
    if not score:
        return None
    return max(score, key=lambda lid: (score[lid], -PRIORITY.index(lid)))


def classify(p):
    title, abstract = p["title"].lower(), p["abstract"].lower()
    m = pick(METHODS, title, abstract) or OTHER_METHOD[0]
    t = pick(TASKS, title, abstract, extra=[("hri", HRI_WORDS), ("multi", MULTI_WORDS)]) or "t-other"
    return m, t


def nodes_of(tree, extra_leaves=()):
    out = []
    for tid, en, vi, den, dvi, leaves in tree:
        out.append({"id": tid, "parent": None, "en": en, "vi": vi, "den": den, "dvi": dvi})
        for leaf in leaves:
            out.append({"id": leaf[0], "parent": tid, "en": leaf[1], "vi": leaf[2], "den": leaf[3], "dvi": leaf[4]})
    for lid, en, vi, den, dvi in extra_leaves:
        out.append({"id": lid, "parent": None, "en": en, "vi": vi, "den": den, "dvi": dvi})
    for n in out:
        if n["id"] in (OTHER_METHOD[0], "t-other"):
            n["color"], n["other"] = "#9a9a9a", True  # "Other" stays grey in charts and covers, and is not counted as a group
    return out


def share(items, key, ids, years):
    n = [i for i in items if i["year"] in years]
    return sum(1 for i in n if i[key] in ids), len(n)


def make_facts(items, mnodes, tnodes):
    name = {n["id"]: n for n in mnodes + tnodes}
    top = {n["id"]: (n["parent"] or n["id"]) for n in mnodes + tnodes}
    pct = lambda a, b: round(100 * a / b) if b else 0
    en = lambda n: f"{n:,}"
    vi = lambda n: f"{n:,}".replace(",", ".")
    y0, y1 = items[0]["year"], items[-1]["year"]
    fm = [n["id"] for n in mnodes if n["parent"] == "fm"]
    rl = [n["id"] for n in mnodes if n["parent"] == "rl"]
    fm0, n0 = share(items, "m", fm, range(y0, 2022))
    fm1, n1 = share(items, "m", fm, [y1])
    rl0, m0 = share(items, "m", rl, range(y0, y0 + 3))
    rl1, m1 = share(items, "m", rl, range(y1 - 2, y1 + 1))
    tasks = Counter(top[i["t"]] for i in items)
    ttop, tn = tasks.most_common(1)[0]
    cells = Counter((top[i["m"]], top[i["t"]]) for i in items if top[i["t"]] != "t-other" and i["m"] != OTHER_METHOD[0])
    (cm, ct), cn = cells.most_common(1)[0]
    L = lambda k, l: name[k][l]
    return {
        "fm": {"en": f"**Foundation models** were **{pct(fm0, n0)}%** of CoRL papers before 2022 and **{pct(fm1, n1)}%** in {y1}.",
               "vi": f"**Mô hình nền tảng** chiếm **{pct(fm0, n0)}%** số bài CoRL trước năm 2022 và **{pct(fm1, n1)}%** vào năm {y1}."},
        "rl": {"en": f"**Reinforcement learning** fell from **{pct(rl0, m0)}%** of papers in {y0}–{y0 + 2} to **{pct(rl1, m1)}%** in {y1 - 2}–{y1}.",
               "vi": f"**Học tăng cường** giảm từ **{pct(rl0, m0)}%** số bài trong giai đoạn {y0}–{y0 + 2} xuống **{pct(rl1, m1)}%** trong giai đoạn {y1 - 2}–{y1}."},
        "task": {"en": f"**{L(ttop, 'en')}** is the most studied task: **{en(tn)}** of {en(len(items))} papers ({pct(tn, len(items))}%).",
                 "vi": f"**{L(ttop, 'vi')}** là nhiệm vụ được nghiên cứu nhiều nhất: **{vi(tn)}** trên {vi(len(items))} bài ({pct(tn, len(items))}%)."},
        "cell": {"en": f"The largest pair is **{L(cm, 'en')} × {L(ct, 'en')}**, with **{cn}** papers.",
                 "vi": f"Cặp lớn nhất là **{L(cm, 'vi')} × {L(ct, 'vi')}**, với **{cn}** bài."},
    }


def download(dest):
    for vol in VOLUMES:
        url = f"https://proceedings.mlr.press/v{vol}/assets/bib/bibliography.bib"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (blog data script)"})
        (dest / f"v{vol}.bib").write_bytes(urllib.request.urlopen(req, timeout=60).read())
        time.sleep(1.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bib-dir", type=Path, help="folder with v78.bib ... v305.bib (downloaded if not given)")
    ap.add_argument("--sample", type=int, default=0, help="print this many random papers with their labels, for a manual check")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        bib_dir = args.bib_dir or Path(tmp)
        if not args.bib_dir:
            download(bib_dir)
        papers = load(bib_dir)
    for p in papers:
        p["m"], p["t"] = classify(p)
    if args.sample:
        random.seed(7)
        for p in random.sample(papers, args.sample):
            print(f'{p["m"]:12} {p["t"]:10} {p["year"]} {p["title"][:110]}')
    mnodes = nodes_of(METHODS, [OTHER_METHOD])
    tnodes = nodes_of(TASKS)
    items = sorted(({"title": p["title"], "authors": p["authors"], "year": p["year"], "venue": f'CoRL {p["year"]}', "url": p["url"],
                     "m": p["m"], "t": p["t"]} for p in papers), key=lambda x: (x["year"], x["title"].lower()))
    for i, it in enumerate(items):
        it["id"] = i
    data = {"root": {"en": "Robot learning", "vi": "Học máy cho robot",
                     "den": f"All {len(items):,} papers of the Conference on Robot Learning (CoRL), {items[0]['year']}–{items[-1]['year']}.",
                     "dvi": f"Tất cả {len(items):,} bài báo của hội nghị CoRL (Conference on Robot Learning), {items[0]['year']}–{items[-1]['year']}.".replace(",", ".", 1)},
            "facts": make_facts(items, mnodes, tnodes),
            "trees": [{"id": "method", "en": "Method", "vi": "Phương pháp", "nodes": mnodes, "field": "m"},
                      {"id": "task", "en": "Task", "vi": "Nhiệm vụ", "nodes": tnodes, "field": "t"}],
            "items": items, "chart": "stack", "itemWord": {"en": ["paper", "papers"], "vi": ["bài báo", "bài báo"]}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// CoRL 2017-2025 papers (PMLR), one method and one task each; generated by scripts/make_blog_robot_learning.py.\n"
                   "window.FAMILY = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    top = {n["id"]: (n["parent"] or n["id"]) for n in mnodes + tnodes}
    print(OUT, len(items), "papers;", "by year", dict(sorted(Counter(i["year"] for i in items).items())))
    print("methods", dict(Counter(top[i["m"]] for i in items).most_common()))
    print("tasks", dict(Counter(top[i["t"]] for i in items).most_common()))
    for k, v in data["facts"].items():
        print(k, "|", v["en"])
    import blog_cover
    blog_cover.stack_cover(mnodes, items, "m", OUT.parent / "cover.svg", OUT.parent / "cover-dark.svg")
    blog_cover.png(OUT.parent / "cover.svg", OUT.parent / "cover.png")


if __name__ == "__main__":
    main()
