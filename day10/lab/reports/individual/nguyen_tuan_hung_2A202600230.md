# Báo cáo cá nhân — Nguyễn Tuấn Hưng

**Họ và tên:** Nguyễn Tuấn Hưng  
**Vai trò:** Monitoring / Docs Owner  
**Độ dài:** ~450 từ

---

## 1. Phụ trách

Trong Day 10, tôi phụ trách phần theo dõi kết quả chạy pipeline và tổng hợp tài liệu bằng chứng. Công việc chính gồm:

- Chạy hai lần pipeline với `run_id` khác nhau để so sánh before/after: `sprint3-before` và `sprint3-after`.
- Đọc log, manifest, file eval để kiểm tra chất lượng dữ liệu theo từng bước.
- Tổng hợp số liệu vào báo cáo nhóm và quality report.
- Chạy `grading_run.py` và đối chiếu kết quả trong `grading_run.jsonl`.

**Bằng chứng trực tiếp tôi dùng trong repo:**

- `artifacts/logs/run_sprint3-before.log`
- `artifacts/logs/run_sprint3-after.log`
- `artifacts/manifests/manifest_sprint3-before.json`
- `artifacts/manifests/manifest_sprint3-after.json`
- `artifacts/eval/before_after_eval.csv`
- `artifacts/eval/grading_run.jsonl`

---

## 2. Quyết định kỹ thuật

Quyết định kỹ thuật quan trọng của tôi là đánh giá kết quả theo chuỗi `log -> manifest -> eval -> grading`, thay vì chỉ nhìn một chỉ số đơn lẻ.

Lý do:

- Log cho biết expectation nào pass/fail và mức `halt/warn`.
- Manifest giúp đối chiếu số lượng bản ghi (`raw_records`, `cleaned_records`, `quarantine_records`) giữa các run.
- Eval phản ánh ảnh hưởng trực tiếp lên retrieval qua `contains_expected` và `hits_forbidden`.
- Grading kiểm tra khả năng trả lời ở bộ câu chấm chính thức.

Cách làm này giúp tôi tránh kết luận sai kiểu “pipeline chạy xong là ổn”, vì thực tế một run có thể `PIPELINE_OK` nhưng chất lượng truy xuất vẫn khác biệt giữa before và after.

---

## 3. Sự cố / anomaly

Sự cố nổi bật là expectation `refund_no_stale_14d_window` ở run `sprint3-before` báo fail:

- `expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=1`

Kết quả này đi kèm thay đổi chất lượng retrieval:

- Ở câu `q_refund_window`, before có `hits_forbidden=yes`.
- Sau khi chạy lại `sprint3-after`, cùng câu này chuyển về `hits_forbidden=no`.

Điểm tôi rút ra là cần xem đồng thời expectation + eval; nếu chỉ nhìn top1 preview thì dễ bỏ sót chunk cấm trong top-k.

---

## 4. Before/after

Từ `artifacts/eval/before_after_eval.csv`:

- Before: `full_pass=3/4`, `no_forbidden=3/4`.
- After: `full_pass=4/4`, `no_forbidden=4/4`.

Theo từng câu:

- `q_refund_window`: `hits_forbidden` đổi từ `yes` (before) sang `no` (after).
- `q_leave_version`: giữ ổn định `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes` ở cả hai run.

Từ `artifacts/eval/grading_run.jsonl`:

- `gq_d10_01`: `contains_expected=true`, `hits_forbidden=false`
- `gq_d10_02`: `contains_expected=true`, `hits_forbidden=false`
- `gq_d10_03`: `contains_expected=true`, `hits_forbidden=false`, `top1_doc_matches=true`

---

## 5. Cải tiến thêm 2 giờ

Nếu có thêm 2 giờ, tôi sẽ bổ sung theo dõi freshness ở 2 boundary (ingest và publish) và tách rõ cảnh báo theo mức độ ưu tiên. Hiện tại log đã có `age_hours` và `freshness_sla_exceeded`, nhưng chưa có cơ chế cảnh báo chủ động ra kênh ngoài. Việc này sẽ giúp vai trò Monitoring / Docs Owner đóng vòng phản hồi nhanh hơn khi dữ liệu vượt SLA.
