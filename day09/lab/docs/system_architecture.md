# System Architecture — Lab Day 09

**Nhóm:** Nhóm 103  
**Ngày:** 2026-04-14  
**Version:** 1.1

---

## 1. Tổng quan kiến trúc

**Pattern đã chọn:** Supervisor-Worker  
**Lý do chọn pattern này (thay vì single agent):**

- Tách trách nhiệm rõ: supervisor chỉ route, worker xử lý nghiệp vụ.
- Dễ debug bằng trace theo từng bước: route_reason, workers_called, mcp_tools_used.
- Dễ mở rộng: thêm tool MCP hoặc worker mới mà không phải sửa toàn pipeline.

---

## 2. Sơ đồ Pipeline

```
User Query
  |
  v
Supervisor (graph.py)
  |- set supervisor_route, route_reason, risk_high, needs_tool
  |
  +--> retrieval_worker --------------------+
  |                                         |
  +--> policy_tool_worker (MCP) --------+   |
  |                                     |   |
  +--> human_review (HITL placeholder) -+   |
                              |
                              v
                       synthesis_worker
                              |
                              v
                      final_answer + sources + confidence
```

---

## 3. Vai trò từng thành phần

### Supervisor (graph.py)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Phân tích task, quyết định worker route, gắn route_reason |
| **Input** | task từ user |
| **Output** | supervisor_route, route_reason, risk_high, needs_tool |
| **Routing logic** | policy/access -> policy_tool_worker; SLA/ticket/escalation -> retrieval_worker; unknown error -> human_review |
| **HITL condition** | Unknown error code hoặc low confidence được trigger ở synthesis |

### Retrieval Worker (workers/retrieval.py)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Retrieve evidence từ ChromaDB, fallback lexical khi cần |
| **Embedding model** | sentence-transformers/all-MiniLM-L6-v2 |
| **Top-k** | Mặc định 3 |
| **Stateless?** | Yes |

### Policy Tool Worker (workers/policy_tool.py)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Kiểm tra policy, exception, temporal scope; gọi MCP tools |
| **MCP tools gọi** | search_kb, get_ticket_info, check_access_permission |
| **Exception cases xử lý** | flash_sale, digital_product, activated_product, temporal v3/v4 |

### Synthesis Worker (workers/synthesis.py)

| Thuộc tính | Mô tả |
|-----------|-------|
| **LLM model** | gemini-1.5-flash (khi có API key) |
| **Temperature** | 0 (qua generation config mặc định judge/fact-first flow) |
| **Grounding strategy** | Fact-first rule-based cho câu trọng điểm, fallback LLM, cuối cùng fallback deterministic |
| **Abstain condition** | Thiếu dữ liệu (policy v3, financial penalty absent) hoặc không có evidence |

### MCP Server (mcp_server.py)

| Tool | Input | Output |
|------|-------|--------|
| search_kb | query, top_k | chunks, sources |
| get_ticket_info | ticket_id | ticket details |
| check_access_permission | access_level, requester_role, is_emergency | can_grant, required_approvers, emergency_override |
| create_ticket | priority, title, description | mock ticket_id, created_at, url |

---

## 4. Shared State Schema

| Field | Type | Mô tả | Ai đọc/ghi |
|-------|------|-------|-----------|
| task | str | Câu hỏi đầu vào | supervisor đọc |
| supervisor_route | str | Worker được chọn | supervisor ghi |
| route_reason | str | Lý do route | supervisor ghi |
| risk_high | bool | Cờ rủi ro cao | supervisor ghi, synthesis đọc |
| needs_tool | bool | Có cần MCP tool | supervisor ghi, policy_tool đọc |
| retrieved_chunks | list | Evidence retrieval | retrieval/policy_tool ghi, synthesis đọc |
| retrieved_sources | list | Nguồn evidence | retrieval/policy_tool ghi, synthesis đọc |
| policy_result | dict | Kết quả policy/tool | policy_tool ghi, synthesis đọc |
| mcp_tools_used | list | Tool calls thực tế | policy_tool ghi |
| workers_called | list | Chuỗi worker đã đi qua | mỗi worker append |
| worker_io_logs | list | Log I/O từng worker | mỗi worker append |
| final_answer | str | Câu trả lời cuối | synthesis ghi |
| sources | list | Source citation | synthesis ghi |
| confidence | float | Mức tin cậy | synthesis ghi |
| hitl_triggered | bool | Có trigger HITL | human_review/synthesis ghi |
| latency_ms | int | Thời gian run | graph ghi |

---

## 5. Lý do chọn Supervisor-Worker so với Single Agent (Day 08)

| Tiêu chí | Single Agent (Day 08) | Supervisor-Worker (Day 09) |
|----------|----------------------|--------------------------|
| Debug khi sai | Khó tách lỗi retrieval/policy/generation | Đọc trace là biết lỗi nằm ở route hay worker |
| Thêm capability mới | Sửa prompt/hàm lớn | Thêm MCP tool hoặc worker độc lập |
| Routing visibility | Không có route_reason | Có route_reason rõ cho từng run |
| Test độc lập | Khó test từng bước | Mỗi worker test độc lập được |

**Quan sát thực tế từ lab:**

- Sau khi thêm fact-first synthesis và temporal-abstain rule, bộ grading cải thiện rõ.
- Route distribution cân bằng hơn cho domain policy và SLA.

---

## 6. Giới hạn và điểm cần cải tiến

1. Cold start của retrieval model còn cao (first query > 10s).
2. Citation hiện vẫn có nguồn nhiễu ở một số câu (nên lọc source theo domain chặt hơn).
3. HITL mới là placeholder auto-approve, chưa có cơ chế dừng/chờ người thật.
