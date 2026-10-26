# BÁO CÁO TRỰC QUAN HÓA DỮ LIỆU WORLD CUP (1930 - 2026)
## Phân tích từ Biểu đồ 1 đến Biểu đồ 5 (Câu hỏi 1 & Câu hỏi 2)

Thư mục này chứa toàn bộ mã nguồn và kết quả trực quan hóa cho **Mục 1 - 3 (Câu hỏi 1)** và **Mục 4 - 5 (Câu hỏi 2)** theo đề cương tại [khdl.txt](file:///d:/code/KHDL_Begin/data_science/khdl.txt).

---

## 1. DANH SÁCH BIỂU ĐỒ ĐÃ ĐƯỢC XUẤT BẢN

| Tên tệp biểu đồ | Tên mục & Loại biểu đồ | Câu hỏi nghiên cứu | Trọng tâm phát hiện |
| :--- | :--- | :--- | :--- |
| [chart_1_quy_mo_vs_khan_gia.png](file:///d:/code/KHDL_Begin/data_science/visualization/chart_1_quy_mo_vs_khan_gia.png) | **Mục 1:** Quy mô giải đấu & Khán giả mỗi trận *(Combo Chart)* | **Câu hỏi 1** | Tăng số trận từ 18 lên 104 trận **không làm sụt giảm** khán giả trung bình/trận (duy trì trên 50.000 khán giả). |
| [chart_2_suc_hut_theo_vong.png](file:///d:/code/KHDL_Begin/data_science/visualization/chart_2_suc_hut_theo_vong.png) | **Mục 2:** Sức hút khán giả theo từng vòng đấu *(Line Chart)* | **Câu hỏi 1** | Vòng Knockout luôn giữ ưu thế khán giả vượt trội hơn vòng bảng; khoảng cách có xu hướng thu hẹp nhờ sức hút ngày càng đồng đều. |
| [chart_3_phan_phoi_lap_day_san.png](file:///d:/code/KHDL_Begin/data_science/visualization/chart_3_phan_phoi_lap_day_san.png) | **Mục 3:** Phân phối tỷ lệ lấp đầy sân vận động *(Boxplot)* | **Câu hỏi 1** | Tỷ lệ lấp đầy sân tăng dần từ ~60% (kỷ nguyên 16 đội) lên mức bão hòa >95% (kỷ nguyên 32 & 48 đội). |
| [chart_4_co_cau_cach_biet_vong_bang.png](file:///d:/code/KHDL_Begin/data_science/visualization/chart_4_co_cau_cach_biet_vong_bang.png) | **Mục 4:** Cơ cấu cách biệt tỷ số vòng bảng *(100% Stacked Bar)* | **Câu hỏi 2** | Trận sát nút/hòa (≤1 bàn) luôn chiếm thế áp đảo (55% - 70%); mở rộng số đội không làm gia tăng tỷ lệ trận đấu một chiều. |
| [chart_5_ty_le_thang_dam_bang_vs_knockout.png](file:///d:/code/KHDL_Begin/data_science/visualization/chart_5_ty_le_thang_dam_bang_vs_knockout.png) | **Mục 5:** Tỷ lệ thắng đậm Vòng bảng vs Knockout đầu tiên *(Dual Line)* | **Câu hỏi 2** | Thắng đậm ở vòng bảng giảm mạnh từ thời kỳ sơ khai (~50%) xuống quanh mức 10% - 20%; vòng Knockout đầu tiên có tính giằng co cao. |

---

## 2. PHÂN TÍCH CHI TIẾT TỪNG BIỂU ĐỒ

### BIỂU ĐỒ 1: Quy mô giải đấu và lượng khán giả mỗi trận
* **Ý nghĩa:** Trả lời trực tiếp câu hỏi: *Mở rộng số lượng trận đấu có làm loãng sức hút khán giả đến sân hay không?*
* **Dữ liệu thực tế:**
  * Giai đoạn 16 đội (1930 - 1978): Số trận từ 17 đến 38 trận, khán giả trung bình dao động từ ~21.000 đến ~50.000 người/trận.
  * Mở rộng 24 đội (1982 - 1994): Số trận tăng lên 52 trận. Khán giả trung bình không giảm mà tăng vọt, đạt đỉnh cao lịch sử năm 1994 tại Mỹ với **68.991 người/trận** nhờ hạ tầng sân vận động quy mô lớn.
  * Mở rộng 32 đội (1998 - 2022): Số trận ổn định ở mức 64 trận. Lượng khán giả trung bình ổn định bền vững ở mức **47.000 - 53.500 người/trận**.
  * Mở rộng 48 đội (2026 - Mô phỏng): Tổng số trận tăng vọt lên **104 trận**, lượng khán giả ước tính đạt **65.490 người/trận**, tổng lượt khán giả toàn giải đạt kỷ lục **6,81 triệu lượt**.
* **Kết luận:** Mở rộng quy mô giải đấu **KHÔNG** làm suy giảm sức hút khán giả mỗi trận.

---

### BIỂU ĐỒ 2: Sức hút khán giả theo từng vòng đấu
* **Ý nghĩa:** Xác định xu hướng tăng/giảm khán giả tập trung ở giai đoạn nào (vòng bảng hay vòng loại trực tiếp).
* **Dữ liệu thực tế:**
  * Vòng Knockout luôn có lượng khán giả trung bình cao hơn Vòng bảng từ 10.000 đến 30.000 người/trận do các trận knock-out thường được ưu tiên bố trí tại các sân vận động trung tâm có sức chứa lớn.
  * Vòng bảng đầu tiên cũng có sự tăng trưởng mạnh mẽ: từ mức ~23.000 người/trận thời kỳ đầu lên mức ~51.000 người/trận tại các kỳ 2006, 2014, 2022.
* **Ghi chú ngoại lệ:** Kỳ 1934 và 1938 thi đấu loại trực tiếp ngay từ đầu; kỳ 1950 thi đấu vòng tròn chung kết (không có trận chung kết knockout chính thức).

---

### BIỂU ĐỒ 3: Phân phối tỷ lệ lấp đầy sân vận động (Boxplot)
* **Ý nghĩa:** Chuẩn hóa theo sức chứa thực tế của sân vận động (`Occupancy_Rate`) để triệt tiêu biến nhiễu sân bãi.
* **Dữ liệu thực tế:**
  * Kỷ nguyên 16 đội: Trung vị lấp đầy vòng bảng là **63.8%**, vòng knockout là **77.3%**. Phân bố trải rộng từ 24% đến 100%.
  * Kỷ nguyên 24 đội: Trung vị lấp đầy tăng lên **89.1%** (vòng bảng) và **95.2%** (vòng knockout).
  * Kỷ nguyên 32 đội & 48 đội: Trung vị lấp đầy đạt trạng thái bão hòa **>95% - 96%** ở cả vòng bảng lẫn vòng knockout, độ lệch chuẩn thu hẹp tối đa.
* **Kết luận:** World Cup ngày nay đã trở thành sự kiện văn hóa toàn cầu bão hòa về nhu cầu vé xem, việc tăng số trận không làm xuất hiện tình trạng khán đài trống.

---

### BIỂU ĐỒ 4: Cơ cấu cách biệt tỷ số ở vòng bảng
* **Ý nghĩa:** Trả lời câu hỏi: *Mở rộng số đội tham dự có khiến vòng bảng xuất hiện nhiều trận đấu một chiều chênh lệch hay không?*
* **Dữ liệu thực tế:**
  * Nhóm trận **Sát nút / Hòa (≤ 1 bàn)** luôn chiếm tỷ trọng chi phối lớn nhất, duy trì từ **52.8% đến 72.9%** qua tất cả các kỳ có vòng bảng.
  * Nhóm trận **Thắng đậm (≥ 3 bàn)** từng chiếm tới 53.3% (1930) và 55.6% (1954), nhưng kể từ năm 1958 đến nay đã giảm mạnh và duy trì ổn định trong khoảng **10% - 25%**, kể cả khi giải mở rộng lên 24 hay 32 đội.
* **Kết luận:** Mở rộng quy mô giải đấu không làm giảm tính cạnh tranh của vòng bảng; khoảng cách trình độ giữa các nền bóng đá thế giới có xu hướng thu hẹp dần nhờ tiến trình chuyên nghiệp hóa toàn cầu.

---

### BIỂU ĐỒ 5: Tỷ lệ thắng đậm ở vòng bảng so với vòng knockout đầu tiên
* **Ý nghĩa:** So sánh mức độ chênh lệch vượt trội giữa Vòng bảng và Vòng Knockout đầu tiên (Round of 16 / Round of 32).
* **Dữ liệu thực tế:**
  * Tỷ lệ thắng đậm ở vòng Knockout đầu tiên dao động giằng co: có những kỳ đạt 0% (như 2014, 2018 - toàn bộ các trận R16 đều cực kỳ sát nút hoặc kéo dài qua hiệp phụ/penalties).
  * Vòng bảng đầu tiên có tỷ lệ thắng đậm tương đối ổn định quanh mức **10.4% - 20.8%** ở kỷ nguyên 32 đội.
  * Ở kỳ 2026 (mô phỏng 48 đội), tỷ lệ thắng đậm vòng bảng ước tính là **25.0%** và vòng Knockout đầu tiên (Round of 32) là **16.7%**, phản ánh việc có thêm các đại diện mới từ các liên đoàn mở rộng nhưng các trận loại trực tiếp vẫn duy trì độ căng thẳng cao.

---

## 3. CÁCH CHẠY LẠI MÃ NGUỒN

Để sinh lại toàn bộ các biểu đồ dạng ảnh PNG chất lượng cao (300 DPI), chạy lệnh:

```bash
python visualization/visualize_charts_1_to_5.py
```
