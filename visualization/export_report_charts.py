"""Export the existing ten charts without outer titles, conclusions or footnotes.

Run: python visualization/export_report_charts.py
Original chart scripts, PNGs, tables and source data are never overwritten.
This renders the existing plot functions; it does not crop or edit raster images.
"""
from pathlib import Path
import hashlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTPUT = HERE / 'figures_report'
sys.path.insert(0, str(HERE))
import visualize_charts_1_to_5 as first
import visualize_charts_6_to_10 as last

NAMES = {
    'chart_1_quy_mo_vs_khan_gia': '01_quy_mo_va_khan_gia',
    'chart_2_suc_hut_theo_vong': '02_khan_gia_theo_vong',
    'chart_3_phan_phoi_lap_day_san': '03_ty_le_lap_day_san',
    'chart_4_co_cau_cach_biet_vong_bang': '04_co_cau_cach_biet',
    'chart_5_ty_le_thang_dam_bang_vs_knockout': '05_thang_dam_theo_vong',
    '06_thang_dam_theo_luot': '06_thang_dam_theo_luot',
    '07_elo_va_cach_biet': '07_elo_va_cach_biet',
    '08_cach_phan_dinh_knockout': '08_cach_phan_dinh_knockout',
    '09_heatmap_qua_90_phut': '09_heatmap_qua_90_phut',
    '10_cua_duoi_di_tiep': '10_cua_duoi_di_tiep',
}


def data_signature(fig):
    """Check that removing decorations leaves all plotted numeric marks unchanged."""
    marks = []
    for ax in fig.axes:
        marks.append((ax.get_xlim(), ax.get_ylim(), ax.get_xlabel(), ax.get_ylabel()))
        for line in ax.lines:
            marks.append((repr(line.get_xdata()), repr(line.get_ydata())))
        for patch in ax.patches:
            marks.append(repr(patch.get_path().vertices))
        for collection in ax.collections:
            marks.append((repr(collection.get_offsets()), repr(collection.get_array())))
    return hashlib.sha256(repr(marks).encode('utf-8')).hexdigest()


def main():
    OUTPUT.mkdir(exist_ok=True)
    protected = list((ROOT/'production').glob('*.csv')) + list((HERE/'tables').glob('*.csv'))
    protected += list(HERE.glob('chart_*.png')) + list((HERE/'figures').glob('*.png'))
    protected += list((ROOT/'reports').glob('*.docx'))
    original = {p: hashlib.sha256(p.read_bytes()).digest() for p in protected}
    savefig = Figure.savefig
    write_table = last.write_table
    exported = []

    def clean_save(fig, filename, *args, **kwargs):
        stem = Path(filename).stem
        if stem not in NAMES:
            raise ValueError(f'Unexpected figure: {stem}')
        # Hide only the redundant X-axis heading, not tick labels or data.
        for ax in fig.axes:
            if ax.get_xlabel().strip().casefold().startswith((
                'kỷ nguyên thể thức world cup', 'kỉ nguyên thể thức world cup',
                'năm diễn ra world cup',
            )):
                ax.set_xlabel('')
        before = data_signature(fig)
        # All figure-level text is an outer heading or footnote in these scripts.
        for text in list(fig.texts):
            text.remove()
        fig._suptitle = None
        # Keep chart 07's panel labels: they identify eras and correlation samples.
        for ax in fig.axes:
            if stem != '07_elo_va_cach_biet':
                ax.set_title('')
                ax.set_title('', loc='left')
                ax.set_title('', loc='right')
        fig.tight_layout(pad=.8, rect=(0, 0, 1, 1))
        assert data_signature(fig) == before, f'Plotted data changed: {stem}'
        target = OUTPUT / (NAMES[stem]+'.png')
        savefig(fig, target, dpi=300, bbox_inches='tight', pad_inches=.08)
        exported.append(target.name)
        print(f'Exported: {target.name}')

    try:
        Figure.savefig = clean_save
        # Calculations remain identical; do not rewrite the source chart tables.
        last.write_table = lambda *args, **kwargs: None
        for plot in [first.plot_chart_1, first.plot_chart_2, first.plot_chart_3,
                     first.plot_chart_4, first.plot_chart_5]:
            plot()
        last.sns.set_theme(style='whitegrid', font='DejaVu Sans')
        df = pd.read_csv(ROOT/'production/worldcup_master_cleaned.csv')
        df = df[df.Year.between(1930, 2026)].copy()
        df['Era'] = np.select([df.Year.lt(1982), df.Year.le(1994), df.Year.le(2022)],
                              last.ERAS[:3], default=last.ERAS[3])
        first_group, knockout = last.stage_filters(df)
        years = sorted(df.Year.unique())
        notes = []
        last.plot_chart_6(df, first_group, notes)
        last.plot_chart_7(df, first_group, notes)
        last.plot_chart_8(df, knockout, years, notes)
        last.plot_chart_9(df, knockout, years, notes)
        last.plot_chart_10(df, knockout, years, notes)
    finally:
        Figure.savefig = savefig
        last.write_table = write_table
    assert len(exported) == 10 and len(set(exported)) == 10
    assert all(hashlib.sha256(p.read_bytes()).digest() == digest for p,digest in original.items())
    print('PASS: 10 clean PNGs; plotted values, axes, original PNGs, tables, source CSVs and Word reports unchanged.')


if __name__ == '__main__':
    main()
