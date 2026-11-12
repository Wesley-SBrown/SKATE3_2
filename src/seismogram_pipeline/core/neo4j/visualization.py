# src/seismogram_pipeline/core/neo4j/visualization.py

from neo4j import RoutingControl
from neo4j_viz import Renderer
from neo4j_viz.neo4j import from_neo4j
from dotenv import load_dotenv

from .connector import get_driver

load_dotenv()

if __name__=='__main__':
    driver = get_driver()
    print("Testing connection...")
    driver.verify_connectivity()
    print("Connected succesfully!")

    query = """
    MATCH (n)-[r]->(m)
    RETURN n,r,m
    """

    print("Fetching full graph from AuraDB...")
    result = driver.execute_query(query, routing_=RoutingControl.READ)

    print("Building visualization graph...")

    VG = from_neo4j(result)

    pinned_nodes = {}
    container_sizes = {}

    for node in VG.nodes:
        # inspect properties to determine node
        props = node.properties or {}
        
        if "box_range" in props or "num_missing" in props:
            node.caption = 'Container'
            pinned_nodes[node.id] = True
            container_sizes[node.id] = 18
        elif "networkCode" in props:
            node.caption = 'Network'
            pinned_nodes[node.id] = True
        elif "stationCode" in props:
            node.caption = 'Station'
            pinned_nodes[node.id] = True
        elif 'boxNum' in props:
            node.caption = 'Box'
            pinned_nodes[node.id] = False
        else:
            node.caption = 'Channel'
            pinned_nodes[node.id] = False
            

    VG.toggle_nodes_pinned(pinned_nodes)

    if container_sizes:
        VG.resize_nodes(sizes=container_sizes)

    rel_colors = {
        "CONTAINS":            "#888888",
        "HAS_STATION":         "#3366CC",
        "HAS_CHANNEL":         "#FF3366",
        "CONTAINS_DATA_FOR":   "#06D090"
    }

    colors = {
        "Container": "#0CEE0C",  
        "Network":   "#04DFF3",  
        "Station":   "#ECE10B",  
        "Box":       "#FF6912",  
        "Channel":   "#E40DD9"   
    }
    VG.color_nodes(field="caption", colors=colors)
    VG.color_relationships(field="caption", colors=rel_colors)
    
    relationship_widths = {rel.id: 5 for rel in VG.relationships}
    VG.resize_relationships(widths=relationship_widths)

    VG.set_legend(nodes=colors, relationships=rel_colors)
    VG.show_legend(visible=True)

    print("Rendering visualization...")
    html = VG.render(
        height="650px",
        renderer=Renderer.WEB_GL,
        max_allowed_nodes=5000
    )

    html_content = html.data.replace(": NaN", ": null").replace(":NaN", ":null")

    output = "graph_visualization.html"
    with open(output, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Visualization saved to: {output}")