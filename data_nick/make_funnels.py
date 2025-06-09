#!/usr/bin/env python3
import json, pathlib, re, collections, plotly.graph_objects as go

# ------------ palette ------------
CLR_EOL      = "#ff6c6c"
CLR_NON_EOL  = "#6c6cff"
CLR_BG       = "#e9eef6"
CLR_TEXT     = "#2c3e50"
FONT_FAMILY  = "Arial"

# ------------ paths --------------
ROOT   = pathlib.Path(__file__).resolve().parent        # data_nick/
OUTDIR = ROOT / "charts"
OUTDIR.mkdir(exist_ok=True)

PORT_RE = re.compile(r"eol_(\d+)\.json", re.I)

totals = collections.Counter()     # port → hosts labelled
eols   = collections.Counter()     # port → hosts EoL-true

def process_file(f: pathlib.Path, port: str):
    try:
        data = json.load(f.open(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"✗ {f} unreadable → skipped")
        return
    totals[port] += len(data)
    eols[port]   += sum(1 for row in data if row.get("is_eol"))

# -------- walk every eol_*.json ----------
for json_file in ROOT.glob("AS*/eol_*.json"):
    m = PORT_RE.match(json_file.name)
    if m:
        process_file(json_file, m.group(1))

if not totals:
    print("No eol_*.json files found.")
    exit()

# -------- build stacked-bar data ---------
ports   = sorted(totals, key=int)
non_eol = [totals[p] - eols[p] for p in ports]
eol     = [eols[p]             for p in ports]

fig = go.Figure([
    go.Bar(name="Non-EoL", x=ports, y=non_eol, marker_color=CLR_NON_EOL),
    go.Bar(name="EoL",     x=ports, y=eol,     marker_color=CLR_EOL)
])
fig.update_layout(
    barmode="stack",
    title="EoL vs Non-EoL hosts per port",
    xaxis_title="Port",
    yaxis_title="Number of labelled hosts",
    font=dict(family=FONT_FAMILY, size=14, color=CLR_TEXT),
    plot_bgcolor=CLR_BG,
    paper_bgcolor="white",
    width=900, height=500,
    margin=dict(l=60, r=40, t=60, b=60),
    legend=dict(x=0.82, y=0.95)
)

out_path = OUTDIR / "stacked_ports.png"
fig.write_image(out_path, engine="kaleido")
print(f"✓ wrote {out_path.relative_to(ROOT)}   (ports: {', '.join(ports)})")
