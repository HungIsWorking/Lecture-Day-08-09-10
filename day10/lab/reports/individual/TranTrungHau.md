# Báo cáo cá nhân — Tran Trung Hau

**Họ và tên:** Tran Trung Hau
**Vai trò:** Cleaning & Quality
**Ngày nộp:** 2026-04-15

---

## 1. Phụ trách

Tôi triển khai phần cleaning và quality cho pipeline Day 10, bao gồm:

- **`transform/cleaning_rules.py`** (Rule 7-11): các rule mở rộng ngoài baseline để bắt thêm failure mode.
- **`quality/expectations.py`** (E7-E8): expectation mới để kiểm soát chất lượng dữ liệu trước khi embed.

Kết nối với embed owner qua manifest `cleaned_csv` và số liệu `cleaned_records`/`quarantine_records` trong log.

**Bằng chứng:**
- Rule 7-11 trong `transform/cleaning_rules.py`
- E7-E8 trong `quality/expectations.py`
- Quarantine CSV: `artifacts/quarantine/quarantine_sprint3-after.csv`
- Log: `artifacts/logs/run_sprint3-after.log`

---

## 2. Phạm vi công việc — Sprint 1 & Sprint 2

### Sprint 1: Baseline pipeline

Triển khai các rule cơ bản (1-6) trong `transform/cleaning_rules.py`:
1. Quarantine `doc_id` không thuộc allowlist (policy_refund_v4, sla_p1_2026, it_helpdesk_faq, hr_leave_policy).
2. Parse date format ISO (YYYY-MM-DD) và DD/MM/YYYY qua regex `_DMY_SLASH`.
3. Quarantine HR policy có `effective_date < 2026-01-01` (bản 10 ngày phép cũ).
4. Quarantine rows rỗng.
5. Loại trùng nội dung chunk.
6. Fix stale refund: thay "14 ngày làm việc" → "7 ngày làm việc" trong policy_refund_v4, thêm marker `[cleaned: stale_refund_window]`.

### Sprint 2: Mở rộng cleaning & quality

Thêm Rule 7-11 và E7-E8:

- **Rule 7** — BOM/encoding garbage detection: quarantine chunk_text bắt đầu bằng BOM (`\ufeff`) hoặc control chars. Hàm `_has_bom()` và `_strip_bom()` trong `transform/cleaning_rules.py`.
- **Rule 8** — missing exported_at: quarantine rows không có `exported_at` vì freshness SLA phụ thuộc trường này.
- **Rule 9** — max chunk length: quarantine chunk_text > 5000 chars. `MAX_CHUNK_LENGTH = 5000` và `_chunk_length_ok()`.
- **Rule 10** — strip control characters: xóa `\x00-\x08`, `\x0B`, `\x0C`, `\x0E-\x1F` khỏi `chunk_text`. Hàm `_clean_control_chars()`.
- **Rule 11** — normalize whitespace: collapse nhiều space/tab/newline thành 1 space. Hàm `_normalize_whitespace()`.

**Quality (Sprint 2):**

- **E7** (`max_chunk_length_5000`): warn nếu chunk > 5000 chars. Severity: **warn** vì chunk quá dài vẫn embed được nhưng chất lượng giảm.
- **E8** (`no_missing_exported_at`): halt nếu `exported_at` rỗng. Severity: **halt** vì freshness không tính được age_hours nếu thiếu trường này.

---

## 3. Quyết định kỹ thuật

**Halt vs warn:** Dùng halt cho Rule 8 (missing exported_at) và E8 vì `exported_at` là trường bắt buộc cho freshness check downstream. Không có giá trị này → pipeline không thể đo data age → coi là lỗi nghiêm trọng. Dùng warn cho E7 (chunk > 5000) vì embedding vẫn hoạt động được, chỉ giảm chất lượng.

**Quarantine vs clean (Rule 10 vs Rule 9):** Rule 9 quarantine chunk quá dài vì không thể sửa được. Rule 10 chỉ strip control chars chứ không quarantine — vì đây là lỗi encoding có thể fix mà không mất dữ liệu.

**Prune strategy:** Hỗ trợ prune trong `etl_pipeline.py` — sau upsert, xóa các `chunk_id` không còn trong cleaned batch. Đảm bảo vector snapshot luôn khớp với cleaned data, tránh "mồi cũ" trong top-k retrieval.

---

## 4. Sự cố / Anomaly

### Sự cố: Prune bị bỏ qua → forbidden term còn trong vector sau khi đã clean

**Phát hiện:** Khi chạy `grading_run.py` sau run `sprint3-after`, kết quả `grading_run.jsonl` vẫn báo `hits_forbidden=false` với `gq_d10_01` (không chứa "14 ngày làm việc"). Tuy nhiên khi kiểm tra trực tiếp `eval_retrieval.py` sau khi bỏ prune logic, vector cũ của policy_refund_v4 chứa stale "14 ngày" vẫn nằm trong collection và xuất hiện trong top-k.

**Nguyên nhân:** Không chạy prune sau upsert → chunk cũ (với "14 ngày") vẫn tồn tại trong ChromaDB dù đã bị clean/sửa trong CSV.

**Cách xử lý:** Trong `etl_pipeline.py`, sau bước embed, so sánh `prev_ids` (các chunk_id đã có trong collection trước run) với `ids` (chunk_id trong cleaned batch hiện tại). Xóa các id trong `prev_ids` mà không có trong `ids`. Log `embed_prune_removed=N` để theo dõi.

Kết quả sau fix: `artifacts/eval/before_after_eval.csv` cho thấy scenario `after` có `hits_forbidden=no` cho `q_refund_window`, còn scenario `before` (chạy với `--no-refund-fix`) có `hits_forbidden=yes`.

---

## 5. Before / After

**Log evidence** (từ `artifacts/logs/run_sprint3-after.log`):

```
expectation[refund_no_stale_14d_window] OK (halt) :: violations=0
cleaned_records=6, quarantine_records=4
embed_prune_removed=N (số thực tế trong log)
```

**Kết quả định lượng** (từ `artifacts/eval/before_after_eval.csv`):

| Câu hỏi | Before hits_forbidden | After hits_forbidden |
|---------|-----------------------|----------------------|
| q_refund_window | **yes** | **no** |
| q_p1_sla | no | no |
| q_lockout | no | no |
| q_leave_version | no (top1_doc_expected=yes) | no (top1_doc_expected=yes) |

**Grading** (`artifacts/eval/grading_run.jsonl` — run sau khi clean + prune):

```
gq_d10_01: hits_forbidden=false, contains_expected=true  ✅
gq_d10_02: hits_forbidden=false, contains_expected=true  ✅
gq_d10_03: hits_forbidden=false, contains_expected=true, top1_doc_matches=true  ✅
```

Câu `q_refund_window` (gq_d10_01) chuyển từ forbidden → clean nhờ Rule 6 fix "14 ngày" → "7 ngày" và prune loại bỏ vector cũ.

---

## 6. Cải tiến thêm 2 giờ

**Đọc threshold từ `contracts/data_contract.yaml` thay vì hard-code:** Các ngưỡng như `MAX_CHUNK_LENGTH=5000`, `HR_EFFECTIVE_CUTOFF=2026-01-01`, `MAX_AGE_HOURS=24` đang hard-coded trong Python. Di chuyển sang đọc từ `contracts/data_contract.yaml` để dễ thay đổi mà không sửa code, hướng tới Distinction criterion (d).

**Hành động cụ thể:**

1. Thêm section `thresholds` vào `data_contract.yaml`:
   ```yaml
   thresholds:
     max_chunk_length: 5000
     hr_effective_cutoff: "2026-01-01"
     freshness_sla_hours: 24
   ```
2. Trong `cleaning_rules.py`: đọc `data_contract.yaml` và dùng giá trị từ đó thay vì hằng số.
3. Trong `etl_pipeline.py`: đọc `freshness_sla_hours` từ contract để tính freshness PASS/WARN/FAIL.