# 🚚 MSME Logistics — B2B Last-Mile Delivery Management

A comprehensive **Frappe/ERPNext** application for **MSME (Micro, Small & Medium Enterprise) B2B logistics operators** to manage last-mile delivery operations, transporter management, delivery trip tracking, SLA compliance monitoring, and cost reconciliation. Built for logistics companies, 3PL operators, and distribution businesses.

## 📋 Overview

This application provides a complete digital solution for managing the lifecycle of B2B last-mile deliveries — from transporter registration and trip planning through real-time tracking, proof-of-delivery capture, SLA compliance monitoring, and cost reconciliation. It includes robust reporting, a customer-facing order tracking portal, and automated notifications.

> 🔄 **Context**: This application was purpose-built for MSME logistics operators in the Indian market, covering the full delivery management workflow from dispatch planning to cost reconciliation with full trip traceability.

---

## ✨ Features

### 🚛 Transporter Management
- Register and manage **Transporters** with detailed profiles
- Define **Vehicle Types** per transporter with capacity (kg) and rate per km
- Configure **Service Areas** using pincode ranges (pincode_from → pincode_to)
- Auto-calculated **SLA Compliance %** and **Total Trips** analytics (updated weekly)
- Link to ERPNext **Supplier** master for accounting and payments
- Configure **Default Transit Days** for ETA estimation
- Validation: overlapping service area detection, duplicate vehicle type prevention

### 📦 Delivery Trip Management
- Create **Delivery Trips** with multi-stop routing
- Workflow-driven status: **Planned → Dispatched → In Transit → Completed → Reconciled**
- Assign transporters, drivers, and vehicles per trip
- Set per-stop **Delivery Windows** (time ranges with start/end)
- Capture **Proof of Delivery (POD)** — image upload + signature per stop
- Auto-record **Actual Dispatch Time** on submit
- Auto-set **Actual Arrival Time** when stop status changes to Delivered
- **POD enforcement**: Block completion if any delivered stop is missing POD image
- Link to standard ERPNext **Delivery Notes** for accounting integration

### 🔗 Customer-Facing Order Tracking
- Public **/track** web page — no login required
- Enter a 12-character tracking ID (**TRK-XXXXXXXX**) to see live status
- Visual **4-step progress stepper**: Shipped → In Transit → Out for Delivery → Delivered
- Color-coded failed delivery and rescheduled badges
- **Current location** and **Estimated Delivery Date** display
- Chronological **tracking timeline** with status, location, and timestamp
- Auto-generated tracking IDs (secure, unique, collision-resistant)
- **Rate-limited API** (10 req/min per IP) for abuse prevention
- ETA derived from trip date + transporter's default transit days (prorated by stop sequence)
- Logged failed lookups for security monitoring

### 💰 Trip Cost Reconciliation
- Reconcile fuel costs and transporter payouts per trip
- Auto-calculate **Total Stops** and **Cost Per Stop** from linked delivery trip
- Track reconciliation date and reconciling user
- Feeds into **Cost Per Delivery** analytics and reports

### 📊 Reports (3)

| Report | Type | Description | Chart |
|--------|------|-------------|-------|
| **SLA Compliance by Transporter** | Script Report | On-time delivery compliance per transporter with % calculation | Bar chart |
| **Cost Per Delivery by Transporter** | Query Report | Cost breakdown per trip with cost-per-stop analysis | Bar chart |
| **Failed Delivery Rate by Area** | Query Report | Failed/rescheduled deliveries with pincode extraction | Pie chart |

### 🔔 Notifications & Automation
- **Daily**: Overdue trip detection — alerts when trips remain in "Planned" past dispatch date
- **Weekly**: Transporter SLA analytics update — recalculates compliance % and trip counts
- **On Submit**: Auto-actual dispatch time recording
- **On Stop Update**: Auto-arrival time when status changes to Delivered
- **On Status Change**: Delivery Status Log entries appended for every stop status change
- **New Tracking ID**: System notification to Dispatch Manager when tracking IDs are generated
- **Failed Delivery**: System notification with trip and stop details

### 🏗️ Delivery Status Page (Internal)
- Dedicated Frappe **Page** (`/app/delivery-status`) for dispatch staff
- Same tracking functionality as the public portal, but within the ERP backend
- Allows dispatch managers to look up any tracking ID from the Frappe interface

### 🛣️ Route Optimization (Extensible)
- Built-in **stub** for external routing API integration (Google Directions / OSRM)
- Collects origin warehouse address and all stop addresses
- Ready-to-implement code structure — just uncomment and add API key
- Falls back gracefully with informative message when not configured

### 🔒 Role-Based Access Control

| Role | Delivery Trip | Transporter | Trip Cost Recon | Delivery Stop |
|------|:------------:|:----------:|:--------------:|:------------:|
| **System Manager** | Full CRUD + Submit/Amend/Cancel | Full CRUD | Full CRUD | Full CRUD |
| **Dispatch Manager** | Full CRUD + Submit/Amend/Cancel | Full CRUD | Full CRUD | Full CRUD |
| **Driver** | Read/Write | Read | — | Read/Write |
| **All** | — | Read | — | — |

---

## 🏗️ DocTypes (8 Total)

The application includes **8 DocTypes** organized into Master Data, Transactions, and Child Tables.

### Master Data (1)

| DocType | Purpose |
|---------|---------|
| **Transporter** | Logistics service providers with vehicle types, service areas, and SLA analytics |

### Transaction DocTypes (2)

| DocType | Purpose | Submittable |
|---------|---------|:-----------:|
| **Delivery Trip** | Core transaction — multi-stop delivery with workflow status | ✅ Yes |
| **Trip Cost Reconciliation** | Fuel cost and payout reconciliation per trip | ❌ No |

### Child Tables (5)

| DocType | Parent | Purpose |
|---------|--------|---------|
| **Delivery Stop** | Delivery Trip | Individual delivery stops with tracking, POD, and delivery window |
| **Delivery Trip Delivery Note** | Delivery Trip | Links to standard ERPNext Delivery Notes |
| **Delivery Status Log** | Delivery Stop | Chronological status change history with timestamps |
| **Transporter Vehicle Type** | Transporter | Vehicle definitions with capacity and rate per km |
| **Transporter Service Area** | Transporter | Pincode range-based service coverage areas |

---

## 🚀 Installation

### Prerequisites
- **Frappe v15+** installed and configured
- **ERPNext v15+** installed (for Delivery Note and Supplier linking)
- Python 3.10+

### Step-by-Step Installation

```bash
# 1. Navigate to your Frappe bench directory
cd ~/frappe-bench

# 2. Get the app
bench get-app https://github.com/your-org/msme_logistics.git

# 3. Install the app on your site
bench --site your-site.local install-app msme_logistics

# 4. Build assets
bench build

# 5. Run migration to sync everything
bench --site your-site.local migrate

# 6. Clear cache
bench --site your-site.local clear-cache
```

> **Note for Frappe v15 users**: If you encounter an esbuild error during `bench get-app`, use the `--skip-assets` flag.

### Quick Start (After Installation)

1. Log in to your Frappe site as **Administrator**
2. Navigate to the **MSME** workspace
3. Start by adding **Transporters** with vehicle types and service areas
4. Create a **Delivery Trip** and add delivery stops with tracking IDs
5. Update stop statuses as deliveries progress
6. Reconcile trip costs after completion
7. Share tracking IDs with customers for real-time visibility

### Insert Demo Data

```bash
# Via Frappe console
bench --site your-site.local console
```

```python
import msme_logistics.commands
msme_logistics.commands.insert_demo_data()
```

Or simply install the app — demo data is auto-inserted via the `after_install` hook.

---

## ⚙️ Configuration

### Site Configuration

No special site configuration is required. The app works out of the box with standard Frappe setup.

### Route Optimization (Optional)

For route optimization with Google Directions API, add to your `site_config.json`:
```json
{
  "google_maps_api_key": "YOUR_API_KEY_HERE"
}
```

Then update `msme_logistics/logistics/api.py` to uncomment the API call block.

---

## 🌐 Web Portal

### Order Tracking (`/track`)
- Public, customer-facing tracking page — no login required
- Enter tracking ID (**TRK-XXXXXXXX**) to view live delivery status
- Visual 4-step stepper with animated active/completed/failed states
- Current location and estimated delivery date display
- Full tracking timeline with chronological history
- Rate-limited API (10 requests/minute/IP)
- Shareable links: `/track?id=TRK-A7X9K2M1`

---

## 📊 Feature Details

### SLA Compliance Calculation

The SLA Compliance report compares `actual_arrival_time` against the `delivery_window_end`:

```
Within SLA = Yes  → TIME(actual_arrival_time) ≤ delivery_window_end
Within SLA = No   → TIME(actual_arrival_time) > delivery_window_end
Within SLA = N/A  → Not yet delivered or missing data
Delay (mins)     → Minutes past the delivery window end
```

### ETA Estimation Logic

The `get_estimated_delivery` API uses a two-priority approach:

```
Priority 1: Manually set `estimated_delivery_date` on the stop → Return as-is
Priority 2: Derive from trip date + transporter's default_transit_days
  → days_to_add = ceil(transit_days × (sequence_no / total_stops))
  → ETA = trip_date + days_to_add
```

### Cost Per Stop Calculation

Auto-calculated on the Trip Cost Reconciliation doctype:

```
Cost Per Stop = (Fuel Cost + Transporter Payout) / Total Stops
```

### Delivery Stop Statuses

| Status | Description |
|--------|-------------|
| **Pending** | Stop planned, not yet attempted |
| **Delivered** | Successfully delivered with POD captured |
| **Failed** | Delivery attempted but unsuccessful |
| **Rescheduled** | Delivery rescheduled to a later date |

### Workflow States & Transitions (Delivery Trip)

```
Planned ──[Dispatch]─────▶ Dispatched
Dispatched ──[Start Transit]──▶ In Transit
In Transit ──[Complete]───▶ Completed
Completed ──[Reconcile]───▶ Reconciled
```

---

## 🔧 Troubleshooting

### Common Issues Quick Reference

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| `LinkValidationError` during install | Roles missing | Re-run `install-app` |
| Child table missing columns | Incomplete migration | Run `bench migrate` twice |
| Reports show blank page | Module Def missing | Run `bench migrate` |
| Tracking page shows "No order found" | Invalid tracking ID format | Ensure ID format is `TRK-XXXXXXXX` |
| POD validation blocks completion | Missing POD image | Upload POD image before completing trip |
| Route optimization returns stub | API not configured | Add Google Maps API key and uncomment code |

### Child Table Fix

The app automatically fixes missing parent columns via:
- `before_request` hook (on first HTTP request)
- `after_migrate` hook (during every `bench migrate`)

---

## 🔔 Design Decisions

| Concept | Implementation |
|---------|---------------|
| Multi-stop trips | Each Delivery Trip has a child table of Delivery Stops with sequenced routing |
| Tracking IDs | Auto-generated `TRK-XXXXXXXX` format using `secrets` module with collision retry |
| SLA Enforcement | Per-stop delivery windows compared against actual arrival timestamps |
| POD Enforcement | Trip cannot transition to Completed if any Delivered stop is missing POD |
| ETA Estimation | Prorated by stop sequence across total transit days |
| Cost Modeling | Separate fuel cost and transporter payout fields for granular analysis |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 📬 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/msme_logistics/issues)

---

<p align="center">
  Built with ❤️ for MSME logistics operators, one delivery at a time.
</p>
