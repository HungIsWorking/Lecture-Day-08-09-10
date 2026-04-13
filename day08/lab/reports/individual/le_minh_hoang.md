# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Lê Minh Hoàng  
**Vai trò trong nhóm:**  Documentation Owner  
**Ngày nộp:** 13/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> Trong lab này, tôi chủ yếu đóng góp ở Sprint 3 và Sprint 4 với vai trò Documentation Owner. Cụ thể, tôi chịu trách nhiệm tổng hợp và chuẩn hóa toàn bộ kiến trúc của pipeline RAG từ các file code như index.py, rag_answer.py và eval.py để xây dựng file architecture.md. Tôi cũng phân tích flow dữ liệu từ bước indexing (chunking, embedding) đến retrieval (hybrid dense + BM25) và generation bằng LLM.

> Ngoài ra, tôi xây dựng tuning-log.md dựa trên config thực tế trong code và kết quả scorecard của nhóm. Tôi không chỉ ghi lại các tham số mà còn liên kết chúng với lỗi cụ thể trong evaluation (ví dụ q08, q09, q10) để đề xuất hướng tuning hợp lý. Công việc của tôi đóng vai trò kết nối giữa phần implementation của các thành viên khác và phần phân tích, giúp nhóm hiểu rõ pipeline hoạt động như thế nào và tại sao cần cải tiến ở đâu.

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Sau lab này, tôi hiểu rõ hơn về hybrid retrieval và vai trò của nó trong hệ thống RAG. Trước đây, tôi nghĩ dense retrieval là đủ, nhưng qua thực nghiệm, tôi nhận ra nó dễ bỏ sót các query dạng keyword cụ thể như mã lỗi (ERR-403) hoặc tên riêng. Việc kết hợp thêm BM25 giúp cải thiện khả năng match chính xác các từ khóa này, đặc biệt trong domain có nhiều thuật ngữ đặc thù.

> Ngoài ra, tôi cũng hiểu rõ hơn về trade-off giữa số lượng context (top_k_select) và chất lượng câu trả lời. Nếu chọn quá ít chunk, hệ thống sẽ thiếu thông tin dẫn đến câu trả lời không đầy đủ (completeness thấp). Nhưng nếu chọn quá nhiều, có thể gây nhiễu cho LLM. Điều này cho thấy retrieval không chỉ là “tìm đúng” mà còn là “tìm đủ và phù hợp”.

_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều khiến tôi bất ngờ là mặc dù hệ thống đã sử dụng hybrid retrieval, vẫn có những câu hỏi bị thiếu thông tin rõ rệt. Ban đầu, tôi giả thuyết rằng lỗi nằm ở embedding hoặc model LLM, nhưng sau khi xem scorecard và trace lại pipeline, tôi nhận ra vấn đề chính lại nằm ở việc top_k_select quá thấp.

> Khó khăn lớn nhất là phân biệt lỗi thuộc về retrieval hay generation. Ví dụ, với các câu trả lời thiếu ý, ban đầu rất dễ nghĩ rằng LLM “hiểu sai”, nhưng thực tế là do context đầu vào không đầy đủ. Việc debug yêu cầu phải nhìn cả chain từ query → retrieved chunks → final answer, chứ không thể chỉ nhìn output. Điều này giúp tôi hiểu rõ hơn cách phân tích lỗi theo từng thành phần trong pipeline.

_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Chọn 1 câu hỏi trong test_questions.json mà nhóm bạn thấy thú vị.
> Phân tích:
> - Baseline trả lời đúng hay sai? Điểm như thế nào?
> - Lỗi nằm ở đâu: indexing / retrieval / generation?
> - Variant có cải thiện không? Tại sao có/không?

**Câu hỏi:** q09 (ERR-403-AUTH)

**Phân tích:** Ở baseline, câu hỏi này có Context Recall = None, cho thấy hệ thống không retrieve được bất kỳ đoạn văn bản liên quan nào đến mã lỗi ERR-403. Kết quả là câu trả lời không grounded vào tài liệu, dù có thể vẫn hợp lý ở mức ngôn ngữ tự nhiên.

Lỗi chính nằm ở retrieval, cụ thể là dense retrieval không hoạt động tốt với các query dạng keyword hoặc mã lỗi. Embedding thường ưu tiên semantic similarity, trong khi “ERR-403” là một token rất cụ thể, khó được biểu diễn tốt trong không gian embedding. Mặc dù hệ thống đã có BM25, nhưng khả năng cao là chunk chứa mã lỗi không nằm trong top_k_search hoặc bị RRF xếp hạng thấp.

Variant 1 (tăng top_k_select) có thể giúp cải thiện trong trường hợp chunk liên quan đã nằm trong top_k_search nhưng bị loại bỏ ở bước select. Tuy nhiên, nếu chunk đó không được retrieve ngay từ đầu, thay đổi này sẽ không có tác dụng. Điều này cho thấy với loại query này, việc tuning BM25 hoặc weighting trong hybrid retrieval có thể quan trọng hơn so với chỉ tăng số lượng context.
_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> Nếu có thêm thời gian, tôi sẽ thử điều chỉnh trọng số giữa dense và BM25 trong hybrid retrieval, hoặc thậm chí test riêng BM25-only cho các query dạng keyword. Lý do là kết quả eval cho thấy các câu chứa mã lỗi hoặc tên riêng đang là điểm yếu của hệ thống.

> Ngoài ra, tôi cũng muốn implement một bước reranking (cross-encoder) sau khi retrieve để chọn context chính xác hơn, thay vì chỉ dựa vào RRF. Điều này có thể cải thiện cả recall và completeness mà không cần tăng quá nhiều top_k_select.

_________________

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
