"""Genera los diagramas de bloques y de flujo de trabajo de PeakGuard."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D


C = {
    "acq_fc": "#dbe9f6", "acq_ec": "#2f6db3",
    "dat_fc": "#d9f0e3", "dat_ec": "#2e8b57",
    "mod_fc": "#e6f4d9", "mod_ec": "#4d7c0f",
    "pro_fc": "#fde8d7", "pro_ec": "#d9822b",
    "biz_fc": "#e9e0f5", "biz_ec": "#6a4c93",
    "gray": "#666666", "text": "#1a1a1a",
    "arrow": "#555555",
}


def box(ax, x, y, w, h, text, fc, ec, fs=9, weight="normal"):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.35,rounding_size=0.9",
        linewidth=1.5, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight=weight, color=C["text"], zorder=3,
            linespacing=1.3)


def arrow(ax, p1, p2, color=None, lw=1.4, ls="-", style="-|>", rad=0.0):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle=style, mutation_scale=11,
        linewidth=lw, color=color or C["arrow"], linestyle=ls,
        connectionstyle=f"arc3,rad={rad}", zorder=1,
        shrinkA=2, shrinkB=2))


def header(ax, x, text, color):
    ax.text(x, 96.5, text, ha="center", va="center",
            fontsize=12, fontweight="bold", color=color)


# ---------------------------------------------------------------------------
# Figura 1: arquitectura y flujo de datos
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(18, 9.8))
ax.set_xlim(0, 100)
ax.set_ylim(0, 104)
ax.axis("off")
fig.suptitle("PeakGuard — Arquitectura y flujo de datos",
             fontsize=17, fontweight="bold", y=0.975)

header(ax, 11, "1. Adquisición", C["acq_ec"])
header(ax, 36, "2. Datos", C["dat_ec"])
header(ax, 65, "3. Modelos", C["mod_ec"])
header(ax, 89, "4. Producto y negocio", C["pro_ec"])

# Adquisición
box(ax, 2, 85, 8.5, 7, "PM5300\nred normal\n(200)", C["acq_fc"], C["acq_ec"], 8.5)
box(ax, 11.5, 85, 8.5, 7, "PM5300\nred regulada\n(201)", C["acq_fc"], C["acq_ec"], 8.5)
box(ax, 4, 73, 14, 7, "Gateway HaLow\nModbus / RS485", C["acq_fc"], C["acq_ec"], 9)

arrow(ax, (6.25, 85), (8, 80.2))
arrow(ax, (15.75, 85), (14, 80.2))
arrow(ax, (18, 76.5), (24, 88.5))

# Datos
box(ax, 24, 85, 24, 7, "Ingesta / buffer local", C["dat_fc"], C["dat_ec"], 9.5)
box(ax, 24, 74, 24, 7, "Serie cruda 1–5 s", C["dat_fc"], C["dat_ec"], 9.5)
box(ax, 24, 61, 24, 9,
    "Calidad y validación física\nS = √3·V·I  ·  Ptotal = ΣPfases\nPF = P/S  ·  huecos · duplicados",
    C["dat_fc"], C["dat_ec"], 8.6)
box(ax, 24, 48, 24, 8,
    "Agregación multi-resolución\n1 min (media) · 15 min · 1 h",
    C["dat_fc"], C["dat_ec"], 8.8)
box(ax, 24, 35, 24, 8,
    "Feature store\nlags · ventanas · calendario · eventos",
    C["dat_fc"], C["dat_ec"], 8.8)

arrow(ax, (36, 85), (36, 81.2))
arrow(ax, (36, 74), (36, 70.2))
arrow(ax, (36, 61), (36, 56.2))
arrow(ax, (36, 48), (36, 43.2))

# Bus de features
ax.plot([51, 51], [39, 88.5], color=C["gray"], linewidth=2.0, zorder=1)
arrow(ax, (48, 39), (51, 39))
arrow(ax, (51, 88.5), (54, 88.5))
arrow(ax, (51, 62), (54, 62))
arrow(ax, (51, 39), (54, 39))

# Modelos
box(ax, 54, 84, 22, 9,
    "Riesgo de pico\nGBM + calibración\n→ probabilidad",
    C["mod_fc"], C["mod_ec"], 9)
box(ax, 54, 57, 22, 10,
    "Estados de carga\nHMM / clustering\n→ base · ocupación · evento",
    C["mod_fc"], C["mod_ec"], 9)
box(ax, 54, 34, 22, 10,
    "Energía y PF\nregresión / STL\n→ reporte",
    C["mod_fc"], C["mod_ec"], 9)

arrow(ax, (65, 57), (65, 84))
ax.text(66.5, 70.5, "probabilidades de estado\ncomo features", fontsize=7.8,
        color=C["gray"], ha="left", va="center")

# Producto
box(ax, 80, 84, 18, 8,
    "Dashboard\nreplay · estados\nreporte · backtest",
    C["pro_fc"], C["pro_ec"], 8.8)
box(ax, 80, 72, 18, 7,
    "Alertas\nTelegram / email", C["pro_fc"], C["pro_ec"], 8.8)
box(ax, 80, 60, 18, 7,
    "Reporte semanal\nenergía · PF · eventos", C["pro_fc"], C["pro_ec"], 8.5)
box(ax, 80, 38, 18, 12,
    "Cliente\nedificio sin BMS\n\nAhorro: demanda +\nreactiva + energía",
    C["biz_fc"], C["biz_ec"], 8.8)
box(ax, 80, 24, 18, 8,
    "Piloto 3–6 meses\nM&V / IPMVP", C["biz_fc"], C["biz_ec"], 8.8)

arrow(ax, (76, 88.5), (80, 88))
arrow(ax, (76, 86.5), (80, 75.5))
arrow(ax, (76, 62), (80, 84), rad=-0.15)
arrow(ax, (76, 39), (80, 63.5), rad=-0.15)
arrow(ax, (86, 84), (86, 50.2))
arrow(ax, (89, 72), (89, 50.2))
arrow(ax, (92, 60), (92, 50.2))
arrow(ax, (89, 38), (89, 32.2))

# Transversal
box(ax, 2, 8, 96, 7,
    "Transversal:  validación temporal (rolling-origin)  ·  explicabilidad (SHAP / estados)  ·  "
    "reproducibilidad (notebooks · git · requirements)  ·  M&V (IPMVP)",
    "#f2f2f2", "#888888", 9)

plt.savefig("diagrama_arquitectura.png", dpi=170, bbox_inches="tight",
            facecolor="white")
plt.close(fig)


# ---------------------------------------------------------------------------
# Figura 2: flujo de trabajo en 12 semanas
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(15, 7.5))

fases = [
    ("Fase 0 · Decisiones y alcance", 1, 1, "data"),
    ("Fase 1 · Auditoría y pipeline", 1, 2, "data"),
    ("Fase 2 · EDA y definición del target", 2, 1, "data"),
    ("Fase 3 · Features", 3, 1, "model"),
    ("Fase 4 · Baseline + GBM + calibración", 4, 1, "model"),
    ("Fase 5 · Estados de carga", 5, 2, "model"),
    ("Fase 6 · Integración estados → features", 6, 1, "model"),
    ("Fase 7 · Dashboard", 7, 2, "product"),
    ("Fase 8 · Backtest y validación", 9, 1, "product"),
    ("Fase 9 · Caso de negocio", 10, 1, "biz"),
    ("Fase 10 · Informe y presentación", 11, 2, "biz"),
]

palette = {
    "data": ("#dbe9f6", "#2f6db3"),
    "model": ("#e6f4d9", "#4d7c0f"),
    "product": ("#fde8d7", "#d9822b"),
    "biz": ("#e9e0f5", "#6a4c93"),
}

for i, (label, start, dur, kind) in enumerate(fases):
    y = len(fases) - i - 1
    fc, ec = palette[kind]
    ax.barh(y, dur, left=start - 1, height=0.62, color=fc, edgecolor=ec,
            linewidth=1.4, zorder=3)
    ax.text(start - 1 + dur / 2, y, f"{start}–{start + dur - 1}",
            ha="center", va="center", fontsize=8, color=C["text"], zorder=4)
    ax.text(-0.2, y, label, ha="right", va="center", fontsize=9.5,
            color=C["text"])

ax.set_xlim(0, 13)
ax.set_ylim(-0.7, len(fases) - 0.3)
ax.set_yticks([])
ax.set_xticks(range(0, 14))
ax.set_xlabel("Semana", fontsize=10)
ax.grid(axis="x", color="#cccccc", linewidth=0.8, alpha=0.7, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

for x, text in [(4, "Modelo MVP"), (8, "Dashboard"), (12, "Entrega")]:
    ax.axvline(x, color="#666666", linestyle="--", linewidth=1.1, zorder=2)
    ax.text(x, len(fases) - 0.05, text, ha="center", va="bottom",
            fontsize=8.5, color="#444444", style="italic")

legend = [
    Line2D([0], [0], color=palette["data"][1], lw=7, label="Datos"),
    Line2D([0], [0], color=palette["model"][1], lw=7, label="Modelos"),
    Line2D([0], [0], color=palette["product"][1], lw=7, label="Producto"),
    Line2D([0], [0], color=palette["biz"][1], lw=7, label="Negocio"),
]
ax.legend(handles=legend, loc="upper center", frameon=False, ncol=4,
          fontsize=9, bbox_to_anchor=(0.5, -0.13))

ax.set_title("PeakGuard — Flujo de trabajo del proyecto (12 semanas)",
             fontsize=15, fontweight="bold", pad=24, loc="left")

plt.tight_layout()
plt.savefig("diagrama_flujo_trabajo.png", dpi=170, bbox_inches="tight",
            facecolor="white")
plt.close(fig)

print("OK: diagrama_arquitectura.png, diagrama_flujo_trabajo.png")
