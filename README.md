<div align="center">

# 🏛️ Startup Policy Intelligence Dashboard

An intelligent platform that aggregates, processes, and provides insights on startup policies and schemes from various government portals using advanced web scraping and Large Language Models (LLMs). Bridging the gap between startups and government policies with AI.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)

---

![Banner Placeholder](https://via.placeholder.com/1200x300/e2e8f0/0f172a?text=Government+Startup+Policy+Dashboard)

</div>

<br>

## 💡 The Problem We Solve: Empowering Startups
Billions of dollars in government grants, tax exemptions, and subsidies go unclaimed every year simply because founders don't know they exist. 

**How our platform directly benefits your startup:**
* **Unlocks Hidden Capital**: We aggregate fragmented schemes from dozens of obscure central (DPIIT, MeitY, SIDBI) and state-level portals into one unified discovery engine.
* **Cuts Through Bureaucratic Jargon**: Nobody has time to read 50-page highly technical government PDFs. Our LLM engine digests complex eligibility criteria into 3 simple bullet points written in plain English.
* **Hyper-Personalized Matching**: Stop guessing if you qualify. Enter your startup's sector (e.g., DeepTech), stage (e.g., Pre-Series A), and demographics—our AI instantly generates a personalized eligibility matrix, recommending the exact top 5 schemes you should apply for right now.
* **Never Miss a Deadline**: With our automated cron scraping pipelines, you are immediately alerted when a new policy relevant to your sector drops or an application window opens. 

---

## ✨ In-Depth Feature Breakdown

### 🤖 1. AI-Powered Medallion ETL Pipeline
Instead of relying on rigid, breakable Regex patterns or static XPath rules to parse complex government text, we utilize a **Medallion Architecture (Bronze, Silver, Gold)** powered directly by **Google Gemini LLMs**. The pipeline fetches unstructured, noisy HTML and PDF files from government websites and relies on state-of-the-art unstructured data extraction via Pydantic schema validation to convert chaos into clean, queryable JSON fields. 

### 🔎 2. Multi-Portal Scraping Engine
Our web scrapers are built with **Playwright** and **BeautifulSoup**, handling everything from simple static HTML to heavily obfuscated JavaScript-rendered portals. Portals natively supported:
* **DPIIT**
* **MeitY**
* **SIDBI**
* **Startup India**
* **State Portals** (Kerala Startup Mission, Startup Odisha, etc.)

### 🎯 3. AI Policy Recommender
Startups simply input their sector, stage (Seed, Pre-Series A, Incubation), and funding requirements. The FastAPI inference engine connects to Gemini (or another LLM) performing semantic matching against the **Gold dataset**—outputting the top 3-5 government policies the startup is actually eligible for, complete with matching scores and reasoning.

### 📊 4. Interactive Insight Dashboards & Frontend
- **Next.js V15 Frontend**: A beautiful Next.js UI leveraging React Server Components for ultra-fast load times. It houses the user-facing discovery UI where founders browse policies.
- **Streamlit Analytics**: A dedicated dashboard for policymakers to view real-time metrics on scheme distribution, sector coverage, and funding landscapes.

---

## 🏗️ Technical Architecture & Data Flow

Our system relies on decoupled microservices to scale web scraping separately from API serving and frontend rendering.

### 🔄 Data Flow Pipeline Diagram
```mermaid
graph TD
    classDef bronze fill:#cd7f32,stroke:#333,stroke-width:2px,color:#fff;
    classDef silver fill:#c0c0c0,stroke:#333,stroke-width:2px,color:#000;
    classDef gold fill:#ffd700,stroke:#333,stroke-width:2px,color:#000;
    classDef external fill:#1e40af,stroke:#2563eb,stroke-width:2px,color:#fff;
    classDef web fill:#047857,stroke:#059669,stroke-width:2px,color:#fff;

    subgraph "External Government Sources"
        S1(Startup India) ::: external
        S2(MeitY) ::: external
        S3(State Portals) ::: external
    end

    subgraph "Bronze Layer (Raw Data Ingestion)"
        Cron((Scheduled Trigger))
        Runner[Bronze Runner Pipeline]
        RawDB[(Supabase: schemes_raw)] ::: bronze
        Cron -->|Spawns| Runner
        Runner -->|Scrapes| S1 & S2 & S3
        Runner -->|Inserts Raw Blob| RawDB
    end

    subgraph "Silver Layer (AI Extraction & Cleansing)"
        SilverRunner[Silver ETL Pipeline]
        Gemini1[Gemini 1.5 Flash - Text to JSON]
        Schema[Pydantic Schemes]
        CleanDB[(Supabase: schemes_clean)] ::: silver
        RawDB -->|Trigger / Batch| SilverRunner
        SilverRunner <-->|Prompts| Gemini1
        Gemini1 -->|Validates against| Schema
        SilverRunner -->|Upserts Clean JSON| CleanDB
    end

    subgraph "Gold Layer (Analytics & Serving)"
        NLP[NLP Enrichment & Tagging]
        GeminiPro[Gemini Pro - Semantic Summaries]
        GoldViews[(Supabase: Gold Views)] ::: gold
        CleanDB -->|Extracts| NLP
        NLP <-->|Semantic Parsing| GeminiPro
        NLP -->|Updates Tags| GoldViews
    end

    subgraph "Presentation Layer"
        API[FastAPI Gateway Container]
        NextUI[Next.js App UI] ::: web
        Streamlit[Streamlit Data Viz] ::: web
        GoldViews -->|SQL / ORM| API
        API -->|REST/JSON| NextUI
        API -->|REST/JSON| Streamlit
    end
```

### ⚙️ Automation & Cron Pipelines
The system is designed to be fully automated. While currently triggered via the FastAPI endpoints (`/pipeline/run-scrapers`), in a production environment, cron jobs (like GitHub Actions or AWS EventBridge) hit these endpoints on a schedule (e.g., weekly) to check for newly published schemes, auto-parse them through the LLM, and update the Next.js frontend without human intervention.
Change detection algorithms (`cleanup_guardrail.py` & `change_detection.py`) monitor URL diffs to avoid redundant LLM calls on unaltered government web pages.

---

## 📂 Project Structure Deep Dive

```text
GOV-DASH/
├── 📁 frontend/          # Next.js 15 web application (Tailwind, TypeScript, App Router)
├── 📁 dashboard/         # Streamlit analytical dashboard views (Alerts, Auth, Sector Mapping)
├── 📁 pipeline/          # Core ETL logic (Bronze, Silver, Gold layers)
│   ├── 📄 bronze_runner.py    # Orchestrates the scrapers.
│   ├── 📄 silver.py           # The LLM parsing logic.
│   ├── 📄 gold.py             # Advanced analytics aggregation.
│   ├── 📄 llm_service.py      # LLM connection multiplexer.
│   ├── 📄 change_detection.py # Delta hashing to avoid rescraping identical pages.
│   └── 📄 schemas.py          # Strict Pydantic validators enforcing API JSON formats.
├── 📁 scrapers/          # Custom web scrapers for each portal (Playwright/BS4)
│   ├── 📄 base_scraper.py     # Base abstract class managing headless browsers & retries.
│   └── 📄 dpiit.py, meity.py... # Domain-specific scrapers.
├── 📁 migrations/        # Supabase PostgreSQL schema definitions
├── 📁 seed/              # Seed data scripts and initial baseline CSVs
├── 📄 main.py            # FastAPI application entry point
└── 📄 requirements.txt   # Python dependencies
```

---

## 🚀 Getting Started Guide

### 1. Prerequisites Installation
Ensure you have Python 3.10+ and Node.js 18+ installed on your system.
Create accounts for:
- [Supabase](https://supabase.com/) (For PostgreSQL & Auth)
- [Google AI Studio](https://aistudio.google.com/app/apikey) (For the Gemini LLM API Key)

### 2. Database Provisioning (Supabase)
Inside your Supabase SQL Editor, you must run the migration scripts sequentially to establish the Medallion architecture tables:
1. `migrations/001_initial_schema.sql` (Creates `schemes_raw`, `schemes_clean`)
2. `migrations/002_add_scheme_versions.sql` (Creates history tracking for change detection)
3. `migrations/003_gold_views.sql` (Creates materialized views for analytics)
4. `migrations/004_auth_schema.sql` 

### 3. Backend Setup (FastAPI & Pipeline)

**Create your virtual environment & install requirements:**
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m playwright install  # Installs browser binaries for Playwright scrapers
```

**Set up Environment Variables:**
Create a `.env` file at the root of `GOV-DASH`:
```env
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-anon-or-service-role-key"
GEMINI_API_KEY="AIzaSyYourGeminiKeyHere"
```

**Start the FastAPI Server:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- API is now live at: `http://localhost:8000`
- API Documentation (Swagger UI): `http://localhost:8000/docs`

### 4. Frontend Setup (Next.js)

**Install Node Dependencies:**
```bash
cd frontend
npm install --legacy-peer-deps
```

**Configure Frontend Environment:**
Create `frontend/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

**Start the Web Client:**
```bash
npm run dev
```
Navigate to `http://localhost:3000` to interact with the platform.

### 5. Start the Analytics Dashboard (Streamlit)
Open a new terminal session, activate your python `venv` and run:
```bash
streamlit run dashboard/app.py
```

---

## 🛡️ Core Endpoints & Manual Overrides

If cron is disabled, you can manually trigger the pipeline phases via the FastAPI swagger docs (`/docs`):

| Endpoint | Layer | Description | Method |
|----------|-------|-------------|--------|
| `/pipeline/run-scrapers` | **Bronze** | Triggers headless browsers to pull latest site updates. | `POST` |
| `/pipeline/run-silver` | **Silver** | Batch-processes raw HTML/Text through Gemini for JSON parsing. | `POST` |
| `/pipeline/run-nlp` | **Gold** | Generates semantic embeddings/tags for search features. | `POST` |
| `/recommend` | **Application**| Submits a startup profile & returns matched policies. | `POST` |

---

## 💻 Tech Stack Justification
- **Backend**: FastAPI (Chosen for async Python support essential for parallel web scraping).
- **Web Scraping**: Playwright (Chosen to bypass JavaScript rendered SPAs and anti-bot challenges on Gov sites) & BeautifulSoup4.
- **AI/LLM Extraction**: Google Gemini 1.5 (Chosen for massive context window enabling digestion of huge PDF policy documents and extremely fast JSON schema adherence).
- **Frontend**: Next.js 15, TailwindCSS, TypeScript (For enterprise-grade UX and SEO capabilities).
- **Data Visualizations**: Streamlit (Allows instant plotting of Pandas dataframes without writing custom graphic React components).
- **Database**: Supabase PostgreSQL (Combines relationship models with pgvector for future RAG expansions).

---

<div align="center">
  <p><i>Building the infrastructure for India's digital startup ecosystem.</i></p>
</div>
