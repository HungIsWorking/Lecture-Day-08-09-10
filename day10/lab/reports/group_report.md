# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Nhóm 130  
**Ngày nộp:** 2026-04-15  
**Repo:** day10/lab

## Vai trò theo rubric (4 vai trò chuẩn)

| Tên | Vai trò Day 10 | Ghi chú bằng chứng |
|-----|-----------------|---------------------|
| Nguyễn Đăng Hải | Ingestion & Embed Owner | Triển khai load_raw_csv, cmd_run/cmd_embed_internal (etl_pipeline.py), eval_retrieval.py, grading_run.py, pruning stale vector (được đề xuất từ Cleaning Owner) |
| Tran Trung Hau | Cleaning & Quality Owner | Triển khai Rule 7-11 (transform/cleaning_rules.py), E7-E8 (quality/expectations.py), phát hiện & fix anomaly prune stale vector |
| Nguyễn Tuấn Hưng | Monitoring / Docs Owner | Chạy thực nghiệm before/after, tổng hợp số liệu, hoàn thiện group report và kiểm tra grading/manifest |

Ghi chú trung thực: 3 thành viên trên đều có báo cáo cá nhân và bằng chứng trong repo. Mỗi vai trò đã tách bạch rõ: Ingestion & Embed Owner (Hải), Cleaning & Quality Owner (Hau), Monitoring / Docs Owner (Hưng).

---

## 1. Pipeline tổng quan

Nguồn raw sử dụng là data/raw/policy_export_dirty.csv. Luồng chạy end-to-end theo etl_pipeline.py:

1. Ingest CSV và map schema.
2. Chạy cleaning rules trong transform/cleaning_rules.py để loại bỏ unknown doc_id, parse ngày, quarantine dữ liệu lỗi, fix stale refund và chuẩn hóa text.
3. Chạy expectation suite trong quality/expectations.py.
4. Embed vào Chroma collection day10_kb, upsert theo chunk_id và prune id không còn trong cleaned để giữ snapshot idempotent.
5. Ghi log và manifest trong artifacts/logs/ và artifacts/manifests/.

Lệnh chạy thực tế:

/home/tuanhung/VINUNI/assignments/day_01_llm_api_foundation/vinuni/bin/python etl_pipeline.py run --run-id sprint3-after

Kết quả run sprint3-after (từ manifest_sprint3-after.json): raw_records=10, cleaned_records=6, quarantine_records=4.

---

## 2. Cleaning & expectation

Code hiện tại có baseline rules + extensions trong transform/cleaning_rules.py (Rule 7-11) và expectation E7-E8 trong quality/expectations.py.

### 2a. Bảng metric_impact

| Rule / Expectation mới | Trước (before) | Sau (after) | Chứng cứ |
|------------------------|--------------------------|----------------------|----------|
| refund_no_stale_14d_window (halt) | violations=1 ở sprint3-before | violations=0 ở sprint3-after | artifacts/logs/run_sprint3-before.log, artifacts/logs/run_sprint3-after.log |
| no_missing_exported_at (halt) | missing_exported_at_count=0 | vẫn 0 trước/sau | artifacts/logs/run_sprint3-before.log |
| max_chunk_length_5000 (warn) | chunks_over_5000=0 | vẫn 0 trước/sau | artifacts/logs/run_sprint3-after.log |
| Prune stale vectors | không có id dư sau run clean | embed_prune_removed=1 khi chuyển giữa before/after | artifacts/logs/run_sprint3-before.log, artifacts/logs/run_sprint3-after.log |

Ví dụ expectation fail ở run before:

- Run sprint3-before ghi nhận expectation refund fail trước khi phục hồi ở run sau.
- Log ghi rõ: expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=1.
- Run sprint3-after chạy lại pipeline chuẩn và expectation này trở về OK.

---

## 3. Before / after ảnh hưởng retrieval

Kịch bản before/after theo Sprint 3:

- Before: python etl_pipeline.py run --run-id sprint3-before --no-refund-fix --skip-validate
- Eval before: python eval_retrieval.py --out artifacts/eval/sprint3-before_eval.csv
- After: python etl_pipeline.py run --run-id sprint3-after
- Eval after: python eval_retrieval.py --out artifacts/eval/sprint3-after_eval.csv

Kết quả định lượng (từ file CSV thật):

- Trước (before): full_pass=3/4, no_forbidden=3/4.
- Sau fix (after): full_pass=4/4, no_forbidden=4/4.
- Câu q_refund_window: hits_forbidden đổi từ yes (before) sang no (after).
- Câu q_leave_version: giữ ổn định contains_expected=yes, hits_forbidden=no, top1_doc_expected=yes ở cả before và after.

Bảng tổng hợp đã lưu trong:

- artifacts/eval/before_after_eval.csv

---

## 4. Freshness & monitoring

Freshness check của run sprint3-before và sprint3-after đều FAIL do dữ liệu raw cũ hơn SLA 24h:

- latest_exported_at: 2026-04-10T08:00:00
- age_hours: 122.293 (before), 122.331 (after)
- sla_hours: 24.0
- reason: freshness_sla_exceeded

Diễn giải: đây là hành vi đúng với snapshot lab. Pipeline vẫn pass ETL/expectation ở run clean và ghi rõ nguyên nhân freshness trong log/manifest.

---

## 5. Liên hệ Day 09

Collection dùng cho Day 10 là day10_kb (khác với day09_kb) để tách bộ test và tránh nhiễu index khi so sánh before/after. Dữ liệu sau clean/embed vẫn cùng domain với Day 09 (refund, SLA, FAQ, HR leave), nên có thể tích hợp lại worker retrieval của Day 09 nếu cấu hình cùng collection.

---

## 6. Rủi ro còn lại & việc chưa làm

- Chưa có source dữ liệu mới theo SLA 24h; cần cập nhật exported_at hoặc đổi SLA nếu theo snapshot.
- Chưa có kênh alert bên ngoài (Slack/Email); hiện tại chỉ lưu log nội bộ.
- Chưa có đầy đủ báo cáo cá nhân của toàn bộ thành viên trong thư mục reports/individual/.
