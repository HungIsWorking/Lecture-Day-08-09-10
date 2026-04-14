# Routing Decisions Log — Lab Day 09

**Nhóm:** Nhóm 103
**Ngày:** 2026-04-14

Nguồn dữ liệu: artifacts/grading_run.jsonl.

---

## Routing Decision #1

**Task đầu vào:**
> Ticket P1 được tạo lúc 22:47. Đúng theo SLA, ai nhận thông báo đầu tiên và qua kênh nào? Deadline escalation là mấy giờ?

**Worker được chọn:** `retrieval_worker`
**Route reason (từ trace):** `task contains SLA/ticket/escalation intent | needs_tool=False`
**MCP tools được gọi:** không có
**Workers called sequence:** retrieval_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): nêu đủ 3 kênh thông báo (Slack #incident-p1, email incident@company.internal, PagerDuty), deadline 22:57, escalation lên Senior Engineer
- confidence: 0.68
- Correct routing? Yes

**Nhận xét:**

Route đúng vì câu hỏi thuần SLA retrieval, không cần policy analysis hoặc MCP tool.

---

## Routing Decision #2

**Task đầu vào:**
> Khách hàng đặt đơn ngày 31/01/2026... chính sách nào áp dụng và có được hoàn tiền không?

**Worker được chọn:** `policy_tool_worker`
**Route reason (từ trace):** `task contains policy/access intent | choose MCP-enabled policy worker | temporal policy scope check needed | needs_tool=True for external policy/tool lookup`
**MCP tools được gọi:** search_kb
**Workers called sequence:** policy_tool_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): đơn trước 01/02/2026 phải theo policy v3; dữ liệu hiện có chỉ có v4; abstain để tránh hallucination
- confidence: 0.56
- Correct routing? Yes

**Nhận xét:**

Route đúng và giúp xử lý temporal scope. Nếu route retrieval thuần rất dễ kết luận sai theo v4.

---

## Routing Decision #3

**Task đầu vào:**
> Sự cố P1 xảy ra lúc 2am, đồng thời cần cấp Level 2 access tạm thời cho contractor để emergency fix.

**Worker được chọn:** `policy_tool_worker`
**Route reason (từ trace):** `task contains policy/access intent | choose MCP-enabled policy worker | risk keywords detected | needs_tool=True for external policy/tool lookup`
**MCP tools được gọi:** search_kb, get_ticket_info, check_access_permission
**Workers called sequence:** policy_tool_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): đủ cả 2 phần: SLA notification/escalation và điều kiện Level 2 emergency bypass
- confidence: 0.58
- Correct routing? Yes

**Nhận xét:**

Đây là case multi-hop khó. Route sang policy_tool_worker giúp gom cả policy access + thông tin SLA trong cùng run.

---

## Routing Decision #4 (bonus)

**Task đầu vào:**
> Mức phạt tài chính cụ thể khi đội IT vi phạm SLA P1 resolution time là bao nhiêu?

**Worker được chọn:** `retrieval_worker`
**Route reason:** `task contains SLA/ticket/escalation intent | needs_tool=False`

**Nhận xét:**

Route đúng, nhưng điểm quan trọng là synthesis phải abstain. Kết quả mới đã không bịa con số phạt và gợi ý liên hệ IT Manager/Finance.

---

## Tổng kết

### Routing Distribution (bộ grading 10 câu)

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 5 | 50% |
| policy_tool_worker | 5 | 50% |
| human_review | 0 | 0% |

### Routing Accuracy

- Câu route đúng: 10 / 10
- Câu route sai (đã sửa bằng cách nào?): 0 trên run cuối
- Câu trigger HITL: 0 / 10 (grading), 1 / 15 trên test thường (ERR-403-AUTH)

### Lesson Learned về Routing

1. Rule-based route đủ ổn trong domain hẹp nếu route_reason rõ và có trace đầy đủ.
2. Cần tách tín hiệu từ task và từ context để tránh false trigger (đã sửa temporal scope chỉ xét task).

### Route Reason Quality

Route_reason hiện tại đã đủ để debug nhanh. Cải tiến tiếp theo là chuẩn hóa thành JSON fields: intent, risk_flags, temporal_scope, decision.
