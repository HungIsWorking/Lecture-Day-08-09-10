# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Tuấn Hưng

**Vai trò trong nhóm:** Tech Lead

**Ngày nộp:** 2026-04-13

**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Với vai trò Tech Lead, tôi đã tham gia vào tất cả các sprint của dự án. Trọng tâm chính của tôi là ở Sprint 2 và 3, đặc biệt là trong việc debug và hoàn thiện pipeline để nó hoạt động trơn tru với Gemini API. Tôi đã trực tiếp xác định và sửa lỗi model embedding không hợp lệ, và sau đó, tôi đã refactor lại toàn bộ phần LLM-as-Judge trong `eval.py` để chuyển từ OpenAI sang Gemini, bao gồm cả việc thêm cơ chế retry và fallback parsing để đảm bảo hệ thống đánh giá hoạt động ổn định. Công việc của tôi đã giúp cả nhóm có được một bộ điểm số đáng tin cậy để thực hiện A/B testing và cải thiện chất lượng của RAG.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Qua lab này, tôi đã hiểu sâu sắc hơn về tầm quan trọng của **Grounded Prompt** và **Evaluation Loop**. Ban đầu, prompt của hệ thống khá đơn giản. Tuy nhiên, khi phân tích kết quả đánh giá, đặc biệt là điểm `Completeness` thấp ở câu hỏi `q01`, tôi nhận ra rằng prompt cần phải được thiết kế một cách chi tiết và chặt chẽ hơn rất nhiều. Tôi đã học được cách "ép" LLM phải tuân thủ các quy tắc, trích dẫn nguồn, và đưa ra câu trả lời đầy đủ bằng cách thêm các chỉ dẫn tường minh vào prompt. Vòng lặp "chạy eval -> phân tích lỗi -> sửa prompt -> chạy lại eval" đã cho tôi thấy đây là một quy trình cốt lõi để cải thiện chất lượng của bất kỳ hệ thống RAG nào.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều khó khăn nhất là việc tích hợp Gemini API vào một codebase vốn được thiết kế cho OpenAI. Giả thuyết ban đầu của tôi là chỉ cần thay đổi tên model và API key là đủ. Tuy nhiên, thực tế phức tạp hơn nhiều. Lỗi đầu tiên là tên model embedding (`text-embedding-004`) không tồn tại, khiến toàn bộ quá trình indexing thất bại. Sau khi sửa lỗi đó, tôi lại phát hiện ra phần LLM-as-Judge hoàn toàn không hoạt động vì nó sử dụng thư viện và cấu trúc API của OpenAI. Việc debug và viết lại logic cho `_call_judge_llm` để tương thích với Gemini, xử lý các lỗi kết nối và đảm bảo output đúng định dạng JSON là phần tốn nhiều thời gian nhất.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** `q07` - "How is access to the 'Confidential' document category controlled?"

**Phân tích:**

Đây là một câu hỏi thú vị vì nó kiểm tra khả năng của RAG trong việc xử lý các truy vấn không có câu trả lời trực tiếp trong ngữ cảnh.

- **Baseline (dense search):** Trả lời tương đối ổn nhưng điểm `Faithfulness` chỉ là 3/5. Câu trả lời đúng khi nói rằng tài liệu không đề cập đến "Confidential", nhưng nó lại suy diễn thêm một chút thông tin không hoàn toàn có trong context, dẫn đến mất điểm. Retrieval đã tìm được văn bản về `access_control_sop.txt` nhưng không có đoạn nào nói về "Confidential".

- **Variant (hybrid search + rerank):** Kết quả còn tệ hơn, với điểm `Faithfulness` giảm xuống 2/5. Việc thêm BM25 (hybrid) và reranker không những không giúp ích mà còn có thể đã đưa vào những đoạn context kém liên quan hơn, khiến LLM càng thêm "bối rối" và tạo ra một câu trả lời suy diễn nhiều hơn. Điều này cho thấy việc thêm các thành phần phức tạp vào pipeline không phải lúc nào cũng tốt và cần được đánh giá cẩn thận. Lỗi ở đây nằm ở cả retrieval (cung cấp context nhiễu) và generation (suy diễn sai).

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Dựa trên phân tích câu hỏi `q07`, nếu có thêm thời gian, tôi sẽ thử nghiệm kỹ thuật **Query Transformation**. Cụ thể, tôi sẽ xây dựng một bước tiền xử lý để phân loại câu hỏi. Nếu câu hỏi yêu cầu định nghĩa hoặc kiểm tra sự tồn tại của một thuật ngữ (như "Confidential"), hệ thống có thể thực hiện một lượt retrieval chỉ để kiểm tra sự hiện diện của thuật ngữ đó. Nếu không tìm thấy, nó có thể trả lời "Tôi không biết" ngay lập tức thay vì để LLM cố gắng suy diễn từ context không liên quan.

---