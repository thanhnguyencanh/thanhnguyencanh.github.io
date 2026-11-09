#!/usr/bin/env python3
"""Data for the Paper Explorer (explorer/data/*.json): every paper of 14 robotics, computer vision and machine
learning venues, from the dblp XML dump (CC0, https://dblp.org/xml/).

Run: python3 scripts/make_paper_explorer.py /path/to/dblp.xml.gz   (then python3 scripts/build_site.py)

Output: explorer/data/index.json (venues, topics, counts) and one columnar file per venue
(t = title, a = authors, y = year, l = link, g = topic bits). Topics come from keyword rules on titles.
"""
import gzip
import html
import html.entities
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "explorer" / "data"
YEARS = range(2015, 2027)
FIELDS = [("rob", "Robotics"), ("cv", "Computer vision"), ("ml", "Machine learning")]
# id, field, short name, full name, dblp key prefix, venue string test
VENUES = [
    ("icra", "rob", "ICRA", "IEEE International Conference on Robotics and Automation", "conf/icra/", lambda v: re.fullmatch(r"ICRA( \(\d+\))?", v) is not None),
    ("iros", "rob", "IROS", "IEEE/RSJ International Conference on Intelligent Robots and Systems", "conf/iros/", lambda v: re.fullmatch(r"IROS( \(\d+\))?", v) is not None),
    ("rss", "rob", "RSS", "Robotics: Science and Systems", "conf/rss/", lambda v: v == "Robotics: Science and Systems"),
    ("corl", "rob", "CoRL", "Conference on Robot Learning", "conf/corl/", lambda v: v == "CoRL"),
    ("ral", "rob", "RA-L", "IEEE Robotics and Automation Letters", "journals/ral/", lambda v: v == "IEEE Robotics Autom. Lett."),
    ("tro", "rob", "T-RO", "IEEE Transactions on Robotics", "journals/trob/", lambda v: v == "IEEE Trans. Robotics"),
    ("ijrr", "rob", "IJRR", "The International Journal of Robotics Research", "journals/ijrr/", lambda v: v == "Int. J. Robotics Res."),
    ("scirob", "rob", "Sci. Robotics", "Science Robotics", "journals/scirobotics/", lambda v: v == "Sci. Robotics"),
    ("cvpr", "cv", "CVPR", "IEEE/CVF Conference on Computer Vision and Pattern Recognition", "conf/cvpr/", lambda v: re.fullmatch(r"CVPR( \(\d+\))?", v) is not None),
    ("iccv", "cv", "ICCV", "IEEE/CVF International Conference on Computer Vision", "conf/iccv/", lambda v: v == "ICCV"),
    ("eccv", "cv", "ECCV", "European Conference on Computer Vision", "conf/eccv/", lambda v: re.fullmatch(r"ECCV( \(\d+\))?", v) is not None),
    ("neurips", "ml", "NeurIPS", "Conference on Neural Information Processing Systems", "conf/nips/", lambda v: v in ("NeurIPS", "NIPS", "NeurIPS Datasets and Benchmarks")),
    ("icml", "ml", "ICML", "International Conference on Machine Learning", "conf/icml/", lambda v: re.fullmatch(r"ICML( \(\d+\)| \(Position Papers\))?", v) is not None),
    ("iclr", "ml", "ICLR", "International Conference on Learning Representations", "conf/iclr/", lambda v: re.fullmatch(r"ICLR( \((Poster|Oral|Spotlight)\))?", v) is not None),
]
# id, name, group, title keywords (a phrase hides the shorter words inside it; plurals match)
TOPICS = [
    ("slam", "SLAM & localization", "Robotics", ["slam", "localization", "localisation", "odometry", "place recognition", "loop closure", "visual-inertial", "mapping"]),
    ("manip", "Manipulation & grasping", "Robotics", ["manipulation", "grasp", "grasping", "pick-and-place", "dexterous", "in-hand", "bimanual", "gripper"]),
    ("loco", "Legged & humanoid robots", "Robotics", ["legged", "quadruped", "quadrupedal", "locomotion", "humanoid", "biped", "bipedal", "walking robot"]),
    ("nav", "Navigation & motion planning", "Robotics", ["navigation", "motion planning", "path planning", "trajectory planning", "trajectory optimization",
                                                       "obstacle avoidance", "collision avoidance", "exploration"]),
    ("drive", "Autonomous driving", "Robotics", ["autonomous driving", "self-driving", "autonomous vehicle", "driving", "vehicle", "traffic", "lane", "bird's-eye", "bev"]),
    ("aerial", "Aerial, marine & field robots", "Robotics", ["drone", "uav", "quadrotor", "quadcopter", "aerial", "underwater", "marine", "agricultural", "field robot", "off-road"]),
    ("hri", "Human-robot interaction", "Robotics", ["human-robot", "hri", "assistive", "exoskeleton", "prosthe", "teleoperation", "shared autonomy", "social robot"]),
    ("multi", "Multi-robot & multi-agent", "Robotics", ["multi-robot", "swarm", "multi-agent", "multiagent"]),
    ("medical", "Medical & surgical", "Robotics", ["surgical", "surgery", "medical", "endoscop", "colonoscop", "catheter", "rehabilitation", "needle"]),
    ("soft", "Soft robots & mechanisms", "Robotics", ["soft robot", "soft actuator", "actuator", "continuum robot", "origami", "mechanism design", "compliant"]),
    ("touch", "Touch & force sensing", "Robotics", ["tactile", "haptic", "force sensing", "force control", "touch"]),
    ("rl", "Reinforcement learning", "Learning", ["reinforcement learning", "reinforcement-learning", "rl", "q-learning", "actor-critic", "policy gradient", "policy optimization", "reward"]),
    ("il", "Imitation learning", "Learning", ["imitation", "demonstration", "behavior cloning", "behavioral cloning", "diffusion policy", "diffusion policies"]),
    ("llm", "LLMs, VLMs & foundation models", "Learning", ["language model", "llm", "vision-language", "vision language", "vlm", "mllm", "multimodal large", "gpt",
                                                         "vision-language-action", "vla", "foundation model", "chatgpt", "instruction tuning", "prompt"]),
    ("gen", "Diffusion & generative models", "Learning", ["diffusion", "generative", "gan", "gans", "vae", "variational autoencoder", "flow matching", "score-based", "normalizing flow"]),
    ("tf", "Transformers & attention", "Learning", ["transformer", "attention", "vit", "self-attention"]),
    ("gnn", "Graph neural networks", "Learning", ["graph neural", "gnn", "graph convolution", "message passing"]),
    ("ssl", "Self-supervised & contrastive", "Learning", ["self-supervised", "contrastive", "masked autoencoder", "unsupervised representation", "self-supervision"]),
    ("transfer", "Few-shot, transfer & continual", "Learning", ["few-shot", "zero-shot", "meta-learning", "domain adaptation", "domain generalization", "transfer learning",
                                                           "continual", "incremental learning", "lifelong", "open-vocabulary", "open-world"]),
    ("robust", "Uncertainty, robustness & safety", "Learning", ["uncertainty", "bayesian", "robust", "robustness", "adversarial", "safe", "safety", "out-of-distribution",
                                                              "calibration", "evidential", "conformal", "certified"]),
    ("theory", "Optimization & theory", "Learning", ["convergence", "regret", "bandit", "sample complexity", "generalization bound", "stochastic gradient",
                                                     "convex", "nonconvex", "non-convex", "optimization", "theory", "theoretical"]),
    ("eff", "Efficient models & compression", "Learning", ["pruning", "quantization", "distillation", "compression", "efficient", "sparse", "low-rank", "lora"]),
    ("det", "Object detection", "Vision", ["detection", "detector", "detecting", "detect"]),
    ("seg", "Segmentation", "Vision", ["segmentation", "segment", "panoptic", "matting"]),
    ("3d", "3D reconstruction, NeRF & Gaussians", "Vision", ["3d reconstruction", "nerf", "neural radiance", "gaussian splatting", "radiance field", "mesh", "multi-view stereo",
                                                             "novel view", "view synthesis", "surface reconstruction", "3d"]),
    ("depth", "Depth, stereo & point clouds", "Vision", ["depth", "stereo", "point cloud", "lidar", "range image"]),
    ("pose", "Pose, tracking & motion", "Vision", ["pose estimation", "tracking", "optical flow", "scene flow", "motion estimation", "keypoint", "6d pose", "6-dof"]),
    ("video", "Video understanding", "Vision", ["video", "action recognition", "temporal action", "spatio-temporal", "spatiotemporal"]),
    ("imgen", "Image & video generation", "Vision", ["text-to-image", "image generation", "image synthesis", "image editing", "super-resolution", "inpainting",
                                                    "text-to-video", "video generation", "style transfer"]),
    ("human", "Humans, faces & bodies", "Vision", ["face", "facial", "human pose", "human body", "hand pose", "person re-identification", "re-identification", "gesture",
                                                  "human motion", "avatar"]),
]
assert len(TOPICS) <= 30  # topic bits must fit a 31-bit integer in JavaScript
STEMS = ("prosthe", "endoscop", "colonoscop")
ENTITY = re.compile(r"&([A-Za-z][A-Za-z0-9]*);")
KEEP = {"amp", "lt", "gt", "quot", "apos"}


def unentity(text):
    return ENTITY.sub(lambda m: m.group(0) if m.group(1) in KEEP else chr(html.entities.name2codepoint.get(m.group(1), 63)), text)


def pattern(word):
    tail = r"" if word in STEMS else r"(?:s|es)?(?![a-z0-9])"
    return re.compile(r"(?<![a-z0-9])" + re.escape(word) + tail)


TOPIC_RX = sorted(((pattern(w), i, len(w)) for i, (_, _, _, words) in enumerate(TOPICS) for w in words), key=lambda x: -x[2])


def topics_of(title):
    text, bits = title.lower(), 0
    for rx, i, _ in TOPIC_RX:
        if rx.search(text):
            bits |= 1 << i
            text = rx.sub(lambda m: "#" * len(m.group(0)), text)
    return bits


PLACEHOLDER = re.compile(r"\[inline-graphic not available: see fulltext\]")  # dblp's stand-in for a logo in a title


def tidy(t):
    t = re.sub(r"\s+", " ", PLACEHOLDER.sub(" ", t)).strip()
    t = re.sub(r"\s*-?\s+:", ":", t)  # "AdaThinking- : One-Token ..." -> "AdaThinking: One-Token ..."
    return re.sub(r"^[:;,.\s]+", "", t)  # a title cannot start with punctuation left by a dropped symbol


def clean_title(el):
    t = tidy("".join(el.itertext()))
    return t[:-1] if t.endswith(".") and not t.endswith("..") else t


def clean_author(name):
    return re.sub(r"\s+\d{4}$", "", name.strip())  # dblp homonym numbers ("Wei Wang 0001")


CODES = [("~n/", "http://papers.nips.cc/paper_files/paper/"), ("~N/", "https://proceedings.neurips.cc/paper_files/paper/"),
         ("~M/", "https://proceedings.neurips.cc/paper/"), ("~i/", "https://proceedings.iclr.cc/paper_files/paper/"),
         ("~c/", "https://openaccess.thecvf.com/content/"), ("~p/", "https://proceedings.mlr.press/"), ("~q/", "http://proceedings.mlr.press/"),
         ("~o/", "https://openreview.net/forum?id="), ("~d/", "https://dblp.org/rec/"),
         ("~AC", "-Abstract-Conference.html"), ("~AD", "-Abstract-Datasets_and_Benchmarks.html"), ("~Ab", "-Abstract.html"), ("~ph", "_paper.html")]


def shorten(url):
    for code, text in CODES:
        url = url.replace(text, code)
    return url


def link_of(rec):
    links = [e.text.strip() for e in rec.findall("ee") if e.text]
    doi = next((u for u in links if "doi.org/" in u), None)
    url = doi or (links[0] if links else "https://dblp.org/rec/" + rec.get("key"))
    return url.split("doi.org/", 1)[1] if doi else shorten(url)  # bare DOI saves space; the page adds https://doi.org/


def records(path):
    """Yield (key, xml text) for records of the chosen venues, scanning the dump line by line.
    One line can close a record and open the next ("</inproceedings><inproceedings ..."), so such lines are split first."""
    prefixes = tuple(v[4] for v in VENUES)
    start = re.compile(r'^<(article|inproceedings) [^>]*key="([^"]+)"')
    boundary = re.compile(r"(</(?:article|inproceedings|proceedings|book|incollection|phdthesis|mastersthesis|www|person|data)>)(?=<)")
    buf, tag, key = None, None, None
    with gzip.open(path, "rt", encoding="iso-8859-1") as f:
        for raw in f:
            for line in (boundary.sub(r"\1\n", raw).splitlines(True) if "><" in raw else (raw,)):
                if buf is None:
                    m = start.match(line)
                    if not (m and m.group(2).startswith(prefixes)):
                        continue
                    tag, key, buf = m.group(1), m.group(2), [line]
                else:
                    buf.append(line)
                if f"</{tag}>" in line:
                    yield key, "".join(buf)
                    buf = None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    venue_of = {v[4]: v for v in VENUES}
    papers = defaultdict(list)
    seen_venue_strings = defaultdict(Counter)
    for key, text in records(Path(sys.argv[1])):
        v = venue_of[next(p for p in venue_of if key.startswith(p))]
        rec = ET.fromstring(unentity(text))
        if rec.get("publtype"):  # informal, withdrawn, etc.
            continue
        where = (rec.findtext("booktitle") or rec.findtext("journal") or "").strip()
        year = int(rec.findtext("year") or 0)
        title_el = rec.find("title")
        if year not in YEARS or title_el is None:
            continue
        if not v[5](where):
            seen_venue_strings[v[0]][f"{where} [{year}]"] += 1
            continue
        title = clean_title(title_el)
        authors = [clean_author(a.text or "") for a in rec.findall("author")]
        if not title or not authors or title.lower() in ("preface", "editorial", "front matter", "message from the general chairs"):
            continue
        papers[v[0]].append((title, authors, year, link_of(rec)))
    for vid, c in seen_venue_strings.items():
        print(vid, "left out:", c.most_common(8))
    OUT.mkdir(parents=True, exist_ok=True)
    meta, total, tagged, topic_count = [], 0, 0, Counter()
    for vid, field, short, name, _, _ in VENUES:
        rows = sorted(papers[vid], key=lambda r: (-r[2], r[0].lower()))
        cols = {"t": [], "a": [], "y": [], "l": [], "g": []}
        for title, authors, year, link in rows:
            bits = topics_of(title)
            cols["t"].append(title)
            cols["a"].append(", ".join(authors[:8]) + (f", +{len(authors) - 8}" if len(authors) > 8 else ""))
            cols["y"].append(year)
            cols["l"].append(link)
            cols["g"].append(bits)
            tagged += bits != 0
            for i in range(len(TOPICS)):
                if bits >> i & 1:
                    topic_count[i] += 1
        (OUT / f"{vid}.json").write_text(json.dumps({"v": vid, **cols}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        by_year = Counter(cols["y"])
        meta.append({"id": vid, "field": field, "short": short, "name": name, "count": len(rows), "years": {str(y): by_year[y] for y in sorted(by_year)}})
        total += len(rows)
        print(f"{short:13} {len(rows):6}  " + " ".join(f"{y}:{by_year[y]}" for y in YEARS))
    index = {"generated": date.today().isoformat(), "source": "dblp XML dump (CC0)", "total": total, "tagged": tagged, "codes": CODES,
             "years": [YEARS[0], YEARS[-1]], "fields": [{"id": f, "name": n} for f, n in FIELDS], "venues": meta,
             "topics": [{"id": t[0], "name": t[1], "group": t[2], "count": topic_count[i]} for i, t in enumerate(TOPICS)]}
    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print("total", total, "papers; with at least one topic:", tagged, f"({round(100 * tagged / max(total, 1))}%)")


if __name__ == "__main__":
    main()
