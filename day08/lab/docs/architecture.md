# Architecture — RAG Pipeline (Day 08 Lab)

## 1. Tổng quan kiến trúc

```
[Raw Docs]
    ↓
[index.py: Preprocess → Chunk → Embed → Store]
    ↓
[ChromaDB Vector Store]
    ↓
[rag_answer.py: Query → Retrieve → Rerank → Generate]
    ↓
[Grounded Answer + Citation]
```

**Mô tả ngắn gọn:**
Hệ thống RAG (Retrieval-Augmented Generation) hỗ trợ giải đáp thắc mắc về các chính sách nội bộ và quy trình kỹ thuật cho nhân viên. Hệ thống giúp tra cứu nhanh thông tin từ các tài liệu PDF/Markdown về HR, IT, SLA và Refund, đảm bảo câu trả lời luôn có dẫn chứng (citation) và giảm thiểu tình trạng ảo giác của AI.

---

## 2. Indexing Pipeline (Sprint 1)

### Tài liệu được index
| File | Nguồn | Department | Số chunk |
|------|-------|-----------|---------|
| `policy_refund_v4.txt` | policy/refund-v4.pdf | Customer Service | 6 |
| `sla_p1_2026.txt` | support/sla-p1-2026.pdf | IT Support | 7 |
| `access_control_sop.txt` | it/access-control-sop.md | IT Security | 6 |
| `it_helpdesk_faq.txt` | support/helpdesk-faq.md | IT Support | 6 |
| `hr_leave_policy.txt` | hr/leave-policy-2026.pdf | HR | 10 |

### Quyết định chunking
| Tham số | Giá trị | Lý do |
|---------|---------|-------|
| Chunk size | 300 tokens (1200 chars) | Cân bằng giữa việc giữ đủ ngữ cảnh và tối ưu độ tập trung cho LLM. |
| Overlap | 50 tokens (200 chars) | Đảm bảo không mất thông tin tại các điểm cắt giữa các chunk. |
| Chunking strategy | Section + Paragraph based | Ưu tiên cắt theo heading (===) để giữ toàn vẹn điều khoản, sau đó mới chia nhỏ theo paragraph. |
| Metadata fields | source, section, effective_date, department, access | Phục vụ filter, kiểm tra độ tươi mới của thông tin và trích dẫn nguồn. |

### Embedding model
- **Model**: Local (`paraphrase-multilingual-MiniLM-L12-v2`)
- **Vector store**: ChromaDB (PersistentClient)
- **Similarity metric**: Cosine Similarity

---

## 3. Retrieval Pipeline (Sprint 2 + 3)

### Baseline (Sprint 2)
| Tham số | Giá trị |
|---------|---------|
| Strategy | Dense (Embedding similarity) |
| Top-k search | 10 |
| Top-k select | 3 |
| Rerank | Không |

### Variant (Sprint 3)
| Tham số | Giá trị | Thay đổi so với baseline |
|---------|---------|------------------------|
| Strategy | Hybrid (Dense + Sparse/BM25) | Kết hợp nghĩa ngữ nghĩa và từ khóa chính xác. |
| Top-k search | 10 | Giữ nguyên độ rộng tìm kiếm. |
| Top-k select | 5 | Tăng số chunk đưa vào prompt để tăng độ đầy đủ (Completeness). |
| Rerank | True | Lọc bỏ các chunk nhiễu khi tăng k_select lên 5. |

**Lý do chọn variant này:**
Sử dụng Hybrid để bắt được các từ khóa chuyên ngành (như mã lỗi ERR-403) mà tìm kiếm semantic đôi khi bỏ lỡ. Kết hợp với Rerank giúp hệ thống có thể tăng số lượng chunk cung cấp cho LLM (k=5) để câu trả lời đầy đủ hơn mà không lo bị nhiễu thông tin, từ đó cải thiện cả điểm Faithfulness và Completeness.

---

## 4. Generation (Sprint 2)

### Grounded Prompt Template
```
Answer only from the retrieved context below.
If the context is insufficient to answer the question, say you do not know and do not make up information.
Cite the source field (in brackets like [1]) when possible.
Keep your answer short, clear, and factual.
Respond in the same language as the question.

Question: {query}

Context:
{context_block}

Answer:
```

### LLM Configuration
| Tham số | Giá trị |
|---------|---------|
| Model | OpenAI `gpt-4o-mini` |
| Temperature | 0 (đảm bảo tính nhất quán cho evaluation) |
| Max tokens | 1024 |

---

## 5. Failure Mode Checklist

| Failure Mode | Triệu chứng | Cách kiểm tra | Ví dụ thực tế |
|-------------|-------------|---------------|---------------|
| **Missing Detail (Low Completeness)** | Câu trả lời đúng nhưng thiếu ý phụ quan trọng. | `score_completeness()` thấp (Ví dụ: 2/5). | Câu **q01**: Baseline chỉ lấy được Resolution time nhưng thiếu Response time do `k_select` quá nhỏ. |
| **Noise Overload (Hallucination/Abstain)** | AI trả lời "Tôi không biết" dù dữ liệu có trong context. | Điểm `Relevance` tụt khi tăng `k`. | Câu **q07**: Khi tăng `k=5` mà không Rerank, AI bị nhiễu và không bắt được thông tin về việc đổi tên tài liệu. |
| **Alias Mismatch** | Retrieval không tìm thấy tài liệu chứa từ khóa viết tắt/tên cũ. | `Context Recall` thấp hoặc 0. | Truy vấn "Approval Matrix" không tìm thấy "Access Control SOP" nếu chỉ dùng Dense Retrieval. |
| **Chunk Fragmentation** | Thông tin bị cắt đôi giữa 2 chunk khiến AI mất liên kết. | Đọc `list_chunks()` kiểm tra đoạn cắt. | Các bảng biểu hoặc danh sách gạch đầu dòng dài bị chia nhỏ quá mức. |
| **Token Overload** | Câu trả lời bị cắt ngang hoặc AI bị "lú" (Lost in the middle). | Kiểm tra `max_tokens` và độ dài context. | Khi nhồi nhét 10+ chunk vào prompt mà không có chiến thuật rerank/priority. |

---

## 6. Diagram

```mermaid
graph LR
    A[User Query] --> B[Dense + Sparse Search]
    B --> C[Hybrid Fusion (RRF)]
    C --> D[Top-10 Candidates]
    D --> E[Cross-Encoder Rerank]
    E --> F[Top-5 Selection]
    F --> G[Build Context Block]
    G --> H[Grounded Prompt]
    H --> I[LLM: gpt-4o-mini]
    I --> J[Answer]
```
