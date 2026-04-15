# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `data/docs/policy_refund_v4.txt` | Manual export CSV (dirty) | Stale 14 ngày từ migration policy-v3; duplicate rows; empty chunk_text | quarantine + expectation `refund_no_stale_14d_window` |
| `data/docs/hr_leave_policy.txt` | Manual export CSV (dirty) | Stale version 2025 (10 ngày) với effective_date 2025-01-01; date format DD/MM/YYYY | quarantine `stale_hr_policy_effective_date` |
| `data/docs/sla_p1_2026.txt` | Manual export CSV (dirty) | Chunk text OK; date format DD/MM/YYYY ở 1 row | quarantine `invalid_effective_date_format` |
| `data/docs/it_helpdesk_faq.txt` | Manual export CSV (dirty) | Date format DD/MM/YYYY; empty chunk_text | quarantine (format + empty) |

**Failure mode tổng hợp:**
- **Encoding BOM**: có thể xuất hiện ở bất kỳ row nào từ CSV export lỗi (Rule 7)
- **Chunk quá dài**: nếu tài liệu dài được chunk không đúng cách, có thể > 5000 chars (Rule 9)
- **Missing exported_at**: row 6 trong dirty CSV có chunk trống nhưng exported_at OK; nhưng raw export tổng thể phải có timestamp (Rule 8)

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | SHA256 hash prefix (16 chars) của `doc_id|chunk_text|seq` — ổn định qua rerun |
| doc_id | string | Có | Key logic tài liệu nguồn (policy_refund_v4, sla_p1_2026, it_helpdesk_faq, hr_leave_policy) |
| chunk_text | string | Có | Đã strip control chars + normalize whitespace + fix stale refund 14→7 ngày |
| effective_date | date | Có | ISO YYYY-MM-DD; quarantine nếu không parse được hoặc < 2026-01-01 (HR) |
| exported_at | datetime | Có | ISO timestamp; dùng cho freshness SLA (ngày 24h mặc định) |

---

## 3. Quy tắc quarantine vs drop

**Quarantine (có ghi log + lý do)**:
- `unknown_doc_id`: doc_id không thuộc allowlist → không xử lý tiếp
- `missing_effective_date` / `invalid_effective_date_format`: không parse được ngày
- `stale_hr_policy_effective_date`: HR policy cũ (effective_date < 2026-01-01)
- `missing_chunk_text`: chunk_text trống
- `duplicate_chunk_text`: nội dung trùng lặp (giữ bản đầu)
- `bom_encoding_garbage`: chunk có BOM hoặc ký tự encoding rác
- `missing_exported_at`: thiếu timestamp cho freshness
- `chunk_text_too_long`: chunk > 5000 chars

**Clean (không quarantine, chỉ sửa)**:
- Control characters (`\x00-\x08`, `\x0B`, `\x0C`, `\x0E-\x1F`) → strip
- Multiple whitespace → collapse to single space
- Stale refund "14 ngày làm việc" → "7 ngày làm việc" + marker `[cleaned: stale_refund_window]`

**Record nào quay lại cleaned**: sau khi fix issue, row được đưa vào cleaned nếu pass tất cả rule.

---

## 4. Phiên bản & canonical

> Source of truth cho policy refund: `data/docs/policy_refund_v4.txt` (v4, effective 2026-02-01, 7 ngày)

**Canonical sources:**

| doc_id | File gốc | Version | Effective date | Content |
|--------|----------|---------|---------------|---------|
| policy_refund_v4 | `data/docs/policy_refund_v4.txt` | v4 | 2026-02-01 | 7 ngày làm việc |
| sla_p1_2026 | `data/docs/sla_p1_2026.txt` | 2026.1 | 2026-01-15 | P1: 15 phút phản hồi |
| it_helpdesk_faq | `data/docs/it_helpdesk_faq.txt` | 2026-01-20 | 2026-01-20 | 5 lần login sai → khóa |
| hr_leave_policy | `data/docs/hr_leave_policy.txt` | 2026 | 2026-01-01 | 12 ngày phép năm (< 3 năm) |
| ~~hr_leave_policy~~ | ~~(2025 old version)~~ | ~~2025~~ | ~~2025-01-01~~ | ~~10 ngày phép năm — STALE~~ |

**Version cutoffs**:
- HR leave policy: chỉ chấp nhận `effective_date >= 2026-01-01`
- Policy refund v4: chỉ chấp nhận chunk chứa "7 ngày", quarantine "14 ngày"