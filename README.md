# README

## MSME Logistics — B2B Last-Mile Delivery Management

**App Name:** MSME Logistics (`msme_logistics`)
**Module:** Logistics
**Domain:** B2B Last-Mile Delivery / 3PL / Distribution (India)
**Required Apps:** Frappe v15, ERPNext v15
**Repository:** https://github.com/Pasha1234565/msme-logistics.git

---

## TABLE OF CONTENTS

1. [Application Overview](#1-application-overview)
2. [System Architecture](#2-system-architecture)
3. [Getting Started](#3-getting-started)
4. [The Day-to-Day Workflow, Step by Step](#4-the-day-to-day-workflow-step-by-step)
5. [Customer-Facing Order Tracking](#5-customer-facing-order-tracking)
6. [Route Optimization (Extensible Stub)](#6-route-optimization-extensible-stub)
7. [Reports](#7-reports)
8. [Workspace Navigation](#8-workspace-navigation)
9. [Scheduled Tasks & Automation](#9-scheduled-tasks--automation)
10. [Setup & Configuration (Fixtures)](#10-setup--configuration-fixtures)
11. [Demo Data](#11-demo-data)
12. [Troubleshooting](#12-troubleshooting)
13. [Appendix](#13-appendix)

---

## 1. APPLICATION OVERVIEW

### 1.1 Purpose
MSME Logistics is a Frappe/ERPNext application built for MSME (Micro, Small & Medium Enterprise) B2B logistics operators — 3PLs, distribution businesses, and in-house dispatch teams — who need to manage the full lifecycle of a last-mile delivery: from transporter onboarding and trip planning through real-time tracking, proof-of-delivery capture, SLA compliance monitoring, and cost reconciliation. It covers:

- **Transporter Management** — vehicle types, pincode-based service areas, SLA analytics
- **Delivery Trip Management** — multi-stop routing with a submittable, workflow-driven trip document
- **Proof of Delivery (POD)** — image + signature capture per stop, enforced before a trip can be marked Completed
- **Customer-Facing Order Tracking** — a public, no-login tracking portal with a rate-limited guest API
- **Trip Cost Reconciliation** — fuel cost and transporter payout reconciliation per trip
- **SLA & Cost Analytics** — dashboards and reports across transporters and service areas

### 1.2 Key Features
- **8 DocTypes** — 3 document/master DocTypes, 5 child tables
- **1 Submittable DocType** — Delivery Trip
- **1 Workflow** — Delivery Trip Workflow (Planned → Dispatched → In Transit → Completed → Reconciled)
- **2 Custom Roles** — Dispatch Manager, Driver
- **2 Scheduled Tasks** — daily overdue-trip check, weekly transporter SLA analytics
- **2 Public/Internal Web Surfaces** — Customer Order Tracking (`/track`), Delivery Status Page (`/app/delivery-status`)
- **3 Reports** — SLA compliance, cost per delivery, failed delivery rate by area
- **Guest Tracking API** — rate-limited, PII-free, exact-match lookup by tracking ID
- **Standard ERPNext Integration** — links to Supplier, Warehouse, Customer, and Delivery Note

---

## 2. SYSTEM ARCHITECTURE

### 2.1 Technology Stack
- **Framework:** Frappe v15 / ERPNext v15
- **Database:** MariaDB
- **Automated Tasks:** Frappe Scheduler (daily, weekly)
- **Optional Dependency:** External routing API (Google Directions / OSRM) for route optimization — stubbed, not required

### 2.2 DocType Structure

| # | DocType Name | Type | Card Section | Submittable |
|---|---------------|------|---------------|:-----------:|
| 1 | Transporter | Document | Master Data | ❌ |
| 2 | Transporter Vehicle Type | Child Table | — | ❌ |
| 3 | Transporter Service Area | Child Table | — | ❌ |
| 4 | Delivery Trip | Document | Transactions | ✅ |
| 5 | Delivery Stop | Child Table | — | ❌ |
| 6 | Delivery Status Log | Child Table | — | ❌ |
| 7 | Delivery Trip Delivery Note | Child Table | — | ❌ |
| 8 | Trip Cost Reconciliation | Document | Transactions | ❌ |

### 2.3 Naming Series Convention

| DocType | Prefix | Format |
|---|---|---|
| Transporter | — | By fieldname (`transporter_name`) |
| Delivery Trip | DT | `DT-.YYYY.-.####` |
| Trip Cost Reconciliation | TCR | `TCR-.YYYY.-.####` |
| Delivery Stop | — | Child table row (`name` = hash) |
| Delivery Status Log | — | Child table row (`name` = hash) |

### 2.4 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW OVERVIEW                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  🚛 TRANSPORTER SETUP                                                 │
│  ┌────────────┐   ┌──────────────────┐   ┌──────────────────┐        │
│  │ Transporter │──▶│ Vehicle Types    │   │ Service Areas     │       │
│  │ (+ Supplier)│   │ (capacity, rate) │   │ (pincode ranges)  │       │
│  └────────────┘    └──────────────────┘   └──────────────────┘        │
│                                                                        │
│  📦 DELIVERY TRIP LIFECYCLE                                           │
│  Planned ──▶ Dispatched ──▶ In Transit ──▶ Completed ──▶ Reconciled   │
│     │             │                            │              │      │
│     │       on submit:                   POD enforced   Trip Cost    │
│     │     Actual Dispatch Time            before this    Reconciliation│
│     ▼             Time recorded          transition is    (fuel cost, │
│  Delivery Stops                             allowed        payout)    │
│  (multi-stop, sequenced)                                              │
│                                                                        │
│  🔗 TRACKING & NOTIFICATIONS                                          │
│  Delivery Stop ──▶ Tracking ID (TRK-XXXXXXXX) ──▶ /track (public)     │
│        │                                          /app/delivery-status│
│        ▼                                            (internal)       │
│  Delivery Status Log (timeline per status change)                    │
│                                                                        │
│  📊 ANALYTICS                                                         │
│  Delivery Stop + Delivery Trip ──▶ SLA Compliance % (weekly job)      │
│  Trip Cost Reconciliation ──▶ Cost Per Delivery reports               │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. GETTING STARTED

### 3.1 Installation
```bash
# From the bench directory
bench get-app https://github.com/Pasha1234565/msme-logistics.git
bench --site your-site.com install-app msme_logistics
bench --site your-site.com migrate
```

### 3.2 Role Setup
Two roles are created automatically on the first migrate after install (via the `setup_workflow_notifications` patch):
1. **Dispatch Manager** — Full operational access: create/write/submit/amend/cancel Delivery Trips, full CRUD on Transporter and Trip Cost Reconciliation
2. **Driver** — Read/write access on Delivery Trip and Delivery Stop; no submit/amend/delete rights, no email/print/share

### 3.3 Initial Configuration
Before using the app day-to-day, set up your masters:
1. **Transporters** — every transporter/3PL you work with, including their Vehicle Types (capacity, rate per km) and Service Areas (pincode ranges)
2. **Default Transit Days** — set on each Transporter so ETA can be derived automatically when no manual date is set
3. **Warehouses** — ensure at least one non-group, non-disabled Warehouse exists as an Origin Warehouse option for trips

### 3.4 Scheduler
Make sure the scheduler is enabled so the daily and weekly automation jobs run:
```bash
bench --site your-site.com scheduler enable
```

---

## 4. THE DAY-TO-DAY WORKFLOW, STEP BY STEP

This is the sequence you'll follow for essentially every delivery trip. It's worth reading through once in full before you start using the app live.

### Step 1 — Register a Transporter

1. Go to **MSME → Master Data → Transporter**.
2. Click **+ Add Transporter**.
3. Fill in the **Transporter Name** (required, unique), and optionally link the **Supplier** record for accounting/payments.
4. Set **Status** (Active/Inactive).
5. In **Vehicle Types**, add one row per vehicle class the transporter operates — e.g. Tata Ace (750 kg, ₹12/km), Ashok Leyland (2000 kg, ₹18.50/km). Duplicate vehicle types are blocked on save.
6. In **Service Areas**, add pincode ranges (e.g. 110001 → 110099) the transporter covers. Overlapping ranges across rows are blocked on save.
7. Set **Default Transit Days** — used to derive an ETA when no manual delivery date is set on a stop.
8. Click **Save**.

> **Total Trips** and **SLA Compliance %** on this form are read-only — they're recalculated automatically by the weekly `weekly_update_transporter_analytics` job, not entered by hand.

### Step 2 — Create a Delivery Trip

1. Click the **New Delivery Trip** shortcut on the dashboard.
2. Choose the **Transporter**, enter the **Driver Name** and **Vehicle No**, and select the **Origin Warehouse**.
3. Set the **Trip Date** and **Planned Dispatch Date**.
4. In the **Delivery Stops** table, add a row per stop: **Sequence No**, **Customer**, **Address**, and optionally a **Delivery Window** (start/end time). Sequence numbers must be unique within the trip.
5. Optionally link existing ERPNext **Delivery Notes** in the **Linked Delivery Notes** table for accounting integration.
6. The trip starts life with **Trip Status = Planned**. Click **Save**, then **Submit** when the trip is confirmed.

**Behind the scenes:** on save, a unique customer-facing **Tracking ID** (`TRK-XXXXXXXX`) is generated for every new stop, and a system notification with the tracking link is sent to the Dispatch Manager. On submit, **Actual Dispatch Time** is recorded automatically.

### Step 3 — Update Stop Status In Transit

As the driver progresses through the route:

1. Open the Delivery Trip (or use the **Delivery Status** page for a focused, single-lookup view).
2. Update each stop's **Status**: Pending → Delivered / Failed / Rescheduled, and its **Current Location** label.
3. Click **Save**.

**Behind the scenes:** every status change is appended to that stop's **Delivery Status Log** with a timestamp, building the timeline customers see on the tracking portal. If a stop is marked **Failed**, a system notification is sent to the Dispatch Manager immediately.

### Step 4 — Capture Proof of Delivery (POD)

For each stop marked **Delivered**:

1. Open the stop row.
2. Upload the **POD Image** and, if available, capture the **POD Signature**.
3. **Actual Arrival Time** is set automatically the first time a stop's status becomes Delivered.

> **Enforced rule:** a trip cannot transition to **Completed** if any stop marked Delivered is missing its POD image. The system blocks the save and lists every stop that still needs a POD.

### Step 5 — Complete and Reconcile the Trip

1. Once all stops are resolved (Delivered/Failed/Rescheduled) and PODs are captured, move the trip to **Completed** via the workflow action.
2. Create a **Trip Cost Reconciliation** record, linking the **Delivery Trip**.
3. Enter the **Fuel Cost** and **Transporter Payout**. **Total Stops** and **Cost Per Stop** are computed automatically from the linked trip.
4. Move the trip to **Reconciled** once reconciliation is complete.

### 4.1 Trip Status Workflow

Delivery Trip status is governed by the **Delivery Trip Workflow**:

```
Planned ──(Dispatch Trip)──▶ Dispatched
Dispatched ──(Mark In Transit)──▶ In Transit
In Transit ──(Complete Trip)──▶ Completed
Completed ──(Reconcile Trip)──▶ Reconciled
```

All transitions after **Planned** require the **Dispatch Manager** role.

---

## 5. CUSTOMER-FACING ORDER TRACKING

### 5.1 Public Tracking Page (`/track`)
A public web page — no login required — where a customer enters their 12-character **Tracking ID** (`TRK-XXXXXXXX`) to see:
- A 4-step visual progress stepper: Shipped → In Transit → Out for Delivery → Delivered
- Color-coded badges for Failed and Rescheduled deliveries
- **Current Location** and **Estimated Delivery Date**
- A chronological tracking **timeline** (status, location, timestamp)

Linking directly to `/track?id=TRK-XXXXXXXX` prefills the tracking ID so customers see results immediately.

### 5.2 Guest Tracking API
The public page is backed by a whitelisted, guest-accessible API (`msme_logistics.api.tracking.track_order`):
- **Exact-match lookup only** — no wildcard or partial search
- **Rate-limited** to 10 requests/minute per IP
- Returns only a whitelisted field set — no customer name, address, phone, or transporter details are ever exposed
- Failed lookups are logged (tracking ID only, no PII) for abuse detection

### 5.3 Estimated Delivery Date Logic
`get_estimated_delivery` resolves an ETA with this priority:
1. A manually set **Estimated Delivery Date** on the stop itself
2. Otherwise, derived from the parent trip's **Trip Date** plus the transporter's **Default Transit Days**, prorated by the stop's position in the sequence

### 5.4 Delivery Status Page (Internal)
A dedicated Frappe **Page** at `/app/delivery-status` gives dispatch staff the same tracking lookup functionality from inside the ERP backend, for looking up any tracking ID without leaving the desk interface.

---

## 6. ROUTE OPTIMIZATION (EXTENSIBLE STUB)

`msme_logistics.logistics.api.optimize_route` is a ready-to-extend stub for external routing integration:
- Collects the origin warehouse address and every stop's address for a given trip
- Skips gracefully (with a message) if a trip has fewer than 3 stops
- Contains commented-out example code for calling the **Google Directions API** or a self-hosted **OSRM** instance, including how to apply the optimized waypoint order back onto each stop's `sequence_no`
- Falls back with an informative message when no routing API key is configured — the app functions normally without it

To activate: uncomment the API call block, add `google_maps_api_key` (or your OSRM endpoint) to `site_config.json`, and install the `requests` package if not already available.

---

## 7. REPORTS

| Report | Type | Based On | Purpose |
|---|---|---|---|
| SLA Compliance by Transporter | Script Report | Delivery Trip / Delivery Stop | On-time delivery compliance % per transporter, with bar chart |
| Cost Per Delivery by Transporter | Query Report | Trip Cost Reconciliation | Cost breakdown per trip with cost-per-stop analysis, with bar chart |
| Failed Delivery Rate by Area | Query Report | Delivery Stop | Failed/rescheduled deliveries with pincode extraction, with pie chart |

---

## 8. WORKSPACE NAVIGATION

**Shortcuts (top row):**
- 🚚 New Delivery Trip
- 📍 Delivery Status
- 👤 Transporter List
- 💰 Trip Cost Recon
- ⚠️ Failed Deliveries

**Key Metrics (number cards):**
- Trips In Transit Today
- Failed Deliveries This Week
- Avg Cost Per Stop

**Cards:**
- **Transactions** — Delivery Trip, Trip Cost Reconciliation
- **Master Data** — Transporter
- **Reports** — SLA Compliance, Cost Per Delivery, Failed Delivery Rate

**Charts:**
- **SLA Compliance by Transporter** — bar chart
- **Cost Per Delivery Trend** — bar chart

---

## 9. SCHEDULED TASKS & AUTOMATION

| Task | Frequency | What it does |
|---|---|---|
| `daily_check_overdue_trips` | Daily | Finds trips still in "Planned" status past their Planned Dispatch Date and raises a "Trip Not Dispatched" notification, including days overdue |
| `weekly_update_transporter_analytics` | Weekly | Recalculates each active Transporter's **Total Trips** and **SLA Compliance %** (share of Delivered stops that arrived within their delivery window) |

Automatic (event-driven), not scheduled:

| Trigger | What happens |
|---|---|
| Delivery Trip submitted | **Actual Dispatch Time** recorded |
| Stop status changes to Delivered | **Actual Arrival Time** auto-set; entry appended to Delivery Status Log |
| Any stop status change | Delivery Status Log entry created |
| Stop status changes to Failed | System notification sent to Dispatch Manager |
| New stop added with a tracking ID | System notification with tracking link sent to Dispatch Manager |

> Make sure the scheduler is enabled on your site: `bench --site your-site.com scheduler enable`

---

## 10. SETUP & CONFIGURATION (FIXTURES)

The following are set up automatically post-install/migrate (via `pre_model_sync` / `post_model_sync` patches):

- **Module Def** — "Logistics" module registered against the app
- **Roles** — Dispatch Manager, Driver
- **Workflow** — Delivery Trip Workflow, with its 5 states and 4 transitions
- **Notifications** — Delivery Failed Alert (system), Trip Not Dispatched Alert (system, 1 day after planned dispatch)
- **Workspace** — MSME workspace with shortcuts, number cards, and charts
- **Dashboard Charts** — created via `create_dashboard_charts` patch

Standard Frappe fixtures (Workspace, DocType, Report, Workflow, Workflow State, Workflow Action, Role, Notification — all filtered to this app's module) are also exported for redeployment across sites.

---

## 11. DEMO DATA

Demo data is seeded automatically on install (via the `seed_demo_data` post-model-sync patch), and can be re-triggered manually:

```bash
bench --site your-site.com execute msme_logistics.patches.insert_demo_data.execute.execute
```

This creates sample **Transporters** (FastTrack Logistics, CityExpress Couriers, SafeHands Transport) with vehicle types and service areas, along with sample **Delivery Trips** in various statuses — enough to explore every workflow above without manual data entry.

To validate the customer order tracking feature end-to-end (tracking ID generation, status log entries, ETA calculation, guest API output, and PII-leak checks), run:

```bash
bench --site your-site.com execute msme_logistics.patches.order_tracking_test.execute
```

---

## 12. TROUBLESHOOTING

| Issue | Cause | Solution |
|---|---|---|
| App not found during install | App not in `apps.txt` | `echo "msme_logistics" >> sites/apps.txt` |
| `(1054, "Unknown column 'parent' in WHERE")` on a child table | Schema sync didn't create standard child-table columns | Handled automatically post-migrate and on first request; to force it manually run `bench --site your-site.com execute msme_logistics.patches.fix_child_table_parent_columns.execute` |
| Delivery Trip Workflow / custom roles missing | Patch didn't run (e.g. fresh site restored from backup) | `bench --site your-site.com execute msme_logistics.patches.setup_workflow_notifications.execute` |
| MSME workspace or dashboard charts missing | Workspace/chart creation was skipped | `bench --site your-site.com execute msme_logistics.patches.create_msme_workspace.execute` and `msme_logistics.patches.create_dashboard_charts.execute` |
| Scheduled tasks not running | Scheduler disabled | `bench --site your-site.com scheduler enable` |
| Trip won't move to Completed | A Delivered stop is missing its POD image | Upload a POD image for every stop listed in the error message, then retry |
| `/track` page shows "not found" for a valid-looking ID | Tracking ID typo, or extra whitespace/case mismatch | The lookup uppercases and trims automatically; double-check the ID matches the `TRK-XXXXXXXX` format exactly (12 characters) |
| Guest API returns rate-limit error | More than 10 requests/minute from the same IP | Wait 60 seconds; if this happens legitimately at scale, review the `rate_limit` decorator in `api/tracking.py` |
| Fixture data not loading | Fixtures not synced | `bench --site your-site.com migrate` |

---

## 13. APPENDIX

### A. Role Permissions

| Role | Delivery Trip | Transporter | Trip Cost Reconciliation | Delivery Stop | Submit/Amend/Cancel |
|---|:---:|:---:|:---:|:---:|:---:|
| Dispatch Manager | Full CRUD | Full CRUD | Full CRUD | Full CRUD | ✅ |
| Driver | Read/Write | Read | — | Read/Write | ❌ |
| System Manager | Full CRUD | Full CRUD | Full CRUD | Full CRUD | ✅ |
| All (guest, via API) | — | — | — | Read-only, whitelisted fields via `track_order` | ❌ |

### B. Key DocType Field Reference

#### Delivery Trip
| Field | Type | Notes |
|---|---|---|
| Transporter | Link → Transporter | Required |
| Driver Name / Vehicle No | Data | Required |
| Origin Warehouse | Link → Warehouse | Required |
| Total Distance (km) | Float | Estimated or actual |
| Delivery Stops | Table → Delivery Stop | At least one stop required to submit; sequence numbers must be unique |
| Linked Delivery Notes | Table → Delivery Trip Delivery Note | Links to standard ERPNext Delivery Notes |
| Trip Status | Select | Planned / Dispatched / In Transit / Completed / Reconciled, driven by the Workflow; read-only field |
| Trip Date / Planned Dispatch Date | Date | Required |
| Actual Dispatch Time / Completed Time | Datetime | Read-only, auto-populated |
| Amended From | Link → Delivery Trip | Read-only, standard amendment field |

#### Delivery Stop (child table)
| Field | Type | Notes |
|---|---|---|
| Sequence No | Int | Required; must be unique within the trip |
| Customer | Link → Customer | Required |
| Delivery Window Start / End | Time | Optional, used for SLA on-time calculation |
| Status | Select | Pending / Delivered / Failed / Rescheduled |
| Tracking ID | Data | Auto-generated (`TRK-XXXXXXXX`), unique, collision-checked |
| Estimated Delivery Date | Date | Manual override; otherwise derived |
| Current Location Label | Data | Free-text, shown on the tracking portal |
| POD Image / POD Signature | Attach / Signature | Required for Delivered stops before trip can be Completed |
| Delivery Status Logs | Table → Delivery Status Log | Auto-appended on every status change |

#### Transporter
| Field | Type | Notes |
|---|---|---|
| Transporter Name | Data | Required, unique (used for naming) |
| Supplier | Link → Supplier | Optional, for accounting/payments |
| Status | Select | Active / Inactive |
| Vehicle Types | Table → Transporter Vehicle Type | No duplicate vehicle types allowed |
| Service Areas | Table → Transporter Service Area | Pincode ranges; overlaps blocked |
| Default Transit Days | Float | Used for derived ETA calculation |
| Total Trips / SLA Compliance % | Int / Percent | Read-only, updated weekly |

### C. Related Documents
- Frappe Framework Documentation: https://frappeframework.com/docs
- ERPNext Documentation: https://docs.erpnext.com
- Google Directions API (optional route optimization): https://developers.google.com/maps/documentation/directions
- OSRM (optional, self-hosted route optimization): https://project-osrm.org/

### D. Repository
- **Repository:** https://github.com/Pasha1234565/msme-logistics.git

---

*End of README*
