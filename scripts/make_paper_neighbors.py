#!/usr/bin/env python3
"""Similar papers for the Paper Explorer: the 10 nearest papers of every paper, by title meaning.

Titles are embedded with SPECTER (sentence-transformers/allenai-specter, Apache-2.0), a model trained on citations to place
related papers close together; neighbours are the highest cosine similarities over all venues.
Output: explorer/data/nn/<venue>.bin, 10 neighbours x 4 bytes per paper, in the order of explorer/data/<venue>.json:
3 bytes global paper index (venues in index.json order) + 1 byte similarity (0-255 for cosine 0-1).

Needs torch and transformers (a GPU makes it take about a minute):
    HF_HOME=/tmp/hf python scripts/make_paper_neighbors.py      (after scripts/make_paper_explorer.py)
"""
import json
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "explorer" / "data"
MODEL = "sentence-transformers/allenai-specter"
K = 10


def main():
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    titles, counts = [], []
    for v in index["venues"]:
        d = json.loads((DATA / f'{v["id"]}.json').read_text(encoding="utf-8"))
        assert len(d["t"]) == v["count"], v["id"]
        titles += d["t"]
        counts.append(len(d["t"]))
    n = len(titles)
    assert n < 2 ** 24
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModel.from_pretrained(MODEL).to(dev).eval()
    if dev == "cuda":
        model = model.half()
    t0 = time.time()
    emb = torch.empty((n, model.config.hidden_size), dtype=torch.float16 if dev == "cuda" else torch.float32, device=dev)
    order = sorted(range(n), key=lambda i: len(titles[i]))  # similar lengths per batch: less padding
    with torch.no_grad():
        for s in range(0, n, 512):
            ids = order[s:s + 512]
            batch = tok([titles[i] for i in ids], padding=True, truncation=True, max_length=64, return_tensors="pt").to(dev)
            cls = model(**batch).last_hidden_state[:, 0]  # SPECTER uses the [CLS] vector
            emb[torch.tensor(ids, device=dev)] = torch.nn.functional.normalize(cls.float(), dim=1).to(emb.dtype)
    print(f"embedded {n} titles in {time.time() - t0:.0f} s on {dev}")
    t0 = time.time()
    nn_idx = np.empty((n, K), dtype=np.int64)
    nn_sim = np.empty((n, K), dtype=np.float32)
    with torch.no_grad():
        for s in range(0, n, 4096):
            sim = emb[s:s + 4096] @ emb.T
            sim[torch.arange(sim.shape[0], device=dev), torch.arange(s, s + sim.shape[0], device=dev)] = -2  # not itself
            val, idx = sim.float().topk(K, dim=1)
            nn_idx[s:s + sim.shape[0]] = idx.cpu().numpy()
            nn_sim[s:s + sim.shape[0]] = val.cpu().numpy()
    print(f"neighbours in {time.time() - t0:.0f} s; median similarity of the 1st / 10th neighbour: "
          f"{np.median(nn_sim[:, 0]):.3f} / {np.median(nn_sim[:, -1]):.3f}")
    rec = np.zeros((n, K, 4), dtype=np.uint8)
    rec[:, :, 0] = nn_idx & 255
    rec[:, :, 1] = (nn_idx >> 8) & 255
    rec[:, :, 2] = (nn_idx >> 16) & 255
    rec[:, :, 3] = np.clip(np.round(nn_sim * 255), 0, 255)
    out = DATA / "nn"
    out.mkdir(exist_ok=True)
    start = 0
    for v, c in zip(index["venues"], counts):
        (out / f'{v["id"]}.bin').write_bytes(rec[start:start + c].tobytes())
        start += c
    index["neighbors"] = {"k": K, "model": MODEL, "bytes": 4}
    (DATA / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    for i in (0, n // 3, 2 * n // 3):  # a few examples to eyeball
        print("\n" + titles[i])
        for j, sv in zip(nn_idx[i][:4], nn_sim[i][:4]):
            print(f"   {sv:.3f}  {titles[j][:110]}")


if __name__ == "__main__":
    main()
