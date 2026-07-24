# 🧵 Textile Tracking & Job Work Management

A comprehensive **Frappe/ERPNext** application for textile and garment manufacturers to manage end-to-end **job work operations**, contractor management, fabric traceability, cutting optimization, and wastage analytics. Built for textile mills, garment manufacturers, and production houses.

## 📋 Overview

This application provides a complete digital solution for managing the lifecycle of textile production sent to external contractors — from raw material procurement and fabric roll tracking through job work orders, cutting plans, production scheduling, and wastage analysis. It includes robust reporting, a Digital Product Passport for EU 2027 compliance, a factory floor dashboard, and a supplier collaboration portal.

> 🔄 **Context**: This application was purpose-built for the textile and garment manufacturing industry, covering the full subcontracting workflow from raw material batch to finished fabric roll with full traceability.

---

## ✨ Features

### 🏭 Contractor Management
- Register and manage **Job Contractors** with detailed profiles and rate cards
- Categorize contractors by process type (Cutting, Stitching, Dyeing, Embroidery, Finishing)
- Track contractor wastage analytics with auto-calculated aggregates
- Rate card management with per-process pricing and effective dates

### 📦 Job Work Orders
- Create full **Job Work Orders** with multi-process tracking
- Per-process contractor assignment, dates, and status tracking
- Workflow-driven status (Draft → Sent → Partially Received → Received → Closed)
- Automatic Stock Entry creation for material transfer and receipt (ERPNext integration)
- Auto-populate processes based on garment type (Shirt, T-Shirt, Saree, Kurta, etc.)
- Garment-type-specific process mapping (10 garment types supported)

### ♻️ Fabric Wastage Management
- **Fabric Wastage Log** with detailed cause categorization
- Wastage categories: Cutting Loss, Contractor Damage, Transit Damage, Quality Reject
- Real-time wastage percentage calculation
- High-wastage alerts (>15%) with system notifications
- Contractor-wise aggregated wastage analytics

### 🧶 Raw Material Traceability
- **Raw Material Batch** tracking with full origin details
- Supplier batch number and country of origin tracking
- Certification tracking (GOTS, OEKO-TEX, BCI, Fair Trade, Organic)
- Storage location management with handling instructions
- Trace forward to Fabric Rolls and Job Work Orders

### 📜 Fabric Roll Management
- Track fabric rolls with measurements, grade, and quality status
- **Digital Product Passport** (EU 2027 compliant) with QR code generation
- Daily production tracking per roll
- Garment production estimates (fabric requirement per garment type/size)
- Wastage percentage calculation from estimated vs actual production
- Process history with chronological manufacturing timeline

### ✂️ Cutting Optimization
- **Pattern Templates** with piece definitions and dimensions
- **Cutting Plans** linked to fabric rolls
- Estimated waste percentage per plan
- Layout preview support for cutting optimization

### 🏗️ Production Scheduling
- **Production Schedule** with shift-based planning (Morning, Evening, Night)
- Machine allocation to production items
- Target meters and time-based scheduling
- Status tracking (Draft → Planned → In Progress → Completed → Cancelled)

### 🏭 Factory Floor Dashboard
- Real-time loom/machine status visualization
- Summary stats (Running, Idle, Down/Maintenance counts)
- Per-machine metrics: meters produced today, RPM, efficiency, defect count
- Today's production schedule overview
- Responsive card-based UI with color-coded status indicators

### 🔗 Supplier Collaboration Portal
- Web-based portal for external suppliers
- View and update delivery schedules
- Revise delivery dates and status (Confirmed, Delayed, Shipped)
- Stats dashboard (total deliveries, pending updates)
- Secure login integration with Frappe authentication

### 📊 Reports (5)

| Report | Type | Description |
|--------|------|-------------|
| **Contractor Wastage Trend** | Query + Script | Wastage % trends per contractor over time with line chart |
| **True Cost Per Piece by Contractor** | Script | Calculates real cost including labor + wastage cost with bar chart |
| **Overdue Job Work Orders** | Query | All orders past expected return date, grouped by contractor |
| **Cutting Efficiency** | Script | Cutting plan analysis with fabric usage, waste %, and bar chart |
| **Lot Genealogy** | Script | Complete traceability tree from raw material batch to fabric rolls |

### 🔔 Notifications & Automation
- Daily contractor wastage stats update (scheduler)
- Daily overdue job work order alerts (system notifications)
- Rate card expiry review reminders (90+ days stale)
- High wastage alerts (>15%) on Fabric Wastage Log submission
- Workflow-based status transitions on Job Work Orders

### 🔒 Role-Based Access Control

| Role | Access Level |
|------|-------------|
| **System Manager** | Full administrative access |
| **Job Work Manager** | Full CRUD on all doctypes, submit/amend/cancel, rate card visibility |
| **Contractor Coordinator** | Create and read access, no delete, no rate card visibility |

---

## 🏗️ DocTypes (18 Total)

The application includes **18 DocTypes** organized into Master Data, Transactions, and Child Tables.

### Master Data (6)

| DocType | Purpose |
|---------|---------|
| **Job Contractor** | External contractors performing textile processes |
| **Loom** | Factory floor machines with status and performance metrics |
| **Raw Material Batch** | Incoming raw material with certification and origin tracking |
| **Fabric Roll** | Finished fabric rolls with measurements and quality grading |
| **Pattern Template** | Cutting pattern definitions with piece dimensions |
| **Machine Output Log** | Per-shift machine production logging |

### Transaction DocTypes (5)

| DocType | Purpose |
|---------|---------|
| **Job Work Order** | Core transaction — fabric sent for processing (submittable) |
| **Fabric Wastage Log** | Wastage recording with category and cause tracking |
| **Cutting Plan** | Cutting layout planning linked to fabric rolls (submittable) |
| **Production Schedule** | Shift-based production planning (submittable) |
| **Vendor Delivery Schedule** | Supplier delivery tracking (submittable) |

### Child Tables (7)

| DocType | Parent | Purpose |
|---------|--------|---------|
| **Contractor Rate Item** | Job Contractor | Per-process rates with effective dates |
| **Job Work Order Process** | Job Work Order | Multi-process tracking per order |
| **Job Work Return** | Job Work Order | Return receipts with wastage logging |
| **Cutting Plan Item** | Cutting Plan | Pattern pieces in cutting layout |
| **Pattern Piece** | Pattern Template | Individual piece dimensions and quantities |
| **Fabric Roll Daily Production** | Fabric Roll | Daily garment production entries |
| **Process History Entry** | Fabric Roll | Chronological manufacturing timeline |

---

## 🚀 Installation

### Prerequisites
- **Frappe v15+** installed and configured
- **ERPNext v15+** installed (for stock integration)
- Python 3.10+

### Step-by-Step Installation

```bash
# 1. Navigate to your Frappe bench directory
cd ~/frappe-bench

# 2. Get the app (use --skip-assets for Frappe v15 to avoid esbuild ordering issues)
bench get-app --skip-assets https://github.com/Pasha1234565/textile_tracking.git

# 3. Install the app on your site
bench --site your-site.local install-app textile_tracking

# 4. Build assets after installation
bench build

# 5. Run migration to sync everything
bench --site your-site.local migrate

# 6. Clear cache
bench --site your-site.local clear-cache
```

> **Note for Frappe v15 users**: If you encounter an esbuild error during `bench get-app`, use the `--skip-assets` flag. This is a known Frappe v15 interaction where the asset build runs before the app is registered in `apps.txt`.

### Quick Start (After Installation)

1. Log in to your Frappe site as **Administrator**
2. Navigate to the **Textile Tracking** workspace
3. Start by adding **Job Contractors** with rate cards
4. Create a **Job Work Order** and send fabric for processing
5. Log returns and wastage when received
6. Track contractor performance via **Reports**

### Insert Demo Data

```bash
# Via CLI command
bench --site your-site.local insert-demo-data

# Or via bench console
bench --site your-site.local console
```

```python
exec(open("../apps/textile_tracking/textile_tracking/commands.py").read())
insert_demo_data()
```

---

## ⚙️ Configuration

### Site Configuration

Ensure your site's `site_config.json` includes:
```json
{
  "host_name": "http://your-domain:8000"
}
```

### Stock Integration

For automatic Stock Entry creation on Job Work Orders:
1. Go to **Stock Settings**
2. Enable **Allow Material Transfer to Subcontractor**
3. Set your **Default Warehouse**

---

## 🌐 Web Portals

### Digital Product Passport (`/dpp/<roll_id>`)
- EU 2027-compliant fabric lifecycle page
- Full traceability: raw material → production → finished roll
- QR code generation for physical roll verification
- Process timeline visualization
- Certification badges (GOTS, OEKO-TEX, Fair Trade)
- Publicly accessible with no login required

### Factory Floor Dashboard (`/loom-dashboard`)
- Real-time machine status monitoring
- Summary stats: running, idle, down/maintenance counts
- Per-machine metrics with color-coded cards
- Today's production schedule display
- Responsive design for shop floor displays

### Supplier Collaboration Portal (`/supplier-portal`)
- Secure login with Frappe authentication
- Delivery schedule overview per supplier
- Inline date/status updates
- Stats dashboard for quick reference
- Designed for external supplier use

---

## 🛠️ Development

### Setting Up for Development

```bash
# Get the app in developer mode
bench get-app --skip-assets https://github.com/Pasha1234565/textile_tracking.git

# Set developer mode
bench --site your-site.local set-config developer_mode 1

# Install for development
bench --site your-site.local install-app textile_tracking

# Watch for changes (auto-builds assets)
bench watch
```

### Project Structure

```
textile_tracking/
├── hooks.py                       # App hooks, fixtures, scheduler, before_request
├── modules.txt                    # Module registration
├── patches.txt                    # Migration patch sequence
├── patches/                       # Migration patches (5 total)
├── commands.py                    # CLI commands for demo data
├── textile/                       # Main module directory
│   ├── api.py                     # Stock transfer/receipt creation
│   ├── tasks.py                   # Scheduled background jobs (3 daily tasks)
│   ├── doctype/                   # All 18 DocType definitions
│   ├── report/                    # 5 Report definitions
│   └── workspace/                 # Workspace configuration
└── www/                           # Web pages (3 portals)
    ├── dpp.html + dpp.py          # Digital Product Passport
    ├── loom_dashboard.html + .py  # Factory Floor Dashboard
    └── supplier_portal.html + .py # Supplier Collaboration Portal
```

### Garment Process Mapping

The app auto-populates processes based on garment type:

| Garment Type | Processes |
|-------------|-----------|
| Shirt | Cutting → Stitching → Finishing |
| T-Shirt | Cutting → Stitching → Finishing |
| Saree | Cutting → Stitching → Dyeing → Embroidery → Finishing |
| Jeans | Cutting → Stitching → Dyeing → Finishing |
| Kurta | Cutting → Stitching → Finishing |
| Dupatta | Cutting → Dyeing → Finishing |
| Fabrics (Roll) | Dyeing → Finishing |
| Dress | Cutting → Stitching → Embroidery → Finishing |

---

## 📊 Feature Details

### True Cost Per Piece Calculation

The True Cost Per Piece report factors in hidden waste costs:

```python
True Cost = (Labor Cost + Wastage Cost) / Qty Received

Labor Cost    = Rate Per Piece × Qty Received
Wastage Cost  = Wastage Qty × Raw Material Valuation Rate
```

### Fabric Requirement Estimates

Built-in fabric consumption database for 8 garment types × 5 sizes (S-XXL):

```
Shirt Size M:  1.4 meters per garment
T-Shirt Size L: 1.2 meters per garment
Saree: 5.5 meters (all sizes)
```

### Workflow States & Transitions

```
Draft ──[Send to Contractor]──▶ Sent
Sent  ──[Partial Return]──────▶ Partially Received
Sent  ──[Full Return]─────────▶ Received
Partially Received ──[Partial Return]──▶ Partially Received
Partially Received ──[Full Return]─────▶ Received
Received ──[Close Order]──────▶ Closed
```

---

## 🔧 Troubleshooting

### Common Issues Quick Reference

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| `LinkValidationError` during install | Roles missing | Re-run `install-app` |
| Child table missing columns (`parent`, `parenttype`, `parentfield`) | Incomplete migration | Run `bench migrate` twice |
| Reports show blank page | Module Def missing | Run `bench migrate` |
| Controller resolution error | Stale DocType records | Re-install the app |
| Workspace blocks broken | Socket.IO disconnected | Clear cache, restart bench |
| Stock Entry not created | Stock Settings not configured | Enable subcontractor transfer |

### Child Table Fix

If child tables are missing parent columns, the app automatically fixes this via:
- `before_request` hook (on first HTTP request)
- `after_migrate` hook (during every `bench migrate`)

### Manual Child Table Repair

```python
frappe.db.sql("ALTER TABLE `tabContractor Rate Item` ADD COLUMN `parent` varchar(255) DEFAULT NULL")
frappe.db.sql("ALTER TABLE `tabContractor Rate Item` ADD COLUMN `parenttype` varchar(255) DEFAULT NULL")
frappe.db.sql("ALTER TABLE `tabContractor Rate Item` ADD COLUMN `parentfield` varchar(255) DEFAULT NULL")
```

---

## 🍃 Design History

| Concept | Implementation |
|---------|---------------|
| Multi-process JWO | Each Job Work Order has a child table of processes, each with its own contractor, dates, and status |
| Garment-specific workflows | Process mapping per garment type auto-populates the processes table |
| Digital Product Passport | Public web page with QR code, process timeline, and full traceability |
| True Cost Analytics | Factors in raw material cost of wastage to reveal hidden costs per contractor |

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

- **Email**: info@example.com
- **Issues**: [GitHub Issues](https://github.com/Pasha1234565/textile_tracking/issues)

---

<p align="center">
  Built with ❤️ for textile manufacturers, one stitch at a time.
</p>
