# Generations 2.0 Design

## Decision Summary
- Approach: Capability-first API with targeted refactors (models availability endpoint, richer schemas, file storage, and modular Playground UI)
- Priority: Phase 8A as a top-priority workstream
- Key outcomes: image/video generation with account-aware model selection and reference files, real file uploads, and job lifecycle visibility

## Goals
- Image and video generation are selectable by account + model and accept reference files.
- File uploads persist to disk and DB and are reusable by ID.
- Video generation uses real job lifecycle states with validated results.
- Playground UI exposes account + model selection and reference inputs for image/video.

## Non-Goals
- Rewrite the full backend architecture beyond required additions.
- Replace adapters with new upstream libraries.
- Large-scale UI redesign outside Playground and related components.

## Backend Data Flow

### File Storage
- Introduce `uploaded_files` table with file metadata and storage path.
- Update `/v1/files` to persist files to disk and DB.
- Add file lookup by ID and enforce MIME/type and size constraints.

### Schemas
- Add `ImageGenerationRequest` and `VideoGenerationRequest` in `backend/app/schemas/native.py`.
- Required fields: `prompt`.
- Optional fields: `account_id`, `provider`, `model`, `reference_file_ids`, and generation options.

### Adapter Contracts
- Update `BaseAdapter.generate_image` and `BaseAdapter.generate_video` to accept reference file paths and structured options.
- `WebApiAdapter.generate_image` accepts references when supported; otherwise it fails with explicit reason.
- `McpCliAdapter.generate_video` returns structured metadata (provider job id, status, output URL/path, progress, errors).

## Jobs and Lifecycle
- Separate video job path in worker/manager.
- Lifecycle: queued → submitted → provider_processing → polling → completed/failed.
- Persist provider metadata and reference file IDs on job record.
- SSE endpoint `/native/jobs/{id}/events` emits lifecycle updates and progress.
- Explicit failure messages for auth, quota, unsupported model, unsupported references, invalid file types.

## Models Availability API
- Add endpoint: `GET /admin/accounts/{account_id}/models?feature=<feature>`
- Response includes: model id, display name, provider, family, capability flags, account id, default/recommended, health flag.
- Account manager filters models by account capability and provider health.
- Default selection strategy per feature (image/video).

## Frontend UI

### Component Split
- `frontend/src/components/playground/ChatPanel.tsx`
- `frontend/src/components/playground/ImagePanel.tsx`
- `frontend/src/components/playground/VideoPanel.tsx`
- `frontend/src/components/playground/FilePicker.tsx`
- `frontend/src/components/playground/ModelSelector.tsx`
- `frontend/src/components/playground/AccountSelector.tsx`
- `frontend/src/components/playground/JobStatusCard.tsx`

### Behavior
- Model dropdown appears for image and video; filtered by account + feature.
- Reload models on account/tool change; show loading and empty states.
- Image/video panels support reference file uploads and file-id reuse.
- Video panel shows job progress and final artifact.

## Verification
- API: verify file upload, model availability filtering, image/video generation with references, and job events SSE.
- Browser MCP: verify model dropdowns, account switching, reference attachments, video progress, and result display.
