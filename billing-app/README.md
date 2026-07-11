# Shivam Engineering — Billing App

A mobile-first billing web app for **Shivam Engineering Concern**.

- **Frontend:** React + Vite + Tailwind (mobile-first) → deploy on GitHub Pages
- **Backend:** FastAPI + Motor (async MongoDB) → deploy on Render
- **Database:** MongoDB Atlas (free M0 tier)
- **PDF:** generated on the backend with ReportLab, a **pixel-exact** copy of the
  original `MUKTA 2.pdf` tax-invoice format.

Receivers (customers) and goods are **saved automatically** each time you bill, so
repeat invoices are fast. Every saved invoice is kept in **history** and can be
re-downloaded as a PDF at any time.

```
billing-app/
├─ backend/          FastAPI service (you run this)
│  ├─ app/
│  │  ├─ pdf/invoice_pdf.py   ← exact invoice layout (the format contract)
│  │  ├─ routers/             ← settings, receivers, goods, invoices
│  │  ├─ models.py  db.py  config.py  main.py
│  ├─ requirements.txt
│  └─ .env.example
└─ frontend/         React app (already installed & building)
   └─ src/pages/     NewInvoice, History, Receivers, Settings
```

---

## STEP 1 — Create a free MongoDB Atlas database

You only do this once. It gives you a `MONGODB_URI` connection string.

1. Go to **https://www.mongodb.com/cloud/atlas/register** and sign up (free, no card).
2. When asked to **Deploy a cluster**, choose the **M0 / Free** tier.
   - Provider: any (AWS is fine). Region: pick the one closest to you (e.g. Mumbai `ap-south-1`).
   - Cluster name: leave default (`Cluster0`). Click **Create Deployment**.
3. A **"Connect to Cluster0"** dialog pops up asking to create a database user:
   - Username: `billing_user` (or anything).
   - Password: click **Autogenerate** and **COPY IT** somewhere safe.
   - Click **Create Database User**.
4. **Network access** — in the left menu go to **Network Access → Add IP Address**:
   - For now click **"Allow access from anywhere"** (`0.0.0.0/0`) → **Confirm**.
     (Simplest for development. Render also needs this.)
5. Get the connection string — left menu **Database → Connect → Drivers**:
   - Driver: **Python**, version 3.12 or later.
   - Copy the string. It looks like:
     ```
     mongodb+srv://billing_user:<db_password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
     ```
   - Replace `<db_password>` with the password you copied in step 3.

Keep that final string — it goes into the backend `.env` next.

---

## STEP 2 — Run the backend (FastAPI)

Open a terminal in `billing-app/backend`. Run these commands (PowerShell on Windows):

```powershell
cd E:\jnandy9.github.io\billing-app\backend

# 1) create & activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
#   (if PowerShell blocks the script, run once:
#    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned  then re-activate)

# 2) install dependencies
pip install -r requirements.txt

# 3) create your .env from the template
copy .env.example .env
#   then open .env and paste your MONGODB_URI from STEP 1
```

Edit **`backend/.env`** so it has your real values:

```
MONGODB_URI=mongodb+srv://billing_user:YOURPASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=billing
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://jnandy9.github.io
```

Now start the server:

```powershell
uvicorn app.main:app --reload --port 8000
```

- Visit **http://localhost:8000/health** → should show `{"status":"ok"}`.
- Interactive API docs: **http://localhost:8000/docs**
- On first start it auto-creates the Shivam Engineering business profile (with the
  PNB + Canara bank details) in your database.

If it fails to start, it almost always means the `MONGODB_URI` is wrong or Network
Access isn't open — recheck STEP 1.

---

## STEP 3 — Run the frontend (React)

The frontend is already installed. In a **second** terminal:

```powershell
cd E:\jnandy9.github.io\billing-app\frontend
npm run dev
```

Open **http://localhost:5173** on your PC, or on your phone using your PC's LAN IP
(e.g. `http://192.168.1.5:5173`) while both are on the same Wi-Fi.

The frontend reads the backend URL from `frontend/.env.development`
(`VITE_API_URL=http://localhost:8000`). That's already set for local dev.

---

## Everyday use

1. **Business** tab → confirm/edit Shivam Engineering details & bank accounts (one time).
2. **New** tab → fill invoice no, pick or type the receiver, add goods, choose tax → **Save & generate PDF**.
   - The receiver and goods are remembered for next time.
   - The PDF opens in a new tab — identical to the `MUKTA 2.pdf` format.
3. **History** tab → re-download or delete any past invoice.
4. **Parties** tab → manage saved customers.

---

## Deploying later (summary — ask when you're ready)

- **Backend → Render:** New Web Service from the repo, root `billing-app/backend`,
  build `pip install -r requirements.txt`, start
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Add env vars `MONGODB_URI`,
  `MONGODB_DB`, `CORS_ORIGINS` (include `https://jnandy9.github.io`).
- **Frontend → GitHub Pages:** set `frontend/.env.production` →
  `VITE_API_URL=https://<your-render-service>.onrender.com`, run `npm run build`,
  publish the `dist/` folder (via a GitHub Action). We'll wire this up together.

---

## Matching the decorative business-name font (optional polish)

The original invoice prints "SHIVAM ENGINEERING CONCERN" in a heavy decorative
font. To reproduce it exactly, drop a `.ttf` of that font at
`backend/app/pdf/fonts/title.ttf` — the PDF picks it up automatically. Without it,
a clean bold font is used (everything else is already pixel-exact).
