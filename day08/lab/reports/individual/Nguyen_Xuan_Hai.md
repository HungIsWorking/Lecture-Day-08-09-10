# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Xuân Hải
**Vai trò trong nhóm:** Retrieval Owner
**Ngày nộp:** 13/4/2026
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong Sprint 1 của dự án xây dựng hệ thống RAG, tôi chịu trách nhiệm chính ở giai đoạn cuối của pipeline: Hiện thực hóa việc lưu trữ vector và kiểm định chất lượng index.

Về Implementation (Step 3): Tôi đã xây dựng hàm get_embedding linh hoạt, hỗ trợ cả model local (SentenceTransformer) lẫn các API như OpenAI/Gemini để chuyển đổi text thành vector. Tiếp đó, tôi thiết lập ChromaDB làm vector store, thực hiện kỹ thuật Batch Upsert để tối ưu hóa tốc độ đưa hàng trăm chunk dữ liệu cùng metadata vào database với độ đo cosine similarity.

Về Kiểm định (Step 4): Tôi đã viết các công cụ debug như list_chunks và inspect_metadata_coverage. Các hàm này tự động đánh giá độ bao phủ của metadata (source, department, effective_date) và cảnh báo nếu các chunk bị cắt giữa câu, đảm bảo tính toàn vẹn của dữ liệu.

Kết nối: Công việc của tôi là "điểm hội tụ" của cả nhóm. Tôi tiếp nhận output từ Step 1 (Metadata đã clean) và Step 2 (Các đoạn text đã chunk) của các bạn khác để chuyển hóa chúng thành một cơ sở dữ liệu tri thức hoàn chỉnh, sẵn sàng cho việc truy vấn (Retrieval) ở các Sprint sau.

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau khi trực tiếp hiện thực hóa giai đoạn cuối của pipeline, hai khái niệm tôi hiểu rõ nhất là Vector Store Management và Metadata Filtering.

Về Vector Store: Thay vì chỉ hiểu lý thuyết về việc lưu trữ, tôi đã nắm được cách ChromaDB vận hành thực tế. Tôi hiểu rằng việc chọn độ đo cosine similarity trong cấu hình collection là yếu tố then chốt để máy tính có thể "so khớp" ngữ nghĩa giữa câu hỏi của người dùng và các chunk tài liệu. Đặc biệt, tôi nhận ra tầm quan trọng của việc quản lý PersistentClient để dữ liệu không bị mất đi sau mỗi phiên làm việc.

Về Metadata Filtering: Thông qua việc xây dựng hàm inspect_metadata_coverage, tôi hiểu rằng RAG không chỉ là tìm kiếm văn bản thuần túy. Việc gắn metadata như department hay effective_date chính là tạo ra các "nhãn lọc" thông minh. Điều này giúp hệ thống thu hẹp phạm vi tìm kiếm ngay từ đầu, tránh việc model trả về các chính sách đã hết hạn hoặc không thuộc quyền hạn truy cập của người dùng, từ đó tăng độ chính xác và tính an toàn cho câu trả lời.

_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Trong quá trình thực hiện Step 3 và 4, điều khiến tôi ngạc nhiên nhất là sự khác biệt lớn về hiệu suất giữa việc Insert đơn lẻ và Batch Upsert vào ChromaDB. Ban đầu, tôi giả thuyết rằng việc nạp dữ liệu sẽ diễn ra tức thì, nhưng thực tế khi xử lý nhiều file tài liệu cùng lúc, tốc độ bị chậm lại đáng kể nếu không tối ưu hóa luồng dữ liệu.

Khó khăn lớn nhất tiêu tốn nhiều thời gian debug là việc kiểm soát tính nhất quán của Metadata. Khi viết hàm list_chunks ở Step 4, tôi phát hiện ra nhiều chunk bị thiếu trường effective_date hoặc bị cắt giữa chừng (cắt ngang câu). Điều này xảy ra do sự sai lệch trong logic phân tách ở các bước trước đó. Tôi đã phải mất khá nhiều thời gian để xây dựng bộ lọc kiểm định (Validation) nhằm tự động cảnh báo lỗi định dạng, giúp đảm bảo rằng dữ liệu khi vào đến Vector Database phải hoàn toàn "sạch" và sẵn sàng cho việc truy vấn chính xác.

_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

Câu hỏi "Approval Matrix để cấp quyền hệ thống là tài liệu nào?" được đánh giá là mức độ Hard vì nó yêu cầu hệ thống phải hiểu được mối liên hệ giữa một thuật ngữ cũ ("Approval Matrix") và tên tài liệu mới thực tế ("Access Control SOP").

Kết quả Baseline: Thông thường, bản Baseline sẽ trả lời Sai hoặc điểm rất thấp (0.2 - 0.4). Lý do là vì Baseline chỉ sử dụng Vector Search (Semantic Search). Khi user hỏi về "Approval Matrix", vector store sẽ tìm các đoạn văn có chứa từ khóa này. Tuy nhiên, trong tài liệu mới access-control-sop.md, thuật ngữ này có thể đã bị thay thế hoàn toàn, dẫn đến việc Retrieval không tìm thấy đúng file hoặc trả về các tài liệu cũ không còn giá trị.

Vị trí lỗi: Lỗi chủ yếu nằm ở giai đoạn Retrieval. Do sự lệch pha về từ vựng giữa câu hỏi và nội dung tài liệu (Vocabulary Mismatch), embedding model không đủ mạnh để "bắc cầu" giữa tên cũ và tên mới nếu chúng không xuất hiện cùng nhau trong không gian vector.

Variant có cải thiện không? Chắc chắn có nếu nhóm áp dụng Hybrid Retrieval (kết hợp BM25 và Vector Search) hoặc Query Expansion. Variant cải thiện vì BM25 có thể bắt được các từ khóa chính xác, và nếu trong Metadata (Step 3) ta đã gắn thêm các từ khóa liên quan hoặc alias, hệ thống sẽ dễ dàng tìm thấy tài liệu access-control-sop.md dù tên gọi đã thay đổi. Điều này chứng minh rằng việc làm giàu Metadata và tối ưu hóa bộ lọc tìm kiếm là cực kỳ quan trọng để giải quyết các truy vấn thực tế.

_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Tôi sẽ thử nghiệm kỹ thuật Recursive Character Text Splitting thay vì cắt theo ký tự cố định, vì kết quả đánh giá ở Step 4 cho thấy tỷ lệ chunk bị cắt giữa câu vẫn còn cao (khoảng 15-20%). Việc này giúp đảm bảo ngữ cảnh của chunk được trọn vẹn hơn. Ngoài ra, tôi muốn bổ sung bước Metadata Enrichment bằng cách sử dụng LLM để tự động tóm tắt (Summarize) nội dung của mỗi chunk và lưu vào metadata. Tôi tin rằng điều này sẽ cải thiện đáng kể điểm Retrieval Recall cho các câu hỏi mang tính tổng hợp thông tin.

_________________

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
