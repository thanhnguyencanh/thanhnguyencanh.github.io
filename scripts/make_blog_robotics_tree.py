#!/usr/bin/env python3
"""Data for the blog post "A family tree of robotics" (blog/robotics-family-tree/data.js).

Source: the robotics venues of the Paper Explorer (explorer/data/*.json, from the dblp dump). Each paper gets one
branch from keyword rules on its title. The post loads the papers from the explorer files, so this script only writes
the tree, one label per paper (in explorer file order) and the facts.

Run after scripts/make_paper_explorer.py:  python3 scripts/make_blog_robotics_tree.py   (then python3 scripts/build_site.py)
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "explorer" / "data"
OUT = ROOT / "blog" / "robotics-family-tree" / "data.js"
VENUES = ["icra", "iros", "ral", "tro", "ijrr", "rss", "corl", "scirob"]
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"  # one character per paper

# (id, en, vi, den, dvi, [(leaf id, en, vi, keywords)])
TREE_RAW = [
    ("manip", "Manipulation", "Thao tác", "Arms and hands that grasp, move and change objects.", "Cánh tay và bàn tay gắp, di chuyển và thay đổi đồ vật.",
     [("m-grasp", "Grasping & picking", "Gắp và nhặt", ["grasp", "grasping", "pick-and-place", "bin picking", "picking"]),
      ("m-dex", "Dexterous & in-hand", "Khéo léo và trong lòng bàn tay", ["dexterous", "in-hand", "multi-fingered", "multifingered", "finger"]),
      ("m-deform", "Deformable objects", "Vật thể biến dạng", ["deformable", "cloth", "fabric", "garment", "rope", "cable manipulation", "cable routing", "linear object"]),
      ("m-contact", "Contact-rich & assembly", "Tiếp xúc nhiều và lắp ráp", ["assembly", "insertion", "peg-in-hole", "contact-rich", "pushing", "non-prehensile", "tool use"]),
      ("m-mobile", "Mobile & bimanual manipulation", "Thao tác di động và hai tay", ["mobile manipulation", "mobile manipulator", "bimanual", "dual-arm", "loco-manipulation"]),
      ("m-general", "General manipulation", "Thao tác tổng quát", ["manipulation", "manipulator", "robot arm", "robotic arm", "pick", "rearrangement"])]),
    ("legs", "Legged & humanoid robots", "Robot có chân và hình người", "Robots that walk, run, climb and jump.", "Robot đi, chạy, leo trèo và nhảy.",
     [("l-quad", "Quadrupeds & legged robots", "Robot bốn chân và có chân", ["quadruped", "quadrupedal", "legged", "hexapod", "gait", "legs"]),
      ("l-human", "Humanoids & bipeds", "Robot hình người và hai chân", ["humanoid", "biped", "bipedal", "whole-body", "walking"]),
      ("l-loco", "Locomotion in general", "Vận động di chuyển nói chung", ["locomotion", "jumping", "climbing", "snake robot", "crawling"])]),
    ("air", "Aerial, marine & space robots", "Robot bay, dưới nước và không gian", "Robots that fly, swim or work in space.", "Robot bay, bơi hoặc làm việc ngoài không gian.",
     [("a-uav", "Drones & aerial robots", "Drone và robot bay", ["drone", "uav", "quadrotor", "quadcopter", "multirotor", "aerial", "flying", "flight", "micro air vehicle"]),
      ("a-marine", "Underwater & marine", "Dưới nước và trên biển", ["underwater", "marine", "auv", "surface vehicle", "ocean", "swimming", "boat", "ship"]),
      ("a-space", "Space robotics", "Robot không gian", ["space", "planetary", "rover", "satellite", "orbital", "lunar", "mars"])]),
    ("plan", "Planning & navigation", "Lập kế hoạch và điều hướng", "Deciding where to go and how to move.", "Quyết định đi đâu và di chuyển như thế nào.",
     [("p-motion", "Motion & path planning", "Lập kế hoạch chuyển động và đường đi", ["motion planning", "path planning", "trajectory planning", "sampling-based", "rrt", "planner",
                                                                                      "collision avoidance", "collision-free", "obstacle avoidance"]),
      ("p-traj", "Trajectory optimization", "Tối ưu quỹ đạo", ["trajectory optimization", "trajectory optimisation", "trajectory generation", "minimum-time", "time-optimal"]),
      ("p-nav", "Navigation & exploration", "Điều hướng và khám phá", ["navigation", "navigating", "exploration", "coverage", "wayfinding", "crowd"]),
      ("p-task", "Task planning & reasoning", "Lập kế hoạch nhiệm vụ và suy luận", ["task planning", "task and motion planning", "tamp", "symbolic", "temporal logic",
                                                                                   "pddl", "long-horizon", "scheduling"])]),
    ("percep", "SLAM & perception", "SLAM và tri giác", "Knowing where the robot is and what is around it.", "Biết robot đang ở đâu và xung quanh có gì.",
     [("s-slam", "SLAM & odometry", "SLAM và đo hành trình", ["slam", "odometry", "visual-inertial", "lidar-inertial", "bundle adjustment", "loop closure", "pose graph", "pose-graph"]),
      ("s-loc", "Localization & place recognition", "Định vị và nhận dạng địa điểm", ["localization", "localisation", "place recognition", "relocalization", "global positioning"]),
      ("s-map", "Mapping & 3D scenes", "Lập bản đồ và cảnh 3D", ["mapping", "map", "3d reconstruction", "occupancy", "point cloud", "nerf", "gaussian splatting",
                                                              "scene graph", "semantic map", "depth", "surface reconstruction", "reconstruction", "next-best-view", "feature field", "neural field", "radiance field"]),
      ("s-obj", "Detection, segmentation & tracking", "Phát hiện, phân đoạn và theo dõi", ["detection", "segmentation", "tracking", "recognition", "pose estimation",
                                                                                         "6d pose", "keypoint", "classification", "object detection"]),
      ("s-calib", "Sensors, calibration & state estimation", "Cảm biến, hiệu chuẩn và ước lượng trạng thái", ["calibration", "state estimation", "kalman", "filter",
                                                                                                            "sensor fusion", "event camera", "radar", "imu"])]),
    ("ctrl", "Control & dynamics", "Điều khiển và động lực học", "How robots move precisely and stably.", "Cách robot chuyển động chính xác và ổn định.",
     [("c-opt", "Optimal & predictive control", "Điều khiển tối ưu và dự báo", ["model predictive control", "model-predictive control", "mpc", "optimal control",
                                                                               "lqr", "receding horizon"]),
      ("c-force", "Force & impedance control", "Điều khiển lực và trở kháng", ["impedance", "admittance", "force control", "compliance control", "interaction control", "hybrid force"]),
      ("c-dyn", "Dynamics & identification", "Động lực học và nhận dạng hệ thống", ["dynamics", "identification", "kinematics", "kinematic", "calibration of", "inverse kinematics",
                                                                                   "jacobian", "redundant"]),
      ("c-robust", "Stability, safety & robust control", "Ổn định, an toàn và điều khiển bền vững", ["stability", "lyapunov", "robust control", "adaptive control", "sliding mode",
                                                                                                   "barrier function", "safety", "safe", "fault", "controller", "control"])]),
    ("learn", "Robot learning", "Học máy cho robot", "Robots that learn skills from data, demonstrations or reward.", "Robot học kỹ năng từ dữ liệu, minh họa hoặc phần thưởng.",
     [("r-rl", "Reinforcement learning", "Học tăng cường", ["reinforcement learning", "reinforcement-learning", "rl", "q-learning", "actor-critic", "policy optimization", "reward"]),
      ("r-il", "Imitation learning", "Học bắt chước", ["imitation", "demonstration", "behavior cloning", "behavioral cloning", "diffusion policy", "diffusion policies",
                                                      "learning from demonstration", "teleoperated data"]),
      ("r-fm", "Foundation models & language", "Mô hình nền tảng và ngôn ngữ", ["language model", "llm", "vision-language", "vision language", "vlm", "vla",
                                                                               "vision-language-action", "foundation model", "natural language", "language"]),
      ("r-sim", "Sim-to-real & learned models", "Sim-to-real và mô hình học được", ["sim-to-real", "sim2real", "domain randomization", "simulation", "learning-based",
                                                                                   "deep learning", "neural network", "learned", "learning"])]),
    ("hri", "Humans & robots", "Con người và robot", "Robots that work with, assist or are guided by people.", "Robot làm việc cùng, hỗ trợ hoặc được con người dẫn dắt.",
     [("h-hri", "Human-robot interaction", "Tương tác người-robot", ["human-robot", "hri", "human-aware", "collaborative robot", "cobot", "handover", "social robot",
                                                                    "trust", "human preferences", "human"]),
      ("h-tele", "Teleoperation & haptics", "Điều khiển từ xa và xúc giác", ["teleoperation", "telerobotic", "haptic", "shared control", "shared autonomy", "telepresence"]),
      ("h-assist", "Assistive, wearable & rehabilitation", "Hỗ trợ, đeo trên người và phục hồi chức năng", ["exoskeleton", "prosthe", "rehabilitation", "assistive", "wearable",
                                                                                                          "wheelchair", "orthosis"])]),
    ("multi", "Multi-robot systems", "Hệ đa robot", "Teams and swarms of robots.", "Nhóm và bầy robot.",
     [("x-team", "Multi-robot coordination", "Phối hợp đa robot", ["multi-robot", "multirobot", "multi-agent", "multiagent", "team", "cooperative", "formation", "fleet", "decentralized",
                                                                  "distributed"]),
      ("x-swarm", "Swarms", "Bầy robot", ["swarm", "swarms", "collective"])]),
    ("hw", "Design & hardware", "Thiết kế và phần cứng", "New bodies, actuators, sensors and mechanisms.", "Thân robot, cơ cấu chấp hành, cảm biến và cơ cấu mới.",
     [("d-soft", "Soft & continuum robots", "Robot mềm và robot liên tục", ["soft robot", "soft", "continuum", "origami", "pneumatic", "inflatable", "tendon"]),
      ("d-act", "Actuators & mechanisms", "Cơ cấu chấp hành và cơ cấu", ["actuator", "actuation", "mechanism", "transmission", "motor", "joint design", "parallel robot",
                                                                       "cable-driven", "linkage", "design"]),
      ("d-sense", "Tactile & sensing hardware", "Phần cứng xúc giác và cảm biến", ["tactile", "skin", "sensor", "sensing", "touch", "force sensor"]),
      ("d-grip", "Grippers & hands", "Tay kẹp và bàn tay robot", ["gripper", "robotic hand", "robot hand", "end-effector", "end effector", "suction"])]),
    ("app", "Application domains", "Lĩnh vực ứng dụng", "Robots for medicine, roads, farms, factories and homes.", "Robot cho y tế, đường phố, nông trại, nhà máy và gia đình.",
     [("ap-med", "Medical & surgical", "Y tế và phẫu thuật", ["surgical", "surgery", "medical", "endoscop", "colonoscop", "catheter", "needle", "laparoscop", "ultrasound",
                                                             "magnetic", "microrobot", "capsule"]),
      ("ap-drive", "Autonomous driving", "Lái xe tự hành", ["autonomous driving", "self-driving", "autonomous vehicle", "driving", "vehicle", "traffic", "lane", "car"]),
      ("ap-field", "Agriculture & field robots", "Nông nghiệp và robot hiện trường", ["agricultur", "farm", "crop", "fruit", "forest", "field robot", "construction", "mining",
                                                                                      "inspection", "off-road", "terrain"]),
      ("ap-ind", "Industry, logistics & service", "Công nghiệp, hậu cần và dịch vụ", ["industrial", "warehouse", "logistics", "manufacturing", "factory", "household", "service robot",
                                                                                         "kitchen", "cooking"])]),
]
# Some groups are merged so the chart needs at most 8 colours (plus grey for Other).
MERGE = [("mobile", "Mobile robots: legs, wings & fins", "Robot di động: chân, cánh và vây", "Robots that walk, fly, swim or explore space.",
          "Robot đi bộ, bay, bơi hoặc khám phá không gian.", ["legs", "air"]),
         ("plan", "Planning & control", "Lập kế hoạch và điều khiển", "Deciding where to go, and moving there precisely and stably.",
          "Quyết định đi đâu, và di chuyển đến đó một cách chính xác, ổn định.", ["plan", "ctrl"]),
         ("people", "Humans & teams", "Con người và nhóm robot", "Robots that work with people, and robots that work with each other.",
          "Robot làm việc cùng con người, và robot làm việc cùng nhau.", ["hri", "multi"])]


def merged(raw, merge):
    into = {old: m for m in merge for old in m[5]}
    out, done = [], set()
    for g in raw:
        m = into.get(g[0])
        if not m:
            out.append(g)
        elif m[0] not in done:
            done.add(m[0])
            out.append(m[:5] + ([leaf for h in raw if h[0] in m[5] for leaf in h[5]],))
    return out


TREE = merged(TREE_RAW, MERGE)
OTHER = ("other", "Other", "Khác", "Papers whose title does not point to one of the branches above.", "Bài báo có tiêu đề không chỉ rõ thuộc nhánh nào ở trên.")
STEMS = ("prosthe", "endoscop", "colonoscop", "laparoscop", "agricultur")
# ties go to the more specific branch; the broad catch-alls come last
ORDER = ["m-dex", "m-deform", "m-contact", "m-mobile", "m-grasp", "l-human", "l-quad", "a-uav", "a-marine", "a-space", "ap-med", "ap-drive", "ap-field", "ap-ind",
         "h-assist", "h-tele", "h-hri", "x-swarm", "x-team", "d-soft", "d-grip", "d-sense", "d-act", "r-fm", "r-il", "r-rl", "s-slam", "s-loc", "p-traj", "p-task",
         "p-motion", "p-nav", "c-opt", "c-force", "s-calib", "s-obj", "s-map", "c-dyn", "l-loco", "m-general", "c-robust", "r-sim"]


def pattern(word):
    tail = r"" if word in STEMS else r"(?:s|es)?(?![a-z0-9])"
    return re.compile(r"(?<![a-z0-9])" + re.escape(word) + tail)


PAIRS = sorted(((pattern(w), leaf[0], len(w)) for top in TREE for leaf in top[5] for w in leaf[3]), key=lambda x: -x[2])
assert set(ORDER) == {leaf[0] for top in TREE for leaf in top[5]}


def classify(title):
    text, score = title.lower(), Counter()
    for rx, lid, _ in PAIRS:
        if rx.search(text):
            score[lid] += 1
            text = rx.sub(lambda m: "#" * len(m.group(0)), text)
    if not score:
        return OTHER[0]
    return max(score, key=lambda lid: (score[lid], -ORDER.index(lid)))


def main():
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    meta = {v["id"]: v for v in index["venues"]}
    nodes = []
    for tid, en, vi, den, dvi, leaves in TREE:
        nodes.append({"id": tid, "parent": None, "en": en, "vi": vi, "den": den, "dvi": dvi})
        for lid, len_, lvi, _ in leaves:
            nodes.append({"id": lid, "parent": tid, "en": len_, "vi": lvi})
    nodes.append({"id": OTHER[0], "parent": None, "en": OTHER[1], "vi": OTHER[2], "den": OTHER[3], "dvi": OTHER[4], "color": "#9a9a9a", "other": True})
    assert sum(1 for n in nodes if not n["parent"] and not n.get("other")) <= 8, "the chart has 8 colours"
    leaf_ids = [n["id"] for n in nodes if n["parent"] or n["id"] == OTHER[0]]
    assert len(leaf_ids) <= len(ALPHABET)
    code = {lid: ALPHABET[i] for i, lid in enumerate(leaf_ids)}
    top = {n["id"]: (n["parent"] or n["id"]) for n in nodes}
    labels, counts, items = {}, {}, []
    for vid in VENUES:
        d = json.loads((DATA / f"{vid}.json").read_text(encoding="utf-8"))
        lab = [classify(t) for t in d["t"]]
        labels[vid] = "".join(code[x] for x in lab)
        counts[vid] = len(lab)
        items += [(y, x, vid) for y, x in zip(d["y"], lab)]
    total = len(items)
    y0, y1 = min(i[0] for i in items), max(i[0] for i in items)
    tops = Counter(top[i[1]] for i in items)
    leaves = Counter(i[1] for i in items)

    def share(lid, years, by_top=False):
        sel = [i for i in items if i[0] in years]
        return sum(1 for i in sel if (top[i[1]] if by_top else i[1]) == lid) / max(1, len(sel))

    early, late = range(y0, y0 + 3), range(y1 - 3, y1)  # three full years at each end (the last year may be partial)
    growth = sorted(((share(l, late) - share(l, early), l) for l in leaf_ids if l != OTHER[0] and leaves[l] >= 150), reverse=True)
    name = {n["id"]: n for n in nodes}
    pct = lambda x: f"{100 * x:.1f}".rstrip("0").rstrip(".")
    up, down = growth[:3], growth[-3:][::-1]
    fmt_en = lambda n: f"{n:,}"
    fmt_vi = lambda n: f"{n:,}".replace(",", ".")
    big, nbig = tops.most_common(1)[0]
    if big == OTHER[0]:
        big, nbig = tops.most_common(2)[1]
    facts = {
        "big": {"en": f"**{name[big]['en']}** is the largest field, with **{fmt_en(nbig)}** of {fmt_en(total)} papers.",
                "vi": f"**{name[big]['vi']}** là lĩnh vực lớn nhất, với **{fmt_vi(nbig)}** trên {fmt_vi(total)} bài báo."},
        "up": {"en": "Fastest risers (share of papers, " + f"{early[0]}–{early[-1]} vs {late[0]}–{late[-1]}): " +
                     "; ".join(f"**{name[l]['en']}** {pct(share(l, early))}% → {pct(share(l, late))}%" for _, l in up) + ".",
               "vi": "Tăng nhanh nhất (tỷ lệ bài báo, " + f"{early[0]}–{early[-1]} so với {late[0]}–{late[-1]}): " +
                     "; ".join(f"**{name[l]['vi']}** {pct(share(l, early))}% → {pct(share(l, late))}%" for _, l in up) + "."},
        "down": {"en": "Largest declines: " + "; ".join(f"**{name[l]['en']}** {pct(share(l, early))}% → {pct(share(l, late))}%" for _, l in down) + ".",
                 "vi": "Giảm nhiều nhất: " + "; ".join(f"**{name[l]['vi']}** {pct(share(l, early))}% → {pct(share(l, late))}%" for _, l in down) + "."},
        "other": {"en": f"**{pct(tops[OTHER[0]] / total)}%** of titles do not name a branch clearly and are listed under Other.",
                  "vi": f"**{pct(tops[OTHER[0]] / total)}%** tiêu đề không chỉ rõ nhánh nào và được xếp vào mục Khác."},
    }
    data = {"root": {"en": "Robotics", "vi": "Robot học",
                     "den": f"All {fmt_en(total)} papers of {len(VENUES)} robotics venues, {y0}–{y1}.",
                     "dvi": f"Tất cả {fmt_vi(total)} bài báo của {len(VENUES)} hội nghị và tạp chí robot, {y0}–{y1}."},
            "facts": facts, "trees": [{"id": "field", "en": "Field", "vi": "Lĩnh vực", "nodes": nodes, "field": "n"}],
            "chart": "stack", "itemWord": {"en": ["paper", "papers"], "vi": ["bài báo", "bài báo"]},
            "shards": {"base": "../../explorer/data/", "venues": VENUES, "counts": counts, "labels": labels, "alphabet": ALPHABET, "leaves": leaf_ids,
                       "names": {v: meta[v]["short"] for v in VENUES}}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// Labels for the robotics papers of the Paper Explorer data, one branch each; generated by scripts/make_blog_robotics_tree.py.\n"
                   "window.FAMILY = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(OUT, total, "papers", y0, "-", y1, "| fields", dict(tops.most_common()))
    for k, v in facts.items():
        print(k, "|", v["en"])
    import blog_cover
    blog_cover.stack_cover(nodes, [{"year": y, "n": x} for y, x, _ in items if y <= late[-1]], "n", OUT.parent / "cover.svg", OUT.parent / "cover-dark.svg")
    blog_cover.png(OUT.parent / "cover.svg", OUT.parent / "cover.png")


if __name__ == "__main__":
    main()
