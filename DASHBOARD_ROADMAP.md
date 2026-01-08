# 🚀 DASHBOARD ESCALATION SYSTEM - IMPLEMENTATION ROADMAP

**Project**: Stetson University Addi Demo - Dashboard Escalation Display
**Date Started**: January 26, 2025
**Last Updated**: January 7, 2026 (Session - Render Deployment Fix)
**Status**: 🟢 In Progress - Escalations Page Complete | Tool Call Capture Next
**Estimated Total Time**: UI/UX complete | Backend tool call extraction pending

**Current Priority**: Capture tool calls from ElevenLabs sync | Should show 12 escalations (6 webhook + 6 tool calls)
**Next Steps**: Extract `escalate_to_human` tool calls from ElevenLabs `analysis` section during sync

## Latest Knowledge (January 2026)
- ✅ **FIXED (Jan 7, 2026):** Render Deployment - Resolved dependency conflict
  - Updated `pydantic-settings` from `2.6.1` → `2.12.0` for compatibility with `pydantic==2.12.3`
  - Fixed `ResolutionImpossible` error during Render build
  - All dependencies now correctly specified in root `requirements.txt`
  - See: `Sessions/2026/JAN/2026-01-07_Render_Deployment_Dependency_Fix.md`
- ✅ **COMPLETE:** Escalations Page UI/UX - All features deployed and working
  - View conversation modal with full transcript
  - Mark as resolved with notes
  - Proper sorting (pending first, resolved below)
  - "Done" priority badge for resolved items
- ✅ **FIXED:** API integration - Using correct endpoints (`PATCH /escalations/{id}/status`)
- ✅ **REMOVED:** "Escalations (New)" test page - Consolidated to single `/escalations` page
- 📋 **PLANNED:** Statistics Page - Comprehensive plan created (see `docs/STATISTICS_PAGE_COMPREHENSIVE_PLAN.md`)
  - Full conversation data table with transcripts
  - Keyword/phrase extraction for insights
  - Deep metrics (response time, sentiment, topics)
  - Export functionality (CSV/JSON)
  - Foundation for future chart visualizations
- 🔍 **INVESTIGATING:** Tool call escalations - Missing 6 escalations from ElevenLabs tool calls
- 🚀 **NEXT:** Statistics Page implementation OR Extract tool calls from ElevenLabs `analysis` section during sync

## Previous Knowledge (November 19, 2025)
- ✅ Gemini Topic Extraction Service: `services/gemini_topic_service.py` - Extracts topics from transcripts
- ✅ Topic Extraction Integrated: Sync endpoint now extracts topics when missing or generic
- 🔧 **ACTION NEEDED:** Add `GOOGLE_GEMINI_API_KEY` to Render environment variables
- 📚 Previous Knowledge:
  - 🚀 Deployment Strategy: `docs/DEPLOYMENT_STRATEGY_ANALYSIS.md`
- ✅ Conversations Page Complete (81%): `Sessions/2025/OCT/OCT30_2025-CONVERSATIONS_PROGRESS.md`
- ✅ UI Fixes Session: `Sessions/2025/OCT/OCT31_2025-UI_FIXES_SESSION.md`
- 📚 RAG Knowledge: `docs/RAG_KNOWLEDGE/CONVERSATIONS_PAGE_IMPLEMENTATION.md`
- Memory pickup: `MEMORY_REFRESH_PROTOCOL.md`

---

## 📋 TABLE OF CONTENTS

1. [Overview & Architecture](#overview--architecture)
2. [Progress Tracker](#progress-tracker)
3. [Statistics Page Plan](#statistics-page-plan) ⭐ **NEW**
4. [Phase 1: Backend Data Models](#phase-1-backend-data-models)
5. [Phase 2: Backend API Endpoints](#phase-2-backend-api-endpoints)
6. [Phase 3: Dashboard Backend Proxy](#phase-3-dashboard-backend-proxy)
7. [Phase 4: Frontend Components](#phase-4-frontend-components)
8. [Phase 5: Integration & Polish](#phase-5-integration--polish)
9. [Phase 6: ElevenLabs Configuration](#phase-6-elevenlabs-configuration)
10. [Testing Procedures](#testing-procedures)
11. [Troubleshooting Guide](#troubleshooting-guide)

---

## STATISTICS PAGE PLAN ⭐ **NEW**

### **Overview**

A comprehensive **Statistics/Analytics page** (`/statistics`) that serves as the data analysis hub for the Addi dashboard. This page will display complete conversation data, provide keyword/phrase extraction, show deep metrics, and enable data export.

**Status**: 📋 **Plan Complete - Ready for Review**  
**Documentation**: `docs/STATISTICS_PAGE_COMPREHENSIVE_PLAN.md`  
**Timeline**: 8-10 hours (with testing breaks)  
**Priority**: High - Foundation for data insights

### **Key Features**

1. **Master Data Table**
   - Complete conversation data with full transcripts
   - Sortable, filterable, searchable
   - Expandable rows for transcripts/summaries
   - Export to CSV/JSON

2. **Summary Cards**
   - Total Conversations
   - Average Response Time (properly formatted - never "0m" for > 0s)
   - Sentiment Mix
   - Top Topic

3. **Keyword Extraction**
   - Top 20 common words
   - Top 10 common phrases (2-4 words)
   - Keyword filtering for table

4. **Deep Metrics**
   - Response time calculations (avg, median, min, max)
   - Sentiment breakdown
   - Topic distribution
   - Outcome breakdown

5. **Future Charts** (Phase 2)
   - Sentiment Distribution (Donut chart)
   - Topic Distribution (Horizontal bar chart)
   - Conversation Volume Over Time (Line chart)
   - Keyword Cloud visualization

### **Implementation Phases**

1. **Phase 1: Backend Statistics API** (2 hours)
   - Create `/api/webhooks/dashboard/statistics` endpoint
   - Keyword/phrase extraction utility
   - Response time formatting utility
   - Calculate metrics

2. **Phase 2: Frontend Statistics Page** (3 hours)
   - Create `/statistics` page route
   - StatisticsTable component
   - StatisticsSummary cards
   - KeywordExtraction component
   - Export functionality

3. **Phase 3: Response Time Display Fix** (30 mins)
   - Format response time properly (never "0m" for > 0s)
   - Update StatCard component
   - Update StatisticsTable

4. **Phase 4: Styling & Polish** (1 hour)
   - Stetson branding
   - Responsive design
   - Loading/empty states
   - Accessibility

5. **Phase 5: Chart Integration** (Future - 2 hours)
   - Sentiment chart
   - Topic chart
   - Time series chart
   - Keyword cloud

### **Critical Requirements**

- ✅ Response time never shows "0m" when duration > 0 seconds
- ✅ Full transcripts accessible in table
- ✅ Keyword extraction (words and phrases)
- ✅ Export includes full transcripts
- ✅ Real-time updates (30s refresh)
- ✅ Mobile responsive

### **Files to Create/Modify**

**Backend**:
- `addi_backend/utils/text_analysis.py` (NEW)
- `addi_backend/utils/time_formatting.py` (NEW)
- `addi_backend/routers/webhooks.py` (MODIFY - add statistics endpoint)

**Frontend**:
- `dashboard_frontend/app/statistics/page.tsx` (NEW)
- `dashboard_frontend/lib/useStatistics.ts` (NEW)
- `dashboard_frontend/lib/utils/formatResponseTime.ts` (NEW)
- `dashboard_frontend/lib/utils/exportStatistics.ts` (NEW)
- `dashboard_frontend/components/organisms/StatisticsTable.tsx` (NEW)
- `dashboard_frontend/components/organisms/StatisticsSummary.tsx` (NEW)
- `dashboard_frontend/components/organisms/KeywordExtraction.tsx` (NEW)
- `dashboard_frontend/components/atoms/StatCard.tsx` (MODIFY)
- `dashboard_frontend/components/organisms/Sidebar.tsx` (MODIFY - add nav link)

### **Next Steps**

1. **Review** comprehensive plan: `docs/STATISTICS_PAGE_COMPREHENSIVE_PLAN.md`
2. **Approve** requirements and timeline
3. **Start Phase 1**: Backend statistics API
4. **Test after each task** as specified
5. **Update roadmap** as tasks complete

---

## OVERVIEW & ARCHITECTURE

### System Architecture
```
┌─────────────────────┐
│   ElevenLabs Agent  │ (Voice AI)
│  "Addi" Assistant   │
└──────────┬──────────┘
           │
           │ POST /api/webhooks/escalation/create
           │ (Server Tool Call)
           ↓
┌──────────────────────────────────────────────────┐
│ BACKEND (Port 44000)                             │
│ ├── POST /escalation/create ✅ WORKING           │
│ │   └── escalations_db.append() ✅ WORKING       │
│ └── GET /dashboard/escalations ❌ MISSING        │
└──────────┬───────────────────────────────────────┘
           │
           │ Proxy Request
           ↓
┌──────────────────────────────────────────────────┐
│ DASHBOARD BACKEND (Port 42000)                   │
│ └── GET /api/dashboard/escalations ❌ MISSING    │
└──────────┬───────────────────────────────────────┘
           │
           │ SWR Fetch (10s polling)
           ↓
┌──────────────────────────────────────────────────┐
│ FRONTEND (Port 41001)                            │
│ ├── useDashboardData() ❌ No escalation fetch    │
│ ├── EscalationCard ❌ Not created                │
│ ├── EscalationList ❌ Not created                │
│ └── EscalationStatCard ❌ Not created            │
└──────────────────────────────────────────────────┘
```

### Data Flow
1. **ElevenLabs** → Student asks for human help → Agent calls `escalate_to_human` tool
2. **Backend (44000)** → Receives POST, stores in `escalations_db[]` ✅
3. **Backend (44000)** → Needs GET endpoint to retrieve escalations ❌
4. **Dashboard Backend (42000)** → Needs proxy endpoint ❌
5. **Frontend (41001)** → Fetches via SWR, displays in components ❌

### Current Escalation Data Structure
```python
{
    "id": "ESC_20250126_143522_1",
    "student_name": "Sarah Johnson",
    "student_email": "sarah.j@example.com",
    "student_phone": "+1-555-0123",
    "inquiry_topic": "Financial Aid Question",
    "best_time_to_call": "Weekday afternoons",
    "conversation_id": "conv_demo_001",
    "created_at": datetime(2025, 1, 26, 14, 35, 22),
    "status": "pending",  # pending | in_progress | resolved
    "assigned_to": None
}
```

---

## PROGRESS TRACKER

### Legend
- ✅ Complete
- 🟢 In Progress
- 🟡 Ready to Start
- ⬜ Waiting
- ❌ Blocked

| Phase | Task | Status | Time Est | Actual Time | Notes |
|-------|------|--------|----------|-------------|-------|
| **Phase 1** | Backend Data Models | ⬜ | 15 min | - | - |
| 1.1 | Add EscalationSummary model | ⬜ | 5 min | - | - |
| 1.2 | Test model compilation | ⬜ | 2 min | - | - |
| 1.3 | Restart backend | ⬜ | 3 min | - | - |
| 1.4 | **TESTING BREAK** | ⬜ | 5 min | - | - |
| **Phase 2** | Backend API Endpoints | ⬜ | 30 min | - | - |
| 2.1 | Add GET /dashboard/escalations | ⬜ | 15 min | - | - |
| 2.2 | Test endpoint with curl | ⬜ | 5 min | - | - |
| 2.3 | Create test escalation | ⬜ | 5 min | - | - |
| 2.4 | **TESTING BREAK** | ⬜ | 5 min | - | - |
| **Phase 3** | Dashboard Backend Proxy | ⬜ | 20 min | - | - |
| 3.1 | Add proxy endpoint | ⬜ | 10 min | - | - |
| 3.2 | Update CORS if needed | ⬜ | 5 min | - | - |
| 3.3 | Test proxy with curl | ⬜ | 5 min | - | - |
| 3.4 | **TESTING BREAK** | ⬜ | 5 min | - | - |
| **Phase 4** | Frontend Components | ⬜ | 45 min | - | - |
| 4.1 | Create EscalationCard.tsx | ⬜ | 15 min | - | - |
| 4.2 | Create EscalationList.tsx | ⬜ | 15 min | - | - |
| 4.3 | Create EscalationStatCard.tsx | ⬜ | 10 min | - | - |
| 4.4 | **TESTING BREAK** | ⬜ | 5 min | - | - |
| **Phase 5** | Integration & Polish | ⬜ | 30 min | - | - |
| 5.1 | Update useDashboardData.ts | ⬜ | 10 min | - | - |
| 5.2 | Update page.tsx | ⬜ | 10 min | - | - |
| 5.3 | Test full flow | ⬜ | 10 min | - | - |
| 5.4 | **FINAL TESTING BREAK** | ⬜ | 10 min | - | - |
| **Phase 6** | ElevenLabs Configuration | ⬜ | 15 min | - | - |
| 6.1 | Review tool configuration | ⬜ | 5 min | - | - |
| 6.2 | Test live escalation | ⬜ | 10 min | - | - |

**Total Estimated Time**: 2 hours 35 minutes
**Total Actual Time**: ___ (Will update as we progress)

---

## PHASE 1: BACKEND DATA MODELS

### 🎯 Goal
Create Pydantic model for escalation dashboard display

### 📂 Files to Modify
- `/Users/jason/Projects/addi_demo/addi_backend/models/calls.py`

### 🔨 Implementation Steps

#### Step 1.1: Add EscalationSummary Model (5 min)

**Add to `calls.py` after `EscalationResponse` (line 111)**:

```python
class EscalationSummary(BaseModel):
    """Summary of escalation for dashboard display"""
    id: str
    student_name: str
    student_email: str
    student_phone: Optional[str]
    inquiry_topic: str
    best_time_to_call: Optional[str]
    conversation_id: Optional[str]
    created_at: datetime
    status: str  # 'pending', 'in_progress', 'resolved'
    assigned_to: Optional[str]
    priority: str  # Derived: 'urgent' (>24h), 'high' (>12h), 'medium' (else)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

**What this does**: Defines the data structure that the dashboard will display

#### Step 1.2: Test Model Compilation (2 min)

**Run**:
```bash
cd /Users/jason/Projects/addi_demo/addi_backend
source ../venv/bin/activate
python3 -c "from models.calls import EscalationSummary; print('✅ Model imported successfully')"
```

**Expected Output**: `✅ Model imported successfully`

#### Step 1.3: Restart Backend (3 min)

**Find backend process**:
```bash
lsof -i :44000
```

**Kill and restart**:
```bash
# Press Ctrl+C in backend terminal, then:
cd /Users/jason/Projects/addi_demo/addi_backend
python3 main.py
```

**Expected Output**:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:44000
```

---

### 🧪 TESTING BREAK 1.4 (5 min)

**What to Test**:
1. Backend restarts without errors
2. Model imports correctly
3. No TypeScript/Python compilation errors

**Commands**:
```bash
# Health check
curl http://localhost:44000/health

# Check OpenAPI docs
open http://localhost:44000/docs
```

**Expected Results**:
- ✅ Health check returns 200 OK
- ✅ Docs page loads
- ✅ No import errors in terminal

**What Can Go Wrong**:
- ❌ Import error → Check syntax in calls.py
- ❌ Backend won't start → Check for duplicate class names

**Action Before Continuing**: Confirm all tests pass ✅

**Progress Log**:
```
Phase 1 Complete: _______________
Issues Encountered: _______________
Time Taken: _______________
```

---

## PHASE 2: BACKEND API ENDPOINTS

### 🎯 Goal
Create GET endpoint to retrieve escalations from escalations_db

### 📂 Files to Modify
- `/Users/jason/Projects/addi_demo/addi_backend/routers/webhooks.py`

### 🔨 Implementation Steps

#### Step 2.1: Add GET /dashboard/escalations Endpoint (15 min)

**Add to `webhooks.py` after the `get_analytics` endpoint (after line 398)**:

```python
@router.get("/dashboard/escalations", response_model=list[EscalationSummary])
async def get_escalations(
    limit: int = 50,
    offset: int = 0,
    status: str = None  # Filter: 'pending', 'in_progress', 'resolved', or None (all)
):
    """
    Get list of escalations for dashboard.
    Automatically calculates priority based on age.
    """
    try:
        from datetime import datetime, timedelta

        # Filter by status if provided
        filtered_escalations = escalations_db
        if status:
            filtered_escalations = [
                esc for esc in escalations_db
                if esc.get("status") == status
            ]

        # Sort by created_at (newest first)
        sorted_escalations = sorted(
            filtered_escalations,
            key=lambda x: x["created_at"],
            reverse=True
        )

        # Apply pagination
        paginated = sorted_escalations[offset:offset + limit]

        # Convert to response format with priority calculation
        summaries = []
        now = datetime.utcnow()

        for esc in paginated:
            # Calculate priority based on age
            age_hours = (now - esc["created_at"]).total_seconds() / 3600

            if age_hours > 24:
                priority = "urgent"
            elif age_hours > 12:
                priority = "high"
            else:
                priority = "medium"

            summary = EscalationSummary(
                id=esc["id"],
                student_name=esc["student_name"],
                student_email=esc["student_email"],
                student_phone=esc.get("student_phone"),
                inquiry_topic=esc["inquiry_topic"],
                best_time_to_call=esc.get("best_time_to_call"),
                conversation_id=esc.get("conversation_id"),
                created_at=esc["created_at"],
                status=esc["status"],
                assigned_to=esc.get("assigned_to"),
                priority=priority
            )
            summaries.append(summary)

        return summaries

    except Exception as e:
        logger.error(f"Failed to get escalations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get escalations: {str(e)}")
```

**What this does**:
- Retrieves escalations from in-memory database
- Filters by status (optional)
- Calculates priority based on age (urgent if >24h old)
- Returns paginated list

#### Step 2.2: Test Endpoint with curl (5 min)

**Restart backend first**:
```bash
# Ctrl+C in backend terminal, then:
cd /Users/jason/Projects/addi_demo/addi_backend
python3 main.py
```

**Test the endpoint**:
```bash
curl http://localhost:44000/api/webhooks/dashboard/escalations
```

**Expected Output** (empty array for now):
```json
[]
```

#### Step 2.3: Create Test Escalation (5 min)

**Run this curl command**:
```bash
curl -X POST http://localhost:44000/api/webhooks/escalation/create \
  -H "Authorization: Bearer YOUR_API_KEY_FROM_ENV" \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "Test Student",
    "student_email": "test@example.com",
    "student_phone": "+1-555-TEST",
    "inquiry_topic": "Dashboard Testing",
    "best_time_to_call": "Afternoon",
    "conversation_id": "test_conv_001"
  }'
```

**Replace `YOUR_API_KEY_FROM_ENV`** with actual key from:
```bash
cat /Users/jason/Projects/addi_demo/addi_backend/.env | grep ELEVENLABS_API_KEY
```

**Expected Response**:
```json
{
  "escalation_id": "ESC_20250126_...",
  "status": "created",
  "message": "Thank you! An admissions counselor will reach out...",
  "estimated_response_time": "within 24 hours"
}
```

**Now test GET again**:
```bash
curl http://localhost:44000/api/webhooks/dashboard/escalations
```

**Expected Output** (should show your test escalation):
```json
[
  {
    "id": "ESC_20250126_...",
    "student_name": "Test Student",
    "student_email": "test@example.com",
    "priority": "medium",
    "status": "pending",
    ...
  }
]
```

---

### 🧪 TESTING BREAK 2.4 (5 min)

**What to Test**:
1. Endpoint returns 200 OK
2. Test escalation appears in response
3. Priority calculation works
4. Filtering by status works

**Test Commands**:
```bash
# Get all escalations
curl http://localhost:44000/api/webhooks/dashboard/escalations

# Get only pending
curl "http://localhost:44000/api/webhooks/dashboard/escalations?status=pending"

# Test pagination
curl "http://localhost:44000/api/webhooks/dashboard/escalations?limit=5&offset=0"
```

**Expected Results**:
- ✅ All commands return 200 OK
- ✅ Test escalation visible
- ✅ Priority is "medium" (less than 12h old)
- ✅ Filtering works

**Action Before Continuing**: Verify test escalation appears correctly ✅

**Progress Log**:
```
Phase 2 Complete: _______________
Escalations in Database: _______________
Issues Encountered: _______________
Time Taken: _______________
```

---

## PHASE 3: DASHBOARD BACKEND PROXY

### 🎯 Goal
Create proxy endpoint on port 42000 to forward requests to port 44000

### 📂 Files to Modify
- `/Users/jason/Projects/addi_demo/dashboard_backend/main.py`

### 🔨 Implementation Steps

#### Step 3.1: Add Proxy Endpoint (10 min)

**Add to `main.py` after the `get_analytics` endpoint (after line 138)**:

```python
@app.get("/api/dashboard/escalations")
async def get_escalations(
    limit: int = 50,
    offset: int = 0,
    status: str = None
):
    """
    Get list of escalations from the backend.
    Optionally filter by status: pending, in_progress, resolved
    """
    try:
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/webhooks/dashboard/escalations",
                params=params
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error("Timeout connecting to backend")
        raise HTTPException(status_code=504, detail="Backend timeout")
    except httpx.HTTPStatusError as e:
        logger.error(f"Backend error: {e.response.status_code}")
        raise HTTPException(status_code=e.response.status_code, detail="Backend error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

**What this does**: Proxies escalation requests from frontend (41001) to backend (44000)

#### Step 3.2: Update CORS (5 min)

**Check current CORS in `main.py` (line 29-35)**:

Current:
```python
allow_origins=["http://localhost:41000", "http://localhost:3000"],
```

**Add port 41001**:
```python
allow_origins=["http://localhost:41000", "http://localhost:41001", "http://localhost:3000"],
```

**Why**: Frontend is on port 41001 (not 41000)

#### Step 3.3: Test Proxy (5 min)

**Restart dashboard backend**:
```bash
# Ctrl+C in dashboard backend terminal, then:
cd /Users/jason/Projects/addi_demo/dashboard_backend
source ../venv/bin/activate
python3 main.py
```

**Test proxy endpoint**:
```bash
curl http://localhost:42000/api/dashboard/escalations
```

**Expected Output**: Same as backend endpoint (your test escalation)

---

### 🧪 TESTING BREAK 3.4 (5 min)

**What to Test**:
1. Proxy endpoint returns data
2. CORS headers present
3. Filtering works through proxy

**Test Commands**:
```bash
# Test proxy
curl http://localhost:42000/api/dashboard/escalations

# Test with status filter
curl "http://localhost:42000/api/dashboard/escalations?status=pending"

# Check CORS headers
curl -i http://localhost:42000/api/dashboard/escalations | grep -i access-control
```

**Expected Results**:
- ✅ Proxy returns same data as backend
- ✅ CORS headers present
- ✅ No timeout errors

**Action Before Continuing**: Confirm proxy works ✅

**Progress Log**:
```
Phase 3 Complete: _______________
Proxy Working: _______________
Issues Encountered: _______________
Time Taken: _______________
```

---

## PHASE 4: FRONTEND COMPONENTS

### 🎯 Goal
Create React components to display escalations

### 📂 Files to Create
- `/Users/jason/Projects/addi_demo/dashboard_frontend/components/organisms/EscalationCard.tsx`
- `/Users/jason/Projects/addi_demo/dashboard_frontend/components/organisms/EscalationList.tsx`
- `/Users/jason/Projects/addi_demo/dashboard_frontend/components/atoms/EscalationStatCard.tsx`

### 🔨 Implementation Steps

#### Step 4.1: Create EscalationCard.tsx (15 min)

**Create file**: `dashboard_frontend/components/organisms/EscalationCard.tsx`

**Content** (see full code in ENHANCED_IMPLEMENTATION_PLAN.md Phase 1C)

**Key Features**:
- Student name, email, phone display
- Priority badge (urgent/high/medium)
- Status badge (pending/in_progress/resolved)
- Inquiry topic with truncation
- Best time to call
- Relative timestamp
- Action buttons (Mark In Progress, Resolve)

#### Step 4.2: Create EscalationList.tsx (15 min)

**Create file**: `dashboard_frontend/components/organisms/EscalationList.tsx`

**Content** (see full code in ENHANCED_IMPLEMENTATION_PLAN.md Phase 1C)

**Key Features**:
- Filter by status
- Empty state message
- Loading skeleton
- Grid of EscalationCard components
- Responsive layout

#### Step 4.3: Create EscalationStatCard.tsx (10 min)

**Create file**: `dashboard_frontend/components/atoms/EscalationStatCard.tsx`

**Content** (simplified StatCard variant for escalations)

**Key Features**:
- Total pending count
- Urgent count (red badge)
- Pulsing animation for urgent
- Click to scroll to escalations section

---

### 🧪 TESTING BREAK 4.4 (5 min)

**What to Test**:
1. TypeScript compilation
2. Components import correctly
3. No React errors

**Test Commands**:
```bash
cd /Users/jason/Projects/addi_demo/dashboard_frontend

# Check TypeScript compilation
npm run type-check

# Check for build errors
npm run build
```

**Expected Results**:
- ✅ No TypeScript errors
- ✅ Build succeeds
- ✅ Components found by imports

**What Can Go Wrong**:
- ❌ TypeScript errors → Check interface definitions
- ❌ Import errors → Check file paths

**Action Before Continuing**: Fix any TypeScript errors ✅

**Progress Log**:
```
Phase 4 Complete: _______________
Components Created: _______________
Issues Encountered: _______________
Time Taken: _______________
```

---

## PHASE 5: INTEGRATION & POLISH

### 🎯 Goal
Wire up components to data and display on dashboard

### 📂 Files to Modify
- `/Users/jason/Projects/addi_demo/dashboard_frontend/lib/useDashboardData.ts`
- `/Users/jason/Projects/addi_demo/dashboard_frontend/app/page.tsx`

### 🔨 Implementation Steps

#### Step 5.1: Update useDashboardData.ts (10 min)

**Add escalation fetching** (after analytics, around line 27):

```typescript
// Escalations - Refresh every 10 seconds
const { data: escalations, error: escalationsError } = useSWR(
  `${API_BASE}/api/dashboard/escalations?status=pending`,
  fetcher,
  {
    refreshInterval: 10000,  // 10 seconds
    revalidateOnFocus: true
  }
)

return {
  interactions: interactions || [],
  analytics,
  escalations: escalations || [],  // Add this line
  activities: [],
  isLoading: !interactions && !analytics && !escalations,
  error: interactionsError || analyticsError || escalationsError,
  refresh: mutateInteractions
}
```

#### Step 5.2: Update page.tsx (10 min)

**Add import** (top of file):
```typescript
import { EscalationList } from '@/components/organisms/EscalationList'
import { EscalationStatCard } from '@/components/atoms/EscalationStatCard'
```

**Replace escalation placeholder** (line 156-163):
```typescript
{/* Escalations Manager */}
<section className="data-section">
  <EscalationList />
</section>
```

**Add stat card to stats grid** (after line 125):
```typescript
<EscalationStatCard
  escalations={escalations}
  animateOnChange={true}
/>
```

#### Step 5.3: Test Full Flow (10 min)

**Open dashboard**:
```bash
open http://localhost:41001
```

**Verify**:
1. Dashboard loads without errors
2. Test escalation appears in list
3. Priority badge shows "medium"
4. Status badge shows "pending"
5. Stat card shows count

---

### 🧪 FINAL TESTING BREAK 5.4 (10 min)

**What to Test**:
1. End-to-end escalation flow
2. Real-time updates
3. Filtering
4. Action buttons

**Test Procedures**:

**Test 1: Create Escalation via API**
```bash
curl -X POST http://localhost:44000/api/webhooks/escalation/create \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "Live Test Student",
    "student_email": "live@test.com",
    "inquiry_topic": "Real-time Update Test"
  }'
```

**Expected**: New escalation appears on dashboard within 10 seconds (no manual refresh)

**Test 2: Check Priority Aging**

Create escalation with old timestamp (modify `created_at` in `escalations_db` directly):
```python
# In backend terminal:
from datetime import datetime, timedelta
escalations_db[0]['created_at'] = datetime.utcnow() - timedelta(hours=25)
```

**Expected**: Priority badge changes to "urgent" (red)

**Test 3: Filter by Status**

Click status filter buttons in EscalationList component

**Expected**: List filters correctly

**Expected Results**:
- ✅ New escalations appear automatically
- ✅ Priority calculation correct
- ✅ Filtering works
- ✅ No console errors
- ✅ Real-time polling works

**Action Before Continuing**: All tests pass ✅

**Progress Log**:
```
Phase 5 Complete: _______________
Dashboard Fully Functional: _______________
Issues Encountered: _______________
Time Taken: _______________
```

---

## PHASE 6: ELEVENLABS CONFIGURATION

### 🎯 Goal
Configure ElevenLabs agent to create escalations via webhook

### 📂 ElevenLabs Dashboard
https://elevenlabs.io → Agents → agent_0301k84pwdr2ffprwkqaha0f178g

### 🔨 Implementation Steps

#### Step 6.1: Review Tool Configuration (5 min)

**Check existing tool**: `escalate_to_human`

**Verify Configuration**:

**✅ Tool Name**: `escalate_to_human`

**✅ Description** (CRITICAL - must be directive):
```
**CRITICAL TOOL**: Immediately use this tool when: (1) student explicitly asks to speak with a human/counselor/admissions advisor, (2) student says 'I want to talk to someone', (3) you cannot fully answer their question, (4) student needs personalized admissions guidance, (5) conversation requires human expertise. ALWAYS ask for student_name and student_email before calling this tool.
```

**✅ URL**: `https://[YOUR-NGROK-URL]/api/webhooks/escalation/create`

**✅ Method**: `POST`

**✅ Parameters Location**: ALL in `request_body_schema.properties` (NOT query params)

**✅ Required Fields**: Only `student_name` and `student_email`

**✅ Headers**:
```json
{
  "Authorization": "Bearer [YOUR-API-KEY]",
  "Content-Type": "application/json"
}
```

**Key Principles from WEBHOOK_TOOL_CONFIGURATION_LESSONS.md**:

1. **Description MUST be directive**:
   - Use "**CRITICAL TOOL**: Immediately use..."
   - List numbered triggers (1), (2), (3)
   - Include explicit examples

2. **Parameters in correct location**:
   - POST with JSON → ALL params in `request_body_schema.properties`
   - NOT in `query_params_schema`

3. **Minimize required fields**:
   - Only mark essential fields as `required: true`
   - Use dynamic variables for auto-populated data:
     - `conversation_id` → `system__conversation_id`
     - `student_phone` → `system__caller_id`

**If tool config needs updates**, follow lessons from WEBHOOK_TOOL_CONFIGURATION_LESSONS.md

#### Step 6.2: Test Live Escalation (10 min)

**Prerequisite**: ngrok tunnel running
```bash
cd /Users/jason/Projects/addi_demo/addi_backend
./scripts/setup_ngrok.sh
```

**Update webhook URL** in ElevenLabs if ngrok URL changed

**Test Procedure**:

1. **Call/Test Addi** via ElevenLabs test interface
2. **Say**: "I need to speak with an admissions counselor"
3. **Provide info when asked**: Name, email
4. **Watch for**:
   - Agent calls `escalate_to_human` tool
   - Backend logs: "Creating escalation for [name]"
   - Dashboard shows new escalation within 10 seconds

**Backend Terminal Should Show**:
```
INFO: Creating escalation for [Student Name] ([email])
INFO: Escalation ESC_20250126_... created successfully
```

**Dashboard Should Show**:
- New escalation card appears
- Student name and email visible
- Status: "pending"
- Priority: "medium" (if recent)

---

### 🧪 TESTING BREAK 6.2 (Includes live test)

**What to Test**:
1. ElevenLabs tool calls webhook
2. Backend receives and stores escalation
3. Dashboard displays within 10 seconds
4. Post-call webhook fires

**Full Demo Flow Test**:

1. **Start Test Call**
2. **Say**: "What marine biology programs do you offer?"
   - **Expected**: Agent queries knowledge base, responds
3. **Say**: "I'd like to speak with someone about financial aid"
   - **Expected**: Agent asks for name and email
4. **Provide**: "Test Student" and "test@example.com"
   - **Expected**: Agent confirms escalation created
5. **End Call**
   - **Expected**: Post-call webhook fires, interaction logged
6. **Check Dashboard**:
   - New interaction in "Recent Conversations"
   - New escalation in "Escalation Manager"
   - Escalation linked to interaction (conversation_id match)

**Expected Results**:
- ✅ Tool called successfully
- ✅ Backend receives webhook
- ✅ Escalation appears on dashboard
- ✅ No 401/403/500 errors
- ✅ Post-call webhook works

**Common Issues & Fixes**:

**❌ "Authorization failed" (401)**:
- Check API key in ElevenLabs tool config matches `.env` file

**❌ "Tool not called" (agent doesn't escalate)**:
- Tool description not directive enough
- Review WEBHOOK_TOOL_CONFIGURATION_LESSONS.md
- Update description to be more explicit

**❌ "Timeout" or "Connection refused"**:
- ngrok tunnel stopped → restart `./scripts/setup_ngrok.sh`
- Backend not running → restart backend

**❌ "Escalation created but not showing on dashboard"**:
- Check frontend console for errors (F12)
- Verify SWR is polling (should refetch every 10s)
- Check dashboard backend proxy is running (port 42000)

**Action Before Continuing**: Live escalation works end-to-end ✅

**Progress Log**:
```
Phase 6 Complete: _______________
Live Escalations Working: _______________
Issues Encountered: _______________
Time Taken: _______________
```

---

## TESTING PROCEDURES

### Manual Test Checklist

**Backend Tests** (Port 44000):
```bash
# Health check
curl http://localhost:44000/health

# Create escalation
curl -X POST http://localhost:44000/api/webhooks/escalation/create \
  -H "Authorization: Bearer $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"student_name":"Test","student_email":"test@test.com","inquiry_topic":"Test"}'

# Get escalations
curl http://localhost:44000/api/webhooks/dashboard/escalations

# Filter by status
curl "http://localhost:44000/api/webhooks/dashboard/escalations?status=pending"
```

**Dashboard Backend Tests** (Port 42000):
```bash
# Health check
curl http://localhost:42000/health

# Get escalations via proxy
curl http://localhost:42000/api/dashboard/escalations

# Check CORS
curl -i http://localhost:42000/api/dashboard/escalations
```

**Frontend Tests** (Port 41001):
1. Open http://localhost:41001
2. Check browser console for errors (F12)
3. Verify escalations display
4. Test filtering
5. Create new escalation (via curl)
6. Wait 10 seconds
7. Verify new escalation appears (no manual refresh)

**ElevenLabs Integration Tests**:
1. Start ngrok tunnel
2. Update webhook URL in ElevenLabs
3. Test call to agent
4. Trigger escalation
5. Verify webhook received
6. Check dashboard updates

---

## TROUBLESHOOTING GUIDE

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'models.calls'`

**Solution**:
```bash
cd /Users/jason/Projects/addi_demo/addi_backend
source ../venv/bin/activate
python3 -c "from models.calls import EscalationSummary"
```

**Problem**: Backend won't start on port 44000

**Solution**:
```bash
# Find process using port
lsof -i :44000

# Kill it
kill -9 [PID]

# Restart
python3 main.py
```

**Problem**: `escalations_db` is empty

**Solution**: Create test escalation via POST /escalation/create

---

### Dashboard Backend Issues

**Problem**: CORS errors in browser console

**Solution**: Verify CORS includes port 41001:
```python
allow_origins=["http://localhost:41000", "http://localhost:41001", "http://localhost:3000"]
```

**Problem**: Proxy timeout

**Solution**: Backend (44000) not running - start it

---

### Frontend Issues

**Problem**: TypeScript errors on EscalationCard

**Solution**: Check interface definitions match backend model

**Problem**: "Cannot read property 'map' of undefined"

**Solution**: Add fallback in component:
```typescript
{escalations?.map(...) || <EmptyState />}
```

**Problem**: No data appearing

**Solution**:
1. Check SWR is fetching (Network tab in DevTools)
2. Verify API endpoint returns data (curl test)
3. Check for console errors

---

### ElevenLabs Issues

**Problem**: Tool not being called by agent

**Solution**:
1. Tool description not directive enough → Add "**CRITICAL TOOL**"
2. Too many required fields → Mark only name+email as required
3. Parameters in wrong location → Move ALL to `request_body_schema`

**Problem**: 401 Authorization failed

**Solution**: API key mismatch
```bash
# Check backend .env
cat /Users/jason/Projects/addi_demo/addi_backend/.env | grep ELEVENLABS_API_KEY

# Compare with ElevenLabs tool config header
```

**Problem**: ngrok tunnel expired

**Solution**:
```bash
cd /Users/jason/Projects/addi_demo/addi_backend
./scripts/setup_ngrok.sh

# Update URL in ElevenLabs tools
```

---

### Render Deployment Issues

**Problem**: `ERROR: ResolutionImpossible` - Dependency conflict during Render build

**Solution**:
1. **Check version compatibility** between related packages (e.g., `pydantic` and `pydantic-settings`)
2. **Update to compatible versions**:
   ```bash
   # Check available versions
   pip index versions pydantic-settings
   
   # Update requirements.txt with compatible version
   # Example: pydantic==2.12.3 requires pydantic-settings>=2.7.0
   ```
3. **Verify root requirements.txt**: Render uses `requirements.txt` in repository root (not subdirectories)
4. **Commit and push**: Render automatically deploys from `main` branch

**Problem**: `ModuleNotFoundError: No module named 'cachetools'` (or other missing dependencies)

**Solution**:
1. **Identify missing dependency**: Check import statements in code
2. **Add to root requirements.txt**: Ensure all dependencies are listed
3. **Check related packages**: Some packages require others (e.g., `pydantic-settings` requires `pydantic`)
4. **Common missing packages**:
   - `cachetools` (used by `rag_service.py`)
   - `tenacity` (used by `rag_service.py`)
   - `pydantic-settings` (used by `config.py`)
   - `google-generativeai` (used by `topic_analyzer.py`)

**Problem**: Build succeeds but runtime fails with import errors

**Solution**:
1. **Verify correct requirements.txt**: Render uses root `requirements.txt`, not `addi_backend/requirements.txt`
2. **Check Python version**: Ensure `render.yaml` specifies correct Python version
3. **Verify all imports**: Check that all imported modules are in `requirements.txt`

**Render Deployment Checklist**:
- [ ] All dependencies in root `requirements.txt`
- [ ] Version compatibility checked (especially related packages like `pydantic`/`pydantic-settings`)
- [ ] No version conflicts between packages
- [ ] `render.yaml` specifies correct Python version
- [ ] Monitor Render logs after push

**Reference**: See `Sessions/2026/JAN/2026-01-07_Render_Deployment_Dependency_Fix.md` for detailed troubleshooting steps

---

## SUCCESS CRITERIA

Dashboard is COMPLETE when all of these work:

**Backend** ✅:
- [ ] EscalationSummary model defined
- [ ] GET /dashboard/escalations endpoint works
- [ ] Priority calculation correct (urgent >24h, high >12h, medium else)
- [ ] Filtering by status works
- [ ] Pagination works

**Dashboard Backend** ✅:
- [ ] Proxy endpoint works
- [ ] CORS configured for port 41001
- [ ] No timeout errors

**Frontend** ✅:
- [ ] EscalationCard displays correctly
- [ ] EscalationList shows all escalations
- [ ] EscalationStatCard shows counts
- [ ] Real-time polling works (10s interval)
- [ ] No TypeScript errors
- [ ] No console errors

**Integration** ✅:
- [ ] ElevenLabs tool calls webhook
- [ ] Backend creates escalation
- [ ] Dashboard shows escalation within 10 seconds
- [ ] Priority badges correct colors
- [ ] Status badges work
- [ ] Filtering works
- [ ] Post-call webhook logs interaction

**End-to-End** ✅:
- [ ] Call agent → trigger escalation → appears on dashboard
- [ ] No manual refresh needed
- [ ] Conversation ID links to interaction
- [ ] Student info displays correctly

---

## ELEVENLABS TOOL CONFIGURATION REFERENCE

### Server Tool: escalate_to_human

**CRITICAL Configuration Requirements** (from WEBHOOK_TOOL_CONFIGURATION_LESSONS.md):

#### 1. Tool Description Template
```
**CRITICAL TOOL**: Immediately use this tool when:
(1) [specific trigger phrase]
(2) [specific scenario]
(3) [specific condition]
ALWAYS ask for [required_field_1] and [required_field_2] before calling this tool.
```

**Example**:
```
**CRITICAL TOOL**: Immediately use this tool when: (1) student explicitly asks to speak with a human/counselor/admissions advisor, (2) student says 'I want to talk to someone', (3) you cannot fully answer their question, (4) student needs personalized admissions guidance, (5) conversation requires human expertise. ALWAYS ask for student_name and student_email before calling this tool.
```

#### 2. Parameter Location (POST with JSON)
```json
{
  "query_params_schema": [],  // ← EMPTY for POST
  "request_body_schema": {
    "properties": [
      // ← ALL parameters go here
    ]
  }
}
```

#### 3. Required Fields Strategy
- Minimize required fields to reduce friction
- Only mark fields as `required: true` if tool will fail without them
- Use dynamic variables for auto-populated data

**Recommended**:
```json
{
  "student_name": {"required": true},
  "student_email": {"required": true},
  "inquiry_topic": {"required": false},
  "best_time_to_call": {"required": false},
  "student_phone": {"required": false, "value_type": "dynamic_variable", "dynamic_variable": "system__caller_id"},
  "conversation_id": {"required": false, "value_type": "dynamic_variable", "dynamic_variable": "system__conversation_id"}
}
```

#### 4. Dynamic Variables
- `system__conversation_id` → Auto-populate conversation ID
- `system__caller_id` → Auto-populate phone number
- Custom variables → Agent-specific data

**Configuration**:
```json
{
  "id": "conversation_id",
  "type": "string",
  "value_type": "dynamic_variable",
  "dynamic_variable": "system__conversation_id",
  "required": false
}
```

#### 5. Headers
```json
{
  "request_headers": [
    {
      "type": "secret",
      "name": "Authorization",
      "secret_id": "[YOUR_SECRET_ID]"
    },
    {
      "type": "value",
      "name": "Content-Type",
      "value": "application/json"
    }
  ]
}
```

---

## POST-CALL WEBHOOK CONFIGURATION

**Reference**: POST_CALL_WEBHOOK_CONFIGURATION.md

### Configuration Steps

**Location**: ElevenLabs Dashboard → Settings → Settings → Post-Call Webhook

**Step 1: Create Webhook**

**Display Name**: `Log Interaction to Backend`

**Callback URL**: `https://[YOUR-NGROK-URL]/api/webhooks/interaction/log`

**Auth Method**: `HMAC` (ElevenLabs generates secret)

**Step 2: Configure Events**

**Webhook Events to Enable**:
- ✅ Transcript (conversation data)
- ⬜ Audio (optional - only if you need audio files)
- ⬜ Call Initiation Failures (optional)

### HMAC Verification (CRITICAL)

**Your backend MUST verify signatures**

**Webhook Secret** (generated by ElevenLabs): Save to `.env`
```bash
ELEVENLABS_WEBHOOK_SECRET=wsec_[your_secret_here]
```

**Backend Implementation** (already in webhooks.py):
```python
async def verify_elevenlabs_signature(
    request: Request,
    elevenlabs_signature: Optional[str] = Header(None, alias="ElevenLabs-Signature")
):
    webhook_secret = os.getenv('ELEVENLABS_WEBHOOK_SECRET')

    if not webhook_secret:
        logger.warning("ELEVENLABS_WEBHOOK_SECRET not configured")
        return True  # Development mode

    body = await request.body()
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(elevenlabs_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return True
```

**What ElevenLabs Sends**:
```
POST /api/webhooks/interaction/log
Headers:
  Content-Type: application/json
  ElevenLabs-Signature: [hmac_hash]

Body:
{
  "conversation_id": "conv_abc123",
  "agent_id": "agent_0301k84...",
  "transcript": [...],
  "duration": 120,
  "metadata": {...}
}
```

---

## AGENT WORKFLOWS (FUTURE ENHANCEMENT)

**Reference**: AGENT_WORKFLOWS_COMPLETE_GUIDE.md

ElevenLabs Agent Workflows provide visual workflow editor for multi-step conversations.

**Available Node Types**:
- **Subagent Nodes** - Different agents for different conversation stages
- **Dispatch Tool Nodes** - Force tool execution at specific points
- **Agent Transfer Nodes** - Hand off to specialized agents
- **Transfer to Number Nodes** - Connect to human via phone
- **End Call Nodes** - Graceful conversation termination

**Use Case for Addi**:
- **Routing Subagent** → Determines if general inquiry vs. application status
- **General Info Subagent** → Handles admissions questions, uses knowledge base
- **Status Check Subagent** → Handles application status, uses `check_student_status` tool
- **Escalation Dispatch** → Automatically escalates complex questions

**Future Implementation**: Create workflow in ElevenLabs dashboard after basic escalation system is working

---

## FINAL NOTES

### Session Continuity

**At each break**, update this document with:
1. **Progress Tracker** - Mark tasks complete, log time
2. **Issues Encountered** - Document problems and solutions
3. **Progress Log** - Note what worked, what didn't

### Knowledge Transfer

**Key Files for Next Session**:
- This roadmap (DASHBOARD_ROADMAP.md)
- ENHANCED_IMPLEMENTATION_PLAN.md (detailed code)
- WEBHOOK_TOOL_CONFIGURATION_LESSONS.md (tool config patterns)
- SESSION_10_HANDOFF.md (previous progress)

### Next Steps After Completion

1. **Add Update Actions** - Mark escalations as "In Progress" or "Resolved"
2. **Add Assignment** - Assign escalations to specific counselors
3. **Add Notes** - Internal notes on escalation cards
4. **Email Integration** - Auto-email counselor when assigned
5. **SMS Notifications** - Text student when escalation resolved
6. **Analytics** - Track escalation resolution time, volume trends

---

**🎯 GO HATTERS! Let's build this dashboard! 🎓**

---

## SESSION 12 UPDATES (October 25, 2025)

### **New Additions**

#### **UI/UX Professional Agent Created**
- **Location**: `/Users/jason/Documents/Vault AI/projects/vault-agent-hub/agents/UI_UX-Agent/`
- **Purpose**: Reusable agent for all UI/UX work
- **Status**: ✅ Ready for use

#### **Critical Issues Identified**
1. **🔴 Tunnel Down** - Dashboard cannot receive live data
   - Fix Required: Restart tunnel and update ElevenLabs URL
   - Documentation: `PRIORITY_ACTION_NOW.md`

2. **⚠️ Layout Issues** - Escalations buried at bottom
   - Fix Required: Reorder sections, add urgent alerts banner
   - Documentation: `UI_UX_AGENT_REVIEW_AND_ACTION_PLAN.md`

3. **⚠️ Table Styling** - Needs professional polish
   - Fix Required: Add priority indicators, hover effects, actions
   - Documentation: `UI_UX_AGENT_REVIEW_AND_ACTION_PLAN.md`

#### **New Priority Tasks**

**IMMEDIATE (Session 13)**:
1. [ ] **Fix tunnel** (5 min) - See `PRIORITY_ACTION_NOW.md`
2. [ ] Verify live data flow
3. [ ] Move escalations to top of page
4. [ ] Add urgent alerts banner
5. [ ] Polish table styling

**SHORT TERM**:
6. [ ] Real-time notifications
7. [ ] Email automation setup
8. [ ] User acceptance testing

#### **New Documents**
- `SESSION_12_UI_UX_REVIEW_SUMMARY.md` - Session summary
- `UI_UX_AGENT_REVIEW_AND_ACTION_PLAN.md` - Implementation plan
- `PRIORITY_ACTION_NOW.md` - Critical tunnel fix
- `UI_UX_AGENT_CREATED.md` - Agent documentation

#### **Roadmap Changes**
- Added UI improvements phase
- Added real-time notifications
- Added email/SMS automation planning
- Prioritized live data verification

### **Next Session Focus**
1. **Restart tunnel** and verify connection
2. **Implement UI improvements** (layout reorganization, table polish)
3. **Test with real ElevenLabs call**
4. **Plan automation** (email, SMS)

---

**Last Updated**: October 25, 2025
**Version**: 1.0
**Status**: Ready for Implementation
