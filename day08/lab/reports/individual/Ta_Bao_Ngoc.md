# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Tạ Bảo Ngọc
**Vai trò trong nhóm:** Eval Owner (Chủ trì Sprint 4)  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong lab này, tôi chịu trách nhiệm chính về Sprint 4 - Hàng rào bảo vệ và đánh giá (Evaluation). Tôi đã trực tiếp xây dựng file `eval.py` và triển khai hệ thống chấm điểm định lượng sử dụng phương pháp LLM-as-a-Judge với 4 metrics cốt lõi: Faithfulness, Answer Relevance, Context Recall và Completeness. 

Công việc của tôi bắt đầu bằng việc thiết kế bộ dữ liệu kiểm thử `test_questions.json` với 11 câu hỏi bao quát từ dễ đến khó, đặc biệt là các câu hỏi "bẫy" để kiểm tra khả năng từ chối trả lời (abstain) khi thiếu thông tin. Tôi đã kết nối kết quả của hai Sprint trước (Index và RAG Answer) để thực hiện A/B Testing, tạo ra bản so sánh chi tiết giữa cấu hình Baseline (Dense) và Variant (Hybrid + Rerank). Qua đó, tôi cung cấp bằng chứng dữ liệu để nhóm đưa ra quyết định tối ưu hóa pipeline cuối cùng.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Khái niệm tôi hiểu rõ nhất sau lab này là **Evaluation Loop (Vòng lặp đánh giá)**. Trước đây, tôi thường đánh giá kết quả của AI một cách cảm tính bằng cách đọc lướt qua. Lab này đã dạy tôi cách chuẩn hóa việc đánh giá thành các con số cụ thể. 

Tôi hiểu sâu sắc về sự khác biệt giữa các metric: **Faithfulness** đảm bảo AI không nói dối (Grounding), còn **Completeness** đảm bảo AI không nói thiếu. Đặc biệt, tôi đã thực chứng được rằng hiệu suất của một hệ thống RAG không chỉ nằm ở việc tìm đúng tài liệu (Recall) mà còn ở cách "nồi cám lợn" thông tin (context block) được LLM xử lý. Việc tăng lượng thông tin cung cấp cho AI (tăng k) là một con dao hai lưỡi - nó có thể giúp câu trả lời đầy đủ hơn nhưng đồng thời cũng làm tăng nhiễu, khiến điểm Relevance sụt giảm nếu không có các kỹ thuật lọc như Rerank.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều làm tôi ngạc nhiên nhất là hiện tượng **"Nhiễu thông tin khi tăng ngữ cảnh"**. Theo giả thuyết ban đầu, tôi nghĩ rằng chỉ cần đưa thật nhiều thông tin vào prompt (tăng top_k_select lên cao) thì câu trả lời sẽ luôn tốt hơn. Tuy nhiên, thực tế ở câu hỏi `q07` (về Approval Matrix), bản Variant với k=5 lại trả về kết quả "Không biết" trong khi Baseline với k=3 lại trả lời được một phần. 

Lỗi mất nhiều thời gian debug nhất chính là việc đồng nhất format JSON giữa LLM Judge và script Python. Đôi khi Gemini trả về code block markdown khiến hàm `json.loads` bị lỗi, buộc tôi phải viết thêm hàm regex để "bóc" nội dung JSON. Điều này giúp tôi rút ra bài học là luôn phải thiết kế hệ thống có tính phòng thủ cao (defensive programming) khi làm việc với các output không định dạng của LLM.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** q07 - "Approval Matrix để cấp quyền hệ thống là tài liệu nào?"

**Phân tích:**
Đây là câu hỏi thú vị nhất vì nó bộc lộ điểm yếu "chết người" của các hệ thống RAG khi xử lý **Alias (Bí danh/Tên cũ)**. 
*   **Baseline (Dense, k=3):** Tuy không nêu được việc tài liệu đã đổi tên, nhưng Baseline vẫn cung cấp được định nghĩa chung về Approval Matrix dựa trên nội dung tìm thấy, đạt điểm **Relevance 5/5** nhưng **Completeness chỉ 2/5**.
*   **Variant (Hybrid + Rerank, k=5):** Đáng ngạc nhiên là Variant lại thất bại nặng nề khi trả lời "Tôi không biết", dẫn đến điểm **Relevance tụt xuống 1/5**. Mặc dù chỉ số `Context Recall` báo cáo là đã tìm thấy tài liệu đúng (`it/access-control-sop.md`), nhưng AI lại không trích xuất được thông tin quan trọng nhất.
*   **Nguyên nhân:** Đây là hiện tượng "Lost in the middle" kết hợp với "Noise Overload". Khi tôi nâng k lên 5, lượng ngữ cảnh đổ vào prompt quá lớn khiến dòng ngắn ngủi *"Tài liệu Approval Matrix cho System Access hiện đã được thay thế bằng Access Control SOP"* bị chìm lấp giữa các điều khoản kỹ thuật khác. Điều này cho tôi bài học quý giá: Không phải cứ "nhồi" nhiều dữ liệu là tốt. Đối với các loại câu hỏi về Alias, chúng ta cần một chiến thuật prompt đặc thù hoặc kỹ thuật **Query Expansion** để AI hiểu rằng nó đang cần đi tìm một sự thay đổi về định danh, thay vì chỉ tìm kiếm nội dung thông thường.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi sẽ thử nghiệm kỹ thuật **Query Transformation (Decomposition)** vì kết quả đánh giá cho thấy hệ thống vẫn gặp khó khăn với các câu hỏi phức tạp chứa nhiều ý hỏi cùng lúc. Ví dụ ở câu q09 về lỗi ERR-403, nếu chúng ta tách câu hỏi thành "Lỗi này là lỗi gì?" và "Cách xử lý thế nào?" để thực hiện 2 lượt search riêng biệt, điểm Context Recall chắc chắn sẽ được cải thiện so với việc search một cụm từ dài duy nhất.
