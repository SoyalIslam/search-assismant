# 📊 Composio API Research & Feasibility Dashboard

An interactive feasibility study and API research analysis of 100 applications, automated using a Python-based DuckDuckGo Scraper & Gemini research agent, cross-checked by human-in-the-loop validation loops, and presented via a premium web dashboard console.

---

## 🚀 Quickstart: Running the Web Dashboard (Recommended)

The easiest way to explore the project, view the research data, and run the agents live is through the web-based controller.

### 1. Prerequisites
Ensure you have `uv` (the fast Python package manager) installed. If you don't have it, install it using:
```bash
# On Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Set Up & Run the Server
Clone the repository, navigate into the directory, and run the launcher script:
```bash
cd composis
chmod +x start.sh
./start.sh
```
This will automatically configure a virtual environment, install local dependencies (`flask` and `requests`), and launch the server on **http://localhost:8080**.

### 3. How to Use the Web Dashboard
* ** 🌱 Instant Demo (5s):** Click **Run Seed Pipeline** in the dashboard. It will instantly populate the database with pre-researched 100-app data, run verification, calculate statistics, and display the charts. No API Key required.
* ** 🤖 Live Research Agent (15m):** Paste your Gemini API key in the dashboard input field, and click **Run LLM Research Agent** to let the agent scrape the web and query the LLM live for all 100 apps.
* ** 🔍 Research a Custom App:** Paste your Gemini API key, type in any app name (e.g., `Slack`, `Zoom`), and click **Run Custom Agent**. The agent will perform a live search, reason, output logs to the console, and dynamically add the new row to the table!

---

## 💻 Manual CLI Runner Guide (Step-by-Step)

If you prefer executing the research and analysis scripts manually in your terminal, follow these steps:

### Step 1: Parse the Input List
Read the raw markdown files and convert them into a structured JSON list of 100 apps:
```bash
python3 parse_apps.py
```
*Creates: `data/apps.json`*

### Step 2: Configure your LLM Credentials
Export your Gemini API Key in your current shell:
```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

### Step 3: Run the Automated Research Agent
Trigger the agent to search the web (DuckDuckGo) and query the LLM (Gemini 1.5 Flash) to research all 100 apps. The `uv run` command will download dependencies on the fly:
```bash
uv run --with google-generativeai --with duckduckgo-search --with requests src/research_agent.py
```
*Creates/Resumes: `data/research_results_v1.json`*

### Step 4: Run the Ground-Truth Verification Loop
Verify the agent's accuracy against a hand-curated ground truth subset of 15 apps, and run self-correction rules to fix discrepancies:
```bash
python3 src/verify_accuracy.py
```
*Creates: `data/ground_truth.json` & `data/research_results_final.json`*

### Step 5: Analyze Feasibility Patterns & Clustering
Cluster the auth methods, calculate statistics (percent self-serve, percent buildable, dominant auth type, and easy wins list):
```bash
python3 src/analyze_patterns.py
```
*Creates: `data/patterns.json`*

### Step 6: Regenerate Web Dashboard Bundle
Compile the final results and analysis patterns into the static assets bundle:
```bash
python3 src/generate_dashboard_assets.py
```
*Updates: `app.js`*

---

## ☁️ Vercel Deployment

This project is optimized to run as a serverless Flask app on Vercel's read-only environment:

1. Create a GitHub repository and push this project:
   ```bash
   git remote add origin <your-repo-url>
   git push -u origin main
   ```
2. Import the repository in your **Vercel Dashboard**.
3. Under the **Environment Variables** section, you can optionally add your `GEMINI_API_KEY` (if you want custom lookups to work instantly on Vercel).
4. Click **Deploy**.
