"""Ajudantes de matplotlib para gráficos explicativos (skill storytelling-charts).

Uso:
    from sc_style import setup, declutter, title_block, label_line_end, label_bars, GRAY, ACCENT

    setup()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ... desenhe tudo em GRAY e a série de interesse em ACCENT ...
    declutter(ax)
    title_block(fig, "Conclusão em uma frase", "subtítulo: o que é, unidade, período")
    fig.savefig("grafico.png", dpi=200, bbox_inches="tight")
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

GRAY = "#A6A6A6"        # contexto
GRAY_DARK = "#595959"   # texto secundário, eixos
TEXT = "#262626"        # títulos
ACCENT = "#1F6FB2"      # destaque principal (azul: seguro para daltonismo)
ACCENT_2 = "#E07B00"    # segundo destaque, se indispensável (laranja contrasta com azul)


def setup() -> None:
    """Padrões globais: sem borda, fontes neutras, texto cinza-escuro."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.edgecolor": GRAY,
        "axes.labelcolor": GRAY_DARK,
        "axes.titlelocation": "left",
        "axes.grid": False,
        "xtick.color": GRAY_DARK,
        "ytick.color": GRAY_DARK,
        "legend.frameon": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def declutter(ax, keep_left: bool = False, keep_bottom: bool = True) -> None:
    """Remove bordas e marcas desnecessárias."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_visible(keep_left)
    ax.spines["bottom"].set_visible(keep_bottom)
    ax.tick_params(length=0)
    if ax.get_legend():
        ax.get_legend().remove()


def title_block(fig, title: str, subtitle: str = "", source: str = "") -> None:
    """Título de conclusão + subtítulo alinhados à esquerda; fonte no rodapé."""
    fig.text(0.0, 1.06, title, fontsize=15, color=TEXT, ha="left", va="bottom", weight="bold",
             transform=fig.transFigure)
    if subtitle:
        fig.text(0.0, 1.0, subtitle, fontsize=11, color=GRAY_DARK, ha="left", va="bottom",
                 transform=fig.transFigure)
    if source:
        fig.text(0.0, -0.06, source, fontsize=9, color=GRAY, ha="left", va="top", transform=fig.transFigure)


def label_line_end(ax, x, y, text: str, color: str, bold: bool = False, dx: float = 0.01) -> None:
    """Rótulo direto no fim de uma linha, na cor da série (substitui a legenda)."""
    xmin, xmax = ax.get_xlim()
    ax.annotate(text, xy=(x, y), xytext=(x + (xmax - xmin) * dx, y), color=color, va="center",
                fontweight="bold" if bold else "normal", annotation_clip=False)


def label_bars(ax, bars, fmt: str = "{:.0f}", only=None, color: str = GRAY_DARK, horizontal: bool = True) -> None:
    """Valores no fim das barras. `only` = índices a rotular (None = todas)."""
    for i, b in enumerate(bars):
        if only is not None and i not in only:
            continue
        if horizontal:
            v = b.get_width()
            ax.text(v, b.get_y() + b.get_height() / 2, " " + fmt.format(v), va="center", ha="left", color=color)
        else:
            v = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, v, fmt.format(v), va="bottom", ha="center", color=color)


def highlight_colors(n: int, idx, accent: str = ACCENT) -> list[str]:
    """Lista de cores: cinza para todas, cor de destaque nos índices `idx`."""
    idx = {idx} if isinstance(idx, int) else set(idx)
    return [accent if i in idx else GRAY for i in range(n)]


if __name__ == "__main__":
    # Demonstração: antes e depois.
    import sys

    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set"]
    infantil = [210, 205, 230, 310, 360, 395, 420, 440, 450]
    adulto = [380, 370, 390, 385, 380, 395, 400, 390, 385]
    esporte = [150, 160, 155, 158, 165, 160, 170, 168, 172]

    setup()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = range(len(meses))
    for serie, nome in ((adulto, "Adulto"), (esporte, "Esporte")):
        ax.plot(x, serie, color=GRAY, lw=2)
        label_line_end(ax, len(meses) - 1, serie[-1], nome, GRAY)
    ax.plot(x, infantil, color=ACCENT, lw=3)
    label_line_end(ax, len(meses) - 1, infantil[-1], "Infantil", ACCENT, bold=True)
    ax.axvline(2.5, color=GRAY, lw=1, ls=":")
    ax.text(2.6, 465, "troca de fornecedor", color=GRAY_DARK, fontsize=10)
    ax.set_xticks(list(x), meses)
    ax.set_ylim(0, 500)
    ax.set_ylabel("devoluções por mês")
    declutter(ax)
    title_block(fig, "Devoluções da linha infantil dobraram após a troca de fornecedor",
                "Devoluções mensais por linha de produto, jan–set", "Fonte: dados ilustrativos.")
    out = sys.argv[1] if len(sys.argv) > 1 else "demo.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print("salvo em", out)
