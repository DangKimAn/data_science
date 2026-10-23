# TỪ ĐIỂN DỮ LIỆU & HƯỚNG DẪN VISUALIZE (DATA DICTIONARY)
**Dự án:** Phân tích Dữ liệu World Cup 2026 (16 $\to$ 24 $\to$ 32 $\to$ 48 đội)  
**Tệp dữ liệu chính bàn giao:** `worldcup_master_cleaned.csv` (1.068 trận, 1930–2026, 0 giá trị thiếu ở cột Attendance).

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
| `Home_Confederation`, `Away_Confederation` | String | Liên đoàn châu lục (UEFA, CONMEBOL, CONCACAF, CAF, AFC, OFC). | Mở rộng địa lý |

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
