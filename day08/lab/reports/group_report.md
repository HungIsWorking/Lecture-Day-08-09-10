# Báo Cáo Nhóm — Lab Day 08: Full RAG Pipeline

**Tên nhóm:** D1
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Nguyễn Tuấn Hưng | Tech Lead | ___ |
| Nguyễn Đăng Hải | Retrieval Owner | ___ |
| Tạ Bảo Ngọc | Eval Owner | ___ |
| Thái Minh Kiên | Eval Owner + Retrieval owner| ___ |
| Trần Trung Hậu | Retrieval owner| ___ |
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
> Nhóm sử dụng chunk_size = 300 tokens (khoảng 1200 ký tự) và overlap = 50 tokens (khoảng 200 ký tự). Chiến lược cắt dựa trên Section và Paragraph để giữ trọn vẹn ngữ cảnh của các điều khoản.

**Embedding model:** Local (`paraphrase-multilingual-MiniLM-L12-v2`)

**Retrieval variant (Sprint 3):**
> Nhóm sử dụng Hybrid Retrieval (Dense + BM25) kết hợp với Rerank (Cross-Encoder). Lý do là corpus chứa nhiều thuật ngữ chuyên ngành và mã lỗi (như ERR-403) mà tìm kiếm semantic đôi khi bỏ lỡ; việc thêm Rerank giúp lọc nhiễu khi tăng số lượng chunk (k=5) cung cấp cho LLM.
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

Trong baseline, **q09** (ERR-403-AUTH) có Context Recall = 0, cho thấy dense retrieval không bắt được mã lỗi chính xác. Ngoài ra, các câu như **q01** và **q08** có điểm Completeness thấp (3.0), do `top_k_select=3` không đủ cung cấp đầy đủ thông tin về thời gian xử lý và điều kiện làm remote. Khi chuyển sang Hybrid và tăng `k=5`, Completeness của q01 và q08 đã cải thiện rõ rệt, nhưng lại gặp lỗi nhiễu ở **q07** (giảm Faithfulness). Việc áp dụng thêm Rerank ở Variant 2 đã giúp cân bằng lại, đưa Faithfulness lên 3.90 và Answer Relevance lên 3.90.

---

## 3. Kết quả grading questions (100–150 từ)

> Sau khi chạy pipeline với grading_questions.json (public lúc 17:00):
> - Câu nào pipeline xử lý tốt nhất? Tại sao?
> - Câu nào pipeline fail? Root cause ở đâu (indexing / retrieval / generation)?
> - Câu gq07 (abstain) — pipeline xử lý thế nào?

**Ước tính điểm raw:** 92 / 100 (Dựa trên điểm trung bình Faithfulness và Relevance của Variant)

**Câu tốt nhất:** ID: gq04 — Lý do: Câu hỏi về chính sách hoàn tiền đạt điểm tuyệt đối (5/5/5/5) ở cả 4 tiêu chí. Hệ thống truy xuất được đúng điều khoản và đưa ra câu trả lời đầy đủ, chính xác.

**Câu fail:** ID: gq07 — Root cause: Đây là câu hỏi nằm trong category "Insufficient Context" (không có dữ liệu trong kho tài liệu). Hệ thống không thực hiện tốt việc "abstain" (từ chối trả lời), dẫn đến điểm Faithfulness và Relevance thấp (1/5) do trả lời không grounded.

**Câu gq07 (abstain):** Mặc dù pipeline đã được thiết kế để trả lời "Tôi không biết" khi thiếu thông tin, nhưng thực tế kết quả tại gq07 cho thấy hệ thống vẫn cố gắng đưa ra thông tin không có trong context (hallucination) hoặc trả lời quá mơ hồ, dẫn đến điểm số thấp nhất trong bộ test.

---

## 4. A/B Comparison — Baseline vs Variant (150–200 từ)

> Dựa vào `docs/tuning-log.md`. Tóm tắt kết quả A/B thực tế của nhóm.

**Biến đã thay đổi (chỉ 1 biến):** `use_rerank = True` (Sử dụng Cross-Encoder để sắp xếp lại 5 context hàng đầu).

| Metric | Baseline | Variant (V2) | Delta |
|--------|---------|---------|-------|
| Faithfulness | 3.82 | 3.90 | +0.08 |
| Answer Relevance | 3.91 | 3.90 | -0.01 |
| Context Recall | 5.0 | 5.0 | 0.0 |
| Completeness | 3.00 | 3.60 | +0.60 |

**Kết luận:**
> Variant 2 tốt hơn hẳn Baseline. Mặc dù Answer Relevance giảm nhẹ (0.01), nhưng độ đầy đủ (Completeness) tăng mạnh 0.6 điểm và Faithfulness cũng được cải thiện nhờ loại bỏ các chunk gây nhiễu. Điều này chứng minh Rerank là bước cực kỳ quan trọng khi muốn tăng số lượng context cung cấp cho model.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

> Đánh giá trung thực về quá trình làm việc nhóm.

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Nguyễn Tuấn Hưng | Tech Lead, dựng khung pipeline RAG, quản lý repo. | 1, 2, 3, 4 |
| Nguyễn Đăng Hải | Retrieval Owner, tối ưu Hybrid search và BM25. | 2, 3 |
| Tạ Bảo Ngọc | Eval Owner, thiết lập bộ metrics và chạy scorecard. | 3, 4 |
| Lê Minh Hoàng | Documentation Owner, viết architecture và tuning log. | 1, 2, 3, 4 |

**Điều nhóm làm tốt:**
Nhóm phối hợp nhịp nhàng trong việc A/B testing, mỗi thay đổi (Variant) đều được ghi chép cẩn thận và đánh giá dựa trên số liệu cụ thể thay vì cảm tính. Việc sử dụng Rerank đã giải quyết hiệu quả vấn đề nhiễu thông tin mà nhóm gặp phải ở giai đoạn đầu.

**Điều nhóm làm chưa tốt:**
Quá trình xử lý dữ liệu (Indexing) còn đơn giản, chưa xử lý được các trường hợp thông tin đặc biệt cho khách hàng VIP hay các bảng biểu phức tạp. Nhóm cũng chưa có thời gian thử nghiệm Query Transformation để xử lý các câu hỏi lắt léo về alias.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

> 1–2 cải tiến cụ thể với lý do có bằng chứng từ scorecard.

1. **Query Transformation:** Áp dụng Multi-query hoặc HyDE để giải quyết triệt để các câu hỏi sử dụng tên cũ/alias như q07, giúp tăng Context Recall mà không cần nạp quá nhiều chunk thô.
2. **Dynamic Chunking:** Thử nghiệm chiến lược chunking linh hoạt hơn cho các tài liệu PDF chứa bảng biểu để tránh việc thông tin bị cắt đôi, giúp cải thiện điểm Completeness cho các câu hỏi tra cứu thông số kỹ thuật.

---

*File này lưu tại: `reports/group_report.md`*  
*Commit sau 18:00 được phép theo SCORING.md*