# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Đăng Hải  
**Vai trò trong nhóm:** Retrieval Owner  
**Ngày nộp:** 13/04/2026  
**Độ dài yêu cầu:** 500-800 từ

---

## 1. Em đã làm gì trong lab này? (100-150 từ)

Trong lab này, em phụ trách vai trò Retrieval Owner, tập trung chính ở Sprint 1 và Sprint 3. Ở Sprint 1, em cùng nhóm thống nhất cách chunk theo section heading (mẫu `=== ... ===`) để giữ ngữ nghĩa theo từng điều khoản thay vì cắt cứng toàn văn bản. Em cũng rà soát metadata mà pipeline cần mang theo cho mỗi chunk như `source`, `section`, `department`, `effective_date`, vì đây là nền tảng cho việc truy vết nguồn và đánh giá context recall. Ở Sprint 3, em chịu trách nhiệm phần retrieval strategy trong `rag_answer.py`: tổ chức lại 3 chế độ dense/sparse/hybrid, dùng Reciprocal Rank Fusion để kết hợp dense với BM25, và bổ sung bước rerank để giảm nhiễu trước khi đưa context cho LLM. Phần việc của em kết nối trực tiếp với Eval Owner vì chất lượng retrieval quyết định điểm context recall và ảnh hưởng đáng kể đến toàn bộ scorecard.

---

## 2. Điều em hiểu rõ hơn sau lab này (100-150 từ)

Điều em hiểu rõ nhất là sự khác nhau giữa “search đúng văn bản” và “search đúng ý”. Dense retrieval mạnh ở semantic matching, nên khi người dùng đặt câu hỏi khác từ vựng trong tài liệu thì hệ thống vẫn có khả năng tìm ra chunk phù hợp. Tuy nhiên, dense có thể hụt các từ khóa đặc thù như mã lỗi, tên gọi cũ, hoặc cụm từ ngắn. Sparse/BM25 thì ngược lại: bắt từ khóa rất tốt nhưng hạn chế khi truy vấn được diễn đạt theo paraphrase. Sau lab, em hiểu rõ hơn vì sao hybrid retrieval phù hợp với corpus nội bộ: tài liệu policy thường dài và diễn đạt tự nhiên, còn tài liệu IT lại chứa nhiều từ khóa cứng. Em cũng hiểu rõ vai trò của rerank: retrieval ban đầu là bước “quét rộng”, còn rerank là bước “lọc tinh” để chọn đúng ngữ cảnh trước khi sinh câu trả lời.

---

## 3. Điều em ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Khó khăn lớn nhất của em là cân bằng giữa recall và noise. Ban đầu, em giả thuyết rằng tăng top-k search sẽ luôn tốt hơn vì thu được nhiều context hơn. Tuy nhiên, khi chạy pipeline thực tế, nếu đưa quá nhiều chunk vào prompt thì chất lượng câu trả lời không tăng tương ứng, thậm chí có lúc giảm vì mô hình bị phân tán ngữ cảnh. Một điểm khác khiến em mất nhiều thời gian debug là sự không đồng nhất của đường dẫn nguồn (`source`) khi đánh giá context recall: expected source trong test set dùng tên file chuẩn hóa, còn metadata retrieve có thể là đường dẫn đầy đủ hoặc định dạng khác. Nếu không matching linh hoạt theo tên file thì kết quả chấm sẽ thiếu công bằng. Em cũng nhận thấy một số query tưởng “dễ” vẫn fail do alias, tức lỗi nằm ở retrieval chứ không phải ở generation.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** q07 - “Approval Matrix để cấp quyền hệ thống là tài liệu nào?”

**Phân tích:**

Đây là câu em đánh giá điển hình cho lỗi retrieval do alias. Baseline dense có rủi ro trả về sai hoặc thiếu vì query dùng tên cũ “Approval Matrix”, trong khi tài liệu hiện tại dùng tên “Access Control SOP”. Nếu embedding không kéo đủ gần giữa hai cách gọi, context trả về sẽ không có chunk chứa quan hệ ánh xạ tên cũ/tên mới; khi đó, dù prompt đã grounded thì generation vẫn khó trả lời chính xác. Vì vậy, lỗi gốc nằm ở retrieval (không phải generation). Với variant, em ưu tiên hybrid retrieval và bổ sung query transform expansion cho alias. Cách này tạo thêm query variant liên quan đến “access control sop”, sau đó hợp nhất kết quả bằng RRF để giữ đồng thời tín hiệu semantic và keyword. Khi đúng chunk được đưa vào top-k, câu trả lời rõ ràng hơn và citation nhất quán hơn. Bài học rút ra là với tài liệu nội bộ doanh nghiệp, việc đổi tên tài liệu hoặc thuật ngữ diễn ra thường xuyên, nên retrieval cần có cơ chế chịu lỗi alias thay vì chỉ phụ thuộc vào dense baseline.

---

## 5. Nếu có thêm thời gian, em sẽ làm gì? (50-100 từ)

Em sẽ thử hai cải tiến cụ thể. Thứ nhất, bổ sung metadata-aware retrieval (ưu tiên theo `department` và `effective_date`) vì các câu hỏi policy/SLA phụ thuộc mạnh vào phiên bản tài liệu, từ đó có thể giảm chunk nhiễu cũ. Thứ hai, em sẽ xây dựng alias dictionary bán tự động từ log query thất bại trong scorecard để mở rộng `transform_query()` theo cách có kiểm soát. Lý do là các câu như q07 cho thấy lỗi lặp lại theo cùng một mẫu thuật ngữ cũ/mới, và đây là lỗi retrieval có thể cải thiện bằng dữ liệu vận hành.

---

*Lưu file này với tên: reports/individual/[ten_ban].md*  
*Ví dụ: reports/individual/nguyen_van_a.md*
