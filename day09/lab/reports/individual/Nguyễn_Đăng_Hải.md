# Báo Cáo Cá Nhân - Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Đăng Hải  
**MSSV:** 2A202600390
**Vai trò trong nhóm:** Supervisor Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500-800 từ

---

## 1. Tôi phụ trách phần nào? (100-150 từ)

Tôi phụ trách vai trò Supervisor Owner và code trực tiếp Sprint 1, đồng thời hỗ trợ Sprint 2 để luồng điều phối chạy thông suốt. File chính tôi làm là `graph.py`, trong đó tôi implement `AgentState`, `supervisor_node()`, `route_decision()`, `human_review_node()`, `build_graph()`, `run_graph()` và `save_trace()`. Quyết định của tôi ở Sprint 1 là tách flow thành supervisor -> worker -> synthesis, có route reason để debug thay vì gom tất cả vào một hàm RAG monolith. Ở Sprint 2, tôi kết nối wrappers worker để state cập nhật đúng contract.

Công việc của tôi kết nối trực tiếp với phần Worker Owner: supervisor route đúng thì retrieval/policy worker mới được gọi đúng lúc. Bằng chứng là trace `run_20260414_164747_687835`, `run_20260414_164758_990376`, `run_20260414_164759_013221` đều có `supervisor_route`, `route_reason`, `workers_called` và `latency_ms` đầy đủ.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150-200 từ)

**Quyết định:** Tôi chọn routing deterministic bằng keyword trong `supervisor_node()` thay vì gọi LLM để classify route.

Lý do lớn nhất là speed và khả năng debug. Trong lab, câu hỏi tập trung vào nhóm rõ ràng (SLA/ticket/escalation, policy/refund, access/emergency). Nếu route bằng LLM thì mỗi query phải thêm 1 lần gọi model, tốn độ trễ và khó tái lập. Với keyword routing, tôi kiểm soát được quy tắc và giải thích được `route_reason`. Các tập keyword tôi dùng là `policy_keywords`, `access_keywords`, `retrieval_keywords`, `risk_keywords`. Tôi cũng đặt `needs_tool` và `risk_high` ở tầng supervisor.

**Trade-off tôi chấp nhận:** keyword routing có thể bỏ sót cách diễn đạt lạ, và cần bảo trì rule set khi domain mở rộng. Đổi lại, nó minh bạch, nhanh, và dễ đo tác động qua trace.

**Bằng chứng từ trace/code:**

```python
# graph.py
if has_policy or has_access:
  route = "policy_tool_worker"
  needs_tool = True
elif has_retrieval:
  route = "retrieval_worker"
```

Trong trace `run_20260414_164759_013221`, câu hỏi "Level 3 ... P1 khẩn cấp" được route vào `policy_tool_worker`, có thêm `risk_high=true` và `route_reason` chứa signal "risk keywords detected".

---

## 3. Tôi đã sửa một lỗi gì? (150-200 từ)

**Lỗi:** Luồng route cho task có mã lỗi lạ chưa trigger human review đúng như thiết kế, do regex detect mã lỗi quá hẹp trong `supervisor_node()`.

**Symptom (pipeline sai gì):** Với một số task mô tả lỗi theo format khác, pipeline vẫn rơi vào nhánh retrieval mặc dù ý định là cần can thiệp người. Trace không có `hitl_triggered=true`, và `workers_called` không chứa `human_review`.

**Root cause:** Pattern regex ban đầu không bao hết biến thể mã lỗi. Nếu regex fail thì flow rơi xuống fallback retrieval.

**Cách sửa:** Tôi mở rộng regex trong `graph.py` thành:

```python
has_unknown_error = bool(re.search(r"\berr[-_ ]?\d{2,5}\b|\berr[-_][a-z0-9-]+\b", task))
```

Sau đó giữ nguyên rule:

```python
if has_unknown_error and not (has_policy or has_access or has_retrieval):
  route = "human_review"
```

**Bằng chứng trước/sau:** Sau khi sửa, trace lưu được đầy đủ `hitl_triggered`, lịch sử có dòng `[human_review] HITL triggered`, và route reason nêu rõ unknown error.

---

## 4. Tôi tự đánh giá đóng góp của mình (100-150 từ)

**Tôi làm tốt nhất ở điểm nào?**

Tôi làm tốt phần thiết kế orchestration: state rõ ràng, route giải thích được, và dễ trace. Team debug nhanh hơn vì nhìn vào `route_reason`, `history`, `workers_called` là biết lỗi nằm ở supervisor hay worker.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Routing deterministic vẫn phụ thuộc keyword, nên độ bền với cách đặt câu hỏi lạ còn giới hạn. Tôi chưa có bộ test route theo edge-case đầy đủ ở Sprint 1.

**Nhóm phụ thuộc vào tôi ở đâu?**

Nếu tôi chưa xong `graph.py`, toàn bộ workers dù code xong vẫn không có điểm vào/ra thống nhất, và không có trace end-to-end.

**Phần tôi phụ thuộc vào thành viên khác:**

Tôi cần worker outputs ổn định từ `workers/retrieval.py` và `workers/policy_tool.py` để synthesis có đủ evidence và confidence hợp lý.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50-100 từ)

Tôi sẽ thêm một lớp route scoring nhẹ cho supervisor (kết hợp keyword + ưu tiên theo cụm ý định) thay vì match có/không. Lý do: trace `run_20260414_164759_013221` cho thấy query vừa có signal policy/access vừa có signal P1/SLA; với câu phức hợp, đôi khi cần gọi retrieval trước để làm giàu context. Cải tiến này có thể giảm route ambiguity và ổn định confidence ở câu multi-hop.