# Routing Decisions Log — Lab Day 09

**Nhóm:** 130
**Ngày:** 14/04/2026

> **Hướng dẫn:** Ghi lại ít nhất **3 quyết định routing** thực tế từ trace của nhóm.
> Không ghi giả định — phải từ trace thật (`artifacts/traces/`).
>
> Mỗi entry phải có: task đầu vào → worker được chọn → route_reason → kết quả thực tế.

---

## Routing Decision #1

**Task đầu vào:**
> "SLA xử lý ticket P1 là bao lâu?" (q01)

**Worker được chọn:** `retrieval_worker`
**Route reason (từ trace):** `task contains SLA/ticket/escalation intent | needs_tool=False`
**MCP tools được gọi:** _(không có — needs_tool=False)_
**Workers called sequence:** `retrieval_worker → synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): "Ticket P1: phản hồi ban đầu 15 phút, resolution 4 giờ. Tự động escalate lên Senior Engineer nếu không phản hồi trong 10 phút."
- confidence: 0.69
- Correct routing? **Yes**

**Nhận xét:** Routing đúng. Câu hỏi chỉ yêu cầu tra cứu thông tin SLA đơn giản, không có policy exception hay access context → đúng khi route thẳng sang retrieval_worker mà không cần gọi MCP tools. Retrieval trả về đúng source `sla_p1_2026.txt`.

---

## Routing Decision #2

**Task đầu vào:**
> "Store credit khi hoàn tiền có giá trị bao nhiêu so với tiền gốc?" (q10)

**Worker được chọn:** `policy_tool_worker`
**Route reason (từ trace):** `task contains policy/access intent | choose MCP-enabled policy worker | needs_tool=True for external policy/tool lookup`
**MCP tools được gọi:** `search_kb`
**Workers called sequence:** `policy_tool_worker → synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): "Trả lời dựa trên evidence gần nhất — trích policy_refund_v4.txt (Điều 2-3: điều kiện được hoàn tiền và ngoại lệ)"
- confidence: 0.42
- Correct routing? **Yes** (route đúng sang policy_tool)

**Nhận xét:** Route đúng theo expected_route từ test_questions.json. Tuy nhiên, **policy_tool over-triggered exception detection**: cờ 2 exceptions (flash_sale_exception + digital_product_exception) trong khi câu hỏi chỉ hỏi về store credit — không phải Flash Sale, không phải digital product. Đây là false positive trong `analyze_policy()`, nhưng không ảnh hưởng correctness của final answer vì synthesis_worker vẫn trích đúng policy content. Confidence thấp (0.42) có thể do policy_result chứa exceptions không liên quan.

---

## Routing Decision #3

**Task đầu vào:**
> "Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?" (q02)

**Worker được chọn:** `policy_tool_worker`
**Route reason (từ trace):** `task contains policy/access intent | choose MCP-enabled policy worker | needs_tool=True for external policy/tool lookup`
**MCP tools được gọi:** `search_kb`
**Workers called sequence:** `policy_tool_worker → synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): "Trả lời dựa trên policy_refund_v4.txt — điều kiện hoàn tiền: trong 7 ngày làm việc"
- confidence: 0.61
- Correct routing? **Yes** (route đúng)

**Nhận xét:** Routing đúng như expected_route. Tương tự q10, policy_tool lại trigger false positive exceptions (flash_sale + digital_product). Câu hỏi này hỏi về thời hạn hoàn tiền thông thường, không có context Flash Sale hay digital product. Tuy nhiên, việc route sang policy_tool thay vì retrieval_worker vẫn có thể chấp nhận được vì nội dung nằm trong policy document. **Vấn đề: policy_tool over-generalize** — bất kỳ câu nào chứa "hoàn tiền" đều bị route sang policy_tool, dẫn đến MCP call không cần thiết cho những câu hỏi đơn giản chỉ cần retrieval.

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**
> "Contractor cần Admin Access (Level 3) để khắc phục sự cố P1 đang active. Quy trình cấp quyền tạm thời như thế nào?" (q13)

**Worker được chọn:** `policy_tool_worker`
**Route reason:** `task contains policy/access intent | choose MCP-enabled policy worker | needs_tool=True for external policy/tool lookup`

**Kết quả thực tế:**
- MCP tools được gọi: `search_kb`, `get_ticket_info`, `check_access_permission`
- Workers called sequence: `policy_tool_worker → synthesis_worker`
- confidence: 0.61
- Correct routing? **Yes** (route đúng)

**Nhận xét:** Đây là trường hợp routing khó nhất trong lab vì nhiều lý do:

1. **Multi-dimensional intent**: Câu hỏi chứa đồng thời P1 incident (SLA context) + Level 3 access (Access Control context). Routing phải nhận diện cả hai, nhưng supervisor chỉ route 1 lần sang `policy_tool_worker` — đủ vì policy_tool gọi cả `search_kb` lẫn `get_ticket_info` và `check_access_permission`.

2. **False positive policy exception**: `analyze_policy()` trả về `digital_product_exception` mặc dù câu hỏi hoàn toàn không liên quan đến digital product. Nguyên nhân: keyword "license" xuất hiện trong context text được retrieve. Đây là bug trong deterministic rule-based policy detection.

3. **Cross-document reasoning**: Câu trả lời đúng cần kết hợp thông tin từ 2 documents: `access_control_sop.txt` (Level 3 cần 3 approvers, không có emergency bypass) + `sla_p1_2026.txt` (P1 notification channels). Retrieval trả về đúng 3 documents.

4. **Answer quality**: Final answer trích đúng nội dung từ SLA và Access Control docs, nhưng chứa cả digital_product exception không liên quan, làm giảm overall coherence.

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 9 | 50% |
| policy_tool_worker | 9 | 50% |
| human_review | 1 (q09 — ERR-403-AUTH không có trong docs) | 5% |

### Routing Accuracy

> Trong số 18 câu nhóm đã chạy, bao nhiêu câu supervisor route đúng?

- Câu route đúng: **15 / 18** (83%)
- Câu route cần cải thiện: **3** — q02, q10, q12 (route policy_tool nhưng over-trigger false positive exceptions; không ảnh hưởng final answer nhưng tăng latency không cần thiết)
- Câu trigger HITL: **1 / 18** (q09 — ERR-403-AUTH, câu hỏi không có answer trong docs)

### Lesson Learned về Routing

> Quyết định kỹ thuật quan trọng nhất nhóm đưa ra về routing logic là gì?
> (VD: dùng keyword matching vs LLM classifier, threshold confidence cho HITL, v.v.)

1. **Keyword matching gây over-generalization**: Supervisor route bất kỳ câu nào chứa "hoàn tiền" hoặc "cấp quyền" sang `policy_tool_worker`. Điều này khiến những câu hỏi đơn giản (chỉ cần tra cứu số liệu từ policy document) vẫn phải chạy qua `policy_tool.analyze_policy()` — tăng latency và gây false positive exceptions. **Cải tiến**: Thêm logic phân biệt "câu hỏi tra cứu số liệu" vs "câu hỏi phân tích exception/policy" bằng cách check thêm keywords như "exception", "được không", "có được không", "điều kiện".

2. **Deterministic policy exception detection gây false positive**: `analyze_policy()` sử dụng keyword matching cứng nhắc — bất kỳ chunk nào chứa "flash sale", "license", "kích hoạt" trong context đều trigger exception, dù câu hỏi gốc không liên quan. **Cải tiến**: Chỉ trigger exception khi keyword đó xuất hiện **trong câu hỏi gốc** (task), không phải chỉ trong retrieved context.

### Route Reason Quality

> Nhìn lại các `route_reason` trong trace — chúng có đủ thông tin để debug không?
> Nếu chưa, nhóm sẽ cải tiến format route_reason thế nào?

Các `route_reason` hiện tại có dạng: `"task contains SLA/ticket/escalation intent | needs_tool=False"` hoặc `"task contains policy/access intent | choose MCP-enabled policy worker | needs_tool=True for external policy/tool lookup"`. Chúng đủ để hiểu **tại sao** route được chọn, nhưng **thiếu** thông tin về **tại sao KHÔNG chọn** worker kia. Ví dụ: không ghi rõ "vì sao không route retrieval_worker" khi chọn policy_tool.

**Cải tiến format route_reason**:
```
route=policy_tool_worker | reason=policy/access keywords detected + risk assessment
  └─ considered: retrieval_worker → REJECTED (task contains policy exception intent)
  └─ considered: human_review → REJECTED (risk_high=False, confidence>=threshold)
```

Format mới giúp debug nhanh hơn bằng cách ghi nhận cả lý do reject các worker khác.