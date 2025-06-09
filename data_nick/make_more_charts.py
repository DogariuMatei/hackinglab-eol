#!/usr/bin/env python3
import json, pathlib, re, collections, plotly.graph_objects as go
from collections import Counter, defaultdict

# ----------  palette ----------
CLR_EOL      = "#ff6c6c"
CLR_NON_EOL  = "#6c6cff"
CLR_BG       = "#e9eef6"
CLR_TEXT     = "#2c3e50"
FONT_FAMILY  = "Arial"

# ----------  paths ----------
ROOT   = pathlib.Path(__file__).resolve().parent       # data_nick/
OUTDIR = ROOT / "charts"
OUTDIR.mkdir(exist_ok=True)

PORT_RE = re.compile(r"eol_(\d+)\.json", re.I)
ASN_RE  = re.compile(r"(AS\d+)", re.I)

# ----------  accumulators ----------
totals_per_port   = Counter()
eols_per_port     = Counter()
totals_per_asn    = Counter()
eols_per_asn      = Counter()
product_counter   = Counter()
product_eol       = Counter()
heatmap           = defaultdict(dict)  # asn → port → (eol,total)

def process_file(f: pathlib.Path):
    m_port = PORT_RE.match(f.name)
    m_asn  = ASN_RE.search(str(f.parent))
    if not (m_port and m_asn):
        return
    port, asn = m_port.group(1), m_asn.group(1)

    data   = json.load(f.open(encoding="utf-8"))
    totals = len(data)
    eols   = sum(1 for row in data if row.get("is_eol"))

    totals_per_port[port] += totals
    eols_per_port[port]   += eols
    totals_per_asn[asn]   += totals
    eols_per_asn[asn]     += eols
    prev_e, prev_t = heatmap[asn].get(port, (0, 0))
    heatmap[asn][port] = (prev_e + eols, prev_t + totals)

    for row in data:
        prod = row.get("server", "unknown").split("/")[0].strip()
        product_counter[prod] += 1
        if row.get("is_eol"):
            product_eol[prod] += 1

for f in ROOT.glob("AS*/eol_*.json"):
    process_file(f)

# ----------  helper: apply uniform layout ----------
def save(fig: go.Figure, filename: str, w=900, h=500):
    fig.update_layout(
        font=dict(family=FONT_FAMILY, size=14, color=CLR_TEXT),
        plot_bgcolor=CLR_BG,
        paper_bgcolor="white",
        margin=dict(l=60, r=40, t=60, b=60),
        width=w, height=h
    )
    fig.write_image(OUTDIR / filename, engine="kaleido")

# ---------- 1  Pie overall ----------
overall_total = sum(totals_per_port.values())
overall_eol   = sum(eols_per_port.values())
overall_live  = overall_total - overall_eol
fig = go.Figure(go.Pie(
        labels = ["EoL", "Non-EoL"],
        values = [overall_eol, overall_live],
        marker = dict(colors=[CLR_EOL, CLR_NON_EOL]),
        textinfo = "value+percent"
))
fig.update_layout(title="Overall share of End-of-Life hosts")
save(fig, "pie_overall.png", w=520, h=520)

# ---------- 2  Bar: total hits per port ----------
ports_sorted = sorted(totals_per_port, key=int)
fig = go.Figure(go.Bar(
        x=ports_sorted,
        y=[totals_per_port[p] for p in ports_sorted],
        marker_color=CLR_NON_EOL
))
fig.update_layout(title="Total responsive hosts per port",
                  xaxis_title="Port", yaxis_title="Hosts")
save(fig, "bar_total_per_port.png")

# ---------- 3  Bar: EoL percent per ASN ----------
asns_sorted = sorted(totals_per_asn,
                     key=lambda k: -eols_per_asn[k]/totals_per_asn[k])
eol_percent = [eols_per_asn[a]/totals_per_asn[a]*100 for a in asns_sorted]
fig = go.Figure(go.Bar(x=asns_sorted, y=eol_percent, marker_color=CLR_EOL))
fig.update_layout(title="EoL percentage per ASN",
                  xaxis_title="ASN", yaxis_title="EoL %")
save(fig, "bar_eol_percent_per_asn.png")

# ---------- 4  Heat-map ASN × port ----------
asn_list  = sorted(heatmap)
port_list = sorted({p for d in heatmap.values() for p in d}, key=int)
z = []
for a in asn_list:
    row = []
    for p in port_list:
        eol, total = heatmap[a].get(p, (0,0))
        row.append((eol/total)*100 if total else None)
    z.append(row)
fig = go.Figure(go.Heatmap(
        z=z, x=port_list, y=asn_list,
        colorscale=[ [0, CLR_BG], [1, CLR_EOL] ],
        colorbar_title="EoL %"
))
fig.update_layout(title="EoL percentage heat-map (ASN × port)",
                  xaxis_title="Port", yaxis_title="ASN")
save(fig, "heatmap_asn_port.png", h=600)

# ---------- 5  Top-10 products ----------
top10         = [prod for prod,_ in product_counter.most_common(10)]
non_eol_vals  = [product_counter[p]-product_eol[p] for p in top10]
eol_vals      = [product_eol[p]                     for p in top10]
fig = go.Figure([
    go.Bar(name="Non-EoL", y=top10, x=non_eol_vals, orientation="h",
           marker_color=CLR_NON_EOL),
    go.Bar(name="EoL",     y=top10, x=eol_vals,     orientation="h",
           marker_color=CLR_EOL)
])
fig.update_layout(barmode="stack",
                  title="Top-10 server products (all scans)",
                  xaxis_title="Hosts", yaxis_title="Product")
save(fig, "bar_top_products.png", h=600)

print("✓ pretty charts written to", OUTDIR.relative_to(ROOT.parent))
