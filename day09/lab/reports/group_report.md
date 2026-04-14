# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Nhóm 103  
**Thành viên:**
| Tên | Vai trò |
|-----|---------|
| Nguyễn Đăng Hải | Supervisor Owner |
| Nguyễn Tuấn Hưng | Worker Owner |
| Trần Trung Hậu | MCP Owner |
| Trần Trung Hậu | Trace & Docs Owner |

**Ngày nộp:** 2026-04-14  
**Repo:** day09/lab

---

## 1. Kiến trúc nhóm đã xây dựng

Nhóm triển khai kiến trúc Supervisor-Worker gồm 3 workers chính: retrieval_worker, policy_tool_worker và synthesis_worker. Luồng xử lý bắt đầu từ supervisor trong graph.py, nơi task được phân loại theo intent (SLA/ticket, policy/refund/access, unknown error) để route đến worker phù hợp. Sau worker chuyên trách, synthesis_worker hợp nhất evidence và trả về final_answer kèm nguồn trích dẫn và confidence.

Routing logic hiện tại dùng rule-based để minh bạch và dễ debug. Với câu hỏi chứa policy/access, supervisor đặt needs_tool=True để policy_tool_worker được phép gọi MCP tools. Với câu hỏi SLA/ticket/escalation, hệ thống route sang retrieval_worker để lấy evidence trực tiếp. Các câu không xác định rõ domain hoặc có mã lỗi lạ có thể trigger human_review (HITL placeholder).

MCP tools đã tích hợp gồm search_kb, get_ticket_info, check_access_permission và create_ticket (mock). Ví dụ trace ở gq09 cho thấy policy_tool gọi đồng thời search_kb + get_ticket_info + check_access_permission để giải bài toán multi-hop giữa SLA và Access Control.

---

## 2. Quyết định kỹ thuật quan trọng nhất

**Quyết định:** Thêm cơ chế fact-first synthesis + abstain guardrails thay vì chỉ dựa vào prompt LLM tổng quát.

**Bối cảnh vấn đề:** Ở phiên bản đầu, nhiều câu trả lời bị verbose và thiếu điểm chấm chính vì synthesis fallback theo kiểu copy snippet. Ngoài ra, câu temporal policy và câu yêu cầu thông tin không có trong tài liệu dễ bị hallucination nếu để LLM suy diễn.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Giữ prompt LLM tổng quát, tinh chỉnh prompt nhiều hơn | Ít sửa code | Khó kiểm soát consistency theo từng tiêu chí grading |
| Kết hợp rule-based fact-first cho nhóm câu trọng điểm + fallback LLM | Kiểm soát được điểm trọng yếu, giảm hallucination | Tăng độ phức tạp logic synthesis |

**Phương án đã chọn và lý do:**

Nhóm chọn phương án 2. Cách này giúp khóa các câu có tiêu chí rõ như notification channels, temporal scope v3/v4, emergency bypass Level 2, và anti-hallucination ở câu không có dữ liệu (mức phạt tài chính). Với cách làm này, output bám đúng grading_criteria hơn trong khi vẫn giữ fallback LLM cho câu mở.

**Bằng chứng từ trace/code:**

- gq02: trả lời đúng kiểu abstain theo temporal scope (v3 không có trong tài liệu hiện có).
- gq07: không bịa mức phạt, nêu rõ thiếu dữ liệu và gợi ý liên hệ bộ phận liên quan.
- gq09: trả lời đủ cả phần SLA và điều kiện Level 2 emergency access trong cùng một câu trả lời.

---

## 3. Kết quả grading questions

Nhóm đã chạy full grading_questions và ghi log vào artifacts/grading_run.jsonl. Pipeline xử lý thành công 10/10 câu, không có crash, không có PIPELINE_ERROR. Theo kiểm tra tự động theo tiêu chí chấm (heuristic theo từng grading_criteria), kết quả ước tính đạt tối đa raw score 96/96.

**Tổng điểm raw ước tính:** 96 / 96

**Câu pipeline xử lý tốt nhất:**
- ID: gq09 — Lý do tốt: trả lời đầy đủ 2 phần cross-doc (SLA notification + Level 2 emergency bypass), có nêu đúng 3 kênh thông báo, mốc 10 phút và điều kiện approval.

**Câu từng gặp khó khăn trong vòng trước khi fix:**
- ID: gq04 và gq10 — Fail trước đó do temporal-abstain bị kích hoạt sai từ context.
  Root cause: policy_tool đọc temporal marker từ merged context thay vì task input.

**Câu gq07 (abstain):**

Hệ thống hiện trả lời đúng tinh thần anti-hallucination: không có thông tin mức phạt trong tài liệu SLA và không bịa con số.

**Câu gq09 (multi-hop khó nhất):**

Trace ghi rõ policy_tool_worker + synthesis_worker, đồng thời mcp_tools_used có search_kb, get_ticket_info, check_access_permission. Câu trả lời cuối đáp ứng đủ các ý chính trong rubric.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được

Metric cải thiện rõ nhất là khả năng debug và quan sát luồng xử lý. Day 08 có điểm chất lượng nội dung tốt (faithfulness 4.80/5, relevance 4.60/5 trên baseline), nhưng khi sai thì khó khoanh vùng lỗi do thiếu trace route. Day 09 thêm route_reason, workers_called, mcp_tools_used nên thời gian tìm nguyên nhân lỗi giảm mạnh.

Về hiệu năng, Day 09 sau warm-up có độ trễ thấp ở phần lớn query (P50 ~27-30 ms trong các batch gần nhất), nhưng vẫn có cold-start spike >10s ở query đầu do nạp embedding model. Điều này là trade-off rõ giữa kiến trúc linh hoạt và chi phí khởi động.

Điều bất ngờ là multi-agent không chỉ giúp câu phức tạp, mà còn giúp câu abstain an toàn hơn vì policy/synthesis có guardrails rõ ràng. Trường hợp multi-agent chưa tốt là khi route policy quá rộng có thể gây MCP call không cần thiết nếu câu hỏi chỉ là fact retrieval đơn giản.

---

## 5. Phân công và đánh giá nhóm

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Nguyễn Đăng Hải | graph.py, routing logic | Sprint 1 |
| Nguyễn Tuấn Hưng | retrieval worker + tuning retrieval | Sprint 2 |
| Trần Trung Hậu | policy_tool + MCP integration | Sprint 2-3 |
| Trần Trung Hậu | eval_trace, trace analysis, docs/report | Sprint 4 |

**Điều nhóm làm tốt:**

- Chia module đúng theo worker boundary nên merge và debug nhanh.
- Có trace đầy đủ để truy ngược quyết định routing và tool calls.
- Cải tiến theo vòng lặp ngắn: chạy grading -> phát hiện lỗi -> fix đúng chỗ -> chạy lại.

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**

- Chưa chuẩn hóa sớm format route_reason dạng machine-readable.
- Có giai đoạn policy exceptions bị over-trigger trước khi thêm negation/temporal fixes.

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**

Nhóm sẽ đặt bộ regression test cho các câu rubric khó (temporal, abstain, multi-hop) ngay từ đầu Sprint 3 để tránh dồn bug vào cuối Sprint 4.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì?

1. Thêm model warm-up và cache retrieval để giảm cold-start latency >10 giây ở query đầu.  
2. Thêm auto-check theo grading_criteria trước khi xuất grading_run.jsonl để phát hiện thiếu ý bắt buộc ngay trong CI cục bộ.
