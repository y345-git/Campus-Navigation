# draw_utils.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.graph_objects as go
import streamlit as st
from config import CAMPUS_POS, BUILDING_BLOCKS, PATH_STRIPS, B1_POS_3D, college_b1_interior

# ----------------------------
# Draw Campus Map (2D)
# ----------------------------
def show_campus(highlight_path=None, title="Campus Map (2D)"):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title)

    # Draw building blocks (gates = white, others grey)
    for name, (x, y, w, h) in BUILDING_BLOCKS.items():
        face = "white" if name.startswith("Gate") else "lightgrey"
        rect = patches.Rectangle((x, y), w, h, linewidth=1.5,
                                 edgecolor="black", facecolor=face)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, name,
                ha="center", va="center", fontsize=9)

    # Draw path strips
    for (x, y, w, h) in PATH_STRIPS:
        rect = patches.Rectangle((x, y), w, h, linewidth=0.6,
                                 edgecolor="none", facecolor="whitesmoke")
        ax.add_patch(rect)

    # Draw node centers
    for name, (x, y) in CAMPUS_POS.items():
        ax.plot(x, y, marker="o", markersize=6, color="black")
        ax.text(x + 1, y - 1.5, name, fontsize=8)

    # Highlight shortest path if available
    if highlight_path and len(highlight_path) > 1:
        for a, b in zip(highlight_path, highlight_path[1:]):
            x1, y1 = CAMPUS_POS[a]
            x2, y2 = CAMPUS_POS[b]
            ax.plot([x1, x2], [y1, y2], color="red", linewidth=4, zorder=5)

    st.pyplot(fig)
    plt.close(fig)

# ----------------------------
# Draw B1 Interior (3D)
# ----------------------------
def show_b1_3d(path=None):
    fig = go.Figure()

    # Graph edges
    edge_x, edge_y, edge_z = [], [], []
    for u, nbrs in college_b1_interior.items():
        for v in nbrs:
            x0, y0, z0 = B1_POS_3D[u]
            x1, y1, z1 = B1_POS_3D[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
            edge_z += [z0, z1, None]
    fig.add_trace(go.Scatter3d(x=edge_x, y=edge_y, z=edge_z,
                               mode="lines",
                               line=dict(color="gray", width=4),
                               name="edges"))

    # Graph nodes
    names = list(B1_POS_3D.keys())
    node_x = [B1_POS_3D[n][0] for n in names]
    node_y = [B1_POS_3D[n][1] for n in names]
    node_z = [B1_POS_3D[n][2] for n in names]
    fig.add_trace(go.Scatter3d(x=node_x, y=node_y, z=node_z,
                               mode="markers+text",
                               marker=dict(size=6, color="skyblue"),
                               text=names,
                               textposition="top center",
                               name="rooms"))

    # Highlight path if available
    if path and len(path) > 1:
        px, py, pz = [], [], []
        for a, b in zip(path, path[1:]):
            x0, y0, z0 = B1_POS_3D[a]
            x1, y1, z1 = B1_POS_3D[b]
            px += [x0, x1, None]
            py += [y0, y1, None]
            pz += [z0, z1, None]
        fig.add_trace(go.Scatter3d(x=px, y=py, z=pz,
                                   mode="lines",
                                   line=dict(color="red", width=8),
                                   name="route"))

    fig.update_layout(
        scene=dict(xaxis=dict(visible=False),
                   yaxis=dict(visible=False),
                   zaxis=dict(visible=False)),
        margin=dict(l=0, r=0, t=30, b=0),
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
