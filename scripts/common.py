from pathlib import Path
import json, sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = ROOT / 'outputs'
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

def save_table(df, name):
    df.to_csv(OUT / (name + '.csv'), index=False, float_format='%.6f')

def store_db(tables):
    with sqlite3.connect(DATA / 'analytics.sqlite') as db:
        for name, df in tables.items():
            df.to_sql(name, db, index=False, if_exists='replace')

def save_dashboard(rows, metrics, series, title, subtitle, units, columns):
    payload = dict(rows=rows, metrics=metrics, series=series, title=title,
                   subtitle=subtitle, units=units, columns=columns)
    (OUT / 'dashboard_data.json').write_text(json.dumps(payload, indent=2))
    template = (ROOT / 'dashboard' / 'template.html').read_text()
    (ROOT / 'dashboard' / 'index.html').write_text(template.replace('__PAYLOAD__', json.dumps(payload).replace('</', r'<\/')))

def chart(df, x, y, title, filename):
    fig, ax = plt.subplots(figsize=(11, 4.8), layout='constrained')
    fig.set_facecolor('#101b30'); ax.set_facecolor('#101b30')
    ax.plot(df[x].astype(str), df[y], color='#5eead4', marker='o', linewidth=2)
    ax.set_title(title, color='white', loc='left', fontsize=16, pad=18)
    ax.tick_params(colors='#cbd5e1', axis='both'); ax.tick_params(axis='x', rotation=45)
    for spine in ax.spines.values(): spine.set_color('#334155')
    ax.grid(axis='y', color='#334155', alpha=.6)
    ax.set_ylabel(y.replace('_', ' ').title(), color='#cbd5e1')
    fig.savefig(OUT / filename, dpi=150); plt.close(fig)
