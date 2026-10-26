"""
HỆ THỐNG TRỰC QUAN HÓA DỮ LIỆU WORLD CUP (1930 - 2026)
Bộ biểu đồ từ Mục 1 đến Mục 5 (Câu hỏi 1 & Câu hỏi 2)
Tuân thủ đầy đủ quy chuẩn trong khdl.txt và DATA_DICTIONARY.md
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Thiết lập thẩm mỹ và hỗ trợ font tiếng Việt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Segoe UI', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", palette="deep")

# Đường dẫn dữ liệu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_PATH = os.path.join(BASE_DIR, 'production', 'worldcup_master_cleaned.csv')
TOURN_PATH = os.path.join(BASE_DIR, 'production', 'dim_tournaments.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'visualization')
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(MASTER_PATH)
dim_tourn = pd.read_csv(TOURN_PATH)

# Chuẩn hóa nhãn Kỷ nguyên thể thức
era_labels = {
    '16 Teams (1930-1978)': 'Kỷ nguyên 16 đội\n(1930 - 1978)',
    '24 Teams (1982-1994)': 'Kỷ nguyên 24 đội\n(1982 - 1994)',
    '32 Teams (1998-2022)': 'Kỷ nguyên 32 đội\n(1998 - 2022)',
    '48 Teams (2026)': 'Kỷ nguyên 48 đội\n(2026 - Mô phỏng)'
}

# --------------------------------------------------------------------------------
# BIỂU ĐỒ 1: QUY MÔ GIẢI ĐẤU VÀ LƯỢNG KHÁN GIẢ MỖI TRẬN (COMBO CHART)
# --------------------------------------------------------------------------------
def plot_chart_1():
    print("Đang vẽ Biểu đồ 1: Quy mô giải đấu và lượng khán giả mỗi trận...")
    fig, ax1 = plt.subplots(figsize=(14, 7), dpi=300)

    years = dim_tourn['Year'].values
    matches = dim_tourn['MatchesPlayed'].values
    mean_att = dim_tourn['Mean_Attendance'].values

    # Màu sắc cột phân theo kỷ nguyên hoặc phân biệt 2026
    colors = ['#2b5c8f' if y < 2026 else '#e26d5c' for y in years]
    bars = ax1.bar(
        years, matches, color=colors, alpha=0.75, width=2.4, edgecolor='black', linewidth=0.8,
        label='Tổng số trận đấu (Cột trái)'
    )

    # Đánh dấu cột 2026 là mô phỏng bằng hoa văn sọc (hatch)
    bars[-1].set_hatch('///')
    bars[-1].set_edgecolor('#c92a2a')

    # Trục phụ cho Khán giả trung bình/trận
    ax2 = ax1.twinx()
    
    # Vẽ đường lịch sử (1930-2022)
    hist_mask = years <= 2022
    line_hist = ax2.plot(
        years[hist_mask], mean_att[hist_mask],
        color='#1b4965', marker='o', markersize=6, linewidth=2.5,
        label='Khán giả TB/trận (Lịch sử)'
    )
    
    # Nối từ 2022 sang 2026 bằng nét đứt (Mô phỏng)
    sim_mask = years >= 2022
    line_sim = ax2.plot(
        years[sim_mask], mean_att[sim_mask],
        color='#d90429', marker='s', markersize=7, linewidth=2.5, linestyle='--',
        label='Khán giả TB/trận (2026 Mô phỏng)'
    )

    # Đánh dấu các mốc mở rộng thể thức bằng đường gióng dọc
    expansion_years = [1982, 1998, 2026]
    expansion_labels = ['Mở rộng 24 đội (1982)', 'Mở rộng 32 đội (1998)', 'Mở rộng 48 đội (2026)']
    for ey, elab in zip(expansion_years, expansion_labels):
        ax1.axvline(x=ey - 2, color='#7f7f7f', linestyle=':', linewidth=1.5, alpha=0.8)
        ax1.text(
            ey - 2, ax1.get_ylim()[1] * 0.92, f'  {elab}',
            rotation=90, verticalalignment='top', fontsize=9.5, fontweight='semibold', color='#333333'
        )

    # Chú thích điểm ngoại lệ USA 1994
    usa_att = dim_tourn[dim_tourn['Year'] == 1994]['Mean_Attendance'].values[0]
    ax2.annotate(
        f'Kỷ lục USA 1994:\n{usa_att:,.0f} người/trận\n(Sân vận động siêu lớn)',
        xy=(1994, usa_att), xytext=(1985, usa_att + 5500),
        arrowprops=dict(facecolor='#1b4965', arrowstyle='->', lw=1.5),
        fontsize=9, fontweight='semibold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#edf6f9', edgecolor='#83c5be')
    )

    # Định dạng trục
    ax1.set_xlabel('Năm diễn ra World Cup', fontsize=12, fontweight='bold', labelpad=10)
    ax1.set_ylabel('Tổng số trận đấu trong giải', fontsize=12, fontweight='bold', color='#2b5c8f', labelpad=10)
    ax2.set_ylabel('Lượng khán giả trung bình mỗi trận (người)', fontsize=12, fontweight='bold', color='#1b4965', labelpad=10)
    
    ax1.set_xticks(years)
    ax1.set_xticklabels(years, rotation=45, ha='right', fontsize=9)
    ax1.set_ylim(0, 115)
    ax2.set_ylim(15000, 80000)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

    # Tiêu đề và ghi chú
    plt.title(
        'BIỂU ĐỒ 1: QUY MÔ SỐ TRẬN VÀ LƯỢNG KHÁN GIẢ TRUNG BÌNH MỖI TRẬN (1930 - 2026)\n'
        'Việc tăng số trận không làm giảm sức hút khán giả; World Cup 2026 tiếp tục duy trì lượng khán giả cao kỷ lục',
        fontsize=13, fontweight='bold', pad=18
    )

    # Gộp legend 2 trục
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

    fig.text(0.12, 0.01, '* Ghi chú: Dữ liệu năm 2026 là mô phỏng/ước tính theo tài liệu quy chuẩn; cột có hoa văn gạch sọc và nét đứt đỏ.', fontsize=8.5, fontstyle='italic', color='#555555')
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'chart_1_quy_mo_vs_khan_gia.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f" -> Đã lưu: {output_path}")


# --------------------------------------------------------------------------------
# BIỂU ĐỒ 2: SỨC HÚT KHÁN GIẢ THEO TỪNG VÒNG ĐẤU (LINE CHART)
# --------------------------------------------------------------------------------
def plot_chart_2():
    print("Đang vẽ Biểu đồ 2: Sức hút khán giả theo từng vòng đấu...")
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)

    # Lọc Vòng bảng đầu tiên
    group_df = df[df['Stage_Detail'] == 'First Group Stage']
    group_att = group_df.groupby('Year')['Attendance'].mean()

    # Lọc Vòng Loại trực tiếp (Early Knockout + Deep Knockout)
    ko_df = df[df['Stage_Group'].isin(['2. Early Knockout', '3. Deep Knockout'])]
    ko_att = ko_df.groupby('Year')['Attendance'].mean()

    # Hợp nhất theo tất cả các năm
    all_years = sorted(df['Year'].unique())
    comp_df = pd.DataFrame(index=all_years)
    comp_df['Group_Attendance'] = group_att
    comp_df['Knockout_Attendance'] = ko_att

    # Vẽ đường Vòng bảng (1930-2022) & mô phỏng 2026
    hist_years = [y for y in all_years if y <= 2022 and y in group_att.index]
    ax.plot(
        hist_years, [group_att[y] for y in hist_years],
        color='#2a9d8f', marker='o', markersize=6, linewidth=2.5,
        label='Vòng bảng đầu tiên (Lịch sử)'
    )
    # Nối sang 2026 nét đứt
    ax.plot(
        [2022, 2026], [group_att[2022], group_att[2026]],
        color='#2a9d8f', marker='o', markersize=6, linewidth=2.5, linestyle='--',
        label='Vòng bảng (2026 Mô phỏng)'
    )

    # Vẽ đường Knockout (1930-2022) & mô phỏng 2026
    hist_ko_years = [y for y in all_years if y <= 2022 and y in ko_att.index]
    ax.plot(
        hist_ko_years, [ko_att[y] for y in hist_ko_years],
        color='#e76f51', marker='s', markersize=6, linewidth=2.5,
        label='Vòng Loại trực tiếp (Lịch sử)'
    )
    # Nối sang 2026 nét đứt
    ax.plot(
        [2022, 2026], [ko_att[2022], ko_att[2026]],
        color='#e76f51', marker='s', markersize=6, linewidth=2.5, linestyle='--',
        label='Vòng Knockout (2026 Mô phỏng)'
    )

    # Đánh dấu các mốc mở rộng thể thức
    expansion_years = [1982, 1998, 2026]
    expansion_labels = ['Mở rộng 24 đội (1982)', 'Mở rộng 32 đội (1998)', 'Mở rộng 48 đội (2026)']
    for ey, elab in zip(expansion_years, expansion_labels):
        ax.axvline(x=ey, color='#7f7f7f', linestyle=':', linewidth=1.5, alpha=0.7)
        ax.text(
            ey - 0.4, 76000, f'{elab}',
            rotation=90, verticalalignment='top', fontsize=9, fontweight='semibold', color='#444444'
        )

    # Chú thích ngoại lệ lịch sử
    ax.annotate(
        '1934 & 1938:\nKhông có vòng bảng',
        xy=(1936, 20000), fontsize=8.5, fontstyle='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#f8f9fa', edgecolor='#ced4da')
    )
    ax.annotate(
        '1950:\nKhông có vòng knockout',
        xy=(1950, 48000), xytext=(1946, 60000),
        arrowprops=dict(facecolor='#555555', arrowstyle='->', lw=1.2),
        fontsize=8.5, fontstyle='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#f8f9fa', edgecolor='#ced4da')
    )

    ax.set_xlabel('Năm diễn ra World Cup', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylabel('Khán giả trung bình / trận (người)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_xticks(all_years)
    ax.set_xticklabels(all_years, rotation=45, ha='right', fontsize=9)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax.set_ylim(10000, 85000)

    plt.title(
        'BIỂU ĐỒ 2: SO SÁNH SỨC HÚT KHÁN GIẢ GIỮA VÒNG BẢNG VÀ VÒNG KNOCKOUT (1930 - 2026)\n'
        'Vòng Knockout luôn giữ ưu thế khán giả vượt trội; vòng bảng tăng trưởng ổn định theo thời gian',
        fontsize=13, fontweight='bold', pad=18
    )
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)

    fig.text(0.12, 0.01, '* Ghi chú: Dữ liệu năm 2026 là mô phỏng/ước tính (biểu thị bằng nét đứt). 1934-1938 đá loại trực tiếp; 1950 đá vòng tròn chung kết.', fontsize=8.5, fontstyle='italic', color='#555555')
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'chart_2_suc_hut_theo_vong.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f" -> Đã lưu: {output_path}")


# --------------------------------------------------------------------------------
# BIỂU ĐỒ 3: PHÂN PHỐI TỶ LỆ LẤP ĐẦY SÂN VẬN ĐỘNG (BOXPLOT THEO 4 GIAI ĐOẠN)
# --------------------------------------------------------------------------------
def plot_chart_3():
    print("Đang vẽ Biểu đồ 3: Phân phối tỷ lệ lấp đầy sân vận động (Boxplot)...")
    fig, ax = plt.subplots(figsize=(13, 7), dpi=300)

    # Chuẩn bị dữ liệu: Gom vòng đấu thành Vòng bảng vs Knockout
    box_df = df.copy()
    box_df['Stage_Type'] = box_df['Stage_Group'].apply(
        lambda x: 'Vòng bảng' if x == '1. Group Stage' else 'Vòng Knockout'
    )
    box_df['Era_Label'] = box_df['Era_Format'].map(era_labels)

    # Thứ tự các kỷ nguyên
    era_order = [
        era_labels['16 Teams (1930-1978)'],
        era_labels['24 Teams (1982-1994)'],
        era_labels['32 Teams (1998-2022)'],
        era_labels['48 Teams (2026)']
    ]

    palette = {'Vòng bảng': '#457b9d', 'Vòng Knockout': '#e63946'}
    sns.boxplot(
        data=box_df, x='Era_Label', y='Occupancy_Rate', hue='Stage_Type',
        order=era_order, palette=palette, ax=ax,
        width=0.6, fliersize=3.5, boxprops=dict(alpha=0.85),
        medianprops=dict(color='black', linewidth=1.8)
    )

    # Hiển thị đường tham chiếu 100% lấp đầy
    ax.axhline(100, color='#2b2d42', linestyle='--', linewidth=1.2, alpha=0.7, label='Mức tối đa 100% sức chứa')

    ax.set_xlabel('Kỷ nguyên thể thức World Cup', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylabel('Tỷ lệ lấp đầy sân (%) [Occupancy Rate]', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylim(20, 108)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}%'))

    plt.title(
        'BIỂU ĐỒ 3: PHÂN PHỐI TỶ LỆ LẤP ĐẦY SÂN VẬN ĐỘNG THEO 4 KỶ NGUYÊN THỂ THỨC (BOXPLOT)\n'
        'Tỷ lệ lấp đầy liên tục tăng trưởng qua các lần mở rộng, đạt mức bão hòa >90% từ kỷ nguyên 32 đội',
        fontsize=13, fontweight='bold', pad=18
    )

    # Annotate trung vị
    for i, era in enumerate(era_order):
        era_sub = box_df[box_df['Era_Label'] == era]
        med_grp = era_sub[era_sub['Stage_Type'] == 'Vòng bảng']['Occupancy_Rate'].median()
        med_ko = era_sub[era_sub['Stage_Type'] == 'Vòng Knockout']['Occupancy_Rate'].median()
        if not np.isnan(med_grp):
            ax.text(i - 0.16, med_grp - 5, f'{med_grp:.1f}%', ha='center', fontsize=8.5, fontweight='bold', color='#1d3557')
        if not np.isnan(med_ko):
            ax.text(i + 0.16, med_ko + 2.5, f'{med_ko:.1f}%', ha='center', fontsize=8.5, fontweight='bold', color='#9b2226')

    ax.legend(title='Phân loại vòng đấu', loc='lower right', frameon=True, facecolor='white', framealpha=0.9)
    fig.text(0.12, 0.01, '* Lưu ý: Sức chứa sân có thành phần ước tính theo tài liệu quy chuẩn; Kỷ nguyên 48 đội (2026) là dữ liệu mô phỏng.', fontsize=8.5, fontstyle='italic', color='#555555')
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'chart_3_phan_phoi_lap_day_san.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f" -> Đã lưu: {output_path}")


# --------------------------------------------------------------------------------
# BIỂU ĐỒ 4: CƠ CẤU CÁCH BIỆT TỶ SỐ Ở VÒNG BẢNG (100% STACKED BAR CHART)
# --------------------------------------------------------------------------------
def plot_chart_4():
    print("Đang vẽ Biểu đồ 4: Cơ cấu cách biệt tỷ số ở vòng bảng (100% Stacked Bar)...")
    fig, ax = plt.subplots(figsize=(15, 7.5), dpi=300)

    # Lọc vòng bảng đầu tiên
    group_df = df[df['Stage_Detail'] == 'First Group Stage'].copy()

    # Tính ma trận tỷ lệ % theo Margin_Category
    ct = pd.crosstab(group_df['Year'], group_df['Margin_Category'], normalize='index') * 100

    # Đảm bảo thứ tự 3 nhóm chuẩn
    cat_order = [
        '1. Sat Nut / Hoa (<=1 ban)',
        '2. Cach Biet (2 ban)',
        '3. Thang Dam (>=3 ban)'
    ]
    ct = ct[cat_order]

    years = ct.index.values
    sat_nut = ct['1. Sat Nut / Hoa (<=1 ban)'].values
    cach_biet = ct['2. Cach Biet (2 ban)'].values
    thang_dam = ct['3. Thang Dam (>=3 ban)'].values

    # Bảng màu hài hòa, phân cực rõ rệt
    colors = ['#2a9d8f', '#e9c46a', '#e76f51']
    bar_width = 2.4

    # Vẽ từng tầng cột chồng
    p1 = ax.bar(years, sat_nut, width=bar_width, color=colors[0], edgecolor='white', linewidth=0.8, label='Sát nút / Hòa (≤ 1 bàn)')
    p2 = ax.bar(years, cach_biet, bottom=sat_nut, width=bar_width, color=colors[1], edgecolor='white', linewidth=0.8, label='Cách biệt vừa phải (2 bàn)')
    p3 = ax.bar(years, thang_dam, bottom=sat_nut + cach_biet, width=bar_width, color=colors[2], edgecolor='white', linewidth=0.8, label='Thắng đậm áp đảo (≥ 3 bàn)')

    # Đánh dấu cột 2026 mô phỏng
    p1[-1].set_hatch('///')
    p2[-1].set_hatch('///')
    p3[-1].set_hatch('///')
    p1[-1].set_edgecolor('#333333')
    p2[-1].set_edgecolor('#333333')
    p3[-1].set_edgecolor('#333333')

    # Hiển thị % bên trong thanh cột nếu đủ diện tích
    for i, yr in enumerate(years):
        # Tầng 1: Sát nút
        v1 = sat_nut[i]
        if v1 >= 12:
            ax.text(yr, v1 / 2, f'{v1:.0f}%', ha='center', va='center', fontsize=7.5, fontweight='bold', color='white')
        # Tầng 2: Cách biệt 2 bàn
        v2 = cach_biet[i]
        if v2 >= 12:
            ax.text(yr, v1 + v2 / 2, f'{v2:.0f}%', ha='center', va='center', fontsize=7.5, fontweight='bold', color='#264653')
        # Tầng 3: Thắng đậm
        v3 = thang_dam[i]
        if v3 >= 12:
            ax.text(yr, v1 + v2 + v3 / 2, f'{v3:.0f}%', ha='center', va='center', fontsize=7.5, fontweight='bold', color='white')

    # Đường phân cách các kỳ mở rộng
    for ey, elab in zip([1982, 1998, 2026], ['Mở rộng 24 đội', 'Mở rộng 32 đội', 'Mở rộng 48 đội']):
        ax.axvline(x=ey - 2, color='#333333', linestyle=':', linewidth=1.5, alpha=0.7)
        ax.text(ey - 2, 102, elab, ha='center', fontsize=9, fontweight='semibold', color='#333333')

    ax.set_xlabel('Năm diễn ra World Cup (Các kỳ có tổ chức vòng bảng)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylabel('Tỷ lệ phần trăm số trận đấu (%)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45, ha='right', fontsize=9)
    ax.set_ylim(0, 110)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}%'))

    plt.title(
        'BIỂU ĐỒ 4: CƠ CẤU CÁCH BIỆT TỶ SỐ TRONG CÁC TRẬN ĐẤU VÒNG BẢNG (1930 - 2026)\n'
        'Tỷ lệ trận đấu sát nút (≤ 1 bàn) duy trì áp đảo 55% - 70%; các kỳ mở rộng không làm bùng nổ trận một chiều',
        fontsize=13, fontweight='bold', pad=20
    )
    ax.legend(loc='lower left', bbox_to_anchor=(0.01, 0.02), frameon=True, facecolor='white', framealpha=0.95, fontsize=10)

    fig.text(0.12, 0.01, '* Lưu ý: Kỳ 1934 và 1938 không tổ chức vòng bảng. Năm 2026 là dữ liệu mô phỏng (cột có hoa văn sọc gạch).', fontsize=8.5, fontstyle='italic', color='#555555')
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'chart_4_co_cau_cach_biet_vong_bang.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f" -> Đã lưu: {output_path}")


# --------------------------------------------------------------------------------
# BIỂU ĐỒ 5: TỶ LỆ THẮNG ĐẬM Ở VÒNG BẢNG SO VỚI VÒNG KNOCKOUT ĐẦU TIÊN (DUAL LINE)
# --------------------------------------------------------------------------------
def plot_chart_5():
    print("Đang vẽ Biểu đồ 5: Tỷ lệ thắng đậm ở vòng bảng vs vòng knockout đầu tiên...")
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)

    # 1. Tỷ lệ thắng đậm ở Vòng bảng đầu tiên
    group_df = df[df['Stage_Detail'] == 'First Group Stage']
    group_blowout = group_df.groupby('Year')['Margin_Category'].apply(
        lambda x: (x == '3. Thang Dam (>=3 ban)').mean() * 100
    )

    # 2. Tỷ lệ thắng đậm ở Vòng Knockout đầu tiên (Early Knockout: R16 từ 1986-2022, R32 năm 2026, và R16 các năm 1934, 1938)
    early_ko = df[df['Stage_Detail'] == 'Early Knockout']
    early_ko_blowout = early_ko.groupby('Year')['Margin_Category'].apply(
        lambda x: (x == '3. Thang Dam (>=3 ban)').mean() * 100
    )

    all_years = sorted(list(set(group_blowout.index.tolist() + early_ko_blowout.index.tolist())))

    # Vẽ đường Vòng bảng (Lịch sử + Mô phỏng 2026)
    grp_hist_years = [y for y in group_blowout.index if y <= 2022]
    ax.plot(
        grp_hist_years, [group_blowout[y] for y in grp_hist_years],
        color='#1d3557', marker='o', markersize=6.5, linewidth=2.5,
        label='Vòng bảng đầu tiên (Lịch sử)'
    )
    if 2026 in group_blowout.index and 2022 in group_blowout.index:
        ax.plot(
            [2022, 2026], [group_blowout[2022], group_blowout[2026]],
            color='#1d3557', marker='o', markersize=6.5, linewidth=2.5, linestyle='--',
            label='Vòng bảng (2026 Mô phỏng)'
        )

    # Vẽ đường Vòng Knockout đầu tiên (Lịch sử + Mô phỏng 2026)
    ko_hist_years = [y for y in early_ko_blowout.index if y <= 2022]
    ax.plot(
        ko_hist_years, [early_ko_blowout[y] for y in ko_hist_years],
        color='#e63946', marker='s', markersize=6.5, linewidth=2.5,
        label='Vòng Knockout đầu tiên [R16/R32] (Lịch sử)'
    )
    if 2026 in early_ko_blowout.index and 2022 in early_ko_blowout.index:
        ax.plot(
            [2022, 2026], [early_ko_blowout[2022], early_ko_blowout[2026]],
            color='#e63946', marker='s', markersize=6.5, linewidth=2.5, linestyle='--',
            label='Vòng Knockout đầu tiên (2026 Mô phỏng)'
        )

    # Đánh dấu các mốc mở rộng thể thức
    for ey, elab in zip([1982, 1998, 2026], ['Mở rộng 24 đội (1982)', 'Mở rộng 32 đội (1998)', 'Mở rộng 48 đội (2026)']):
        ax.axvline(x=ey, color='#6c757d', linestyle=':', linewidth=1.5, alpha=0.7)
        ax.text(ey - 0.4, 52, elab, rotation=90, verticalalignment='top', fontsize=9, fontweight='semibold', color='#333333')

    # Chú thích các giai đoạn vắng bóng vòng Knockout đầu tiên
    ax.axvspan(1954, 1982, color='#ced4da', alpha=0.25, label='1954-1982: Vào thẳng Tứ kết hoặc đá Vòng bảng 2')
    ax.text(1968, 48, '1954-1982:\nKhông có vòng R16\n(Đá Tứ kết hoặc Vòng bảng 2)', ha='center', fontsize=8.5, fontstyle='italic', color='#495057')

    ax.set_xlabel('Năm diễn ra World Cup', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylabel('Tỷ lệ trận thắng đậm (Cách biệt ≥ 3 bàn) [%]', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_xticks(all_years)
    ax.set_xticklabels(all_years, rotation=45, ha='right', fontsize=9)
    ax.set_ylim(-2, 60)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}%'))

    plt.title(
        'BIỂU ĐỒ 5: TỶ LỆ TRẬN THẮNG ĐẬM (≥ 3 BÀN) Ở VÒNG BẢNG SO VỚI VÒNG KNOCKOUT ĐẦU TIÊN (1930 - 2026)\n'
        'Xu hướng thắng đậm ở vòng bảng giảm dần theo thời gian; vòng Knockout đầu tiên duy trì tính giằng co',
        fontsize=13, fontweight='bold', pad=18
    )
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)

    fig.text(0.12, 0.01, '* Ghi chú: Thắng đậm định nghĩa là chênh lệch tỷ số ≥ 3 bàn. Vòng Knockout đầu tiên là R16 (1934, 1938, 1986-2022) và R32 (2026 mô phỏng).', fontsize=8.5, fontstyle='italic', color='#555555')
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'chart_5_ty_le_thang_dam_bang_vs_knockout.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f" -> Đã lưu: {output_path}")


if __name__ == '__main__':
    print("=" * 70)
    print("BẮT ĐẦU TẠO 5 BIỂU ĐỒ TRỰC QUAN HÓA THEO YÊU CẦU...")
    print("=" * 70)
    plot_chart_1()
    plot_chart_2()
    plot_chart_3()
    plot_chart_4()
    plot_chart_5()
    print("=" * 70)
    print("HOÀN THÀNH TẤT CẢ 5 BIỂU ĐỒ TRONG THƯ MỤC VISUALIZATION!")
    print("=" * 70)
