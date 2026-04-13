# Tuning Log — RAG Pipeline (Day 08 Lab)

> Template: Ghi lại mỗi thay đổi và kết quả quan sát được.
> A/B Rule: Chỉ đổi MỘT biến mỗi lần.

---

## Baseline (Sprint 2)

**Ngày:** 13/04/2026
**Config:**
```
retrieval_mode = hybrid (dense + BM25)
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
| Faithfulness | 4.8 /5 |
| Answer Relevance | 5 /5 |
| Context Recall | 5 /5 |
| Completeness | 3.9 /5 |

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
**Biến thay đổi:** top_k_select (3 -> 5) 
**Lý do chọn biến này:**
> Từ baseline: các lỗi chủ yếu nằm ở thiếu thông tin (completeness) và thiếu recall (q09, q08, q10). Code cho thấy retrieval đã là hybrid + RRF, nên vấn đề không phải ở phương pháp retrieve mà là số lượng context được đưa vào LLM. Vì vậy tăng top_k_select là thay đổi hợp lý nhất theo A/B rule.

**Config thay đổi:**
```
top_k_select = 5
# Các tham số còn lại giữ nguyên như baseline
```

**Scorecard Variant 1:**
| Metric | Baseline | Variant 1 | Delta |
|--------|----------|-----------|-------|
| Faithfulness | 4.8/5 | ?/5 | +/- |
| Answer Relevance | 5/5 | ?/5 | +/- |
| Context Recall | 5/5 | ?/5 | +/- |
| Completeness | 3.9/5 | ?/5 | +/- |

**Nhận xét:**
> TODO: Variant 1 cải thiện ở câu nào? Tại sao?
> Có câu nào kém hơn không? Tại sao?

**Kết luận:**
> TODO: Variant 1 có tốt hơn baseline không?
> Bằng chứng là gì? (điểm số, câu hỏi cụ thể)

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

> TODO (Sprint 4): Điền sau khi hoàn thành evaluation.

1. **Lỗi phổ biến nhất trong pipeline này là gì?**
   > _____________

2. **Biến nào có tác động lớn nhất tới chất lượng?**
   > _____________

3. **Nếu có thêm 1 giờ, nhóm sẽ thử gì tiếp theo?**
   > _____________
