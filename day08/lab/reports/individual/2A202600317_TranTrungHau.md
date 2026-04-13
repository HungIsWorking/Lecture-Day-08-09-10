# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Trần Trung Hậu  
**Vai trò trong nhóm:** Retrieval Owner
**Ngày nộp:** 13/4/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

**Sprint 1 — Phần tôi làm trong `index.py`**

Sau khi nhóm thống nhất, tôi chịu trách nhiệm cấu hình chunk và logic preprocess + chunking trong `index.py`.

Về cấu hình, nhóm chọn `CHUNK_SIZE = 300 tokens` và `CHUNK_OVERLAP = 50 tokens` — phù hợp với tài liệu policy, vừa đủ 1 điều khoản mà không loãng context.

Về preprocess, hàm `preprocess_document()` trích xuất metadata (Source, Department, Effective Date, Access) từ header file và xóa header khỏi nội dung chính. Tôi thêm bước normalize loại bỏ dòng trống thừa.

Về chunking, tôi thay cắt cứng theo ký tự bằng cách tách theo paragraph (`\n\n`) và dùng `_find_natural_boundary()` để tìm ranh giới tự nhiên (dấu xuống dòng, dấu chấm), tránh cắt giữa câu. Phần này là đầu vào cho embedding và build_index mà team sẽ implement tiếp. 

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

**Concept 1 — Chunking thông minh hơn chunking cứng**

Trước lab, tôi nghĩ chunking chỉ là cắt text thành từng đoạn đều nhau theo số ký tự. Thực tế, cắt cứng sẽ cắt giữa câu, giữa điều khoản — khiến chunk mất ngữ cảnh. Tôi hiểu ra rằng nên **ưu tiên ranh giới tự nhiên** (paragraph, dấu xuống dòng, dấu chấm) trước, rồi mới đến giới hạn kích thước. Chunk tốt không phải chunk nhỏ nhất mà là chunk có ngữ cảnh hoàn chỉnh nhất.

**Concept 2 — Metadata không chỉ là nhãn**

Tôi tưởng metadata chỉ để hiển thị cho đẹp. Nhưng thực ra metadata (department, effective_date, access) giúp **filter và rerank** kết quả retrieval. Ví dụ: query về "chính sách hoàn tiền" có thể ưu tiên chunk từ department CS và có effective_date gần nhất, thay vì lấy chunk cũ từ department khác. Metadata là công cụ retrieval, không phải trang trí.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

**Token khác Ký tự — điều tôi bất ngờ**

Ban đầu tôi nghĩ `CHUNK_SIZE = 300` nghĩa là 300 ký tự. Thực tế, code dùng `chunk_chars = CHUNK_SIZE * 4 = 1200` ký tự vì ước lượng 1 token ≈ 4 ký tự. Sự khác biệt này khiến chunk thực tế lớn hơn tôi tưởng gấp 4 lần.

**Cắt giữa câu thì sao?**

Giả thuyết ban đầu: cắt đều theo ký tự thì cũng không sao, máy nào biết đâu là ranh giới câu. Thực tế: khi đọc lại output từ `list_chunks()`, tôi thấy chunk bị cắt ngay giữa một điều khoản — "phản hồi ban đầu 15 phút và thời gian xử lý (res" — mất nửa câu, mất ngữ cảnh. Đó là lý do tôi phải implement `_find_natural_boundary()` để tìm dấu xuống dòng và dấu chấm trước khi cắt.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** "Approval Matrix để cấp quyền hệ thống là tài liệu nào?" (q07, hard)

**Baseline:** Dense retrieval chỉ dùng embedding similarity. Query "Approval Matrix" tìm theo ngữ nghĩa, nhưng trong ChromaDB, tài liệu đã được đổi tên thành "Access Control SOP". Embedding model không biết "Approval Matrix" = "Access Control SOP" → cosine similarity thấp → chunk liên quan bị miss hoặc xếp thấp trong top-k. Baseline **sẽ không trả lời đúng** — expected answer là "Access Control SOP" nhưng model không retrieve được đúng chunk.

**Lỗi nằm ở đâu:** Lỗi chủ yếu ở **retrieval** — dense search thuần túy không xử lý được alias/tên cũ. Indexing đã tốt (preprocess đúng metadata), nhưng retrieval strategy không cover được trường hợp này.

**Variant cải thiện:** Hybrid retrieval (dense + BM25) **có cải thiện** vì BM25 match chính xác từ khóa "Approval Matrix" trong text, bất kể embedding similarity. Khi kết hợp cả hai signal, chunk chứa cụm "Approval Matrix" sẽ được boost lên top, dù semantic similarity không cao.

_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi sẽ cải thiện hai phần:

Thứ nhất, tăng overlap lên 80-100 tokens cho các tài liệu policy dài. Kết quả eval có thể cho thấy chunk ở ranh giới điều khoản bị mất ngữ cảnh — overlap lớn hơn giúp chunk sau giữ được đầy đủ thông tin hơn.

Thứ hai, implement metadata-aware retrieval: filter theo `effective_date` để ưu tiên tài liệu mới nhất khi trả lời query về chính sách hiện hành. Hiện tại retrieval chỉ dùng similarity score, nhưng với metadata, tôi có thể boost chunk có `effective_date` gần nhất — tránh trả lời bằng tài liệu cũ đã lỗi thời.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
