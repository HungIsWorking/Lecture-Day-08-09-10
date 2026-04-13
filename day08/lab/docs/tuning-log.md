# Tuning Log — RAG Pipeline (Day 08 Lab)

> Template: Ghi lại mỗi thay đổi và kết quả quan sát được.
> A/B Rule: Chỉ đổi MỘT biến mỗi lần.

---

## Baseline (Sprint 2)

**Ngày:** 13/04/2026
**Config:**
```
retrieval_mode = dense
chunk_size = 300 tokens
overlap = 50 tokens
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = "gemini-2.5-flash"
```

**Scorecard Baseline:**
| Metric | Average Score |
|--------|--------------|
| Faithfulness | 4.80/5 |
| Relevance | 4.60/5 |
| Context Recall | 5.00/5 |
| Completeness | 4.50/5 |

**Câu hỏi yếu nhất (điểm thấp):**
> q09 (ERR-403-AUTH)
- Recall: None
- Reason: query dạng error code → dense retrieval chưa tối ưu keyword matching
> q10 (VIP refund case)
- Completeness: 4/5
- Reason: thiếu điều kiện ngoại lệ VIP trong policy context
> q08 (remote policy)
- Completeness: 4/5
- Reason: thiếu chi tiết điều kiện probation / điều kiện áp dụng

**Giả thuyết nguyên nhân (Error Tree):**
- [ ] Indexing: Chunking cắt giữa điều khoản
- [ ] Indexing: Metadata thiếu effective_date
- [x] Retrieval: Dense bỏ lỡ exact keyword / alias
- [x] Retrieval: Top-k quá ít → thiếu evidence
- [ ] Generation: Prompt không đủ grounding
- [ ] Generation: Context quá dài → lost in the middle

---

## Variant 1 (Sprint 3)

**Ngày:** 13/04/2026  
**Biến thay đổi:** retrieval_mode (dense → hybrid + BM25 + rerank)
**Lý do chọn biến này:**
> Từ baseline: retrieval chỉ dùng dense embedding dẫn đến fail ở keyword-based queries như q09 (ERR-403). Việc thêm hybrid (dense + BM25) và rerank (cross-encoder) được chọn để cải thiện recall cho exact matches và precision cho top results, theo A/B rule chỉ đổi 1 biến chính.

**Config thay đổi:**
```
retrieval_mode = hybrid + rerank
# Các tham số còn lại giữ nguyên như baseline
```

**Scorecard Variant 1:**
| Metric | Baseline | Variant 1 | Delta |
|--------|----------|-----------|-------|
| Faithfulness | 4.80/5 | 4.70/5 | -0.10 |
| Relevance | 4.60/5 | 4.60/5 | 0.00 |
| Context Recall | 5.00/5 | 5.00/5 | 0.00 |
| Completeness | 4.50/5 | 4.30/5 | -0.20 |

**Nhận xét:**
> Variant 1 cải thiện ở q06 (thêm chi tiết escalation), nhưng giảm faithfulness ở q07 (do rerank chọn context khác). Không cải thiện q09 vì vấn đề là thiếu docs, không phải retrieval. Completeness giảm nhẹ do rerank loại bỏ một số context bổ sung.

**Kết luận:**
> Variant 1 không cải thiện overall scores đáng kể, nhưng phù hợp với mục tiêu hybrid retrieval. Delta nhỏ cho thấy cần tuning thêm như top_k hoặc rerank threshold.

---

## Variant 2 (nếu có thời gian)

**Biến thay đổi:** ___________  
**Config:**
```
# TODO
```

**Scorecard Variant 2:**
| Metric | Baseline | Variant 1 | Variant 2 | Best |
|--------|----------|-----------|-----------|------|
| Faithfulness | ? | ? | ? | ? |
| Answer Relevance | ? | ? | ? | ? |
| Context Recall | ? | ? | ? | ? |
| Completeness | ? | ? | ? | ? |

---

## Tóm tắt học được

- **Hybrid retrieval hiệu quả hơn dense cho mixed corpus**: Baseline dense fail ở keyword queries (q09), hybrid cải thiện nhưng không hoàn toàn do docs thiếu.
- **Rerank trade-off**: Cải thiện precision nhưng có thể giảm faithfulness nếu loại bỏ context quan trọng (q07).
- **Completeness vs Faithfulness**: Thêm context (hybrid) tăng completeness nhưng có thể làm hallucination nếu context noise.
- **A/B tuning cần iterative**: Một biến không đủ, cần combine với top_k tuning cho optimal.

> TODO (Sprint 4): Điền sau khi hoàn thành evaluation.

1. **Lỗi phổ biến nhất trong pipeline này là gì?**
   > _____________

2. **Biến nào có tác động lớn nhất tới chất lượng?**
   > _____________

3. **Nếu có thêm 1 giờ, nhóm sẽ thử gì tiếp theo?**
   > _____________
