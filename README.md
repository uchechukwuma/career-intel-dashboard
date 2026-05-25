# 📊 Career Intelligence Analytical Dashboard

An enterprise-grade, modular Business Intelligence (BI) platform engineered to process, model, and visualize data-driven labor market signals from 23+ German sources updated daily. This system utilizes an ETL-structured architecture to strictly decouple database abstraction, data cleaning pipelines, global session state management, and declarative presentation layers.

## 🏗️ Technical Architecture & Data Pipeline Flow

```mermaid
graph LR
    subgraph Data Layer
        A[(MongoDB Database)] ===> B[src/database.py]
    end

    subgraph Processing & Cleaning Layer
        B ===> C[src/clean.py]
        C ===> D[src/filters.py]
    end

    subgraph Analytics & Presentation Layer
        D ===> E[src/insights.py]
        D ===> F[src/charts.py]
        E & F ===> G[src/components.py]
        G ===> H[streamlit_app.py]
    end

    style A fill:#47A248,stroke:#fff,stroke-width:1px,color:#fff
    style H fill:#FF4B4B,stroke:#fff,stroke-width:1px,color:#fff
```

## Core Engineering & Software Features
* ** NoSQL Database Abstraction (database.py):** Configured a decoupled storage connection pulling directly from a MongoDB backend. Implemented fail-safe termination gates (st.stop()) to gracefully halt application rendering and alert users in the event of connection timeouts.

* **Deterministic Text Transformation (clean.py):** Built optimized parsing functions (get_clean_company_string, clean_entity_name) to normalize raw multi-source company names, remove character noise, and standardize text metadata across various scrapers.

* **Dual-Mode High-Performance Filtering (filters.py):** Solved frontend performance bottlenecks using a toggleable state optimization model. Features a Simple Mode for fast-cached array matches and a Grouped Mode (consolidate_topics) for algorithmic parsing and consolidation of textually similar topic groups.

* **Two-Tier Monetization & Access Guard:** Programmed session-state authorization layers linked to Streamlit Secrets (st.secrets) and environment variables (os.getenv). Dynamically segments users into a Free Preview Tier (restricted to a 7-day trailing data window) and a Premium Tier (unlocking 180 days of historical data, advanced metrics, and CSV exports).

* **Declarative UI Componentization (components.py & charts.py):** Separated charts and structural widgets out of the bootstrap file. Raw analytics data is computed in insights.py and rendered using isolated HTML/CSS injection blocks for clean UI consistency.

## 📁 Project Structure
```text
├── .devcontainer/             # Standardized development container settings
├── .streamlit/                # App custom themes and secure connection configs
├── src/                       # Core Analytical & Data Engineering Layer
│   ├── __init__.py            # Explicit package initializer
│   ├── charts.py              # Declarative Plotly data visualization engines
│   ├── clean.py               # Data-cleansing, text parsing, and string normalization
│   ├── components.py          # Custom modular UI metric cards and layout components
│   ├── config.py              # Central system thresholds, constants, and color parameters
│   ├── database.py            # MongoDB engine abstractor, load configurations, and queries
│   ├── export.py              # Premium reporting engine for flat file extractions (CSV)
│   ├── filters.py             # Dual-mode global session state filter controls
│   └── insights.py            # AI/Analytical metrics generation logic
├── tests/                     # Unit testing suites for validation rules
├── requirements.txt           # Explicit Python dependencies with locked versions
├── runtime.txt                # Cloud deployment target specification
└── streamlit_app.py           # Application Bootstrap and UI Layout Controller
```

## Prerequisites & Setup
This application is optimized to run inside a Python 3.11 environment.

1. Clone the Repository
```Bash
git clone [https://github.com/yourusername/career-intelligence-streamlit_dashboard.git](https://github.com/yourusername/career-intelligence-streamlit_dashboard.git)
cd career-intelligence-streamlit_dashboard
```

2. Set Up Local Secrets & Environment
Create a .env file in your root folder (or use .streamlit/secrets.toml for local Streamlit testing) to securely map your database URI and premium system bypass:

```text
MONGODB_URI=your_mongodb_connection_string
PREMIUM_PASSWORD=your_secure_dashboard_password
```

3. Initialize Virtual Environment & Install Dependencies
```PowerShell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
## Install application dependencies
pip install -r requirements.txt
```
4. Run the Dashboard Platform
```Bash
streamlit run streamlit_app.py
```
The localized container web server will boot and display on http://localhost:8501.

## Quality Assurance & Continuous Testing
Data transformations, regex cleaning routines, and query limits are validated continuously via a separate test harness. Execute the validation suite using:

```Bash
pytest tests/
```
## Housekeeping & Resource Cleanup
To drop local cached instances, reset active stream states, or wipe out local environment memory, close the execution terminal wrapper or run:

```PowerShell
deactivate  # Disables active python virtual environment loops
```
