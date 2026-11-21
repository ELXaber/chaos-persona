"""One-off: record the median residual norm of every layer so exports can skip the slow transformers pass.

Run it from the neuron-steering checkout (the folder is neuron-steering, the Python package inside it is
neuron_steering with an underscore):

    cd C:\\neuron-steering
    uv run python C:\\CAIOS\\skills\\model_editor\\record_norms.py [--model Qwen/Qwen3.5-4B] [--layers 32] [-o out.json]

Running a script by path puts the SCRIPT's folder on sys.path, not the current folder, so this file adds the
checkout itself (the current folder, or --repo) before importing neuron_steering.

Default output: <Project_Andrew>/working/model_edits/resid_norms.json (apply.py reads it automatically;
or point CAIOS_EDIT_RESID_NORMS at the file). Uses ncvec.build, the same function the export uses.
It loads the model through transformers by itself: neither llama-server nor the GUI server needs to be running,
and it is kinder to your VRAM if they are stopped.
"""
import argparse
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3.5-4B")
    ap.add_argument("--layers", type=int, default=32)
    ap.add_argument("--repo", default=os.getcwd(), help="the neuron-steering checkout (default: current folder)")
    here = os.path.dirname(os.path.abspath(__file__))
    default_out = os.path.normpath(os.path.join(here, "..", "..", "working", "model_edits", "resid_norms.json"))
    ap.add_argument("-o", "--out", default=default_out)
    a = ap.parse_args()

    repo = os.path.abspath(a.repo)
    if not os.path.isdir(os.path.join(repo, "neuron_steering")):
        sys.exit(f"No neuron_steering package in {repo}. cd into the neuron-steering checkout or pass --repo.")
    sys.path.insert(0, repo)
    from neuron_steering import ncvec   # noqa: E402  (import after the path fix)

    layer_ids = range(1, a.layers)   # llama.cpp control vectors cannot steer layer 0
    pushes = [ncvec.parse_push(f"{l}:0:1") for l in layer_ids]   # neuron 0 is only a placeholder
    _, norms = ncvec.build(a.model, pushes)
    data = {str(l): float(norms[l]) for l in layer_ids}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print(f"wrote {len(data)} layer norms to {a.out}")


if __name__ == "__main__":
    main()
