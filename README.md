# Composio AI Product Ops Intern Take-Home Assignment

An interactive feasibility and API research study of 100 applications, completed using an automated Python research agent, validation loops, and a premium web-based console dashboard.

---

## 🚀 Web Dashboard Portal
We have added a lightweight Flask-based backend server (`server.py`) that acts as a web portal to let you trigger research, view live logs, and add custom apps directly from the browser without running manual CLI scripts!

### Running the Web Server
Make sure you have `uv` installed, then run the one-click launcher script in your terminal:
```bash
./start.sh
```
This boots the server on **http://localhost:8080**.

### Web Portal Features
1. **Interactive Agent Controls:**
   - **Run Seed Pipeline:** Overwrites the dataset with seeded values and compiles statistics (takes ~5s). Perfect for an instant demo.
   - **Run LLM Research Agent:** Scrapes and queries Gemini API for all 100 apps (takes ~15 minutes). Requires `GEMINI_API_KEY` configured in the terminal.
2. **Research Custom App (Live Agent):**
   - Type any app name and website hint in the web interface and click "Run Custom Agent".
   - The backend spawns the scraper + LLM, researches the custom app, updates the database, and appends it to the table matrix dynamically!
3. **Live Monospace Console:**
   - Prints log outputs and execution progress in real-time in a terminal component.
4. **Feasibility Matrix Filters:**
   - Search box for instantaneous text searching across app names and descriptions.
   - Dropdown selectors to filter by category, authentication method, or buildability status.

---

## 🛠️ Project Structure
```bash
├── index.html                  # Main interactive dashboard page
├── style.css                   # Custom CSS styling (dark mode, glassmorphism)
├── app.js                      # UI logic and embedded researched dataset
├── server.py                   # Flask server providing HTTP API endpoints and static assets
├── start.sh                    # One-click shell launcher for the server
├── parse_apps.py               # Parses extracted markdown tables into structured JSON
├── get_all_chunks.py           # Notion scraper utility using API cursors
├── render_markdown.py          # Notion block to markdown table renderer
├── src/
│   ├── research_agent.py       # Automated DDG Search & Gemini API researcher
│   ├── seed_data.py            # High-quality pre-researched seed data generator
│   ├── verify_accuracy.py      # Ground-truth verification & self-correction loop
│   ├── analyze_patterns.py     # Clusters data and extracts auth/gate patterns
│   └── generate_dashboard_assets.py # Compiles final dataset into app.js
└── data/
    ├── apps.json               # Input list of 100 apps parsed from Notion
    ├── ground_truth.json       # Manually verified sample of 15 apps
    ├── research_results_v1.json # Output of the research agent
    ├── research_results_final.json # Corrected and verified feasibility data
    └── patterns.json           # Aggregated statistics and clustering patterns
```

---

## 💻 Manual CLI Runner Guide
If you prefer running the pipeline step-by-step manually in the terminal:

1. **Set your Gemini API Key:**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```

2. **Execute the Research Agent:**
   ```bash
   uv run --with google-generativeai --with duckduckgo-search --with requests src/research_agent.py
   ```

3. **Run Ground-Truth Verification:**
   ```bash
   python3 src/verify_accuracy.py
   ```

4. **Regenerate Statistics and Dashboard Assets:**
   ```bash
   python3 src/analyze_patterns.py
   python3 src/generate_dashboard_assets.py
   ```
