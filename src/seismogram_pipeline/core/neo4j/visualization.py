# src/seismogram_pipeline/core/neo4j/visualization.py

import os
import pickle
import numpy as np
from cmcrameri import cm
from collections import Counter
import matplotlib.colors as mcolors
from neo4j import RoutingControl
from neo4j_viz import Renderer
from neo4j_viz.neo4j import from_neo4j
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from .connector import get_driver

load_dotenv()

CACHE_FILE = "graph_cache.pkl"
FORCE_REFRESH = False  # Change to True to sync with database changes

def get_categorical_hex(
    cmap: mcolors.ListedColormap, labels: list[str], 
    start: float = 0.0, stop: float = 0.99
) -> dict[str, str]:
    """
    Samples evenly spaced hex colors from a Crameri categorical colormap.
    By setting the start value to be larger than the stop, it reverses the color order

    Parameters
    ----------
    cmap : matplotlib.colors.ListedColormap
        Input color map for nodes/relationships
    labels : list[str]
        Ordered node/relationship labels to apply the color map to
    start : float
        Left bound on color range
    stop : float
        Right bound on color range

    Returns
    -------
    dict[str, str] 
        Dictionary of labels and their corresponding hex values
    """
    positions = np.linspace(start, stop, len(labels))
    return {
        label: mcolors.to_hex(cmap(pos))
        for label, pos in zip(labels, positions)
    }

def inject_annotations_and_style(
    html_str: str, annotations: list[dict], legend_html: str
) -> str:
    """
    Creates a layer of annotations on top of the output graph html for display

    Parameters
    ----------
    html_str : str
        HTML page as a string
    annotations : list[dict]
        Annotations for the network-station and container-box clusters
    legend_html : str
        Custom legend html string

    Returns
    -------
    str
        Modified input HTML string with annotations
    """
    
    annotation_divs = "\n".join(
        f'<div class="cluster-label" style="top: {a["top"]}; left: {a["left"]};">{a["text"]}</div>'
        for a in annotations
    )

    custom_css_and_html = f"""
    <style>
        html, body {{
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            height: 100% !important;
            overflow: hidden !important;
            background: #f8f9fa !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        .custom-schema-legend {{
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 9500;
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid #e0e3e7;
            border-radius: 8px;
            padding: 12px 14px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            color: #1f2328;
            min-width: 245px;
        }}
        .schema-title {{
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #111111;
        }}
        .schema-section-header {{
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.05em;
            color: #57606a;
            margin-bottom: 4px;
        }}
        .schema-body {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
        }}
        .schema-nodes-col {{
            display: flex;
            flex-direction: column;
            padding-top: 16px;
        }}
        .schema-node-row {{
            height: 44px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 500;
        }}
        .schema-dot {{
            width: 11px;
            height: 11px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        .schema-label, .schema-rel-label {{
            color: #1f2328;
        }}
        .schema-count {{
            color: #57606a;
            font-weight: 400;
        }}
        .schema-wires-col {{
            margin-left: 6px;
            flex-shrink: 0;
            padding-top: 16px;
        }}
        .schema-rels-col {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        .schema-rel-row {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11.5px;
            font-weight: 500;
        }}
        .schema-line {{
            width: 14px;
            height: 3px;
            border-radius: 2px;
            flex-shrink: 0;
        }}
        .cluster-label {{
            position: absolute;
            z-index: 9999;
            font-size: 17px;
            font-weight: 600;
            color: #111111;
            text-align: center;
            line-height: 1.25;
            pointer-events: none;
            background: rgba(248, 249, 250, 0.85);
            padding: 3px 7px;
            border-radius: 4px;
        }}
    </style>
    {legend_html}
    {annotation_divs}
    """
    return html_str.replace("</body>", f"{custom_css_and_html}\n</body>")

def build_schema_legend_html(
    node_colors: dict[str, str], rel_colors: dict[str, str],
    node_counts: Counter, rel_counts: Counter,
) -> str:
    """
    Builds a custom legend html layer on top of the graph visualization.
    Contains a hierarchical relationship layout mapping the nodes to one another

    Parameters
    ----------
    node_colors : dict[str,str]
        Dictionary mapping of node types to hex colors
    rel_colors : dict[str,str]
        Dictionary mapping of relationship types to hex colors
    node_counts : Counter
        Total number of each type of node to display on the legend
    rel_counts : Counter
        Total number of each type of relationship to display on the legend

    Returns
    -------
    str
        Isolated legend html string
    """
    ordered_nodes = ["Network", "Container", "Box", "Station", "Channel"]
    ordered_rels = ["HAS_STATION", "CONTAINS", "CONTAINS_DATA_FOR", "HAS_CHANNEL"]

    # Vertical centers for each node inside the SVG
    row_y = {lbl: 22 + i * 44 for i, lbl in enumerate(ordered_nodes)}
    # X of the node circle centers in the SVG
    NODE_X = 18
    BRACKET_X = 96  # outer right track for the Network -> Station jump

    # Edge definitions: (rel_name, from_node, to_node, route)
    # route: "straight" = adjacent vertical, "bracket" = right side detour
    edges = [
        ("CONTAINS",            "Container", "Box",     "straight"),
        ("CONTAINS_DATA_FOR",   "Box",       "Station", "straight"),
        ("HAS_CHANNEL",         "Station",   "Channel", "straight"),
        ("HAS_STATION",         "Network",   "Station", "bracket")
    ]

    # Circle radius so arrow tips land on the perimeter, not the center
    R = 6

    def edge_path(rel:str, src:str, dst:str, route:str) -> str:
        color = rel_colors[rel]
        marker = f"url(#arrow-{rel})"
        ys, ye = row_y[src], row_y[dst]
        count = rel_counts.get(rel, 0)
        mid_y = (ys + ye) / 2

        if route == "straight":
            # start/end just outside the circles so the arrowhead is visible
            d = f"M {NODE_X} {ys + R} L {NODE_X} {ye - R}"
            label_x = NODE_X + 10
        else:
            # route out to BRACKET_X, down, then back into the Station circle
            d = (f"M {NODE_X + R} {ys} "
                 f"L {BRACKET_X} {ys} "
                 f"L {BRACKET_X} {ye} "
                 f"L {NODE_X + R} {ye}")
            label_x = BRACKET_X + 6

        return f"""
        <path d="{d}" fill="none" stroke="{color}" stroke-width="2.2"
              stroke-linejoin="round" marker-end="{marker}" />
        <text x="{label_x}" y="{mid_y + 3}" font-size="9" fill="#57606a"
              font-family="inherit">{count:,}</text>"""

    # Node circles drawn inside the svg so wires connect to them
    def node_circle(lbl:str) -> str:
        return f"""
        <circle cx="{NODE_X}" cy="{row_y[lbl]}" r="{R}" fill="{node_colors[lbl]}"
                stroke="#ffffff" stroke-width="1.5" />"""

    markers = "\n".join(f"""
        <marker id="arrow-{rel}" viewBox="0 0 10 10" refX="7" refY="5"
                markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="{rel_colors[rel]}" />
        </marker>""" for rel in ordered_rels)

    svg_height = row_y[ordered_nodes[-1]] + R + 4
    svg_wires = f"""
    <svg width="150" height="{svg_height}" viewBox="0 0 150 {svg_height}"
         style="overflow: visible;">
        <defs>{markers}</defs>
        {"".join(node_circle(lbl) for lbl in ordered_nodes)}
        {"".join(edge_path(rel, s, d, r) for rel, s, d, r in edges)}
    </svg>
    """

    # Left column: color key + counts (no wire alignment dependency)
    node_rows_html = ""
    for lbl in ordered_nodes:
        node_rows_html += f"""
        <div class="schema-node-row">
            <span class="schema-dot" style="background: {node_colors[lbl]};"></span>
            <span class="schema-label">{lbl} <span class="schema-count">({node_counts.get(lbl, 0):,})</span></span>
        </div>"""

    rel_rows_html = ""
    for rel in ordered_rels:
        rel_rows_html += f"""
        <div class="schema-rel-row">
            <span class="schema-line" style="background: {rel_colors[rel]};"></span>
            <span class="schema-rel-label">{rel} <span class="schema-count">({rel_counts.get(rel, 0):,})</span></span>
        </div>"""

    return f"""
    <div class="custom-schema-legend">
        <div class="schema-title">Schema &amp; Legend</div>
        <div class="schema-section-header">NODES &amp; HIERARCHY</div>
        <div class="schema-body">
            <div class="schema-nodes-col">{node_rows_html}</div>
            <div class="schema-wires-col">{svg_wires}</div>
        </div>
        <div class="schema-section-header" style="margin-top: 10px;">RELATIONSHIPS</div>
        <div class="schema-rels-col">{rel_rows_html}</div>
    </div>
    """

def export_html_to_png(
    html_path: str,
    png_path: str,
    closeup_png_path: str | None = None,
    width: int = 1280,
    height: int = 720,
) -> None:
    """
    
    """
    abs_html_path = f"file://{os.path.abspath(html_path)}"
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--enable-webgl", "--ignore-gpu-blocklist"])
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=2,
        )
        page.goto(abs_html_path)
        page.wait_for_timeout(3500)

        # Zoom out slightly and pan up so the bottom cluster isn't clipped in the full view
        page.mouse.move(width / 2, height / 2)
        page.mouse.wheel(0, 160)
        page.wait_for_timeout(300)
        page.mouse.down()
        page.mouse.move(width / 2, height / 2 - 35, steps=10)
        page.mouse.up()
        page.wait_for_timeout(300)

        # Hide every UI button, toolbar, and corner badge except the Legend
        page.evaluate("""
            () => {
                const isLegend = (el) => {
                    const cls = (el.className || '').toString().toLowerCase();
                    const txt = (el.innerText || '');
                    return cls.includes('legend') || txt.includes('NODES') || txt.includes('RELATIONSHIPS');
                };
                document.querySelectorAll('button, a, [role="toolbar"], [class*="toolbar" i], [class*="control" i], [class*="menu" i], [class*="badge" i], [class*="watermark" i]').forEach(el => {
                    if (!el.closest('[class*="legend" i]') && !isLegend(el)) {
                        el.style.display = 'none';
                    }
                });
                // Hide any tiny floating corner icon outside the legend
                document.querySelectorAll('div, span').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.width < 40 && rect.height > 0 && rect.height < 40 && rect.bottom > 680) {
                        el.style.display = 'none';
                    }
                });
            }
        """)
        page.wait_for_timeout(200)

        # Save the full overview PNG
        page.screenshot(path=png_path)

        # Zoom in on the Network & Hugo-Benioff clusters and save a cropped snapshot
        if closeup_png_path:
            # Hide only the full-view cluster labels
            page.evaluate("""
                () => {
                    document.querySelectorAll('.cluster-label').forEach(el => {
                        el.style.display = 'none';
                    });
                    // Align the legend neatly inside the top-right corner of the cropped region
                    document.querySelectorAll('.custom-schema-legend').forEach(el => {
                        el.style.top = '35px';
                        el.style.right = '20px';
                    });
                }
            """)

            # Zoom in toward the top-center region where CI Network & Hugo-Benioff sit
            focus_x, focus_y = width * 0.48, height * 0.25
            page.mouse.move(focus_x, focus_y)
            for _ in range(4):
                page.mouse.wheel(0, -140)
                page.wait_for_timeout(150)

            page.mouse.down()
            page.mouse.move(focus_x - 30, focus_y + 45, steps=10)
            page.mouse.up()
            page.wait_for_timeout(300)

            # Inject clean labels back in, positioned specifically for the zoomed-in crop
            page.evaluate("""
                () => {
                    const addLabel = (text, top, left) => {
                        const div = document.createElement('div');
                        div.className = 'cluster-label';
                        div.style.top = top;
                        div.style.left = left;
                        div.style.fontSize = '15px';
                        div.innerHTML = text;
                        document.body.appendChild(div);
                    };
                    addLabel('CI: Southern California<br>Seismic Network Cluster', '55px', '130px');
                    addLabel('Container Cluster:<br>Hugo-Benioff', '45px', '550px');
                }
            """)
            page.wait_for_timeout(200)

            page.screenshot(
                path=closeup_png_path,
                clip={
                    "x": 110,
                    "y": 20,
                    "width": 1170,
                    "height": 420,
                },
            )

        browser.close()

if __name__ == "__main__":
    # Check if refresh is needed or if cache is missing
    if not FORCE_REFRESH and os.path.exists(CACHE_FILE):
        print(f"Loading graph from local cache ({CACHE_FILE})...")
        with open(CACHE_FILE, "rb") as f:
            VG = pickle.load(f)
    else:
        driver = get_driver()
        print("Testing connection...")
        driver.verify_connectivity()
        print("Connected successfully!")

        query = """
        MATCH (n)-[r]->(m)
        RETURN n,r,m
        """

        print("Fetching full graph from AuraDB...")
        result = driver.execute_query(query, routing_=RoutingControl.READ)

        print("Building visualization graph...")
        VG = from_neo4j(result)

        # Save to cache
        print(f"Saving graph cache to {CACHE_FILE}...")
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(VG, f)

    print("Configuring layout and styling...")
    pinned_nodes = {}
    node_sizes = {}
    initial_positions = {}

    # Define positions for the containers
    CONTAINER_POSITIONS = {
        "Hugo-Benioff": (220.0, -280.0),
        "Harry-Wood": (560.0, 40.0),
        "Beno-Gutenberg": (100.0, 220.0),
        "Charles-Richter": (-420.0, 220.0),
    }

    # Apply positioning and styling to the nodes
    for node in VG.nodes:
        props = node.properties or {}
        if "networkCode" in props:
            node.caption = "Network"
            pinned_nodes[node.id] = True
            node_sizes[node.id] = 10
            initial_positions[node.id] = (-350.0, -250.0)
            print(f"Positioned Network {node.id} -> {initial_positions[node.id]}")
        elif "box_range" in props or "num_missing" in props:
            node.caption = "Container"
            pinned_nodes[node.id] = True
            node_sizes[node.id] = 10
            all_vals = " ".join(str(v) for v in props.values())
            matched = False
            for key, pos in CONTAINER_POSITIONS.items():
                if key in all_vals:
                    initial_positions[node.id] = pos
                    print(f"Positioned Container '{key}' ({node.id}) -> {pos}")
                    matched = True
                    break
            if not matched:
                print(f"WARNING: Unmatched Container properties: {props}")
        elif "stationCode" in props:
            node.caption = "Station"
            pinned_nodes[node.id] = False
        elif "boxNum" in props:
            node.caption = "Box"
            pinned_nodes[node.id] = False
        else:
            node.caption = "Channel"
            pinned_nodes[node.id] = False

    if hasattr(VG, "set_node_positions"):
        VG.set_node_positions(initial_positions)
    else:
        for node in VG.nodes:
            if node.id in initial_positions:
                node.x, node.y = initial_positions[node.id]

    VG.toggle_nodes_pinned(pinned_nodes)

    # Resizing
    relationship_widths = {
        # Puts stronger emphasis on the relationship between Box->Station
        rel.id: (5 if rel.caption == "CONTAINS_DATA_FOR" else 3)
        for rel in VG.relationships
    }
    
    VG.resize_nodes(sizes=node_sizes)
    VG.resize_relationships(widths=relationship_widths)

    # Collect counts of each node & relationship type for the legend
    node_counts = Counter(node.caption for node in VG.nodes)
    rel_counts = Counter(rel.caption for rel in VG.relationships)

    # Define separate order for color mapping with decent color contrast
    node_labels = ["Container", "Station", "Network", "Channel", "Box"]
    rel_labels = ["CONTAINS", "HAS_CHANNEL", "CONTAINS_DATA_FOR", "HAS_STATION"]

    # Get color mappings for the nodes & relationships
    node_colors = get_categorical_hex(
        cm.batlow, node_labels, start=0.05, stop=0.78
    )
    rel_colors = get_categorical_hex(
        cm.roma, rel_labels, start=0.9, stop=0.1
    )

    VG.color_nodes(field="caption", colors=node_colors)
    VG.color_relationships(field="caption", colors=rel_colors)

    VG.show_legend(visible=False)

    print("Rendering visualization...")
    html = VG.render(
        height="720px",
        renderer=Renderer.WEB_GL,
        max_allowed_nodes=5000,
    )

    html_content = html.data.replace(": NaN", ": null").replace(":NaN", ":null")

    annotations = [
        {
            "text": "CI: Southern<br>California Seismic<br>Network Cluster",
            "top": "20%",
            "left": "14%",
        },
        {
            "text": "Container Cluster:<br>Hugo-Benioff",
            "top": "14%",
            "left": "64%",
        },
        {
            "text": "Container Cluster:<br>Harry-Wood",
            "top": "46%",
            "left": "53%",
        },
        {
            "text": "Container Cluster:<br>Beno-Gutenberg",
            "top": "74%",
            "left": "59%",
        },
        {
            "text": "Container Cluster:<br>Charles-Richter",
            "top": "65%",
            "left": "13%",
        },
    ]
    legend_html = build_schema_legend_html(node_colors, rel_colors, node_counts, rel_counts)

    html_content = inject_annotations_and_style(html_content, annotations, legend_html)

    output_html = "graph_visualization.html"
    output_png = "graph_visualization.png"
    closeup_png = "graph_visualization_closeup.png"

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Exporting high-res images to {output_png} and {closeup_png}...")
    export_html_to_png(
        output_html,
        output_png,
        closeup_png_path=closeup_png,
        width=1280,
        height=720,
    )