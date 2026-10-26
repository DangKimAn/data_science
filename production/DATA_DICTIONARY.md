# TỪ ĐIỂN DỮ LIỆU & HƯỚNG DẪN VISUALIZE (DATA DICTIONARY)
**Dự án:** Phân tích Dữ liệu World Cup 2026 (16 $\to$ 24 $\to$ 32 $\to$ 48 đội)  
**Tệp dữ liệu chính bàn giao:** `worldcup_master_cleaned.csv` (1.068 trận, 1930–2026, 52 cột, tích hợp Elo & Hạt giống Vòng bảng).  
**Bảng Dimension bổ trợ:** `dim_tournaments.csv`, `dim_stadiums.csv`, `dim_confederations.csv`, `dim_team_elo.csv`, `dim_group_standings.csv`, `dim_qualifiers_summary.csv` (23 kỳ), `dim_financials.csv` (23 chu kỳ).

---

## 1.1 CẤU TRÚC CÁC BẢNG DIMENSION BỔ TRỢ

### A. `dim_qualifiers_summary.csv` (Quy mô Vòng loại qua 23 kỳ - TV3 / Intro Slide)
- `Year`: Năm World Cup (1930 - 2026).
- `Host_Country`: Quốc gia đăng cai.
- `Era_Format`: Kỷ nguyên thể thức (16, 24, 32, 48 Teams).
- `Teams_In_Qualifiers`: Tổng số liên đoàn tham gia vòng loại (tăng từ 13 lên 211).
- `Teams_In_Finals`: Số đội lọt vào VCK (13 -> 48).
- `Matches_In_Qualifiers`: Số trận đấu diễn ra ở vòng loại (lên tới 920 trận ở 2026).
- `Qualification_Rate`: Tỷ lệ giành vé vào VCK = $(Teams\_Finals / Teams\_Qualifiers) \times 100\%$.

### B. `dim_financials.csv` (Doanh thu & Tiền thưởng FIFA - TV1 Thương mại)
- `Year`: Kỳ giải đấu (1930 - 2026).
- `Host_Country`: Quốc gia đăng cai.
- `Era_Format`: Kỷ nguyên thể thức.
- `Total_Revenue_USD_M`: Doanh thu chu kỳ 4 năm của FIFA (Triệu USD - $1.9B năm 1998 -> $11B năm 2026).
- `Prize_Money_USD_M`: Tổng quỹ tiền thưởng chia cho các đội (Triệu USD - $20M năm 1982 -> $652M năm 2026).
- `Champion_Payout_USD_M`: Tiền thưởng cho đội vô địch (Triệu USD - $1.4M năm 1982 -> $50M năm 2026).
- `Runner_Up_Payout_USD_M`: Tiền thưởng cho đội Á quân (Triệu USD - $0.9M năm 1982 -> $35M năm 2026).
- `TV_Rights_Share_Pct`: Tỷ trọng doanh thu từ bản quyền truyền hình (%).
- `Prize_Share_Of_Revenue_Pct`: Tỷ lệ tiền thưởng trên tổng doanh thu (%).
- `Revenue_Growth_Index_1998_Base`: Chỉ số tăng trưởng doanh thu lấy mốc năm 1998 = 100.0 (năm 2026 đạt 578.9).

### C. `dim_dead_rubbers.csv` (Chi tiết 249 trận Matchday 3 & Phân loại tính chất thủ tục - TV2)
- `MatchID`: Mã định danh duy nhất của trận đấu.
- `Year`, `Era_Format`, `Stage`, `Datetime`: Thông tin giải đấu và thời gian thi đấu.
- `Home Team Name`, `Away Team Name`: Hai đội chạm trán ở lượt cuối vòng bảng.
- `Home_Pre_Match_Status`, `Away_Pre_Match_Status`: Trạng thái toán học của từng đội trước giờ bóng lăn (`Qualified`, `Eliminated`, `Contending`).
- `Match_Stakes`: Phân loại 4 nhóm (`1. Both Qualified`, `2. Both Eliminated`, `3. One-sided Dead Rubber`, `4. Decisive / High Stakes`).
- `Is_Dead_Rubber`: Cờ Boolean (`True` nếu trận đấu có yếu tố thủ tục).
- `Is_Full_Dead_Rubber`: Cờ Boolean (`True` nếu cả 2 đội đều đã an bài số phận).
- `Home Team Goals`, `Away Team Goals`, `Total_Goals`, `Goal_Margin`: Kết quả và số bàn thắng.

---

---

## 1. DANH SÁCH CÁC CỘT TRONG `worldcup_master_cleaned.csv`

| Tên cột | Kiểu dữ liệu | Mô tả chi tiết | Phục vụ biểu đồ của ai? |
| :--- | :--- | :--- | :--- |
| `Year` | Int | Năm diễn ra kỳ World Cup (1930 đến 2026). | Cả nhóm |
| `Country` | String | Quốc gia đăng cai giải đấu. | Cả nhóm |
| `Stage` | String | Tên vòng đấu nguyên bản (ví dụ: `Group A`, `Round of 16`, `Final`). | Cả nhóm |
| `Era_Format` | Categorical | Kỷ nguyên thể thức: `16 Teams (1930-1978)`, `24 Teams (1982-1994)`, `32 Teams (1998-2022)`, `48 Teams (2026)`. | **Trục chính cho cả 3 thành viên** |
| `Stage_Group` | Categorical | 3 phân khúc chuẩn: `1. Group Stage`, `2. Early Knockout` (R32/R16), `3. Deep Knockout` (Tứ kết $\to$ Chung kết). | **TV1 & TV3** |
| `Stage_Detail` | Categorical | Chi tiết: `First Group Stage`, `Second Group Stage` (1974/78/82), `Early Knockout`, `Deep Knockout`. | Phân tích bổ trợ |
| `Matchday` | Categorical | Lượt trận vòng bảng: `Matchday 1`, `Matchday 2`, `Matchday 3`, `Not Group Stage`. | **TV2 (Phân tích trận thủ tục)** |
| `Home Team Name`, `Away Team Name` | String | Tên đội chủ nhà và đội khách (đã làm sạch lỗi mã hóa). | Cả nhóm |
| `Home Team Goals`, `Away Team Goals` | Int | Số bàn thắng trong thời gian thi đấu chính thức + hiệp phụ. | Cả nhóm |
| `Total_Goals` | Int | Tổng số bàn thắng trong trận = Home + Away. | TV2 |
| `Goal_Margin` | Int | Độ chênh lệch tỷ số = $\lvert \text{Home Goals} - \text{Away Goals} \rvert$. | TV2 |
| `Margin_Category` | Categorical | Nhóm cách biệt tỷ số: `1. Sat Nut / Hoa (<=1 ban)`, `2. Cach Biet (2 ban)`, `3. Thang Dam (>=3 ban)`. | **TV2 (Stacked Bar Chart)** |
| `Win conditions` | String | Diễn biến đặc biệt nguyên bản (a.e.t., penalties). | Cả nhóm |
| `Match_Resolution` | Categorical | Kết quả trận đấu: `1. Normal Time - Blowout (>=2)`, `2. Normal Time - Close (<=1)`, `3. Extra Time`, `4. Penalties`. | **TV3 (Phân tích cấu trúc Knock-out)** |
| `Is_Extra_Time` | Boolean | `True` nếu trận đấu kéo dài vào Hiệp phụ. | TV3 |
| `Is_Penalties` | Boolean | `True` nếu trận đấu phải giải quyết bằng Luân lưu 11m. | TV3 |
| `Is_Golden_Goal` | Boolean | `True` nếu trận đấu kết thúc bằng Bàn thắng vàng (1998, 2002). | TV3 (Annotate biểu đồ) |
| `Attendance` | Float | Số lượng khán giả thực tế theo dõi trận đấu (đã phục hồi đủ 100%). | **TV1 (Sức hút thương mại)** |
| `Max_Capacity` | Int | Sức chứa tối đa của sân vận động tổ chức. | TV1 |
| `Occupancy_Rate` | Float (%) | Tỷ lệ lấp đầy sân = $(\text{Attendance} / \text{Max\_Capacity}) \times 100\%$. | **TV1 (Triệt tiêu nhiễu sân Mỹ)** |
| `Capacity_Source` | Categorical | Nguồn dữ liệu sức chứa: `Official_Or_Historical` vs `Imputed_From_Attendance`. | TV1 |
| `Home_Confederation`, `Away_Confederation` | String | Liên đoàn châu lục (UEFA, CONMEBOL, CONCACAF, CAF, AFC, OFC). | Mở rộng địa lý |
| `Home_Team_Elo`, `Away_Team_Elo` | Int | Điểm số World Football Elo Ratings của hai đội ngay trước giải đấu. | **TV2 & TV3 (Cửa trên / Cửa dưới)** |
| `Elo_Diff` | Int | Độ chênh lệch điểm đẳng cấp Elo = $\lvert \text{Home\_Elo} - \text{Away\_Elo} \rvert$. | **TV2 (Tương quan tỷ số)** |
| `Underdog_Team`, `Favorite_Team` | String | Tên đội cửa dưới (Elo thấp hơn) và đội cửa trên (Elo cao hơn). | **TV3 (Phân tích Upsets)** |
| `Is_Upset` | Boolean | `True` nếu đội cửa dưới giành chiến thắng hoặc loại đội cửa trên. | **TV3 (Địa chấn Knock-out)** |
| `Home_Group_Rank`, `Away_Group_Rank` | Int | Thứ hạng vòng bảng của 2 đội (1: Nhất bảng, 2: Nhì bảng, 3: Hạng ba vé vớt). | **TV3 (Phân loại hạt giống)** |
| `Matchup_Type` | Categorical | Phân loại kịch bản cặp đấu knock-out: `1. Winner vs Runner-up (1 vs 2)`, `2. Winner vs 3rd Place (1 vs 3 Wildcard)`, v.v. | **TV3 (Kiểm định vé vớt)** |
| `Contains_Third_Placed_Team` | Boolean | `True` nếu trận knock-out có sự góp mặt của đội hạng 3 vé vớt. | **TV3 (Phân tích tử thủ/luân lưu)** |
| `Match_Stakes` | Categorical | Tính chất trận Matchday 3: `1. Both Qualified`, `2. Both Eliminated`, `3. One-sided Dead Rubber`, `4. Decisive / High Stakes`. | **TV2 (Kiểm chứng trận thủ tục)** |
| `Is_Dead_Rubber` | Boolean | `True` nếu trận đấu có tính chất thủ tục (cả 2 vào, cả 2 bị loại, hoặc 1 chiều). | **TV2 (Phân tích Matchday 3)** |
| `Is_Full_Dead_Rubber` | Boolean | `True` nếu cả 2 đội đều đã an bài số phận (Both Qualified hoặc Both Eliminated). | **TV2 (Trận thủ tục tuyệt đối)** |
| `Home_Pre_Match_Status`, `Away_Pre_Match_Status` | Categorical | Trạng thái toán học của từng đội trước giờ bóng lăn Matchday 3: `Qualified`, `Eliminated`, `Contending`. | **TV2 (Bóc tách tâm lý thi đấu)** |

---

## 2. HƯỚNG DẪN CODE VẼ BIỂU ĐỒ CHO TỪNG THÀNH VIÊN

### THÀNH VIÊN 1: Thương Mại & Sức Hút Khán Đài
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('worldcup_master_cleaned.csv')
dim_tourn = pd.read_csv('dim_tournaments.csv')

# CHART 1 (Baseline): Combo Chart (Tổng số trận vs Khán giả trung bình cả giải)
fig, ax1 = plt.subplots(figsize=(10, 5))
color = 'tab:blue'
ax1.set_xlabel('Kỷ nguyên thể thức')
ax1.set_ylabel('Tổng số trận đấu (MatchesPlayed)', color=color)
bars = ax1.bar(dim_tourn['Era_Format'].unique(), dim_tourn.groupby('Era_Format')['MatchesPlayed'].sum(), color=color, alpha=0.6, width=0.4)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Khán giả trung bình / trận (Attendance per Match)', color=color)
ax2.plot(dim_tourn['Era_Format'].unique(), df.groupby('Era_Format')['Attendance'].mean(), color=color, marker='o', linewidth=2.5)
plt.title('Baseline: Quy mô trận đấu & Khán giả trung bình qua 4 kỷ nguyên')
plt.show()

# CHART 2 (Deep-dive): Tách 3 phân khúc Stage_Group để bóc tách biến nhiễu sân bãi
plt.figure(figsize=(10, 6))
stage_era_att = df.groupby(['Era_Format', 'Stage_Group'])['Occupancy_Rate'].mean().reset_index()
sns.lineplot(data=stage_era_att, x='Era_Format', y='Occupancy_Rate', hue='Stage_Group', marker='o', linewidth=2.5)
plt.title('Deep-dive: Tỷ lệ lấp đầy sân (% Occupancy Rate) theo 3 phân khúc vòng đấu')
plt.ylabel('Tỷ lệ lấp đầy trung bình (%)')
plt.ylim(40, 105)
plt.show()
```

---

### THÀNH VIÊN 2: Chuyên Môn & Chênh Lệch Trình Độ
```python
# CHART 1 (Baseline): 100% Stacked Bar tỷ lệ cách biệt bàn thắng ở Vòng bảng
group_df = df[df['Stage_Group'] == '1. Group Stage']
ct = pd.crosstab(group_df['Era_Format'], group_df['Margin_Category'], normalize='index') * 100
ct.plot(kind='bar', stacked=True, figsize=(10, 6), colormap='coolwarm')
plt.title('Baseline: Tỷ trọng các mức cách biệt bàn thắng ở Vòng bảng')
plt.ylabel('Tỷ lệ phần trăm (%)')
plt.legend(title='Khoảng cách tỷ số')
plt.show()

# CHART 2 (Deep-dive): Kiểm chứng "Trận cầu thủ tục" ở Matchday 3 vòng bảng
md_df = group_df[group_df['Matchday'].isin(['Matchday 1', 'Matchday 2', 'Matchday 3'])]
md_analysis = md_df.groupby(['Era_Format', 'Matchday'])['Total_Goals'].mean().unstack()
md_analysis.plot(kind='bar', figsize=(10, 5))
plt.title('Deep-dive: Số bàn thắng trung bình theo lượt trận (Matchday 1, 2, 3) qua các kỷ nguyên')
plt.ylabel('Số bàn thắng trung bình')
plt.show()
```

---

### THÀNH VIÊN 3: Cấu Trúc & Độ Khắc Nghiệt Knock-out
```python
# CHART 1 (Baseline): Tỷ lệ % số trận phải kéo dài quá 90 phút (Hiệp phụ / Luân lưu)
ko_df = df[df['Stage_Group'].isin(['2. Early Knockout', '3. Deep Knockout'])]
ko_overtime = ko_df.groupby('Era_Format')['Is_Extra_Time'].mean() * 100
ko_overtime.plot(kind='bar', color='purple', figsize=(8, 5))
plt.title('Baseline: Tỷ lệ trận Knock-out kéo dài > 90 phút qua 4 kỷ nguyên')
plt.ylabel('Tỷ lệ trận đấu có Hiệp phụ / Penalty (%)')
plt.show()

# CHART 2 (Deep-dive): Phân bố kết quả Knock-out (Thắng chóng vánh vs Tử thủ hiệp phụ/pen)
plt.figure(figsize=(11, 6))
res_ct = pd.crosstab(ko_df['Era_Format'], ko_df['Match_Resolution'], normalize='index') * 100
res_ct.plot(kind='bar', stacked=True, figsize=(11, 6), colormap='viridis')
plt.title('Deep-dive: Cấu trúc kết quả các vòng Knock-out (Phân cực Thắng cách biệt vs Kéo dài)')
plt.ylabel('Tỷ lệ phần trăm (%)')
plt.show()
```
