#!/usr/bin/env python3
import json, pathlib, re, collections, plotly.graph_objects as go

ROOT   = pathlib.Path(__file__).resolve().parent          # data_nick/
OUTDIR = ROOT / "charts"
OUTDIR.mkdir(exist_ok=True)

PORT_RE = re.compile(r"eol_(\d+)\.json", re.I)            # capture 80, 443, …

totals = collections.Counter()   # port → hosts with label
eols   = collections.Counter()   # port → hosts labelled EoL

def process_file(f: pathlib.Path, port: str):
    try:
        data = json.load(f.open(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"✗ {f} unreadable → skipped")
        return
    totals[port] += len(data)
    eols[port]   += sum(1 for row in data if row.get("is_eol") is True)

def main():
    # 1. walk AS*/eol_*.json
    for json_file in ROOT.glob("AS*/eol_*.json"):
        m = PORT_RE.match(json_file.name)
        if m:
            process_file(json_file, m.group(1))

    if not totals:
        print("No eol_*.json files found.")
        return

    # 2. prepare stacked-bar data
    ports = sorted(totals, key=int)
    non_eol = [totals[p] - eols[p] for p in ports]
    eol     = [eols[p]                 for p in ports]

    fig = go.Figure([
        go.Bar(name="Non-EoL", x=ports, y=non_eol, marker_color="#6c6cff"),
        go.Bar(name="EoL",     x=ports, y=eol,     marker_color="#ff4d4d")
    ])
    fig.update_layout(
        barmode="stack",
        title="",
        xaxis_title="Port",
        yaxis_title="Number of labelled hosts",
        width=900, height=500,
        legend=dict(x=0.82, y=0.95)
    )

    out_path = OUTDIR / "stacked_ports.png"
    fig.write_image(out_path, engine="kaleido")
    print(f"✓ wrote {out_path.relative_to(ROOT)}   "
          f"(ports: {', '.join(ports)})")

if __name__ == "__main__":
    main()
