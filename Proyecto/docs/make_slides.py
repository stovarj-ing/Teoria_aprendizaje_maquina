"""Genera las diapositivas de PeakGuard (16:9) con python-pptx."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "reports" / "figures"
DOCS = ROOT / "docs"

NAVY = RGBColor(0x1F, 0x3A, 0x5F)
BLUE = RGBColor(0x2F, 0x6D, 0xB3)
GREEN = RGBColor(0x2E, 0x8B, 0x57)
ORANGE = RGBColor(0xD9, 0x82, 0x2B)
PURPLE = RGBColor(0x6A, 0x4C, 0x93)
GRAY = RGBColor(0x66, 0x66, 0x66)
LIGHT = RGBColor(0xF2, 0xF2, 0xF2)
LBLUE = RGBColor(0xDB, 0xE9, 0xF6)
LGREEN = RGBColor(0xD9, 0xF0, 0xE3)
LORANGE = RGBColor(0xFD, 0xE8, 0xD7)
LPURPLE = RGBColor(0xE9, 0xE0, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


# ---------------------------------------------------------------------------
# Figuras auxiliares
# ---------------------------------------------------------------------------
def make_charts():
    plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.25,
                         "axes.spines.top": False, "axes.spines.right": False})

    models = ["Base", "Persist.", "GBM", "Logit", "GAM"]
    pr = [0.027, 0.367, 0.428, 0.458, 0.491]
    colors = ["#999999", "#D9822B", "#6A4C93", "#2F6DB3", "#2E8B57"]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    bars = ax.bar(models, pr, color=colors, width=0.62)
    for b, v in zip(bars, pr):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}",
                ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, 0.58)
    ax.set_ylabel("PR-AUC (mediana 5 folds)")
    ax.set_title("Modelo vs baselines")
    fig.tight_layout()
    fig.savefig(DOCS / "fig_pr_models.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    days = [11, 16, 21, 26]
    train = [0.598, 0.540, 0.503, 0.475]
    test = [0.221, 0.237, 0.292, 0.400]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.plot(days, train, "o-", color="#6A4C93", label="train")
    ax.plot(days, test, "o-", color="#2E8B57", label="holdout")
    ax.set_xlabel("días de entrenamiento")
    ax.set_ylabel("PR-AUC")
    ax.set_title("Curva de aprendizaje")
    ax.legend(frameon=False)
    ax.set_xticks(days)
    fig.tight_layout()
    fig.savefig(DOCS / "fig_learning_curve.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig = plt.figure(figsize=(12, 2.2))
    fig.patch.set_alpha(0)
    fig.text(0.5, 0.68,
             r"$\mathrm{logit}(\hat{p}_t)=-9.015+1.236\,z_{Pmax15}"
             r"-1.021\,\mathrm{weekend}-0.850\,z_{\cos}$",
             ha="center", va="center", fontsize=22, color="#1F3A5F")
    fig.text(0.5, 0.30,
             r"$+0.604\,z_{\sin}+0.604\,z_{Pmean15}-0.556\,z_{V}"
             r"+0.538\,z_{PF}$",
             ha="center", va="center", fontsize=22, color="#1F3A5F")
    fig.savefig(DOCS / "fig_equation.png", dpi=250, transparent=True,
                bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Helpers de diapositivas
# ---------------------------------------------------------------------------
def add_slide(prs, title, subtitle=None, number=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.85))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background(); bar.shadow.inherit = False
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(0.85),
                                    prs.slide_width, Inches(0.05))
    accent.fill.solid(); accent.fill.fore_color.rgb = ORANGE
    accent.line.fill.background(); accent.shadow.inherit = False

    tb = slide.shapes.add_textbox(Inches(0.45), Inches(0.10), Inches(12.4), Inches(0.65))
    tf = tb.text_frame; tf.clear(); tf.word_wrap = True
    p = tf.paragraphs[0]; r = p.add_run(); r.text = title
    r.font.size = Pt(25); r.font.bold = True; r.font.color.rgb = WHITE
    r.font.name = "Calibri"
    if subtitle:
        tb2 = slide.shapes.add_textbox(Inches(0.45), Inches(0.92), Inches(12.4), Inches(0.35))
        tf2 = tb2.text_frame; tf2.clear(); tf2.word_wrap = True
        p2 = tf2.paragraphs[0]; r2 = p2.add_run(); r2.text = subtitle
        r2.font.size = Pt(12); r2.font.color.rgb = GRAY; r2.font.name = "Calibri"
    if number is not None:
        foot = slide.shapes.add_textbox(Inches(0.45), Inches(7.12), Inches(10), Inches(0.25))
        pf = foot.text_frame; pf.clear()
        p = pf.paragraphs[0]; r = p.add_run()
        r.text = "PeakGuard · Teoría de Aprendizaje de Máquina · UNAL Manizales"
        r.font.size = Pt(8); r.font.color.rgb = GRAY
        num = slide.shapes.add_textbox(Inches(12.35), Inches(7.10), Inches(0.6), Inches(0.3))
        pn = num.text_frame; pn.clear()
        p = pn.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT
        r = p.add_run(); r.text = str(number)
        r.font.size = Pt(9); r.font.color.rgb = GRAY
    return slide


def set_text(tf, text, size, color, bold=False, align=PP_ALIGN.LEFT):
    tf.clear(); tf.word_wrap = True
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = line
        r.font.size = Pt(size); r.font.color.rgb = color; r.font.bold = bold
        r.font.name = "Calibri"


def add_text(slide, left, top, width, height, text, size=12, color=NAVY,
             bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    set_text(tf, text, size, color, bold, align)
    return tb


def add_bullets(slide, left, top, width, height, items, size=12, color=NAVY,
                bullet_color=ORANGE):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame; tf.clear(); tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(5)
        r = p.add_run(); r.text = "• "
        r.font.size = Pt(size); r.font.color.rgb = bullet_color; r.font.bold = True
        r.font.name = "Calibri"
        r2 = p.add_run(); r2.text = item
        r2.font.size = Pt(size); r2.font.color.rgb = color; r2.font.name = "Calibri"
    return tb


def add_card(slide, left, top, width, height, title, body, fill=LIGHT,
             line=GRAY, title_color=NAVY, body_size=11, title_size=14):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line; shp.line.width = Pt(1)
    shp.shadow.inherit = False
    tf = shp.text_frame; tf.clear(); tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.12)
    tf.margin_top = tf.margin_bottom = Inches(0.08)
    p = tf.paragraphs[0]; r = p.add_run(); r.text = title
    r.font.size = Pt(title_size); r.font.bold = True; r.font.color.rgb = title_color
    r.font.name = "Calibri"
    if body:
        for line in str(body).split("\n"):
            p2 = tf.add_paragraph(); p2.space_before = Pt(2)
            r2 = p2.add_run(); r2.text = line
            r2.font.size = Pt(body_size); r2.font.color.rgb = NAVY; r2.font.name = "Calibri"
    return shp


def add_table(slide, data, left, top, width, height, font_size=11,
              header_fill=NAVY, header_color=WHITE):
    rows, cols = len(data), len(data[0])
    shp = slide.shapes.add_table(rows, cols, Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    table = shp.table
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = str(data[r][c])
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            para = cell.text_frame.paragraphs[0]
            para.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            for run in para.runs:
                run.font.size = Pt(font_size)
                run.font.name = "Calibri"
                if r == 0:
                    run.font.bold = True
                    run.font.color.rgb = header_color
                else:
                    run.font.color.rgb = NAVY
            if r == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = header_fill
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if r % 2 else LIGHT
    return table


def add_picture(slide, name, left, top, width):
    path = name if Path(name).is_absolute() else ROOT / name
    slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(width))


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------
def build():
    make_charts()
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 1. Título
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(4.8), prs.slide_width, Inches(0.06))
    band.fill.solid(); band.fill.fore_color.rgb = ORANGE; band.line.fill.background()
    add_text(s, 0.8, 2.1, 11.8, 1.0, "PeakGuard", 48, WHITE, True)
    add_text(s, 0.85, 3.15, 11.8, 0.7, "De la subestación al modelo de riesgo de picos", 24, WHITE)
    add_text(s, 0.85, 5.1, 11.8, 0.5,
             "Proyecto final · Teoría de Aprendizaje de Máquina", 14, WHITE)
    add_text(s, 0.85, 5.55, 11.8, 0.5,
             "Sebastián Tovar · Universidad Nacional de Colombia, Sede Manizales · 2026", 12,
             RGBColor(0xC9, 0xD6, 0xE3))

    # 2. Red de adquisición
    s = add_slide(prs, "Cómo se capturan los datos", "Flujo: medidor → Ethernet → switch → gateway HaLow → servidor", 2)
    boxes = [
        ("Medidor\nPM5300", "P, Q, S, V, I, PF\nModbus TCP"),
        ("Ethernet", "Enlace local\n100 Mbps"),
        ("Switch", "Concentra\n200 y 201"),
        ("Gateway\nHaLow", "IEEE 802.11ah\nlargo alcance"),
        ("Servidor", "Ingesta\nCSV / XLSX"),
    ]
    xs = [0.4, 2.9, 5.4, 7.9, 10.4]
    for x, (head, body) in zip(xs, boxes):
        shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(1.8),
                                 Inches(2.2), Inches(1.25))
        shp.fill.solid(); shp.fill.fore_color.rgb = LBLUE
        shp.line.color.rgb = BLUE; shp.line.width = Pt(1.5); shp.shadow.inherit = False
        tf = shp.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        set_text(tf, head, 13, NAVY, True, PP_ALIGN.CENTER)
        add_text(s, x, 3.15, 2.2, 0.8, body, 10, GRAY, align=PP_ALIGN.CENTER)
    for x in [2.62, 5.12, 7.62, 10.12]:
        arr = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(2.3),
                                 Inches(0.26), Inches(0.25))
        arr.fill.solid(); arr.fill.fore_color.rgb = ORANGE; arr.line.fill.background()
        arr.shadow.inherit = False
    add_card(s, 0.4, 4.25, 12.5, 1.7, "¿Por qué HaLow?",
             "Edificios sin Wi-Fi industrial · largo alcance y bajo consumo · el gateway hace de puente al servidor.\n"
             "Muestreo: 10 s / 30 s / 8–9 s. NILM del 201: 0,5 s en una ventana de 4,76 h.",
             LIGHT, GRAY, NAVY, 12, 15)
    add_text(s, 0.4, 6.1, 12.5, 0.6,
             "El medidor mide; el switch concentra; HaLow transporta; el servidor guarda y procesa.",
             12, GRAY, align=PP_ALIGN.CENTER)

    # 3. Datos
    s = add_slide(prs, "Qué se mide y qué se guarda", "Dos medidores, tres cadencias y una serie de 1 min", 3)
    data = [
        ["Medidor", "Red", "Filas", "Cadencia", "Uso"],
        ["200", "Normal 208 V", "154.626", "10/30/8–9 s", "Modelo"],
        ["201", "Regulada 220 V", "167.044", "10/30/8–9/1 s", "Comparación"],
    ]
    add_table(s, data, 0.5, 1.35, 8.0, 1.4, 11)
    cards = [
        ("47 días", "con datos en el rango"),
        ("66.767 min", "serie de 1 min"),
        ("45,3 %", "de minutos faltantes"),
        ("35.375 min", "útiles; 948 picos"),
    ]
    for i, (big, small) in enumerate(cards):
        y = 1.35 + i * 1.28
        shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.85), Inches(y),
                                 Inches(4.05), Inches(1.1))
        shp.fill.solid(); shp.fill.fore_color.rgb = LGREEN
        shp.line.color.rgb = GREEN; shp.line.width = Pt(1); shp.shadow.inherit = False
        tf = shp.text_frame; tf.clear(); tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = big
        r.font.size = Pt(20); r.font.bold = True; r.font.color.rgb = GREEN; r.font.name = "Calibri"
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = small
        r2.font.size = Pt(10); r2.font.color.rgb = NAVY; r2.font.name = "Calibri"
    add_bullets(s, 0.5, 3.2, 8.0, 2.6, [
        "200: PF válido; solo 2 muestras > 1. Es el medidor del modelo.",
        "201: PF > 1 en 70,8 % de las muestras. P, Q, S e I usables; el PF no.",
        "NILM 200: vacío. NILM 201: 4,76 h a 0,5 s; caso de estudio.",
        "Sin armónicos: solo el proxy D = √(S² − P² − Q²).",
    ], 12)
    add_text(s, 0.5, 6.35, 12.4, 0.4,
             "La cobertura es la limitación principal: 26 de los 47 días tienen menos de 80 % de cobertura.",
             11, ORANGE, True)

    # 4. Problema
    s = add_slide(prs, "El problema", "Un pico de 20 s puede fijar la factura del mes", 4)
    cards = [
        ("Cargo por demanda", "Un pico de 20 s fija el máximo del mes.\nPico observado: 18,24 kW.\nCada kW evitado vale el cargo.", LBLUE, BLUE),
        ("Factor de potencia", "PF 0,51; Q 9,6 kVAR.\nCompensar a 0,95: ~7,9 kVAR.\nCorriente 30,6 A → 15,5 A.", LORANGE, ORANGE),
        ("Desperdicio", "Base: 128,7 kWh/día.\nLaboral: 169,8 kWh/día.\nFin de semana: 131,0 kWh/día.", LPURPLE, PURPLE),
    ]
    for i, (title, body, fill, line) in enumerate(cards):
        add_card(s, 0.5 + i * 4.15, 1.5, 3.9, 3.3, title, body, fill, line, NAVY, 13, 16)
    band = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(5.2),
                              Inches(12.3), Inches(1.1))
    band.fill.solid(); band.fill.fore_color.rgb = NAVY; band.line.fill.background()
    tf = band.text_frame; tf.clear(); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = "¿Se puede anticipar el pico y explicar qué lo causa?"
    r.font.size = Pt(22); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = "Calibri"

    # 5. Pipeline
    s = add_slide(prs, "Pipeline de datos", "Del ZIP a la serie de 1 min y al target", 5)
    steps = ["ZIP", "Inventario", "1 min\n(media)", "Calidad\nfísica", "Features", "Target"]
    xs = [0.5 + i * 2.08 for i in range(6)]
    for x, step in zip(xs, steps):
        shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(1.5),
                                 Inches(1.85), Inches(0.95))
        shp.fill.solid(); shp.fill.fore_color.rgb = LBLUE
        shp.line.color.rgb = BLUE; shp.line.width = Pt(1); shp.shadow.inherit = False
        tf = shp.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        set_text(tf, step, 11, NAVY, True, PP_ALIGN.CENTER)
    for x in [2.37, 4.45, 6.53, 8.61, 10.69]:
        arr = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(1.82),
                                 Inches(0.18), Inches(0.28))
        arr.fill.solid(); arr.fill.fore_color.rgb = ORANGE; arr.line.fill.background()
        arr.shadow.inherit = False
    add_picture(s, FIGS / "01_serie_P.png", 0.5, 2.8, 7.6)
    add_bullets(s, 8.35, 2.75, 4.5, 3.2, [
        "1 min = media de 10 s, no una muestra decimada.",
        "Huecos marcados; no se interpolan para el modelo.",
        "Física: S = √3VI, P = ΣP, PF = P/S.",
        "Muestra útil: 35.375 min; 948 positivos (2,68 %).",
    ], 11)
    add_text(s, 0.5, 6.55, 12.3, 0.35,
             "La serie cruda conserva los picos; la media de 1 min los suaviza sin borrarlos.",
             10, GRAY, align=PP_ALIGN.CENTER)

    # 6. Target
    s = add_slide(prs, "El target: una probabilidad, no un instante", "¿Cuál es la probabilidad de superar 12 kW en los próximos 15 min?", 6)
    add_card(s, 0.5, 1.35, 5.7, 2.0, "Definición",
             "Y_t = 1{ max(P[t+1 … t+15]) > 12 kW }\n"
             "Horizonte H = 15 min · umbral 12 kW · tasa base 2,68 %.",
             LBLUE, BLUE, NAVY, 14, 16)
    add_bullets(s, 0.5, 3.6, 5.7, 2.8, [
        "El pico dura 10–30 s; el target es una ventana de riesgo.",
        "El precursor es plano: el pico es un salto súbito.",
        "Por eso se predice probabilidad, no el minuto exacto.",
        "La decisión se toma con un umbral por costo.",
    ], 11)
    add_picture(s, FIGS / "02_ejemplo_dia.png", 6.35, 1.35, 6.5)
    add_text(s, 6.35, 5.2, 6.5, 0.5,
             "17-11: la probabilidad sube antes de los picos de 09:30 y 15:00.",
             10, GRAY, align=PP_ALIGN.CENTER)

    # 7. Ecuación
    s = add_slide(prs, "La ecuación", "7 features, 8 parámetros, coeficientes estandarizados", 7)
    add_picture(s, DOCS / "fig_equation.png", 0.55, 1.15, 12.2)
    cards = [
        ("7 features", "Pmax15, Pmean15, V, PF, hora (sen/cos), weekend."),
        ("Signos", "Pmax15 y PF suben el riesgo; V, weekend y hora lo modulan."),
        ("No es una tabla", "Se calcula con una suma y una sigmoide."),
        ("Calibración", "Fuera de muestra, antes de elegir el umbral."),
    ]
    for i, (title, body) in enumerate(cards):
        add_card(s, 0.5 + (i % 2) * 6.2, 3.65 + (i // 2) * 1.55, 5.95, 1.35,
                 title, body, LIGHT, GRAY, NAVY, 11, 14)

    # 8. Validación
    s = add_slide(prs, "Validación temporal", "Rolling-origin: 5 folds por bloques de días; sin split aleatorio", 8)
    data = [
        ["Modelo", "PR-AUC", "Brier"],
        ["Tasa base", "0,027", "0,026"],
        ["Persistencia", "0,367", "0,102"],
        ["GBM", "0,428", "0,017"],
        ["Logística (ecuación)", "0,458", "0,014"],
        ["GAM (splines)", "0,491", "0,016"],
    ]
    add_table(s, data, 0.5, 1.35, 7.0, 2.6, 12)
    add_picture(s, DOCS / "fig_pr_models.png", 7.85, 1.25, 5.0)
    add_text(s, 0.5, 4.35, 12.3, 1.2,
             "La ecuación compite con el GBM y el GAM la supera levemente. "
             "No hace falta un modelo opaco: la estructura está en las features.",
             13, NAVY, True, PP_ALIGN.CENTER)
    add_text(s, 0.5, 5.6, 12.3, 0.8,
             "Holdout calibrado: PR-AUC 0,380 · Brier 0,016. La persistencia en ese bloque fue 0,511; "
             "la variabilidad entre períodos es alta y se reporta.",
             10, GRAY, align=PP_ALIGN.CENTER)

    # 9. Generalización
    s = add_slide(prs, "¿Memoriza?", "Tres controles: brecha, etiquetas barajadas y curva de aprendizaje", 9)
    cards = [
        ("Brecha 0,095", "train 0,474 / holdout 0,380"),
        ("Etiquetas barajadas", "0,021 vs base 0,020"),
        ("Curva de aprendizaje", "0,221 → 0,400"),
    ]
    for i, (title, body) in enumerate(cards):
        add_card(s, 0.5 + i * 4.15, 1.35, 3.9, 1.2, title, body, LGREEN, GREEN, GREEN, 11, 14)
    add_picture(s, DOCS / "fig_learning_curve.png", 0.5, 2.9, 7.0)
    add_bullets(s, 8.0, 2.85, 4.8, 3.0, [
        "El train baja y el test sube con más datos.",
        "Con etiquetas barajadas cae a la tasa base.",
        "No es un lookup: aprende una función suave.",
        "La brecha se reduce al agregar días.",
    ], 11)
    add_text(s, 0.5, 6.8, 12.3, 0.3,
             "La conclusión es empírica y verificable: el modelo generaliza, no memoriza.",
             10.5, ORANGE, True, PP_ALIGN.CENTER)

    # 10. Evaluación operativa
    s = add_slide(prs, "Evaluación operativa retrospectiva", "58 episodios de pico; simulación de alertas sobre predicciones OOF", 10)
    data = [
        ["Carga", "Modelo recall", "Modelo prec.", "Persist. recall"],
        ["2 %", "0,397", "0,375", "0,638"],
        ["5 %", "0,638", "0,273", "0,879"],
        ["10 %", "0,845", "0,281", "0,948"],
        ["20 %", "1,000", "0,228", "1,000"],
    ]
    add_table(s, data, 0.5, 1.3, 6.8, 1.9, 10)
    add_card(s, 7.6, 1.3, 5.2, 1.9, "Punto de costo (C_FN/C_FP=10)",
             "Umbral 0,0019 · recall 1,0 · precisión 0,26\n"
             "2,08 FA/día · 19 % de carga · lead 15 min",
             LORANGE, ORANGE, NAVY, 10, 13)
    add_picture(s, FIGS / "03_tradeoff.png", 0.75, 3.3, 11.4)
    add_text(s, 0.5, 6.82, 12.3, 0.25,
             "A igual carga, el modelo es más preciso y alerta menos; la persistencia detecta más a bajo costo.",
             9.5, GRAY, align=PP_ALIGN.CENTER)

    # 11. Límites
    s = add_slide(prs, "Dónde falla", "Análisis al 5 % de carga de alerta; la cobertura manda", 11)
    cards = [
        ("45,3 %", "minutos faltantes"),
        ("26 días", "cobertura < 80 %"),
        ("10/30/8–9 s", "cadencia mixta"),
        ("PF 201 > 1", "70,8 % de las muestras"),
        ("Sin armónicos", "solo el proxy D"),
    ]
    for i, (big, small) in enumerate(cards):
        x = 0.45 + i * 2.52
        shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(1.3),
                                 Inches(2.35), Inches(1.25))
        shp.fill.solid(); shp.fill.fore_color.rgb = LORANGE
        shp.line.color.rgb = ORANGE; shp.line.width = Pt(1); shp.shadow.inherit = False
        tf = shp.text_frame; tf.clear(); tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = big
        r.font.size = Pt(15); r.font.bold = True; r.font.color.rgb = ORANGE; r.font.name = "Calibri"
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = small
        r2.font.size = Pt(9); r2.font.color.rgb = NAVY; r2.font.name = "Calibri"
    add_picture(s, FIGS / "03_error_cobertura.png", 0.5, 3.0, 6.2)
    add_bullets(s, 7.0, 2.95, 5.8, 3.0, [
        "Los picos perdidos se concentran donde la cobertura es baja.",
        "El 201 no se usa para modelar por el PF roto.",
        "Sin armónicos no se pueden atribuir cargas capacitivas.",
        "Los picos duran 10–30 s: el target de 15 min es una ventana.",
        "El piloto necesita 3–6 meses continuos.",
    ], 11)
    add_text(s, 0.5, 6.4, 12.3, 0.4,
             "La limitación principal no es el modelo: es la continuidad de los datos.",
             11, ORANGE, True, PP_ALIGN.CENTER)

    # 12. Filtro
    s = add_slide(prs, "¿Filtrar la señal ayuda?", "Ablación: crudo vs MA15 vs EMA15 vs Savitzky-Golay 15", 12)
    data = [
        ["Features", "MAE media", "Skill", "PR-AUC pico", "Brier"],
        ["Crudo", "0,197", "0,624", "0,446", "0,0141"],
        ["EMA15", "0,196", "0,628", "0,443", "0,0139"],
        ["MA15", "0,203", "0,617", "0,426", "0,0142"],
        ["SG15", "0,208", "0,596", "0,422", "0,0141"],
    ]
    add_table(s, data, 0.5, 1.35, 7.4, 2.2, 10)
    add_bullets(s, 8.2, 1.3, 4.6, 3.4, [
        "Media: EMA15 mejora 0,9 %; MA y SG empeoran.",
        "Pico: el crudo es el mejor o está empatado.",
        "El pico es alta frecuencia; el filtro lo atenúa.",
        "No filtres el target: cambia el problema y puede filtrar pasado.",
        "Filtro centrado: usa futuro; hay que hacerlo causal.",
    ], 10.5)
    add_text(s, 0.5, 3.8, 7.4, 1.6,
             "El filtro no es una varita mágica. Si el objetivo es el pico, quedate con el crudo y P_max15. "
             "Si el objetivo es la media, probá EMA15; no filtres el target.",
             12, NAVY, True, PP_ALIGN.CENTER)
    add_text(s, 0.5, 6.3, 12.3, 0.4,
             "Resultado de ablación: se reporta, no se usa como modelo final.",
             10, GRAY, align=PP_ALIGN.CENTER)

    # 13. Producto / siguiente paso
    s = add_slide(prs, "De modelo a servicio", "El MVP está listo; el piloto es el siguiente paso", 13)
    add_card(s, 0.5, 1.3, 6.0, 3.9, "PeakGuard",
             "Alerta temprana + explicación + reporte semanal.\n\n"
             "Valor: cargo por demanda, factor de potencia y desperdicio.\n\n"
             "Cliente: edificios sin BMS, campus, hoteles, clínicas.",
             LBLUE, BLUE, NAVY, 13, 18)
    add_card(s, 6.9, 1.3, 5.9, 3.9, "Siguiente paso",
             "Piloto de 3–6 meses con datos continuos.\n\n"
             "Tarifa real, etiquetas de eventos y calidad de datos.\n\n"
             "Después: multi-sitio y comparación normal vs regulada.",
             LGREEN, GREEN, NAVY, 13, 18)
    add_text(s, 0.5, 5.55, 12.3, 0.9,
             "MVP listo: 01 datos · 02 modelo · 03 evaluación retrospectiva. "
             "Lo que falta no es algoritmo: es continuidad y operación.",
             13, ORANGE, True, PP_ALIGN.CENTER)

    # 14. Conclusiones
    s = add_slide(prs, "Conclusiones", None, 14)
    add_bullets(s, 0.7, 1.4, 11.9, 4.8, [
        "La red de adquisición (medidor → Ethernet → switch → HaLow → servidor) permite 10 s y 0,5 s.",
        "Los picos son reales, trifásicos y cortos: 10–30 s, no ruido.",
        "Se pueden predecir como riesgo (probabilidad), no como instante exacto.",
        "La ecuación de 7 features es competitiva, interpretable y no memoriza.",
        "El filtro no mejora el pico; la cobertura es la limitación principal.",
        "El siguiente paso es un piloto de 3–6 meses, no otro modelo.",
    ], 16)
    add_text(s, 0.7, 6.35, 11.9, 0.5, "Gracias.", 26, NAVY, True)

    out = DOCS / "PeakGuard_presentacion.pptx"
    prs.save(out)
    print("OK:", out)


if __name__ == "__main__":
    build()
