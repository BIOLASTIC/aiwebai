# Generations 2.0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver account-aware model selection, real file uploads, and reference-aware image/video generation with reliable job lifecycle visibility across API and Playground.

**Architecture:** Add durable file storage and richer request schemas, update adapter contracts for reference inputs, introduce a capability-filtered models endpoint, and split Playground into modular panels for image/video features.

**Tech Stack:** FastAPI, SQLAlchemy (SQLite), React 18 + Vite, shadcn/ui.

---

### Task 1: Add uploaded file storage model

**Files:**
- Modify: `backend/app/db/models.py`
- Test: `backend/tests/unit/test_files.py`

**Step 1: Write the failing test**

```python
def test_uploaded_file_model_fields():
    file = UploadedFile(
        file_id="file_test",
        filename="ref.png",
        mime_type="image/png",
        size_bytes=123,
        storage_path="/tmp/ref.png",
        purpose="reference",
        owner_user_id=1,
    )
    assert file.file_id == "file_test"
    assert file.storage_path
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_files.py::test_uploaded_file_model_fields -v`
Expected: FAIL (model missing)

**Step 3: Write minimal implementation**

```python
class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id = mapped_column(Integer, primary_key=True)
    file_id = mapped_column(String(64), unique=True, index=True)
    filename = mapped_column(String(255))
    mime_type = mapped_column(String(100))
    size_bytes = mapped_column(Integer)
    storage_path = mapped_column(String(512))
    purpose = mapped_column(String(50))
    owner_user_id = mapped_column(Integer, index=True)
    created_at = mapped_column(DateTime, default=utcnow)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_files.py::test_uploaded_file_model_fields -v`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 2: Implement file storage service

**Files:**
- Create: `backend/app/storage/files.py`
- Test: `backend/tests/unit/test_file_storage.py`

**Step 1: Write the failing test**

```python
def test_store_and_lookup_file(tmp_path):
    storage = FileStorage(base_dir=tmp_path)
    file_id = storage.save_bytes(b"abc", filename="ref.png", mime_type="image/png")
    meta = storage.get_metadata(file_id)
    assert meta.filename == "ref.png"
    assert meta.mime_type == "image/png"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_file_storage.py::test_store_and_lookup_file -v`
Expected: FAIL (FileStorage missing)

**Step 3: Write minimal implementation**

```python
class FileStorage:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def save_bytes(self, data: bytes, filename: str, mime_type: str) -> str:
        file_id = f"file_{uuid4().hex}"
        path = self.base_dir / file_id
        path.write_bytes(data)
        return file_id

    def get_metadata(self, file_id: str) -> FileMetadata:
        ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_file_storage.py::test_store_and_lookup_file -v`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 3: Persist files in `/v1/files`

**Files:**
- Modify: `backend/app/api/openai/files.py`
- Modify: `backend/app/db/models.py`
- Test: `backend/tests/integration/test_files.py`

**Step 1: Write the failing test**

```python
def test_files_upload_persists(client):
    resp = client.post("/v1/files", files={"file": ("ref.png", b"abc", "image/png")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"].startswith("file_")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_files.py::test_files_upload_persists -v`
Expected: FAIL (placeholder response)

**Step 3: Write minimal implementation**

```python
file_id = storage.save_bytes(data, filename, mime_type)
db.add(UploadedFile(...))
db.commit()
return {"id": file_id, ...}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_files.py::test_files_upload_persists -v`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 4: Add reference-aware image/video request schemas

**Files:**
- Modify: `backend/app/schemas/native.py`
- Test: `backend/tests/unit/test_schemas.py`

**Step 1: Write the failing test**

```python
def test_video_request_schema():
    req = VideoGenerationRequest(prompt="hi", reference_file_ids=["file_1"], model="vid")
    assert req.reference_file_ids == ["file_1"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_schemas.py::test_video_request_schema -v`
Expected: FAIL (schema missing)

**Step 3: Write minimal implementation**

```python
class VideoGenerationRequest(BaseModel):
    prompt: str
    account_id: int | None = None
    provider: str | None = None
    model: str | None = None
    reference_file_ids: list[str] = []
    duration: int | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
    fps: int | None = None
    metadata: dict | None = None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_schemas.py::test_video_request_schema -v`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 5: Update adapter contracts for references

**Files:**
- Modify: `backend/app/adapters/base.py`
- Modify: `backend/app/adapters/webapi_adapter.py`
- Modify: `backend/app/adapters/mcpcli_adapter.py`
- Test: `backend/tests/unit/test_adapters.py`

**Step 1: Write the failing test**

```python
def test_generate_video_signature_accepts_references():
    sig = inspect.signature(BaseAdapter.generate_video)
    assert "reference_files" in sig.parameters
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_adapters.py::test_generate_video_signature_accepts_references -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
async def generate_video(self, prompt: str, model: str | None, account_id: int | None, reference_files: list[Path] | None, options: dict | None) -> VideoResult:
    ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_adapters.py::test_generate_video_signature_accepts_references -v`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 6: Add capability-filtered models endpoint

**Files:**
- Modify: `backend/app/api/admin/models.py`
- Modify: `backend/app/accounts/manager.py`
- Modify: `backend/app/models/registry.py`
- Test: `backend/tests/integration/test_models.py`

**Step 1: Write the failing test**

```python
def test_models_filtered_by_account_and_feature(client):
    resp = client.get("/admin/accounts/1/models?feature=video")
    assert resp.status_code == 200
    assert all(m["capabilities"]["video"] for m in resp.json())
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_models.py::test_models_filtered_by_account_and_feature -v`
Expected: FAIL (endpoint missing)

**Step 3: Write minimal implementation**

```python
@router.get("/accounts/{account_id}/models")
def list_account_models(account_id: int, feature: str | None = None):
    return registry.list_available(account_id, feature)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_models.py::test_models_filtered_by_account_and_feature -v`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 7: Update native tasks to accept references and accounts

**Files:**
- Modify: `backend/app/api/native/tasks.py`
- Modify: `backend/app/jobs/manager.py`
- Test: `backend/tests/integration/test_native_tasks.py`

**Step 1: Write the failing test**

```python
def test_video_request_accepts_references(client):
    body = {"prompt": "vid", "reference_file_ids": ["file_1"], "model": "vid"}
    resp = client.post("/native/tasks/video", json=body)
    assert resp.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_native_tasks.py::test_video_request_accepts_references -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
req = VideoGenerationRequest(**payload)
job = jobs.create_video_job(req, reference_files)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_native_tasks.py::test_video_request_accepts_references -v`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 8: Implement video job lifecycle states

**Files:**
- Modify: `backend/app/jobs/manager.py`
- Modify: `backend/app/jobs/worker.py`
- Modify: `backend/app/jobs/events.py`
- Test: `backend/tests/integration/test_jobs.py`

**Step 1: Write the failing test**

```python
def test_video_job_lifecycle_events(client):
    job = create_video_job()
    events = list(job_events(job.id))
    assert "submitted" in [e["status"] for e in events]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_jobs.py::test_video_job_lifecycle_events -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
update_job_status(job, "submitted")
update_job_status(job, "provider_processing")
update_job_status(job, "polling")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_jobs.py::test_video_job_lifecycle_events -v`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 9: Create Playground components

**Files:**
- Create: `frontend/src/components/playground/ChatPanel.tsx`
- Create: `frontend/src/components/playground/ImagePanel.tsx`
- Create: `frontend/src/components/playground/VideoPanel.tsx`
- Create: `frontend/src/components/playground/FilePicker.tsx`
- Create: `frontend/src/components/playground/ModelSelector.tsx`
- Create: `frontend/src/components/playground/AccountSelector.tsx`
- Create: `frontend/src/components/playground/JobStatusCard.tsx`
- Modify: `frontend/src/pages/Playground.tsx`
- Test: `frontend/src/pages/Playground.test.tsx`

**Step 1: Write the failing test**

```tsx
it("shows model dropdown for image and video", () => {
  render(<Playground />)
  expect(screen.getByText("Model")).toBeInTheDocument()
})
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --runTestsByPath src/pages/Playground.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

```tsx
<ModelSelector feature={selectedTool} accountId={selectedAccount} />
```

**Step 4: Run test to verify it passes**

Run: `npm test -- --runTestsByPath src/pages/Playground.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 10: Wire model availability to UI

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/components/playground/ModelSelector.tsx`
- Test: `frontend/src/components/playground/ModelSelector.test.tsx`

**Step 1: Write the failing test**

```tsx
it("loads models by account and feature", async () => {
  render(<ModelSelector accountId={1} feature="video" />)
  expect(await screen.findByText("No video models")).toBeInTheDocument()
})
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --runTestsByPath src/components/playground/ModelSelector.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

```tsx
api.get(`/admin/accounts/${accountId}/models`, { params: { feature } })
```

**Step 4: Run test to verify it passes**

Run: `npm test -- --runTestsByPath src/components/playground/ModelSelector.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 11: Add reference file UI for image/video

**Files:**
- Modify: `frontend/src/components/playground/ImagePanel.tsx`
- Modify: `frontend/src/components/playground/VideoPanel.tsx`
- Modify: `frontend/src/components/playground/FilePicker.tsx`
- Test: `frontend/src/components/playground/FilePicker.test.tsx`

**Step 1: Write the failing test**

```tsx
it("shows selected reference files", () => {
  render(<FilePicker selected={[{ id: "file_1", name: "ref.png" }]} />)
  expect(screen.getByText("ref.png")).toBeInTheDocument()
})
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --runTestsByPath src/components/playground/FilePicker.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

```tsx
{selected.map(file => <Chip key={file.id}>{file.name}</Chip>)}
```

**Step 4: Run test to verify it passes**

Run: `npm test -- --runTestsByPath src/components/playground/FilePicker.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
```

---

### Task 12: Verify API + UI flows

**Files:**
- Modify: `complete.md`

**Step 1: Run API checks (one by one)**

Run:
```bash
python test_endpoints.py
```
Expected: All endpoints pass

**Step 2: Run browser MCP checks**

Run: Use MCP browser to verify:
- Model dropdown changes with account + tool
- Upload references for image/video
- Video job progress and result

**Step 3: Update progress**

Update `complete.md` with new completion status and test results.

**Step 4: Commit**

```bash
```

---

Plan complete and saved to `docs/plans/2026-03-16-generations-2.0.md`. Two execution options:

1. Subagent-Driven (this session) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Parallel Session (separate) - Open new session with executing-plans, batch execution with checkpoints

Which approach?
