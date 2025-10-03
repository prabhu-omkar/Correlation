import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


def center_window(fig):
    """Center the matplotlib window on screen (TkAgg backend)."""
    try:
        backend = matplotlib.get_backend()
        manager = fig.canvas.manager
        if 'Tk' in backend:
            win = manager.window
            win.update_idletasks()
            w = win.winfo_width()
            h = win.winfo_height()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
            win.geometry(f'+{x}+{y}')
    except Exception:
        pass  # silently skip if backend doesn't support it

# ── Load & Merge ──────────────────────────────────────────────
df_happiness = pd.read_csv('happiness_data.csv')
df_chocolate = pd.read_csv('chocolate_data.csv')
df_income    = pd.read_csv('income_data.csv')

df = pd.merge(df_happiness, df_chocolate,
              left_on='Country name', right_on='Entity', how='inner')
df = pd.merge(df, df_income,
              left_on='Country name', right_on='Country Name', how='inner')

df.rename(columns={
    'Cocoa beans - Food available for consumption (kilograms per year per capita)': 'Chocolate_kg',
    '2023': 'Income'
}, inplace=True)

df['Income'] = pd.to_numeric(df['Income'], errors='coerce')
df.dropna(subset=['Income', 'Ladder score', 'Chocolate_kg'], inplace=True)

# ── Color Palette ─────────────────────────────────────────────
BG       = '#0f0f1a'
CARD_BG  = '#1a1a2e'
ACCENT1  = '#e8a838'   # warm gold
ACCENT2  = '#4fc3f7'   # cool blue
ACCENT3  = '#81c784'   # soft green
TEXT     = '#d0d0d8'
MUTED    = '#888899'
GRID_CLR = '#2a2a3e'

plt.rcParams.update({
    'figure.facecolor': BG,
    'axes.facecolor':   CARD_BG,
    'axes.edgecolor':   GRID_CLR,
    'axes.labelcolor':  TEXT,
    'axes.grid':        True,
    'grid.color':       GRID_CLR,
    'grid.alpha':       0.5,
    'text.color':       TEXT,
    'xtick.color':      MUTED,
    'ytick.color':      MUTED,
    'font.family':      'sans-serif',
    'font.size':        11,
})


def label_points(ax, data, x, y, label_col, n=5):
    """Label the top-n points by y-value."""
    top = data.nlargest(n, y)
    for _, row in top.iterrows():
        ax.annotate(
            row[label_col], (row[x], row[y]),
            textcoords="offset points", xytext=(8, 6),
            fontsize=7.5, color=MUTED, fontstyle='italic',
            path_effects=[pe.withStroke(linewidth=2, foreground=CARD_BG)]
        )


def add_regression(ax, data, xcol, ycol, color, use_log_x=False):
    """Fit & draw a regression line clipped to data range."""
    x = np.log10(data[xcol]) if use_log_x else data[xcol].values.astype(float)
    y = data[ycol].values.astype(float)
    mask = np.isfinite(x) & np.isfinite(y)
    z = np.polyfit(x[mask], y[mask], 1)
    p = np.poly1d(z)
    xs = np.linspace(x[mask].min(), x[mask].max(), 200)
    plot_x = 10**xs if use_log_x else xs
    ax.plot(plot_x, p(xs), color=color, lw=2, ls='--', alpha=0.6, zorder=5)


def pearson_r(x, y):
    mask = np.isfinite(x) & np.isfinite(y)
    return np.corrcoef(x[mask], y[mask])[0, 1]


# ══════════════════════════════════════════════════════════════
#  SLIDE 1 — The Tempting Correlation
# ══════════════════════════════════════════════════════════════
fig1 = plt.figure(figsize=(10, 7))
center_window(fig1)

# Axes for the scatter — sits in the top portion
ax1 = fig1.add_axes([0.09, 0.44, 0.86, 0.48])  # [left, bottom, width, height]

# Color dots by income (foreshadowing)
norm_inc = (df['Income'] - df['Income'].min()) / (df['Income'].max() - df['Income'].min())
cmap = LinearSegmentedColormap.from_list('gold', ['#5c3d1a', ACCENT1, '#fff4cc'])

ax1.scatter(
    df['Ladder score'], df['Chocolate_kg'],
    c=norm_inc, cmap=cmap, s=85, alpha=0.85,
    edgecolors='black', linewidths=0.4, zorder=10
)

add_regression(ax1, df, 'Ladder score', 'Chocolate_kg', ACCENT1)

r1 = pearson_r(df['Ladder score'].values, df['Chocolate_kg'].values)

ax1.set_xlabel('Happiness Score  (World Happiness Report)', fontsize=12, labelpad=8)
ax1.set_ylabel('Chocolate Consumption  (kg / capita / yr)', fontsize=12, labelpad=8)

fig1.suptitle('Does Chocolate Buy Happiness?', fontsize=22, fontweight='bold',
              color=ACCENT1, y=0.96)

ax1.text(0.97, 0.05, f'r = {r1:.2f}', transform=ax1.transAxes,
         fontsize=13, fontweight='bold', color=ACCENT1, ha='right', va='bottom',
         bbox=dict(facecolor=BG, edgecolor=ACCENT1,
                   boxstyle='round,pad=0.4', alpha=0.9))



# ── Explanation text in the bottom region ──
lines = [
    ("AT FIRST GLANCE", dict(fontsize=13, fontweight='bold', color=ACCENT1)),
    ("", dict(fontsize=6)),
    ("There's a clear upward trend — countries that eat more chocolate per",
     dict(fontsize=11, color=TEXT)),
    ("capita also report being happier. Tempting to think chocolate = happiness!",
     dict(fontsize=11, color=TEXT)),
    ("", dict(fontsize=6)),
    ("But this is a textbook case of  CORRELATION ≠ CAUSATION.",
     dict(fontsize=11.5, fontweight='bold', color='#ff8a65')),
    ("Two variables moving together doesn't prove one causes the other.",
     dict(fontsize=10.5, color=MUTED)),
    ("A hidden third factor — a 'confounding variable' — may drive both.",
     dict(fontsize=10.5, color=MUTED)),
    ("", dict(fontsize=6)),
    ("Close this window to reveal the hidden variable  →",
     dict(fontsize=11, fontstyle='italic', color=ACCENT1)),
]

y_pos = 0.35
for text, kwargs in lines:
    fig1.text(0.5, y_pos, text, ha='center', va='top', **kwargs)
    y_pos -= 0.035

plt.show()


# ══════════════════════════════════════════════════════════════
#  SLIDE 2 — Revealing the Confounding Variable
# ══════════════════════════════════════════════════════════════
fig2 = plt.figure(figsize=(14, 6))
center_window(fig2)

fig2.suptitle('The Hidden Variable:  National Wealth',
              fontsize=20, fontweight='bold', color=ACCENT2, y=0.99)

# Two scatter axes side-by-side in the upper portion
ax2 = fig2.add_axes([0.06, 0.44, 0.41, 0.46])   # left plot
ax3 = fig2.add_axes([0.55, 0.44, 0.41, 0.46])   # right plot

# ── Left: Income → Happiness ──
ax2.scatter(df['Income'], df['Ladder score'],
            c=ACCENT2, s=70, alpha=0.7, edgecolors='black', linewidths=0.3, zorder=10)
add_regression(ax2, df, 'Income', 'Ladder score', ACCENT2, use_log_x=True)

r2 = pearson_r(np.log10(df['Income']).values, df['Ladder score'].values)
ax2.set_xscale('log')
ax2.set_title('Wealth  →  Happiness', fontsize=14, fontweight='bold',
              color=ACCENT2, pad=10)
ax2.set_xlabel('GDP per Capita  (log scale, US$)', fontsize=11, labelpad=6)
ax2.set_ylabel('Happiness Score', fontsize=11, labelpad=6)
ax2.text(0.97, 0.05, f'r = {r2:.2f}', transform=ax2.transAxes,
         fontsize=13, fontweight='bold', color=ACCENT2, ha='right', va='bottom',
         bbox=dict(facecolor=BG, edgecolor=ACCENT2,
                   boxstyle='round,pad=0.4', alpha=0.9))


# ── Right: Income → Chocolate ──
ax3.scatter(df['Income'], df['Chocolate_kg'],
            c=ACCENT3, s=70, alpha=0.7, edgecolors='black', linewidths=0.3, zorder=10)
add_regression(ax3, df, 'Income', 'Chocolate_kg', ACCENT3, use_log_x=True)

r3 = pearson_r(np.log10(df['Income']).values, df['Chocolate_kg'].values)
ax3.set_xscale('log')
ax3.set_title('Wealth  →  Chocolate', fontsize=14, fontweight='bold',
              color=ACCENT3, pad=10)
ax3.set_xlabel('GDP per Capita  (log scale, US$)', fontsize=11, labelpad=6)
ax3.set_ylabel('Chocolate Consumption  (kg / capita)', fontsize=11, labelpad=6)
ax3.text(0.97, 0.05, f'r = {r3:.2f}', transform=ax3.transAxes,
         fontsize=13, fontweight='bold', color=ACCENT3, ha='right', va='bottom',
         bbox=dict(facecolor=BG, edgecolor=ACCENT3,
                   boxstyle='round,pad=0.4', alpha=0.9))


# ── Explanation text — bottom region ──
lines2 = [
    ("THE REAL STORY", dict(fontsize=13, fontweight='bold', color=ACCENT2)),
    ("", dict(fontsize=5)),
    ("When we introduce GDP per capita, the mystery vanishes:",
     dict(fontsize=11, color=TEXT)),
    ("", dict(fontsize=5)),
    ("Wealth → Happiness  —  Richer nations invest in healthcare, education & safety nets,",
     dict(fontsize=10.5, color=ACCENT2)),
    ("all of which are strong predictors of life satisfaction.",
     dict(fontsize=10.5, color=MUTED)),
    ("", dict(fontsize=5)),
    ("Wealth → Chocolate  —  Chocolate is a processed, imported luxury good.",
     dict(fontsize=10.5, color=ACCENT3)),
    ("Higher disposable income simply means more purchasing power for it.",
     dict(fontsize=10.5, color=MUTED)),
    ("", dict(fontsize=5)),
    ("CONCLUSION:  Chocolate doesn't cause happiness.  NATIONAL WEALTH is the",
     dict(fontsize=11.5, fontweight='bold', color='#ff8a65')),
    ("confounding variable that independently drives both upward.",
     dict(fontsize=11.5, fontweight='bold', color='#ff8a65')),
    ("This is why we say  \"correlation does not imply causation.\"",
     dict(fontsize=10.5, fontstyle='italic', color=MUTED)),
]

y_pos = 0.38
for text, kwargs in lines2:
    fig2.text(0.5, y_pos, text, ha='center', va='top', **kwargs)
    y_pos -= 0.030

plt.show()              
# Pearson correlation metrics calculation
