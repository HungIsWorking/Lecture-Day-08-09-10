# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Thái Minh Kiên
**Vai trò trong nhóm:** Retrieval Owner + Eval Owner
**Ngày nộp:** 13/04/2026
**Đồ dài yêu cầu:** 500–800 từ

---

## 1. Em đã làm gì trong lab này? (100-150 từ)

Trong dự án này, với vai trò là người phụ trách mảng Retrieval và Evaluation, Em đã tập trung vào việc tối ưu hóa khả năng tìm kiếm và đánh giá chất lượng câu trả lời của hệ thống RAG. Cụ thể, Em đã thực hiện các nhiệm vụ sau:

*   **Xây dựng Evaluation Suite:** Em đã viết các phần TODO trong file `eval.py` để tích hợp phương pháp "LLM-as-a-judge". Em đã thiết kế các prompt chấm điểm dựa trên 4 metric trọng tâm: Faithfulness, Answer Relevance, Context Recall và Completeness.
*   **Thử nghiệm và Đo lường (Testing):** Em đã hỗ trợ bạn Ngọc (Eval owner) thực hiện note các kết quả thử nghiệm để so sánh giữa cấu hình Baseline (chỉ dùng Dense Retrieval) và các Variant (Hybrid Retrieval + Reranking). Ngoài ra, Em cũng tham gia hỗ trợ viết báo cáo tổng hợp kết quả cho nhóm.

---

## 2. Điều Em hiểu rõ hơn sau lab này (100-150 từ)

Sau khi hoàn thành lab, Em đã hiểu sâu sắc hơn về hai khái niệm cực kỳ quan trọng trong RAG chuyên nghiệp: **Hybrid Retrieval** và **Reranking**.

Thứ nhất, **Hybrid Retrieval** không chỉ đơn thuần là cộng hai kết quả tìm kiếm lại với nhau. Em nhận ra rằng Dense Retrieval (Embedding) rất mạnh trong việc hiểu ngữ nghĩa nhưng lại thường bỏ lỡ các từ khóa chính xác (như mã lỗi kỹ thuật hoặc tên riêng viết tắt). Việc kết hợp với BM25 thông qua thuật toán RRF (Reciprocal Rank Fusion) giúp hệ thống "bắt" được cả ý nghĩa lẫn các từ khóa trọng yếu, tạo ra một danh sách ứng viên (candidate list) toàn diện hơn nhiều.

Thứ hai là **Reranking**. Đây là bước "phễu" lọc quan trọng. Em hiểu rằng việc lấy nhiều context (k lớn) có thể tăng độ đầy đủ cho câu trả lời, nhưng đồng thời cũng mang lại nhiều "nhiễu". Sử dụng Cross-Encoder để rerank giúp chúng ta chọn ra được 3-5 đoạn văn bản thực sự liên quan nhất trước khi đưa vào LLM, giúp cải thiện đáng kể điểm Faithfulness và tránh làm LLM bị phân tâm bởi các thông tin ngoại lai.

---

## 3. Điều Em ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều khiến Em ngạc nhiên nhất chính là hiện tượng **"Noise-to-Signal Ratio"** (tỷ lệ nhiễu trên tín hiệu) khi chúng Em thử nghiệm Variant 1.

Ban đầu, Em tự tin rằng chỉ cần tăng `top_k_select` từ 3 lên 5 để cung cấp nhiều ngữ cảnh hơn thì điểm Completeness (độ đầy đủ) sẽ tăng lên mà không có tác dụng phụ. Tuy nhiên, kết quả Eval cho thấy ở một số câu hỏi (như câu q07), điểm Faithfulness và Answer Relevance lại bị tụt giảm. Lý do là khi nạp quá nhiều đoạn văn bản không liên quan trực tiếp vào prompt, LLM (gpt-4o-mini) có xu hướng trở nên quá "an toàn" và trả lời "Em không biết" hoặc bị nhầm lẫn giữa các mốc thời gian/số liệu từ các chunk khác nhau.
---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ) Câu 7

**Câu hỏi:** Approval Matrix để cấp quyền hệ thống là tài liệu nào?

**Phân tích:**
Câu hỏi này là một thử thách thú vị vì nó kiểm tra khả năng xử lý "alias" (tên hiệu/tên cũ) của hệ thống. Trong dữ liệu, tài liệu có tên hiện tại là `access-control-sop.md`, nhưng người dùng vẫn hỏi bằng tên cũ là "Approval Matrix".

*   **Baseline (Dense Retrieval only):** Ở mức cấu hình cơ bản với `k_select=3`, hệ thống đôi khi tìm thấy đúng tài liệu nhờ sự tương đồng ngữ nghĩa. Tuy nhiên, câu trả lời thường ngắn gọn và không giải thích rõ mối liên hệ giữa tên cũ và tên mới.
*   **Lỗi nằm ở đâu:** Vấn đề chính nằm ở **Retrieval**. Nếu chỉ dùng Dense, mức độ relevance điểm số không đủ vượt trội để loại bỏ các chunk trùng lặp về từ khóa IT chung chung khác.
*   **Variant (Hybrid + Rerank):** Kết quả được cải thiện rõ rệt ở Variant 2. Nhờ **BM25**, từ khóa "Approval Matrix" (xuất hiện trong nội dung mô tả tên cũ của SOP) được bắt trúng ngay lập tức. Sau đó, **Reranker** đã đẩy chunk chứa thông tin "Tài liệu này hiện có tên mới là Access Control SOP" lên vị trí hàng đầu.
*   **Kết quả:** Variant trả lời chính xác và đầy đủ: "Tài liệu 'Approval Matrix' hiện đã được thay thế bằng Access Control SOP (access-control-sop.md)". Điều này chứng minh rằng sự kết hợp giữa kiến trúc Hybrid và lọc nhiễu là chìa khóa để xử lý các truy vấn có tính đặc thù cao trong doanh nghiệp.

---

## 5. Nếu có thêm thời gian, Em sẽ làm gì? (50-100 từ)

Em sẽ thử nghiệm kỹ thuật **Query Transformation (Decomposition & Expansion)**. Qua kết quả eval, Em thấy một số câu hỏi phức tạp vẫn khiến hệ thống "bối rối" về việc chọn chunk. Nếu có thêm thời gian, Em muốn dùng LLM để phân rã câu hỏi người dùng thành các sub-queries hoặc mở rộng query với các từ đồng nghĩa (Expansion) trước khi thực hiện retrieval. Em tin rằng điều này sẽ giúp giải quyết triệt để các trường hợp Alias khó hơn nữa và nâng điểm Completeness lên mức tuyệt đối 5/5 cho toàn bộ bộ test.

---

*Lưu file này với tên: `reports/individual/thai_minh_kien.md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
