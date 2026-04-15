# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

**Sự cố 1:** User / agent trả lời sai: "14 ngày" thay vì "7 ngày" cho câu hỏi về cửa sổ hoàn tiền.
- Lý do: chunk từ `policy_refund_v4` vẫn chứa nội dung stale bản v3 (14 ngày)
- Detection: `eval_retrieval.py` thấy `hits_forbidden=yes` cho `q_refund_window`

**Sự cố 2:** Agent trả lời "10 ngày phép năm" thay vì "12 ngày" cho câu hỏi về nghỉ phép.
- Lý do: chunk từ `hr_leave_policy` bản 2025 bị quarantine đúng nhưng bản 2026 chưa được embed
- Detection: `grading_run.jsonl` thấy `hits_forbidden=yes` hoặc `top1_doc_matches=false` cho `gq_d10_03`

**Sự cố 3:** Freshness check FAIL trên manifest mới.
- Lý do: `exported_at` trong CSV cũ hơn 24 giờ (SLA mặc định); hoặc `latest_exported_at` bị rỗng
- Detection: `freshness_check=FAIL` trong log

---

## Detection

Các metric báo hiệu sự cố:

| Metric | Công cụ | Ngưỡng |
|--------|---------|--------|
| `hits_forbidden=yes` trên eval | `eval_retrieval.py` / `grading_run.py` | 0 expected |
| `expectation[refund_no_stale_14d_window] FAIL` | Log pipeline | 0 expected |
| `expectation[hr_leave_no_stale_10d_annual] FAIL` | Log pipeline | 0 expected |
| `quarantine_records` tăng bất thường | Log pipeline | baseline 4–6 records |
| `freshness_check=FAIL` | `etl_pipeline.py freshness` | 0 expected |
| `embed_prune_removed` > 0 sau rerun đúng | Log pipeline | 0 nếu không thay đổi |

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra `artifacts/manifests/*.json` mới nhất | Tìm `run_id`, `cleaned_records`, `quarantine_records` |
| 2 | Mở `artifacts/quarantine/quarantine_<run-id>.csv` | Xem lý do quarantine: stale HR, duplicate, missing date |
| 3 | Chạy `python eval_retrieval.py --out artifacts/eval/before_after_eval.csv` | So sánh `contains_expected` / `hits_forbidden` |
| 4 | Chạy `python grading_run.py --out artifacts/eval/grading_run.jsonl` | Kiểm tra 3 dòng JSONL: gq_d10_01/02/03 |
| 5 | Kiểm tra `artifacts/logs/run_<run-id>.log` | Tìm expectation FAIL, embed_prune_removed, freshness |
| 6 | So sánh chunk text trong ChromaDB (`day10_kb` collection) | Đảm bảo không còn "14 ngày làm việc" hoặc "10 ngày phép năm" |

---

## Mitigation

**Khi phát hiện stale refund chunk (14 ngày):**
1. Kiểm tra `artifacts/quarantine/*.csv` — đảm bảo chunk 14 ngày bị quarantine hoặc đã được fix text
2. Rerun pipeline chuẩn: `python etl_pipeline.py run`
3. Verify: `grep "14 ngày làm việc" artifacts/cleaned/*.csv` → không có kết quả
4. Verify eval: `python grading_run.py` → gq_d10_01 `hits_forbidden=false`

**Khi phát hiện stale HR chunk (10 ngày):**
1. Kiểm tra `artifacts/quarantine/quarantine_*.csv` có dòng `hr_leave_policy` với `reason=stale_hr_policy_effective_date`
2. Rerun pipeline: bản 2026 (effective_date 2026-02-01, 12 ngày phép) sẽ được clean và embed
3. Verify: `python grading_run.py` → gq_d10_03 `contains_expected=true` và `top1_doc_matches=true`

**Khi freshness FAIL:**
1. Kiểm tra SLA: `exported_at` trong CSV mẫu là 2026-04-10 — cũ hơn 5 ngày so với ngày chạy
2. Giải thích: đây là data snapshot mô phỏng; SLA 24h áp dụng cho "data export" chứ không phải pipeline run
3. Hoặc cập nhật `exported_at` trong CSV nếu muốn freshness PASS
4. Tùy chọn: điều chỉnh `FRESHNESS_SLA_HOURS=168` (7 ngày) trong `.env` nếu dùng data snapshot cũ

---

## Prevention

**Thêm expectation / guardrail:**

| Guardrail | File | Mục đích |
|-----------|------|----------|
| `refund_no_stale_14d_window` (halt) | `quality/expectations.py` E3 | Ngăn chunk 14 ngày đi qua pipeline |
| `hr_leave_no_stale_10d_annual` (halt) | `quality/expectations.py` E6 | Ngăn bản HR 2025 đi qua pipeline |
| `no_missing_exported_at` (halt) | `quality/expectations.py` E8 | Đảm bảo freshness luôn tính được |
| `max_chunk_length_5000` (warn) | `quality/expectations.py` E7 | Cảnh báo chunk quá dài |
| Rule 7 (BOM detection) | `transform/cleaning_rules.py` | Ngăn encoding garbage |
| Rule 8 (exported_at) | `transform/cleaning_rules.py` | Ngăn row không có timestamp |
| Rule 9 (max length) | `transform/cleaning_rules.py` | Ngăn chunk quá dài |

**Alert channel:** log `freshness_check=FAIL` → check `artifacts/logs/run_*.log`; expectation halt → pipeline return code 2

**Owner:** mỗi rule/expectation có owner được ghi trong `group_report.md`