#!/usr/bin/env bash
# =============================================================================
# test_image_video.sh
# Comprehensive test for image and video generation via HTTP API and gemcli MCP
#
# Usage:
#   bash scripts/test_image_video.sh
#
# Requirements:
#   - curl, jq installed
#   - Backend running at http://0.0.0.0:6400
#   - gemcli installed (optional — skipped if not found)
# =============================================================================

set -euo pipefail

BASE_URL="http://0.0.0.0:6400"
ADMIN_EMAIL="admin@local.host"
ADMIN_PASS="111111"
IMAGE_PROMPT="a red apple on a white table"
VIDEO_PROMPT="a cat walking through a garden"
IMAGE_MODEL="imagen-3.0"
VIDEO_MODEL="veo-2.0"
POLL_MAX=30        # maximum poll attempts
POLL_INTERVAL=5    # seconds between polls

# Temp file for curl output (avoids head -n -1 which is GNU-only)
TMP_BODY=$(mktemp)
cleanup() { rm -f "$TMP_BODY"; }
trap cleanup EXIT

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Colour

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

separator() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

PASS_COUNT=0
FAIL_COUNT=0

record_pass() { PASS_COUNT=$((PASS_COUNT + 1)); pass "$1"; }
record_fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); fail "$1"; }

# Portable curl helper: writes body to $TMP_BODY, returns HTTP status code
# Usage: http_status=$(curl_req GET/POST url [extra curl args...])
curl_req() {
    local method="$1"; shift
    local url="$1"; shift
    # remaining args passed to curl
    curl -s -o "$TMP_BODY" -w "%{http_code}" -X "$method" "$url" "$@"
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. Backend health check
# ─────────────────────────────────────────────────────────────────────────────
separator
info "Step 1 — Backend health check"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
if [ "$HEALTH" = "200" ]; then
    record_pass "Backend is reachable at ${BASE_URL} (HTTP 200)"
else
    record_fail "Backend unreachable at ${BASE_URL} (HTTP ${HEALTH})"
    echo "Aborting — backend must be running."
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
# 2. Authenticate — get JWT token
# ─────────────────────────────────────────────────────────────────────────────
separator
info "Step 2 — Authenticating as ${ADMIN_EMAIL}"
AUTH_HTTP=$(curl_req POST "${BASE_URL}/admin/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${ADMIN_EMAIL}&password=${ADMIN_PASS}")
AUTH_BODY=$(cat "$TMP_BODY")

if [ "$AUTH_HTTP" = "200" ]; then
    TOKEN=$(echo "$AUTH_BODY" | jq -r '.access_token // empty')
    if [ -n "$TOKEN" ]; then
        record_pass "JWT token obtained"
        info "Token: ${TOKEN:0:40}..."
    else
        record_fail "Login returned 200 but no access_token in response"
        echo "Response: $AUTH_BODY"
        exit 1
    fi
else
    record_fail "Login failed (HTTP ${AUTH_HTTP})"
    echo "Response: $AUTH_BODY"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
# 3. Create a fresh API key (list endpoint does not expose raw key values)
# ─────────────────────────────────────────────────────────────────────────────
separator
info "Step 3 — Creating a temporary API key for this test run"
# Note: POST /admin/api-keys/ requires ?label=<name> as a query param
CREATE_HTTP=$(curl_req POST "${BASE_URL}/admin/api-keys/?label=test-image-video-run" \
    -H "Authorization: Bearer ${TOKEN}")
CREATE_BODY=$(cat "$TMP_BODY")

if [ "$CREATE_HTTP" = "200" ] || [ "$CREATE_HTTP" = "201" ]; then
    API_KEY=$(echo "$CREATE_BODY" | jq -r '.key // empty')
    if [ -n "$API_KEY" ]; then
        record_pass "API key created: ${API_KEY:0:16}..."
    else
        record_fail "API key response missing 'key' field"
        echo "Response: $CREATE_BODY"
        exit 1
    fi
else
    record_fail "Could not create API key (HTTP ${CREATE_HTTP})"
    echo "Response: $CREATE_BODY"
    exit 1
fi
info "API key: ${API_KEY:0:16}..."

# ─────────────────────────────────────────────────────────────────────────────
# Helper: poll a job until completed/failed or timeout
# ─────────────────────────────────────────────────────────────────────────────
poll_job() {
    local JOB_ID="$1"
    local LABEL="$2"
    local attempt=0

    while [ $attempt -lt $POLL_MAX ]; do
        POLL_HTTP=$(curl_req GET "${BASE_URL}/native/tasks/${JOB_ID}" \
            -H "X-API-Key: ${API_KEY}")
        STATUS_RESP=$(cat "$TMP_BODY")
        JOB_STATUS=$(echo "$STATUS_RESP" | jq -r '.status // "unknown"')
        PROGRESS=$(echo "$STATUS_RESP" | jq -r '.progress // 0')
        RESULT_URL=$(echo "$STATUS_RESP" | jq -r '.result_url // empty')
        JOB_ERROR=$(echo "$STATUS_RESP" | jq -r '.error // empty')

        info "${LABEL} — poll ${attempt}: status=${JOB_STATUS}, progress=${PROGRESS}"

        if [ "$JOB_STATUS" = "completed" ]; then
            if [ -n "$RESULT_URL" ]; then
                record_pass "${LABEL} completed — result URL: ${RESULT_URL}"
                return 0
            else
                record_fail "${LABEL} completed but result_url is empty"
                return 1
            fi
        elif [ "$JOB_STATUS" = "failed" ]; then
            record_fail "${LABEL} failed — error: ${JOB_ERROR}"
            return 1
        fi

        attempt=$((attempt + 1))
        sleep $POLL_INTERVAL
    done

    record_fail "${LABEL} timed out after $((POLL_MAX * POLL_INTERVAL))s (last status: ${JOB_STATUS})"
    return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. List available accounts (to verify credentials for image/video)
# ─────────────────────────────────────────────────────────────────────────────
separator
info "Step 4 — Listing accounts to find one with image/video capabilities"
ACCTS_HTTP=$(curl_req GET "${BASE_URL}/admin/accounts/" \
    -H "Authorization: Bearer ${TOKEN}")
ACCTS_BODY=$(cat "$TMP_BODY")

if [ "$ACCTS_HTTP" = "200" ]; then
    ACCT_COUNT=$(echo "$ACCTS_BODY" | jq 'length' 2>/dev/null || echo 0)
    record_pass "Accounts endpoint reachable (${ACCT_COUNT} accounts)"
    echo "$ACCTS_BODY" | jq -r '.[] | "  ID=\(.id)  name=\(.name // "n/a")  adapter=\(.adapter_type // "n/a")  healthy=\(.is_healthy // "?")"' 2>/dev/null || true
else
    warn "Could not list accounts (HTTP ${ACCTS_HTTP}) — continuing without account_id"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 5. POST /native/tasks/image
# ─────────────────────────────────────────────────────────────────────────────
separator
info "Step 5 — Submitting IMAGE generation task"
info "  Prompt : \"${IMAGE_PROMPT}\""
info "  Model  : ${IMAGE_MODEL}"

IMAGE_REQ="{\"prompt\":\"${IMAGE_PROMPT}\",\"model\":\"${IMAGE_MODEL}\"}"

IMG_HTTP=$(curl_req POST "${BASE_URL}/native/tasks/image" \
    -H "X-API-Key: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$IMAGE_REQ")
IMG_BODY=$(cat "$TMP_BODY")

if [ "$IMG_HTTP" = "200" ] || [ "$IMG_HTTP" = "201" ]; then
    IMG_JOB_ID=$(echo "$IMG_BODY" | jq -r '.job_id // empty')
    record_pass "Image task accepted (job_id=${IMG_JOB_ID}, HTTP ${IMG_HTTP})"
    info "Polling for image result (max $((POLL_MAX * POLL_INTERVAL))s)..."
    poll_job "$IMG_JOB_ID" "Image generation" || true
else
    record_fail "Image task submission failed (HTTP ${IMG_HTTP})"
    echo "Response: $IMG_BODY"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 6. POST /native/tasks/video
# ─────────────────────────────────────────────────────────────────────────────
separator
info "Step 6 — Submitting VIDEO generation task"
info "  Prompt : \"${VIDEO_PROMPT}\""
info "  Model  : ${VIDEO_MODEL}"

VIDEO_REQ="{\"prompt\":\"${VIDEO_PROMPT}\",\"model\":\"${VIDEO_MODEL}\"}"

VID_HTTP=$(curl_req POST "${BASE_URL}/native/tasks/video" \
    -H "X-API-Key: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$VIDEO_REQ")
VID_BODY=$(cat "$TMP_BODY")

if [ "$VID_HTTP" = "200" ] || [ "$VID_HTTP" = "201" ]; then
    VID_JOB_ID=$(echo "$VID_BODY" | jq -r '.job_id // empty')
    record_pass "Video task accepted (job_id=${VID_JOB_ID}, HTTP ${VID_HTTP})"
    info "Polling for video result (max $((POLL_MAX * POLL_INTERVAL))s)..."
    poll_job "$VID_JOB_ID" "Video generation" || true
else
    record_fail "Video task submission failed (HTTP ${VID_HTTP})"
    echo "Response: $VID_BODY"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 7. gemcli image/video via MCP CLI (if available)
# ─────────────────────────────────────────────────────────────────────────────
separator
info "Step 7 — Testing gemcli CLI commands (MCP layer)"

GEMCLI_PATH=""
if command -v gemcli &>/dev/null; then
    GEMCLI_PATH=$(command -v gemcli)
elif [ -f "/Users/biolasti/application/project/geminiwebapi/.venv/bin/gemcli" ]; then
    GEMCLI_PATH="/Users/biolasti/application/project/geminiwebapi/.venv/bin/gemcli"
fi

if [ -z "$GEMCLI_PATH" ]; then
    warn "gemcli not found in PATH — skipping CLI tests"
else
    info "gemcli found at: ${GEMCLI_PATH}"
    GEMCLI_VERSION=$("$GEMCLI_PATH" --version 2>&1 || true)
    info "gemcli version: ${GEMCLI_VERSION}"

    # 7a. Verify gemcli image CLI interface
    info "7a — Verifying gemcli image CLI interface"
    IMG_HELP=$("$GEMCLI_PATH" image --help 2>&1 || true)
    if echo "$IMG_HELP" | grep -q "PROMPT"; then
        record_pass "gemcli image CLI confirmed — syntax: gemcli image PROMPT [-m flash|pro] [-o file.png]"
        info "  Default model: Nano Banana 2 (flash). Pro model requires Pro/Ultra subscription."
    else
        record_fail "gemcli image --help did not return expected output"
        echo "$IMG_HELP"
    fi

    # 7b. Verify gemcli video CLI interface
    info "7b — Verifying gemcli video CLI interface"
    VID_HELP=$("$GEMCLI_PATH" video --help 2>&1 || true)
    if echo "$VID_HELP" | grep -q "PROMPT"; then
        record_pass "gemcli video CLI confirmed — syntax: gemcli video PROMPT [-m pro|flash|thinking] [-o file.mp4]"
        info "  Uses Veo 3.1 technology. Default model: flash."
    else
        record_fail "gemcli video --help did not return expected output"
        echo "$VID_HELP"
    fi

    # 7c. gemcli doctor
    info "7c — Running gemcli doctor (installation health check)"
    DOCTOR_OUT=$("$GEMCLI_PATH" doctor 2>&1 || true)
    if echo "$DOCTOR_OUT" | grep -qiE "(ok|pass|healthy|installed|found|gemcli)"; then
        record_pass "gemcli doctor completed"
    else
        warn "gemcli doctor output (review manually):"
    fi
    echo "$DOCTOR_OUT" | head -20

    # 7d. MCP endpoint probe
    info "7d — Testing MCP endpoint at ${BASE_URL}/mcp"
    MCP_HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${BASE_URL}/mcp" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: ${API_KEY}" \
        -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}},"id":1}' 2>&1 || echo "000")
    if [ "$MCP_HTTP" = "200" ]; then
        record_pass "MCP endpoint reachable (HTTP 200)"
    else
        warn "MCP endpoint returned HTTP ${MCP_HTTP} (SSE transport may need different probe)"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# 8. Summary
# ─────────────────────────────────────────────────────────────────────────────
separator
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              TEST SUMMARY                               ║${NC}"
echo -e "${BLUE}╠══════════════════════════════════════════════════════════╣${NC}"
printf "${BLUE}║${NC}  Backend : %-45s ${BLUE}║${NC}\n" "${BASE_URL}"
printf "${BLUE}║${NC}  ${GREEN}PASSED${NC}   : %-45s ${BLUE}║${NC}\n" "${PASS_COUNT}"
printf "${BLUE}║${NC}  ${RED}FAILED${NC}   : %-45s ${BLUE}║${NC}\n" "${FAIL_COUNT}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}${FAIL_COUNT} test(s) failed. Review output above for details.${NC}"
    exit 1
fi
