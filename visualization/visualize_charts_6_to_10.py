"""Render charts 06, 07, 08, 09, 10 for repository data 1930–2026, without modifying inputs.

Run: python visualization/visualize_charts_6_to_10.py
Charts 07/10 use PRE-TOURNAMENT Elo by the user's explicit choice.
2026 is included as supplied by the user, without a simulation label.

BẢN ĐỒ MÃ NGUỒN (tìm tên hàm bằng Ctrl+F):
  - write_table(), save(): xuất bảng CSV đối chiếu và ảnh PNG 300 DPI.
  - stage_filters(): chọn vòng bảng đầu và knockout chính trong bộ nhớ.
  - plot_chart_6(): hình 06 — cột nhóm tỷ lệ thắng đậm theo lượt vòng bảng.
  - plot_chart_7(): hình 07 — scatter chênh lệch Elo trước giải và tỷ số.
  - knockout_sample(): chuẩn bị mẫu chung cho hình 08 và 09.
  - plot_chart_8(): hình 08 — cột chồng phân định knockout.
  - plot_chart_9(): hình 09 — heatmap tỷ lệ quá 90 phút theo kỳ/vòng.
  - plot_chart_10(): hình 10 — cửa dưới theo Elo trước giải đi tiếp.
  - main(): đọc dữ liệu, gọi các hàm và ghi danh mục kết quả.

Script .py đủ để tái tạo hình; .ipynb là notebook tùy chọn để chạy từng ô.
Các chú thích dưới đây giải thích từng bước, không thay đổi dữ liệu đầu vào.
"""
from pathlib import Path
import hashlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter

# PHẦN 1 — CẤU HÌNH: đường dẫn, giai đoạn, nhãn và màu dùng chung.
ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
FIGURES = OUT / 'figures'
TABLES = OUT / 'tables'
ERAS = ['Trước 1982', '24 đội (1982–1994)', '32 đội (1998–2022)', '48 đội (2026)']
CONFEDS = ['UEFA', 'CONMEBOL', 'CONCACAF', 'CAF', 'AFC', 'OFC']
ROUNDS = ['Vòng 32 đội', 'Vòng 16 đội', 'Tứ kết', 'Bán kết', 'Chung kết']
CAT = ['Thắng ≥2 bàn trong 90 phút', 'Thắng 1 bàn trong 90 phút',
       'Hiệp phụ, không luân lưu', 'Luân lưu']
COLORS = ['#457b9d', '#2a9d8f', '#e9c46a', '#e76f51']


def write_table(data, name):
    """Lưu bảng số liệu đứng sau hình; giữ NA, không đổi thành 0."""
    data.to_csv(TABLES / f'{name}.csv', index=False, encoding='utf-8-sig', na_rep='NA')


def save(fig, name, note):
    """Chú thích một dòng theo kiểu hình 01–05; giải thích dài xem danh mục."""
    short_notes = {
        '06_thang_dam_theo_luot': 'Tỷ lệ gộp theo giai đoạn; nhãn = % (số trận thắng đậm/tổng trận).',
        '07_elo_va_cach_biet': 'Elo trước giải; mỗi chấm là một trận, đường đen là trung vị theo nhóm Elo.',
        '08_cach_phan_dinh_knockout': 'Loại tranh hạng ba và cặp đá lại; 1950 không có knockout, 1974/1978 chỉ có chung kết.',
        '09_heatmap_qua_90_phut': 'Ô xám: không có vòng/mẫu hợp lệ; 1950 không có knockout. Nhãn = % và số trận/tổng trận.',
        '10_cua_duoi_di_tiep': 'Cửa dưới: thấp hơn ≥100 Elo trước giải; mỗi cặp tính một lần, loại tranh hạng ba.',
    }
    for ax in fig.axes:
        if ax.get_xlabel() == 'Năm tổ chức':
            ax.set_xlabel('Năm diễn ra World Cup', fontsize=12, fontweight='bold', labelpad=9)
    fig.tight_layout(rect=(0, .055, 1, .98))
    fig.text(.035, .012, '* Nguồn: dataset của nhóm, 1930–2026. ' + short_notes.get(name, note.replace('\n', ' ')),
             fontsize=8.5, fontstyle='italic', va='bottom', color='#555555')
    fig.savefig(FIGURES / f'{name}.png', dpi=300, bbox_inches='tight')
    plt.close(fig)


def expansion_marks(ax):
    """Mốc mở rộng có nhãn trực tiếp, không cần người xem tra chú giải."""
    for year, label in [(1982,'24 đội'), (1998,'32 đội'), (2026,'48 đội')]:
        ax.axvline(year, color='#64748b', linestyle=':', linewidth=1.2, alpha=.6, zorder=0)
        ax.text(year, .96, label, transform=ax.get_xaxis_transform(), ha='center', va='top',
                fontsize=9, color='#475569', bbox=dict(facecolor='white',edgecolor='none',alpha=.85,pad=1))


def no_knockout_1950(ax):
    """1950 là không áp dụng, không phải dữ liệu thiếu hoặc tỷ lệ 0%."""
    ax.axvspan(1947.5, 1952.5, color='#e2e8f0', alpha=.65, zorder=0)
    ax.text(1950, 48, '1950\nKhông có\nvòng loại\ntrực tiếp', ha='center', va='center',
            fontsize=9, color='#475569', bbox=dict(boxstyle='round,pad=.4',
            facecolor='#f8fafc', edgecolor='#94a3b8'))


def stage_filters(df):
    """Chỉ tạo bộ lọc: không ghi lại master và không sửa pipeline."""
    first = df.Stage_Detail.eq('First Group Stage')
    # Explicit first-group filter: Group 6 in 1950 is the final group.
    first &= ~(df.Year.eq(1950) & df.Stage.eq('Group 6'))
    third = df.Stage.str.contains('third|bronze', case=False, na=False)
    ko = df.Stage_Group.isin(['2. Early Knockout', '3. Deep Knockout']) & ~third
    return first, ko


# PHẦN 2 — BIỂU ĐỒ 06: TỶ LỆ THẮNG ĐẬM THEO LƯỢT VÒNG BẢNG.
# X: giai đoạn thể thức; Y: % trận cách biệt >=3; mỗi nhóm gồm lượt 1, 2, 3.
def plot_chart_6(df, first, notes):
    # Bước 1: chọn vòng bảng đầu, kiểm tra lịch ba lượt tương thích từng kỳ.
    source = df[first].copy()
    rows, excluded, included = [], [], []
    for year, subset in source.groupby('Year'):
        ordinary = subset[subset.Matchday.isin(['Matchday 1', 'Matchday 2', 'Matchday 3'])]
        team_counts = pd.concat([ordinary['Home Team Name'], ordinary['Away Team Name']]).value_counts()
        counts = ordinary.Matchday.value_counts()
        # Restrict to compatible 3-game schedules and provided chronological labels.
        valid = team_counts.eq(3).all() and len(counts) == 3 and counts.nunique() == 1
        if not valid:
            excluded.append(dict(Year=year, Reason='Lịch vòng bảng không tương thích 3 lượt cân bằng'))
            continue
        included.append(year)
        for md, group in ordinary.groupby('Matchday'):
            goals = pd.to_numeric(group.Goal_Margin, errors='coerce')
            good = goals.notna() & goals.ge(0)
            rows.append(dict(Year=year, Era=group.Era.iloc[0], Matchday=md,
                N=int(good.sum()), Missing=int((~good).sum()), Blowouts=int(goals[good].ge(3).sum()),
                Excluded_Playoffs=len(subset) - len(ordinary)))
    # Bước 2: xuất mẫu từng kỳ và cộng tử số/mẫu số theo giai đoạn + lượt.
    detail = pd.DataFrame(rows)
    write_table(detail, '06_mau_theo_ky_va_luot')
    write_table(pd.DataFrame(excluded, columns=['Year', 'Reason']), '06_cac_ky_loai')
    summary = detail.groupby(['Era', 'Matchday'], sort=False).agg(
        N=('N', 'sum'), Missing=('Missing', 'sum'), Blowouts=('Blowouts', 'sum'),
        Years=('Year', lambda s: ', '.join(map(str, sorted(s.unique()))))).reset_index()
    summary['Rate'] = 100 * summary.Blowouts / summary.N.replace(0, np.nan)
    write_table(summary, '06_thang_dam_theo_luot')
    # Bước 3: vẽ cột nhóm; nhãn trên cột là số trận thắng đậm/tổng trận hợp lệ.
    fig, ax = plt.subplots(figsize=(14, 7))
    for j, md in enumerate(['Matchday 1', 'Matchday 2', 'Matchday 3']):
        subset = summary[summary.Matchday.eq(md)].set_index('Era').reindex(ERAS)
        positions = np.arange(len(ERAS)) + (j - 1) * .24
        bars = ax.bar(positions, subset.Rate, width=.23, color=COLORS[j], label=f'Lượt {j+1}')
        for bar, (_, r) in zip(bars, subset.iterrows()):
            if pd.notna(r.Rate):
                ax.annotate(f'{r.Rate:.1f}%\n({int(r.Blowouts)}/{int(r.N)} trận)', (bar.get_x()+bar.get_width()/2, bar.get_height()),
                            xytext=(0, 5), textcoords='offset points', ha='center', fontsize=9)
    ax.set(xticks=range(len(ERAS)), xticklabels=ERAS, ylabel='Tỷ lệ trận thắng cách biệt từ 3 bàn', ylim=(0, 45),
           title='06. Lượt nào có nhiều trận thắng đậm hơn?\nSo sánh ba lượt của vòng bảng đầu tiên')
    ax.set_xlabel('Kỷ nguyên thể thức World Cup', fontsize=12, fontweight='bold', labelpad=10)
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.grid(axis='x', visible=False)
    ax.legend(title='Màu cột = lượt thi đấu', loc='upper left', ncol=3)
    save(fig, '06_thang_dam_theo_luot', 'Cách đọc: cột cao hơn = tỷ lệ thắng đậm cao hơn. Ví dụ 5/24 = 5 trận thắng đậm trong 24 trận.\n'
         'Chỉ lấy lịch 3 lượt tương thích theo nhãn cung cấp; loại play-off. Danh sách kỳ trong CSV.')
    notes.append(f'06: ĐÃ VẼ; n={int(summary.N.sum())}; kỳ dùng: {included}. Kiểm tra tương thích lịch, không xác minh nguồn ngoài.')


# PHẦN 3 — CHUẨN BỊ MẪU CHUNG CHO HÌNH 08 VÀ 09 (CHƯA VẼ).
def knockout_sample(df, ko):
    """Chuẩn hóa nhãn vòng trong bộ nhớ, tách đá lại và phân định không chồng."""
    sample = df[ko].copy()
    sample['Round'] = sample.Stage.str.lower().map({
        'preliminary round': 'Vòng 16 đội', 'first round': 'Vòng 16 đội',
        'round of 16': 'Vòng 16 đội', 'round of 32': 'Vòng 32 đội', 'quarter-finals': 'Tứ kết', 'quarter-final': 'Tứ kết',
        'semi-finals': 'Bán kết', 'semi-final': 'Bán kết', 'final': 'Chung kết'})
    sample['Exception'] = ''
    # Repeated pair in the same round identifies replay-related observations;
    # exclude the entire pair from the main modern-resolution denominator.
    sample['Pair'] = sample.apply(lambda r: '|'.join(sorted([r['Home Team Name'], r['Away Team Name']])), axis=1)
    replay = sample.duplicated(['Year', 'Round', 'Pair'], keep=False)
    sample.loc[replay, 'Exception'] = 'Cặp có đá lại'
    sample['Category'] = pd.NA
    for idx, r in sample.iterrows():
        if r.Exception:
            continue
        if pd.isna(r.Round):
            sample.loc[idx, 'Exception'] = 'Nhãn vòng chưa xác định'
        elif r.Is_Penalties == True:
            sample.loc[idx, 'Category'] = CAT[3]
        elif r.Is_Extra_Time == True:
            sample.loc[idx, 'Category'] = CAT[2]
        elif r.Is_Extra_Time == False and r.Is_Penalties == False and r.Goal_Margin >= 1 and str(r.Match_Resolution).startswith(('1. Normal Time', '2. Normal Time')):
            sample.loc[idx, 'Category'] = CAT[0] if r.Goal_Margin >= 2 else CAT[1]
        else:
            sample.loc[idx, 'Exception'] = 'Thiếu/xung đột trạng thái phân định'
    sample['Overtime'] = sample.Category.isin(CAT[2:])
    return sample


# PHẦN 4 — BIỂU ĐỒ 08 VÀ 09: HAI HÌNH DÙNG CÙNG MẪU KNOCKOUT.
def plot_chart_8(df, ko, years, notes):
    # Bước chung: loại tranh hạng ba qua bộ lọc ko; xuất cả mẫu và ngoại lệ.
    sample = knockout_sample(df, ko)
    write_table(sample, '08_09_mau_tran_va_ngoai_le')
    valid = sample[sample.Category.notna()]
    # BIỂU ĐỒ 08 — cột chồng 100% bốn cách phân định, theo từng năm.
    # Mẫu số chỉ gồm trận đủ điều kiện; trận đá lại/không rõ ghi riêng.
    rows = []
    for year in years:
        all_matches = sample[sample.Year.eq(year)]
        matches = valid[valid.Year.eq(year)]
        for cat in CAT:
            count = int(matches.Category.eq(cat).sum())
            rows.append(dict(Year=year, Category=cat, Numerator=count, N=len(matches),
                Exceptions=len(all_matches)-len(matches), Rate=100*count/len(matches) if len(matches) else np.nan))
    table = pd.DataFrame(rows)
    write_table(table, '08_cach_phan_dinh_knockout')
    fig, ax = plt.subplots(figsize=(18, 8))
    bottom = np.zeros(len(years))
    for cat, color in zip(CAT, COLORS):
        vals = table[table.Category.eq(cat)].set_index('Year').reindex(years).Rate.to_numpy()
        ax.bar(years, vals, bottom=bottom, width=2.6, color=color, label=cat, edgecolor='white', linewidth=.8)
        for y, height, base in zip(years, vals, bottom):
            if np.isfinite(height) and height >= 10:
                ax.text(y, base+height/2, f'{height:.1f}%', ha='center', va='center',
                        fontsize=8, fontweight='bold', color='#25334a' if color==COLORS[2] else 'white')
        bottom += np.nan_to_num(vals)
    for y in years:
        row = table[table.Year.eq(y)].iloc[0]
        if row.N:
            ax.text(y, 102, f'n={int(row.N)}', ha='center', fontsize=8, color='#475569')
    no_knockout_1950(ax)
    ax.set(xticks=years, ylabel='Tỷ trọng trận theo cách phân định', ylim=(0, 112),
           title='08. Các trận loại trực tiếp được phân định như thế nào?\nMỗi cột là 100% số trận hợp lệ của một kỳ World Cup')
    ax.set_xlabel('Năm diễn ra World Cup', fontsize=12, fontweight='bold', labelpad=10)
    expansion_marks(ax)
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.grid(axis='x',visible=False)
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Màu = cách xác định đội thắng', loc='upper center', bbox_to_anchor=(.5, -.18), ncol=4, fontsize=9)
    save(fig, '08_cach_phan_dinh_knockout', f'Cách đọc: số trong mảng màu = tỷ lệ; n trên cột = số trận được tính. Loại tranh hạng ba và {sample.Category.isna().sum()} trận ngoại lệ.\n'
         '1950 đá vòng bảng chung kết, không có vòng loại trực tiếp; khoảng xám không phải tỷ lệ 0%. Nhãn 90 phút theo nguồn.')
    notes.append(f'08: ĐÃ VẼ; n hợp lệ={len(valid)}, ngoại lệ={len(sample)-len(valid)}.')


def plot_chart_9(df, ko, years, notes):
    """Hình 09: heatmap tỷ lệ quá 90 phút, mỗi ô có mẫu số hợp lệ."""
    sample = knockout_sample(df, ko)
    valid = sample[sample.Category.notna()]
    # BIỂU ĐỒ 09 — heatmap: X = năm, Y = vòng, màu = % quá 90 phút.
    # Mỗi ô có tỷ lệ và n; không tồn tại/không đủ mẫu để NA, không tô thành 0%.
    rows = []
    for rnd in ROUNDS:
        for year in years:
            all_matches = sample[sample.Year.eq(year) & sample.Round.eq(rnd)]
            matches = valid[valid.Year.eq(year) & valid.Round.eq(rnd)]
            n = len(matches)
            k = int(matches.Overtime.sum())
            rows.append(dict(Year=year, Round=rnd, Numerator=k, N=n,
                Exceptions=len(all_matches)-n, Rate=100*k/n if n else np.nan))
    heat = pd.DataFrame(rows)
    write_table(heat, '09_heatmap_qua_90_phut')
    values = heat.pivot(index='Round', columns='Year', values='Rate').reindex(index=ROUNDS, columns=years)
    labels = heat.assign(Label=heat.apply(lambda r: f'{r.Rate:.1f}%\n{r.Numerator}/{r.N}' if r.N else '', axis=1)).pivot(index='Round', columns='Year', values='Label').reindex(index=ROUNDS, columns=years)
    fig, ax = plt.subplots(figsize=(20, 8))
    ax.set_facecolor('#e2e8f0')
    sns.heatmap(values, annot=labels, fmt='', vmin=0, vmax=100, cmap='YlOrRd', linewidths=.5,
                cbar_kws={'label':'Tỷ lệ quá 90 phút (%)'}, ax=ax, annot_kws={'fontsize':8})
    for row in range(len(ROUNDS)):
        for col in range(len(years)):
            if pd.isna(values.iloc[row,col]):
                ax.text(col+.5,row+.5,'—',ha='center',va='center',color='#64748b',fontsize=11)
    ax.set(title='09. Ở vòng nào, trận đấu thường kéo dài quá 90 phút?\nMàu đậm hơn = tỷ lệ hiệp phụ / luân lưu cao hơn', xlabel='Năm tổ chức', ylabel='Vòng loại trực tiếp')
    # Ý nghĩa ô xám được ghi ngay trong dòng chú thích; tránh lặp một legend riêng.
    save(fig, '09_heatmap_qua_90_phut', 'Cách đọc ô: 25% và 1/4 nghĩa là 1 trong 4 trận kéo dài quá 90 phút; 0% nghĩa là có trận nhưng không có hiệp phụ.\n'
         'Ô xám không phải 0%. Năm 1950 không có knockout; R32 chỉ có năm 2026. Gồm bàn thắng vàng; loại tranh hạng ba và cặp đá lại.')
    notes.append(f'09: ĐÃ VẼ; cùng mẫu hợp lệ n={len(valid)}; bảng có n theo ô.')


def plot_chart_7(df, first, notes):
    """Hình 07: sức mạnh TRƯỚC GIẢI và tỷ số; mỗi giai đoạn một ô."""
    # Bước 1: chỉ lấy vòng bảng đầu, loại trận hiệp phụ/luân lưu lịch sử.
    base = df[first & df.Is_Extra_Time.eq(False) & df.Is_Penalties.eq(False)].copy()
    for column in ['Home_Team_Elo', 'Away_Team_Elo', 'Goal_Margin']:
        base[column] = pd.to_numeric(base[column], errors='coerce')
    good = base[['Home_Team_Elo', 'Away_Team_Elo', 'Goal_Margin']].notna().all(axis=1)
    sample = base[good].copy()
    sample['Elo_Gap'] = (sample.Home_Team_Elo - sample.Away_Team_Elo).abs()
    write_table(sample, '07_elo_va_cach_biet_mau_tran')
    # Bước 2: bảng bắt buộc về mức chênh lệch Elo và bao phủ, theo kỳ/giai đoạn.
    for key, suffix in [('Year', 'theo_ky'), ('Era', 'theo_giai_doan')]:
        rows = []
        for label, subset in base.groupby(key, sort=False):
            eligible = sample[sample[key].eq(label)]
            rows.append({key: label, 'N_Base': len(subset), 'N_Elo': len(eligible),
                'Missing_Elo': int(subset[['Home_Team_Elo', 'Away_Team_Elo']].isna().any(axis=1).sum()),
                'Coverage': 100*len(eligible)/len(subset), 'Mean_Gap': eligible.Elo_Gap.mean(),
                'Median_Gap': eligible.Elo_Gap.median(),
                'Gap_GE100_Rate': 100*eligible.Elo_Gap.ge(100).mean(),
                'Spearman': eligible.Elo_Gap.rank().corr(eligible.Goal_Margin.rank()) if len(eligible)>2 else np.nan})
        write_table(pd.DataFrame(rows), '07_elo_'+suffix)
    # Bước 3: scatter không jitter; đường nối là trung vị theo nhóm gap 100 Elo.
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True, sharey=True)
    for ax, era, color in zip(axes.flat, ERAS, COLORS):
        subset = sample[sample.Era.eq(era)]
        ax.scatter(subset.Elo_Gap, subset.Goal_Margin, s=30, alpha=.45, color=color, label='Mỗi chấm = một trận')
        bins = subset.assign(Gap_Bin=(subset.Elo_Gap//100)*100).groupby('Gap_Bin').agg(
            X=('Elo_Gap', 'median'), Y=('Goal_Margin', 'median'), N=('MatchID', 'size'))
        bins = bins[bins.N.ge(5)]
        ax.plot(bins.X, bins.Y, color='#333333', marker='o', lw=1.5, label='Trung vị (nhóm ≥5 trận)')
        rho = subset.Elo_Gap.rank().corr(subset.Goal_Margin.rank())
        ax.set_title(f'{era} — {len(subset)} trận\nTương quan thứ hạng (Spearman): {rho:.2f}', fontsize=10)
        ax.set(xlabel='Chênh lệch sức mạnh trước giải (điểm Elo)', ylabel='Chênh lệch tỷ số (bàn)')
        ax.axhline(3, color='#94a3b8',ls=':',lw=1)
        ax.grid(alpha=.35)
    axes.flat[0].legend(fontsize=8,loc='upper right')
    fig.suptitle('07. Chênh lệch sức mạnh có đi cùng tỷ số cách biệt hơn?\nSang phải = lệch Elo hơn; lên cao = lệch tỷ số hơn', fontsize=13, fontweight='bold')
    save(fig, '07_elo_va_cach_biet', 'Chấm = trận; đường đen = trung vị từng nhóm 100 Elo (nhóm ít nhất 5 trận); đường ngang chấm ở 3 bàn = ngưỡng thắng đậm.\n'
         'Spearman gần 0: liên hệ đơn điệu yếu; gần 1: liên hệ cùng chiều mạnh. Không chứng minh nhân quả. Dùng Elo trước giải, chỉ vòng bảng đầu 90 phút.')
    notes.append(f'07: ĐÃ VẼ; n={len(sample)}; dùng Elo trước giải, có bảng bao phủ và chênh lệch Elo.')


def plot_chart_10(df, ko, years, notes):
    """Hình 10: cửa dưới theo Elo TRƯỚC GIẢI; mỗi cặp đá lại chỉ đếm một lần."""
    source = knockout_sample(df, ko)
    ties = []
    # Bước 1: gom cặp bằng kỳ + vòng + hai đội; dùng kết quả trận cuối có sẵn.
    for (year, rnd, pair), matches in source.groupby(['Year', 'Round', 'Pair'], dropna=False):
        matches = matches.sort_values(['Datetime', 'MatchID'])
        opening, final = matches.iloc[0], matches.iloc[-1]
        home, away = opening['Home Team Name'], opening['Away Team Name']
        eh, ea = opening.Home_Team_Elo, opening.Away_Team_Elo
        winner = final.Winner
        valid_elo = pd.notna(eh) and pd.notna(ea)
        known = winner in [home, away]
        gap = abs(eh-ea) if valid_elo else np.nan
        underdog = home if valid_elo and eh<ea else away if valid_elo and ea<eh else None
        # Kiểm tra đội thắng có xuất hiện ở vòng kế tiếp (nếu có), không tự sửa Winner.
        rank = {r: i for i, r in enumerate(ROUNDS)}
        later = source[source.Year.eq(year) & source.Round.map(rank).eq(rank.get(rnd, -2)+1)]
        if known and not later.empty:
            known = winner in (set(later['Home Team Name']) | set(later['Away Team Name']))
        ties.append(dict(Year=year, Round=rnd, Pair=pair, Matches_In_Tie=len(matches),
            Opening_MatchID=opening.MatchID, Home_Elo_PreTournament=eh, Away_Elo_PreTournament=ea,
            Elo_Gap=gap, Underdog=underdog, Winner=winner, Elo_Available=valid_elo,
            Advancement_Known=known, Upset=bool(known and winner==underdog)))
    ties = pd.DataFrame(ties)
    write_table(ties, '10_mau_cap_knockout')
    # Bước 2: ngưỡng chính 100; bảng độ nhạy thêm 50 và 150; CI Wilson 95%.
    rows = []
    for threshold in [50, 100, 150]:
        for year in years:
            all_ties = ties[ties.Year.eq(year)]
            eligible = all_ties[all_ties.Elo_Available & all_ties.Advancement_Known & all_ties.Elo_Gap.ge(threshold)]
            n, k = len(eligible), int(eligible.Upset.sum())
            p = k/n if n else np.nan
            if n:
                z = 1.95996398454
                center = (p+z*z/(2*n))/(1+z*z/n)
                half = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
                low, high = 100*(center-half), 100*(center+half)
            else:
                low, high = np.nan, np.nan
            rows.append(dict(Year=year, Threshold=threshold, Total_Ties=len(all_ties),
                Ties_With_Elo=int(all_ties.Elo_Available.sum()),
                Elo_Coverage=100*all_ties.Elo_Available.mean() if len(all_ties) else np.nan,
                Unknown_Advancement=int((~all_ties.Advancement_Known).sum()), N=n, Upsets=k,
                Rate=100*p, Wilson_Lower=low, Wilson_Upper=high))
    table = pd.DataFrame(rows)
    write_table(table, '10_cua_duoi_di_tiep_va_do_nhay')
    # Bước 3: biểu đồ điểm + khoảng tin cậy, ghi trực tiếp tử số/mẫu số.
    main = table[table.Threshold.eq(100) & table.N.gt(0)]
    fig, ax = plt.subplots(figsize=(18, 8))
    ax.errorbar(main.Year, main.Rate, yerr=[np.maximum(0, main.Rate-main.Wilson_Lower),
                np.maximum(0, main.Wilson_Upper-main.Rate)], fmt='none', capsize=4, ecolor='#94a3b8',elinewidth=1.3,zorder=1)
    for small, marker_color in [(False,'#1b4965'),(True,'white')]:
        subset = main[main.N.lt(5).eq(small)]
        ax.scatter(subset.Year,subset.Rate,s=65,facecolor=marker_color,edgecolor='#1b4965',linewidth=1.5,zorder=3)
    for _, row in main.iterrows():
        ax.annotate(f'{row.Rate:.1f}%\n({int(row.Upsets)}/{int(row.N)})', (row.Year,row.Rate),
                    xytext=(0, 9), textcoords='offset points', ha='center', fontsize=8,color='#1e293b')
    expansion_marks(ax)
    no_knockout_1950(ax)
    ax.set(xticks=years, ylim=(-5, 115), ylabel='Tỷ lệ đội cửa dưới giành quyền đi tiếp', xlabel='Năm tổ chức',
        title='10. Đội bị đánh giá thấp hơn có thường giành quyền đi tiếp?\nCửa dưới = thấp hơn đối thủ ít nhất 100 điểm Elo trước giải')
    ax.set_yticks(range(0,101,20))
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.grid(axis='x',visible=False)
    ax.legend(handles=[Line2D([],[],marker='o',color='none',markerfacecolor='#1b4965',markeredgecolor='#1b4965',label='Tỷ lệ quan sát (ít nhất 5 cặp)'),
        Line2D([],[],marker='o',color='none',markerfacecolor='white',markeredgecolor='#1b4965',label='Dưới 5 cặp: mẫu nhỏ'),
        Line2D([],[],color='#94a3b8',marker='_',label='Thanh xám: khoảng tin cậy 95%')],loc='upper left',bbox_to_anchor=(0,-.10),ncol=3,fontsize=9)
    ax.tick_params(axis='x', rotation=45)
    save(fig, '10_cua_duoi_di_tiep', 'Cách đọc: 23% (3/13) = 3 lần cửa dưới đi tiếp trong 13 cặp đủ điều kiện. Thanh dài hơn = ước lượng kém chắc chắn hơn.\n'
        'Mỗi cặp chỉ tính một lần, gồm kết quả đá lại; loại tranh hạng ba. Khoảng tin cậy Wilson 95%; 1950 không có knockout. Ngưỡng 50/150 trong CSV.')
    notes.append(f'10: ĐÃ VẼ; {len(ties)} cặp đầu vào, ngưỡng 100 có n={int(main.N.sum())}; Elo trước giải, Wilson 95%.')


# ĐIỂM CHẠY CHÍNH: mỗi hàm plot_chart_N vẽ đúng một biểu đồ.
def main():
    FIGURES.mkdir(exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    sns.set_theme(style='whitegrid', font='DejaVu Sans')
    inputs = list((ROOT / 'production').glob('*.csv')) + [OUT / 'README.md']
    original = {p: hashlib.sha256(p.read_bytes()).digest() for p in inputs if p.is_file()}
    df = pd.read_csv(ROOT / 'production/worldcup_master_cleaned.csv')
    df = df[df.Year.between(1930, 2026)].copy()
    df['Era'] = np.select([df.Year.lt(1982), df.Year.le(1994), df.Year.le(2022)], ERAS[:3], default=ERAS[3])
    first, ko = stage_filters(df)
    years = sorted(df.Year.unique())
    notes = ['DANH MỤC BIỂU ĐỒ CÒN THIẾU (06–10)',
        'Phạm vi: 1930–2026 theo xác nhận của người dùng; không thay đổi hình 01–05, README hoặc CSV nguồn.',
        'Hình 07/10 dùng Elo trước giải theo lựa chọn của người dùng, không phải Elo trước từng trận.',
        'Câu 2: 06, 07. Câu 3: 08, 09, 10. Đã bỏ hình liên đoàn, đánh số lại hình cửa dưới từ 11 thành 10.',
        'Các cột/mẫu số và NA được lưu trong tables/.',
        'Lưu ý đầu vào: 1950 Group 6 không thuộc mẫu vòng bảng đầu (chỉ lọc trong bộ nhớ).']
    # Vẽ hình 06.
    plot_chart_6(df, first, notes)
    # Vẽ hình 07 bằng Elo trước giải.
    plot_chart_7(df, first, notes)
    # Vẽ hình 08 và 09 bằng cùng mẫu knockout đủ điều kiện.
    plot_chart_8(df, ko, years, notes)
    plot_chart_9(df, ko, years, notes)
    # Vẽ hình 10 bằng Elo trước giải và kết quả cuối từng cặp.
    plot_chart_10(df, ko, years, notes)
    assert all(hashlib.sha256(p.read_bytes()).digest() == digest for p, digest in original.items()), 'Input changed'
    notes.append('Đã kiểm tra SHA-256: CSV production và README (nếu có) giữ nguyên.')
    # Giữ danh mục giải thích 10 hình; nhật ký kỹ thuật xuất sang tệp riêng.
    (OUT / 'trang_thai_xuat_bieu_do.txt').write_text('\n'.join(notes)+'\n', encoding='utf-8')
    print('\n'.join(notes))


if __name__ == '__main__':
    main()
