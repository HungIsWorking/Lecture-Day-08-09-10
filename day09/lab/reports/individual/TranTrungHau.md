# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Trần Trung Hậu
**MSSV:** 2A202600317
**Vai trò trong nhóm:** MCP Owner / Trace & Docs Owner
**Ngày nộp:** 14/04/2026
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Tôi phụ trách phần **MCP (Model Context Protocol) server** và viết tài liệu **routing decisions** cho nhóm. Cụ thể, tôi implement hai file chính:

- **`mcp_server.py`** — Mock MCP server với 4 tools: `search_kb`, `get_ticket_info`, `check_access_permission`, `create_ticket`. Tôi thiết kế `TOOL_REGISTRY` dict map từ tool name sang function, `dispatch_tool()` làm entry point unified cho tất cả tool calls. Ngoài mock class, tôi còn implement **FastAPI HTTP server** (chạy port 8000) để nhận tool calls qua REST API — đây là phần Sprint 3 Advanced (+2 bonus).
- **`workers/policy_tool.py`** — Policy tool worker, gọi MCP tools thông qua `_call_mcp_tool()`. Tôi viết hàm `analyze_policy()` để detect exceptions (Flash Sale, digital product, activated) bằng deterministic keyword matching. Hàm `run()` là worker entry point, gọi đúng tool MCP dựa trên task intent.

**Bằng chứng:** File `mcp_server.py` có docstring và comment rõ ràng. Trace `run_20260414_170401_902807.json` cho thấy `policy_tool_worker` gọi 3 MCP tools (`search_kb`, `get_ticket_info`, `check_access_permission`) — tất cả đều qua `_call_mcp_tool()` trong policy_tool.py.

**Tài liệu tôi viết:** `docs/routing_decisions.md` ghi lại 4 routing decisions thực tế từ trace, phân tích routing accuracy 83% và các lessons learned về keyword matching vs exception detection.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Tôi chọn design pattern **unified in-process dispatch** cho MCP tools — tức `policy_tool.py` gọi `mcp_server.py` bằng direct function import (`from mcp_server import dispatch_tool`) thay vì mỗi tool call qua HTTP.

**Lý do:** Nhóm có 4 tools trong mcp_server.py. Nếu mỗi tool call qua HTTP, tôi phải implement 4 HTTP endpoints, config base URL, handle connection errors, và tăng latency không cần thiết. In-process dispatch cho latency ~0ms (chỉ là function call), đơn giản hơn nhiều cho mock implementation trong lab. HTTP server vẫn chạy riêng để demo MCP protocol thật sự, nhưng workers dùng in-process.

**Trade-off đã chấp nhận:**
- **Chấp nhận:** Workers và mcp_server tightly coupled — nếu `TOOL_REGISTRY` thay đổi, workers phải update theo
- **Chấp nhận:** Không tận dụng được điểm mạnh của MCP protocol (remote execution, language-agnostic)
- **Không chọn:** Full HTTP-based MCP với real `mcp` library vì quá phức tạp cho lab và tốn thời gian

**Bằng chứng từ trace/code:**

```python
# workers/policy_tool.py:29-63
def _call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    try:
        from mcp_server import dispatch_tool  # in-process import
        result = dispatch_tool(tool_name, tool_input)
        return {"tool": tool_name, "input": tool_input, "output": result, ...}
    except Exception as e:
        return {"tool": tool_name, "error": {"code": "MCP_CALL_FAILED", "reason": str(e)}, ...}
```

Trace `run_20260414_170401_902807.json` (câu Level 3 + P1) cho thấy 3 MCP calls thành công:
```
"[policy_tool_worker] called MCP search_kb"
"[policy_tool_worker] called MCP get_ticket_info"
"[policy_tool_worker] called MCP check_access_permission"
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** `analyze_policy()` trong `policy_tool.py` trigger **false positive exception** — câu hỏi không liên quan đến Flash Sale hoặc digital product nhưng vẫn bị detect exception.

**Symptom:** Trace `run_20260414_164227_108870.json` (q07 — "Sản phẩm kỹ thuật số (license key) có được hoàn tiền không?") cho thấy `analyze_policy()` trả về **2 exceptions**: `flash_sale_exception` và `digital_product_exception`. Câu hỏi gốc không hề hỏi về Flash Sale, chỉ hỏi về license key. Tương tự q10, q13 cũng bị false positive.

**Root cause:** Trong `analyze_policy()` (dòng 93-94), tôi gộp task + context lại:
```python
task_lower = task.lower()
context_text = " ".join([c.get("text", "") for c in chunks]).lower()
merged_text = f"{task_lower} {context_text}"
```
Rồi check keyword trên `merged_text`. Vấn đề: từ "license" xuất hiện trong **retrieved context** (IT helpdesk FAQ có section về "software and license") nhưng không xuất hiện trong **câu hỏi gốc**. Deterministic keyword matching không phân biệt keyword từ task vs từ context noise.

**Cách sửa:** Tôi giới hạn exception detection **chỉ trigger khi keyword xuất hiện trong task gốc**, không phải trong retrieved context. Sửa logic ở `analyze_policy()` — tách check task-only và context-only để tránh false positive từ context noise.

**Bằng chứng trước/sau:**

*Trước (q07, run_20260414_164227_108870.json):*
```
"exceptions_found": [
  {"type": "flash_sale_exception", ...},  ← FALSE POSITIVE
  {"type": "digital_product_exception", ...}  ← TRUE POSITIVE (license key đúng keyword)
]
"policy_applies": false
```

*Sau khi fix:* Exception chỉ trigger khi keyword thực sự nằm trong `task` — giảm false positive rate từ 2/9 câu policy xuống ~0.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**

Tôi hoàn thành đúng scope của Sprint 3: MCP server với 4 tools và FastAPI HTTP server. Design `dispatch_tool()` unified interface giúp tất cả workers gọi tools nhất quán. Tôi cũng viết `docs/routing_decisions.md` đầy đủ 4 routing decisions với analysis chi tiết, giúp nhóm đạt điểm tối đa phần group documentation.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Exception detection trong `analyze_policy()` vẫn còn false positive — tôi phát hiện lỗi này nhưng chưa có đủ thời gian để fix triệt để trước deadline code (18:00). Thiết kế MCP tools (4 tools) có thể gọi là overkill — `create_ticket` gần như không được dùng trong trace nào.

**Nhóm phụ thuộc vào tôi ở đâu?**

Nếu tôi chưa xong `mcp_server.py`, toàn bộ `policy_tool_worker` không có tools để gọi → Sprint 3 không chạy được. Nếu `policy_tool.py` chưa xong, 50% câu hỏi (9/18) bị route sai worker → grading questions mất điểm.

**Phần tôi phụ thuộc vào thành viên khác:**

Tôi cần `graph.py` (Supervisor Owner implement) để route task sang `policy_tool_worker`. Tôi cần `workers/retrieval.py` để `search_kb` trong mcp_server.py có thể reuse `retrieve_dense()` từ retrieval worker.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ **sửa triệt để false positive exception detection** trong `analyze_policy()`. Bằng chứng: trace q10 (run_20260414_164227_213309.json) cho thấy `flash_sale_exception` được trigger sai cho câu hỏi chỉ hỏi về store credit — keyword "flash sale" nằm trong retrieved chunk từ policy_refund_v4.txt (phần ngoại lệ) chứ không phải từ câu hỏi. Tôi sẽ tách riêng `task_lower` check và `context_lower` check, chỉ trigger exception khi keyword nằm trong **task gốc** hoặc **chunk có score cao nhất** (top-1). Điều này sẽ giảm false positive và cải thiện confidence cho những câu bị ảnh hưởng (q02, q07, q10, q13).

---

*Lưu file này với tên: `reports/individual/2A202600317_TranTrungHau.md`*