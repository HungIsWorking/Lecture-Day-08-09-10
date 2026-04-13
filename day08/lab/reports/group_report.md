# Báo Cáo Nhóm — Lab Day 08: Full RAG Pipeline

**Tên nhóm:** D1
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Nguyễn Tuấn Hưng | Tech Lead | ___ |
| Nguyễn Đăng Hải | Retrieval Owner | ___ |
| Tạ Bảo Ngọc | Eval Owner | ___ |
| Lê Minh Hoàng | Documentation Owner | ___ |

**Ngày nộp:** ___________  
**Repo:** ___________  
**Độ dài khuyến nghị:** 600–900 từ

---

> **Hướng dẫn nộp group report:**
>
> - File này nộp tại: `reports/group_report.md`
> - Deadline: Được phép commit **sau 18:00** (xem SCORING.md)
> - Tập trung vào **quyết định kỹ thuật cấp nhóm** — không trùng lặp với individual reports
> - Phải có **bằng chứng từ code, scorecard, hoặc tuning log** — không mô tả chung chung

---

## 1. Pipeline nhóm đã xây dựng (150–200 từ)

> Mô tả ngắn gọn pipeline của nhóm:
> Pipeline của nhóm được xây dựng theo kiến trúc RAG tiêu chuẩn gồm ba bước: indexing, retrieval và generation. Ở bước indexing, tài liệu .txt được đọc từ thư mục data/docs, sau đó được preprocess và chia thành các chunk với kích thước trung bình để đảm bảo cân bằng giữa ngữ cảnh và độ chính xác khi retrieve.

**Chunking decision:**
> Nhóm sử dụng chunk_size = 300 tokens và overlap = 50 tokens

_________________

**Embedding model:** models/gemini-embedding-001

_________________

**Retrieval variant (Sprint 3):**
> Nêu rõ variant đã chọn (hybrid / rerank / query transform) và lý do ngắn gọn.
> Nhóm sử dụng hybrid retrieval (dense + BM25) kết hợp bằng RRF. Lý do là corpus chứa cả nội dung tự nhiên (policy) và các token đặc biệt (mã lỗi, tên riêng), nên cần kết hợp semantic matching và keyword matching để tăng recall.
_________________

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

> Chọn **1 quyết định thiết kế** mà nhóm thảo luận và đánh đổi nhiều nhất trong lab.
> Phải có: (a) vấn đề gặp phải, (b) các phương án cân nhắc, (c) lý do chọn.

**Quyết định:** Sử dụng hybrid retrieval (dense + BM25) thay vì chỉ dùng dense retrieval.

**Bối cảnh vấn đề:**Trong quá trình evaluation baseline, nhóm nhận thấy một số câu hỏi không retrieve được context phù hợp, đặc biệt là các query chứa mã lỗi hoặc keyword cụ thể (ví dụ q09 với “ERR-403”). Điều này dẫn đến Context Recall thấp và câu trả lời không grounded.

_________________

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Dense only | Tốt cho semantic search | Bỏ sót keyword/mã lỗi |
| BM25 only	| Match chính xác keyword |	Không hiểu ngữ nghĩa |
| Hybrid (dense + BM25) |	Kết hợp ưu điểm cả hai |	Phức tạp hơn, cần merge |

**Phương án đã chọn và lý do:**

Nhóm chọn hybrid retrieval kết hợp bằng Reciprocal Rank Fusion (RRF). Lý do là phương án này tận dụng được khả năng hiểu ngữ nghĩa của dense embedding và khả năng match chính xác của BM25, đặc biệt phù hợp với corpus có cả văn bản tự nhiên và token đặc biệt.

**Bằng chứng từ scorecard/tuning-log:**

Trong baseline, q09 (ERR-403) có Context Recall = None, cho thấy dense retrieval không đủ. Ngoài ra, các câu như q08, q10 bị thiếu thông tin (completeness thấp), cho thấy cần tăng khả năng retrieve đa dạng context. Điều này củng cố quyết định sử dụng hybrid thay vì chỉ dense.

---

## 3. Kết quả grading questions (100–150 từ)

> Sau khi chạy pipeline với grading_questions.json (public lúc 17:00):
> - Câu nào pipeline xử lý tốt nhất? Tại sao?
> - Câu nào pipeline fail? Root cause ở đâu (indexing / retrieval / generation)?
> - Câu gq07 (abstain) — pipeline xử lý thế nào?

**Ước tính điểm raw:** ___ / 98

**Câu tốt nhất:** ID: ___ — Lý do: ___________________

**Câu fail:** ID: ___ — Root cause: ___________________

**Câu gq07 (abstain):** ___________________

---

## 4. A/B Comparison — Baseline vs Variant (150–200 từ)

> Dựa vào `docs/tuning-log.md`. Tóm tắt kết quả A/B thực tế của nhóm.

**Biến đã thay đổi (chỉ 1 biến):** ___________________

| Metric | Baseline | Variant | Delta |
|--------|---------|---------|-------|
| ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | ___ |

**Kết luận:**
> Variant tốt hơn hay kém hơn? Ở điểm nào?

_________________

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

> Đánh giá trung thực về quá trình làm việc nhóm.

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| ___ | ___________________ | ___ |
| ___ | ___________________ | ___ |
| ___ | ___________________ | ___ |
| ___ | ___________________ | ___ |

**Điều nhóm làm tốt:**

_________________

**Điều nhóm làm chưa tốt:**

_________________

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

> 1–2 cải tiến cụ thể với lý do có bằng chứng từ scorecard.

_________________

---

*File này lưu tại: `reports/group_report.md`*  
*Commit sau 18:00 được phép theo SCORING.md*