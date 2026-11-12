#!/usr/bin/env python3
"""Research trends for each venue of the Paper Explorer: trends/data.json, read by assets/trends.js.

From explorer/data (dblp titles, years and topic bits), per venue: papers per year, papers per topic per year, and the title
terms whose share of papers rose or fell most between two windows: the last two editions in dblp ("recent") and the last
two editions at least four years before them ("earlier"). Terms are single words and two-word phrases of titles, with
plurals folded and function words removed.

Run after scripts/make_paper_explorer.py:  python3 scripts/make_conference_trends.py   (then python3 scripts/build_site.py)
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "explorer" / "data"
OUT = ROOT / "trends" / "data.json"

KIND = {"icra": "conference", "iros": "conference", "rss": "conference", "corl": "conference", "cvpr": "conference", "iccv": "conference",
        "eccv": "conference", "neurips": "conference", "icml": "conference", "iclr": "conference",
        "ral": "journal", "tro": "journal", "ijrr": "journal", "scirob": "journal"}
SITE = {"icra": "https://www.ieee-ras.org/conferences-workshops/fully-sponsored/icra", "iros": "https://www.ieee-ras.org/conferences-workshops/financially-co-sponsored/iros",
        "rss": "https://roboticsconference.org/", "corl": "https://www.corl.org/", "cvpr": "https://cvpr.thecvf.com/",
        "iccv": "https://iccv.thecvf.com/", "eccv": "https://www.ecva.net/", "neurips": "https://neurips.cc/", "icml": "https://icml.cc/",
        "iclr": "https://iclr.cc/", "ral": "https://www.ieee-ras.org/publications/ra-l", "tro": "https://www.ieee-ras.org/publications/t-ro",
        "ijrr": "https://journals.sagepub.com/home/ijr", "scirob": "https://www.science.org/journal/scirobotics"}

# function words break phrases; generic words may sit inside a phrase ("language model") but are not reported alone
STOP = set("""a an the and or of for to in on at by with without from into onto over under via using use uses based toward towards
through across between within beyond against about as is are be been being can could do does not no its it this that these those
their our we you vs versus than then when where which what how why who whose more most less least very much many few one two three
all any each every both either neither other such same own up down out off only also just yet still even while if so else whether
per de la le et new novel study case paper part ii iii iv""".split())
GENERIC = set("""model learning network method approach framework system data task problem robot robotic robotics image object
analysis application performance improving improved efficient effective large scale towards toward via deep neural based
multi high low real time using general generalized simple fast better good""".split())
# words that describe a paper's format or style rather than its topic ("Position: ...", "Demonstrating ...", "Enhancing ...")
FORMAT = set("""position demonstrating enhancing leveraging unleashing rethinking revisiting exploring empowering boosting unlocking
harnessing advancing""".split())
FOLD = {"llms": "llm", "vlms": "vlm", "vlas": "vla", "nerfs": "nerf", "gaussians": "gaussian", "policies": "policy", "strategies": "strategy",
        "dynamics": "dynamics", "kinematics": "kinematics", "robotics": "robotics", "physics": "physics", "graphics": "graphics",
        "lidar": "lidar", "lidars": "lidar", "data": "data"}
TOKEN = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*")


def norm(word):
    w = word.lower().replace("'", "")
    if w in FOLD:
        return FOLD[w]
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("s") and not w.endswith(("ss", "us", "is", "ics", "ous")):
        return w[:-1]
    return w


def terms(title):
    """The set of terms of one title: kept words, and two-word phrases of adjacent kept words; with their surface forms."""
    raw = TOKEN.findall(title.lower())
    surface = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", title)
    out, forms = set(), {}
    keep = [None if (w in STOP or w in FORMAT or len(w) < 2 or w.isdigit()) else norm(w) for w in raw]
    for i, k in enumerate(keep):
        if k is None:
            continue
        if k not in GENERIC:
            out.add(k); forms[k] = surface[i] if i < len(surface) else k
        if i + 1 < len(keep) and keep[i + 1] is not None and not (k in GENERIC and keep[i + 1] in GENERIC):
            p = k + " " + keep[i + 1]
            out.add(p); forms[p] = " ".join(surface[i:i + 2]) if i + 1 < len(surface) else p
    return out, forms


def display(forms):
    """Lower case, unless the usual spelling has inner capitals or is an acronym (NeRF, LiDAR, LLM, 3D)."""
    word = forms.most_common(1)[0][0]
    return " ".join(w if (re.search(r"[A-Z].*[A-Z]", w) or re.search(r"\d", w)) else w.lower() for w in word.split())


def windows(years):
    recent = years[-2:]
    early = [y for y in years if y <= recent[0] - 4][-2:]
    return (early if len(early) == 2 else years[:2]), recent


def main():
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    topics = [{"id": t["id"], "name": t["name"], "group": t["group"]} for t in index["topics"]]
    out = []
    for v in index["venues"]:
        d = json.loads((DATA / f'{v["id"]}.json').read_text(encoding="utf-8"))
        years = sorted(set(d["y"]))
        per_year, topic_year = Counter(d["y"]), defaultdict(Counter)
        term_year, form = defaultdict(Counter), defaultdict(Counter)
        for t, y, g in zip(d["t"], d["y"], d["g"]):
            for i in range(len(topics)):
                if g >> i & 1:
                    topic_year[i][y] += 1
            ts, forms = terms(t)
            for k in ts:
                term_year[k][y] += 1
                form[k][forms[k]] += 1
        early, recent = windows(years)
        nE, nR = sum(per_year[y] for y in early), sum(per_year[y] for y in recent)

        def shares(k):
            return sum(term_year[k][y] for y in early) / nE, sum(term_year[k][y] for y in recent) / nR

        def pick(rising, n):
            floor = max(8, 0.004 * (nR if rising else nE))
            cand = []
            for k, c in term_year.items():
                cr, ce = sum(c[y] for y in recent), sum(c[y] for y in early)
                if (cr if rising else ce) < floor:
                    continue
                e, r = shares(k)
                cand.append(((r - e) if rising else (e - r), k))
            cand.sort(reverse=True)
            win = recent if rising else early
            count = lambda k: sum(term_year[k][y] for y in win)
            phrases = defaultdict(list)  # word -> the phrases that contain it
            for k in term_year:
                if " " in k:
                    for w in k.split():
                        phrases[w].append(k)
            chosen = []
            for score, k in cand:
                if score <= 0 or len(chosen) >= n:
                    break
                if " " not in k:  # report the phrase instead of the word when the phrase covers most of its uses
                    best = max(phrases.get(k, []), key=count, default=None)
                    if best and count(best) >= 0.6 * count(k) and best not in chosen:
                        e, r = shares(best)
                        if (r - e if rising else e - r) > 0:
                            k = best
                # skip a word or phrase that mostly repeats one already chosen ("splatting" after "gaussian splatting")
                ck = count(k)
                if any((k in c.split() or c in k.split() or set(k.split()) & set(c.split())) and
                       sum(term_year[c][y] for y in win) >= 0.6 * ck for c in chosen):
                    continue
                chosen.append(k)
            return [{"t": display(form[k]), "k": k, "e": round(shares(k)[0], 4), "r": round(shares(k)[1], 4),
                     "c": [term_year[k][y] for y in years]} for k in chosen]

        partial = KIND[v["id"]] == "journal" and years[-1] == int(index["generated"][:4])  # this year's volume is still growing
        out.append({"id": v["id"], "short": v["short"], "name": v["name"], "field": v["field"], "kind": KIND[v["id"]], "site": SITE[v["id"]], "partial": partial,
                    "years": years, "n": [per_year[y] for y in years],
                    "topics": [[topic_year[i][y] for y in years] for i in range(len(topics))],
                    "early": early, "recent": recent, "rising": pick(True, 12), "falling": pick(False, 8)})
        print(f'{v["short"]:13} {years[0]}-{years[-1]} early {early} recent {recent} | up: ' +
              ", ".join(f'{x["t"]} {100 * x["e"]:.1f}->{100 * x["r"]:.1f}' for x in out[-1]["rising"][:7]) +
              " | down: " + ", ".join(f'{x["t"]} {100 * x["e"]:.1f}->{100 * x["r"]:.1f}' for x in out[-1]["falling"][:5]))
    data = {"generated": index["generated"], "source": index.get("source", "dblp"), "topics": topics, "fields": index["fields"], "venues": out}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(OUT, f"{OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
