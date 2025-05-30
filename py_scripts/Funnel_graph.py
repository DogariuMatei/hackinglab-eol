import csv
import json
import plotly.graph_objects as go
def main():
    # 1. This is the output file from a zmap scan
    with open("output_AS20857_19may_80.csv", newline='', encoding='utf-8') as csvfile:
        zmap_hits = sum(1 for _ in csvfile)  # Number of lines

    # This one is the ip + version file
    with open("clean_versions_with_ip_AS20857_80_19may.json", encoding='utf-8') as f:
        versions_data = json.load(f)
        num_versions = len(versions_data)

    # This one is the success eol check file
    with open("AS20857_80_19may_success_1.json", encoding='utf-8') as f:
        meaningful_versions_data = json.load(f)
        num_meaningful_versions = len(meaningful_versions_data)
        num_eol_hosts = sum(1 for entry in meaningful_versions_data if entry.get("is_eol") is True)

    # Prepare data for funnel
    labels = [
        "Responses port 80",
        "With version",
        "Meaningful versions",
        "EOL hosts"
    ]


    values = [
        zmap_hits,
        num_versions,
        num_meaningful_versions,
        num_eol_hosts
    ]

    # Make the funnel
    fig = go.Figure(go.Funnel(
        y = labels,
        x = values,
        textinfo="value",
        marker=dict(color="#6c6cff"),
        opacity=0.7
    ))

    fig.update_layout(
        font=dict(family="Arial", size=24, color="#2c3e50"),
        plot_bgcolor="#e9eef6",
        paper_bgcolor="white",
        margin=dict(l=50, r=50, t=20, b=20),
        width=700, height=350
    )

    fig.show()


if __name__ == "__main__":
    main()