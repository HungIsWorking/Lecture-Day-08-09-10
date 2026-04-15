# Báo cáo cá nhân — Nguyễn Đăng Hải

**Họ và tên:** Nguyễn Đăng Hải
**Vai trò:** Ingestion & Embed Owner
**Ngày nộp:** 2026-04-15

---

## 1. Phụ trách

Trong Day 10, tôi phụ trách hai phần đầu và cuối của pipeline: **Ingestion** (nạp dữ liệu raw) và **Embed** (embed cleaned data vào ChromaDB, đánh giá retrieval).

**Công việc cụ thể:**

- **`transform/cleaning_rules.py`** — hàm `load_raw_csv()`: đọc CSV raw, strip whitespace, trả về `List[Dict]`.
- **`etl_pipeline.py`** — `cmd_run()` và `cmd_embed_internal()`: điều phối toàn bộ luồng ingest → clean → validate → embed → log → manifest → freshness.
- **`eval_retrieval.py`** — toàn bộ script: đánh giá retrieval bằng keyword matching trên top-k chunks, xuất CSV với `contains_expected`, `hits_forbidden`, `top1_doc_expected`.
- **`grading_run.py`** — chạy grading chính thức với bộ câu hỏi từ `data/grading_questions.json`, xuất `grading_run.jsonl`.

Kết nối: raw CSV (ingest) → cleaned CSV (cleaning owner nhận) → ChromaDB upsert → eval CSV → grading JSONL.

**Bằng chứng trong repo:**

- `transform/cleaning_rules.py` — `load_raw_csv()`, dòng 112-118
- `etl_pipeline.py` — `cmd_run()` (dòng 49-128) và `cmd_embed_internal()` (dòng 131-177)
- `eval_retrieval.py` — toàn bộ file
- `grading_run.py` — toàn bộ file
- `artifacts/manifests/manifest_sprint3-after.json`
- `artifacts/eval/before_after_eval.csv`
- `artifacts/eval/grading_run.jsonl`

---

## 2. Quyết định kỹ thuật

### 2a. Ingestion — load_raw_csv

Dùng `csv.DictReader` để map schema tự động theo header CSV. Mỗi giá trị được `.strip()` để loại bỏ trailing whitespace từ CSV export. Không parse ngày ở bước này — chỉ preserve raw string để cleaning owner xử lý sau.

Lý do: tách biệt ingest (chỉ nạp và chuẩn hóa format) và transform (parse và clean). Điều này giúp testing dễ hơn — có thể mock raw CSV mà không cần chạy ingest.

### 2b. Embed — upsert theo chunk_id (SHA256 hash prefix)

Mỗi chunk có `chunk_id = f"{doc_id}_{seq}_{sha256[:16]}"`, được tính trong `cleaning_rules.py`. Khi embed, dùng `col.upsert(ids=ids, documents=documents, metadatas=metadatas)` thay vì `add`. Upsert đảm bảo:

- Nếu `chunk_id` đã tồn tại → update document + metadata
- Nếu chưa → insert mới
- Chạy 2 lần không duplicate vector

### 2c. Embed — Prune stale ids sau upsert

Sau upsert, so sánh `prev_ids` (các id trong collection trước run) với `ids` (các id trong cleaned batch hiện tại). Các id trong `prev_ids` mà không có trong `ids` → xóa khỏi collection. Log `embed_prune_removed=N`. Bọc try/except để prune không crash pipeline nếu ChromaDB lỗi.

**Quyết định này được đề xuất từ Cleaning Owner** (TranTrungHau): sau khi phát hiện cleaned đã sạch nhưng eval vẫn thấy "14 ngày" trong top-k, cleaning owner xác định nguyên nhân là vector cũ chưa bị xóa → tôi triển khai prune trong embed để fix.

### 2d. Top-k = 3 cho eval_retrieval

Dùng `n_results=3`. Không k=1 vì dễ miss forbidden term ở position 2-3. Không k>3 vì mục đích chỉ kiểm tra chunk cấm có xuất hiện trong context retrieval hay không.

---

## 3. Sự cố / anomaly

### Sự cố: Dữ liệu raw cũ vượt SLA freshness

**Phát hiện:** Khi chạy `sprint3-after` và đọc `artifacts/manifests/manifest_sprint3-after.json`, trường `latest_exported_at = 2026-04-10T08:00:00`. Tính ra `age_hours = 122.293`, vượt xa `sla_hours = 24.0`. Kết quả: `freshness_check=FAIL reason=freshness_sla_exceeded`.

**Nguyên nhân:** Không phải lỗi pipeline — dữ liệu raw trong `data/raw/policy_export_dirty.csv` thực sự đã export từ 2026-04-10, tức 5 ngày trước thời điểm chạy (2026-04-15). Đây là hành vi đúng với snapshot lab — dữ liệu test được giữ ở trạng thái cũ để kiểm tra pipeline handle freshness đúng cách.

**Cách xử lý:** Pipeline vẫn tiếp tục chạy (không halt) vì freshness FAIL không phải halt — dữ liệu vẫn hợp lệ, chỉ là cũ. Freshness check được gọi sau khi embed xong, kết quả được ghi vào manifest và log để downstream monitoring biết.

**Diễn giải:** Đây là trường hợp monitoring phân biệt được giữa "dữ liệu cũ nhưng hợp lệ" vs "dữ liệu sai". Pipeline vẫn pass ETL/quality vì cleaning đã làm đúng việc; freshness chỉ cảnh báo chứ không dừng.

---

## 4. Before / After

**Từ `artifacts/eval/before_after_eval.csv`** — kết quả embed sau khi đã clean + prune:

| Câu hỏi | Before hits_forbidden | After hits_forbidden | top1_doc |
|---------|-----------------------|----------------------|----------|
| q_refund_window | **yes** | **no** | policy_refund_v4 |
| q_p1_sla | no | no | sla_p1_2026 |
| q_lockout | no | no | it_helpdesk_faq |
| q_leave_version | no | no | hr_leave_policy |

**Từ `artifacts/eval/grading_run.jsonl`** (chạy sau khi embed chuẩn):

```
gq_d10_01: top1_doc_id=policy_refund_v4, contains_expected=true, hits_forbidden=false  ✅
gq_d10_02: top1_doc_id=sla_p1_2026,     contains_expected=true, hits_forbidden=false  ✅
gq_d10_03: top1_doc_id=hr_leave_policy, contains_expected=true, hits_forbidden=false,
           top1_doc_matches=true                               ✅
```

**Manifest** (`manifest_sprint3-after.json`):
- `raw_records=10`, `cleaned_records=6`, `quarantine_records=4` → 40% data bị quarantine (bản cũ, lỗi format, trùng lặp)
- `chroma_collection=day10_kb` — khác với `day09_kb` để tránh nhiễu index

---

## 5. Cải tiến thêm 2 giờ

**Thêm metadata filter khi query trong eval_retrieval.py:** Hiện tại eval chỉ query không filter và kiểm tra kết quả bằng keyword matching. Thêm bước query có filter `where={"doc_id": expect_doc_id}` để đánh giá ranking quality một cách chủ động — phân biệt giữa "đúng document ở top-1" và "đúng document nằm trong top-k nhưng bị đẩy xuống dưới bởi document khác".

**Hành động cụ thể:**
1. Trong `eval_retrieval.py`, thêm `col.query(query_texts=[text], n_results=k, where={"doc_id": expect_doc_id})` để lấy chunk chỉ từ document kỳ vọng.
2. So sánh position của expect_doc_id giữa filtered query và unfiltered query → tính ranking drift. Điều này giúp đánh giá retrieval quality có bị nhiễu từ document cùng domain hay không.

**Lý do:** Hiện tại top-1 doc_id được lấy từ metadata của top-k unfiltered results — không kiểm soát chủ động bằng filter. Thêm filter giúp đánh giá ranking precision chính xác hơn, hướng tới Distinction criterion (ranking quality).