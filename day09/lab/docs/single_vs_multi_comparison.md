# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** Nhóm 103
**Ngày:** 2026-04-14

Nguồn số liệu:
- Day 08: results/scorecard_baseline.md, results/scorecard_variant.md
- Day 09: artifacts/grading_run.jsonl, artifacts/traces/*.json

---

## 1. Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Faithfulness (/5) | 4.80 | ước tính rất cao trên grading (không có judge /5 trực tiếp) | N/A | Day 09 dùng rubric criteria thay cho judge /5 |
| Relevance (/5) | 4.60 | ước tính cao trên grading | N/A | Không dùng cùng judge pipeline để so trực tiếp |
| Completeness (/5) | 4.50 | cải thiện ở các câu multi-detail sau khi thêm fact-first synthesis | N/A | Day 09 có kiểm tra tiêu chí câu hỏi cụ thể |
| Avg latency (ms) | N/A | 815 (test 15 câu), 1179 (grading 10 câu) | N/A | Day 08 scorecard không lưu latency |
| Abstain quality | q09 có trả lời thiếu gợi ý liên hệ | gq07 abstain đúng, không bịa số liệu | Improved | Day 09 có explicit abstain rules |
| Multi-hop coverage | Trung bình | Tốt trên gq09 (đủ SLA + Level 2 emergency) | Improved | Có route qua policy_tool + MCP |
| Routing visibility | Không có | Có route_reason và workers_called | Improved | Debug rõ nguyên nhân hơn |
| Debug time (estimate) | ~30 phút | ~8-10 phút | giảm ~20 phút | Có trace + worker boundaries |

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Cao | Cao |
| Latency | Không có số đo trong scorecard | Rất nhanh sau warm-up (P50 ~27 ms) |
| Observation | Trả lời đúng nhưng khó giải thích đường đi | Trả lời đúng và có trace worker rõ |

**Kết luận:** Với câu đơn giản, chất lượng hai hệ khá gần nhau; Day 09 có lợi thế lớn ở khả năng quan sát và debug.

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Có câu thiếu chi tiết | Đạt đủ ý chính ở gq09 |
| Routing visible? | Không | Có |
| Observation | Khó biết sai ở retrieval hay synthesis | Có thể lần theo route_reason và mcp_tools_used |

**Kết luận:** Day 09 tốt hơn cho câu multi-hop vì có tách vai trò và tool calls rõ ràng.

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | Có case không đủ context | Có rule abstain chủ động (gq02, gq07) |
| Hallucination cases | Vẫn có nguy cơ nếu prompt chung | Giảm rõ do fact-first + abstain guardrails |
| Observation | Không có cơ chế policy-scope riêng | Có temporal scoping và anti-hallucination riêng |

**Kết luận:** Day 09 kiểm soát hallucination tốt hơn cho câu "thiếu dữ liệu tài liệu".

---

## 3. Debuggability Analysis

### Day 08 — Debug workflow

Khi answer sai, nhóm phải đọc lại chuỗi xử lý RAG gần như nguyên khối. Không có route trace nên khó biết lỗi nằm ở retrieval, prompt, hay generation.

Thời gian ước tính tìm ra một lỗi: khoảng 30 phút.

### Day 09 — Debug workflow

Khi answer sai, nhóm xem ngay route_reason và worker sequence. Sau đó test độc lập worker gây lỗi.

Thời gian ước tính tìm ra một lỗi: khoảng 8-10 phút.

**Ví dụ debug thực tế:**

Temporal-abstain trước đó bị trigger sai cho câu không có mốc ngày vì parser đọc từ context. Đã sửa bằng cách chỉ kiểm tra temporal marker trên task input trong policy_tool.

---

## 4. Extensibility Analysis

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa prompt/hàm chính | Thêm MCP tool + route rule |
| Thêm 1 domain mới | Khó tách module | Thêm worker mới |
| Thay đổi retrieval strategy | Sửa pipeline lõi | Sửa retrieval_worker độc lập |
| A/B test một phần | Khó | Dễ hơn (đổi từng worker) |

**Nhận xét:** Day 09 mở rộng tốt hơn rõ ràng nhờ kiến trúc module hóa.

---

## 5. Cost & Latency Trade-off

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 1 synthesis call + retrieval |
| Complex query | 1 LLM call | 1 synthesis call + 1-3 MCP tool calls |
| MCP tool call | N/A | Có (search_kb, get_ticket_info, check_access_permission) |

**Nhận xét về cost-benefit:**

Day 09 có overhead orchestration và MCP cho query phức tạp, nhưng đổi lại giảm hallucination và tăng khả năng debug/kiểm soát logic nghiệp vụ.

---

## 6. Kết luận

**Multi-agent tốt hơn single agent ở điểm nào?**

1. Debuggability và observability tốt hơn nhiều (route_reason, worker IO logs).
2. Xử lý câu policy/temporal/multi-hop an toàn hơn, đặc biệt abstain đúng khi thiếu dữ liệu.

**Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**

1. Cold start retrieval model vẫn cao, query đầu có thể >10 giây.

**Khi nào KHÔNG nên dùng multi-agent?**

Khi bài toán chỉ cần FAQ đơn giản, domain ít biến động và không cần trace chi tiết.

**Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**

Thêm warm-up model, structured route_reason JSON, và bộ auto-check criteria trước khi ghi grading output.
