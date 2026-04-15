# Quality Report — Lab Day 10 (Nhóm 130)

**run_id:** sprint3-before, sprint3-after  
**Ngày:** 2026-04-15

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước | Sau | Ghi chú |
|--------|-------|-----|---------|
| raw_records | 10 | 10 | Từ manifest_sprint3-before.json và manifest_sprint3-after.json |
| cleaned_records | 6 | 6 | Không đổi giữa run before/after trên cùng bộ raw |
| quarantine_records | 4 | 4 | Không đổi trên cùng bộ raw |
| Expectation halt? | FAIL (refund_no_stale_14d_window, violations=1) | PASS (tất cả halt = OK) | Khác biệt thể hiện rõ giữa run before và run after |

---

## 2. Before / after retrieval (bắt buộc)

Đã lưu đủ 3 file bằng chứng:

- artifacts/eval/sprint3-before_eval.csv
- artifacts/eval/sprint3-after_eval.csv
- artifacts/eval/before_after_eval.csv

**Câu hỏi then chốt:** refund window (q_refund_window)  
**Trước:** contains_expected=yes, hits_forbidden=yes  
**Sau:** contains_expected=yes, hits_forbidden=no

**Merit:** versioning HR ở q_leave_version

**Trước:** contains_expected=yes, hits_forbidden=no, top1_doc_expected=yes  
**Sau:** contains_expected=yes, hits_forbidden=no, top1_doc_expected=yes

Tổng quan retrieval:

- Trước (before): full_pass=3/4, no_forbidden=3/4
- Sau fix: full_pass=4/4, no_forbidden=4/4

---

## 3. Freshness & monitor

Kết quả freshness của cả 2 run đều FAIL với cùng nguyên nhân:

- latest_exported_at = 2026-04-10T08:00:00
- sla_hours = 24
- age_hours = 122.293 (before) và 122.331 (after)

Giải thích: dữ liệu raw là snapshot mẫu cũ trong lab, nên freshness FAIL là kỳ vọng đúng theo SLA 24h. Pipeline vẫn chạy thành công và log rõ lý do freshness_sla_exceeded.

---

## 4. Thực nghiệm before/after (Sprint 3)

Run before đã chạy bằng lệnh thật:

python etl_pipeline.py run --run-id sprint3-before --no-refund-fix --skip-validate

Mục đích so sánh before/after:

- Giữ nguyên cùng bộ dữ liệu raw để so sánh nhất quán.
- Đối chiếu trực tiếp run before và run after trên cùng bộ câu eval.

Cách phát hiện:

- Log: expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=1
- Eval giảm từ full_pass=4/4 xuống full_pass=3/4
- Câu q_refund_window đổi từ hits_forbidden=no thành hits_forbidden=yes

---

## 5. Hạn chế & việc chưa làm

- Chưa có dữ liệu tươi theo SLA 24h vì đang dùng snapshot mẫu.
- Chưa có kênh alert bên ngoài (Slack/Email); hiện chỉ log nội bộ trong artifacts/logs/.
