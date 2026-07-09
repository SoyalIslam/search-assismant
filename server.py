import os
import sys
import json
import subprocess
import threading
import time
from flask import Flask, jsonify, request, send_from_directory, Response

app = Flask(__name__, static_folder=".")

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DIR_PATH, "data")
RESULTS_PATH = os.path.join(DATA_DIR, "research_results_final.json")
LOG_FILE = os.path.join(DIR_PATH, "pipeline.log")
PATTERNS_PATH = os.path.join(DATA_DIR, "patterns.json")

RESEARCH_DATA = []
PATTERNS_DATA = {}

def load_data():
    global RESEARCH_DATA, PATTERNS_DATA
    try:
        if os.path.exists(RESULTS_PATH):
            with open(RESULTS_PATH) as f:
                RESEARCH_DATA = json.load(f)
        if os.path.exists(PATTERNS_PATH):
            with open(PATTERNS_PATH) as f:
                PATTERNS_DATA = json.load(f)
    except Exception as e:
        print(f"Error loading JSON data: {e}")

load_data()

# Global status tracking
pipeline_status = {
    "running": False,
    "current_step": "idle",
    "completed_apps": 0,
    "total_apps": 100,
    "error": None
}

def run_pipeline_worker(use_seed=False):
    global pipeline_status
    pipeline_status["running"] = True
    pipeline_status["error"] = None
    
    try:
        # Clear log file
        with open(LOG_FILE, "w") as f:
            f.write("")
            
        def log_message(msg):
            print(msg)
            with open(LOG_FILE, "a") as f:
                f.write(msg + "\n")
                
        if use_seed:
            pipeline_status["current_step"] = "Seeding data..."
            log_message("🌱 Phase 1: Seeding pre-researched high-quality datasets...")
            # Run seed_data.py
            cmd = [sys.executable, os.path.join(DIR_PATH, "src", "seed_data.py")]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=DIR_PATH)
            for line in proc.stdout:
                log_message(line.strip())
            proc.wait()
        else:
            pipeline_status["current_step"] = "Running agent research..."
            log_message("🔍 Phase 1: Running LLM Research Agent (requires GEMINI_API_KEY)...")
            # Run research_agent.py via uv
            cmd = ["uv", "run", "--with", "google-generativeai", "--with", "duckduckgo-search", "--with", "requests", "src/research_agent.py"]
            # Fallback if uv is not in path or fails
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=DIR_PATH)
            for line in proc.stdout:
                log_message(line.strip())
                # Update status completed count if printed
                match = re.search(r'Processed (\d+)/100', line)
                if match:
                    pipeline_status["completed_apps"] = int(match.group(1))
            proc.wait()

        # Step 2: Verification
        pipeline_status["current_step"] = "Running verification loop..."
        log_message("\n📊 Phase 2: Running ground-truth verification and self-correction loops...")
        cmd = [sys.executable, os.path.join(DIR_PATH, "src", "verify_accuracy.py")]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=DIR_PATH)
        for line in proc.stdout:
            log_message(line.strip())
        proc.wait()
        
        # Step 3: Analysis
        pipeline_status["current_step"] = "Running pattern analysis..."
        log_message("\n📈 Phase 3: Running clustering and statistical pattern analysis...")
        cmd = [sys.executable, os.path.join(DIR_PATH, "src", "analyze_patterns.py")]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=DIR_PATH)
        for line in proc.stdout:
            log_message(line.strip())
        proc.wait()
        
        # Step 4: Regenerate Assets
        pipeline_status["current_step"] = "Compiling dashboard assets..."
        log_message("\n💻 Phase 4: Compiling research dataset into app.js dashboard bundle...")
        cmd = [sys.executable, os.path.join(DIR_PATH, "src", "generate_dashboard_assets.py")]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=DIR_PATH)
        for line in proc.stdout:
            log_message(line.strip())
        proc.wait()
        
        log_message("\n🎉 Pipeline Execution Completed Successfully!")
        pipeline_status["current_step"] = "completed"
    except Exception as e:
        pipeline_status["error"] = str(e)
        pipeline_status["current_step"] = "failed"
        with open(LOG_FILE, "a") as f:
            f.write(f"\n❌ Error in pipeline: {e}\n")
    finally:
        pipeline_status["running"] = False

# Static routes
@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")

@app.route("/style.css")
def serve_css():
    return send_from_directory(".", "style.css")

@app.route("/app.js")
def serve_js():
    load_data()
    logic_path = os.path.join(DIR_PATH, "src", "app_logic.js")
    logic_code = ""
    if os.path.exists(logic_path):
        with open(logic_path) as f:
            logic_code = f.read()
    else:
        # Fallback to local app.js if app_logic.js is missing
        if os.path.exists(os.path.join(DIR_PATH, "app.js")):
            return send_from_directory(".", "app.js")
            
    js_content = f"const RESEARCH_DATA = {json.dumps(RESEARCH_DATA, indent=2)};\n"
    js_content += f"const PATTERNS_DATA = {json.dumps(PATTERNS_DATA, indent=2)};\n\n"
    js_content += logic_code
    
    return Response(js_content, mimetype="application/javascript")

# API routes
@app.route("/api/status")
def get_status():
    return jsonify(pipeline_status)

@app.route("/api/logs")
def get_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            return Response(f.read(), mimetype="text/plain")
    return Response("No logs found.", mimetype="text/plain")

@app.route("/api/run", methods=["POST"])
def trigger_pipeline():
    global pipeline_status
    if pipeline_status["running"]:
        return jsonify({"success": False, "message": "Pipeline is already running."}), 400
        
    use_seed = request.json.get("seed", False)
    req_key = request.json.get("api_key")
    if req_key:
        os.environ["GEMINI_API_KEY"] = req_key
        
    # Check if api key is provided in environment if not seeding
    if not use_seed and not os.environ.get("GEMINI_API_KEY"):
        return jsonify({"success": False, "message": "Gemini API Key is not provided. Cannot run LLM agent."}), 400
        
    thread = threading.Thread(target=run_pipeline_worker, args=(use_seed,))
    thread.daemon = True
    thread.start()
    return jsonify({"success": True, "message": "Pipeline started in background."})

@app.route("/api/research-single", methods=["POST"])
def research_single_app():
    """Trigger research for a single custom app and append it to the dataset on the fly!"""
    app_name = request.json.get("name")
    hint = request.json.get("website_hint", "")
    req_key = request.json.get("api_key")
    if req_key:
        os.environ["GEMINI_API_KEY"] = req_key
        
    if not app_name:
        return jsonify({"success": False, "message": "App name is required."}), 400
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"success": False, "message": "Gemini API Key is not provided. Cannot run LLM agent."}), 400

    # Spawning research task in a worker thread/process
    def task():
        try:
            # We import research_app dynamically
            sys.path.append(os.path.join(DIR_PATH, "src"))
            from research_agent import research_app
            
            # Load existing apps to assign next ID
            apps_json_path = os.path.join(DATA_DIR, "apps.json")
            if os.path.exists(apps_json_path):
                with open(apps_json_path) as f:
                    apps = json.load(f)
                    next_id = max([a["id"] for a in apps]) + 1
            else:
                next_id = 101
                
            app_meta = {
                "id": next_id,
                "name": app_name,
                "website_hint": hint,
                "category": "Custom Research"
            }
            
            # Perform research
            result = research_app(app_meta)
            
            # Load existing final results, append new one, save
            final_results = []
            if os.path.exists(RESULTS_PATH):
                with open(RESULTS_PATH) as f:
                    final_results = json.load(f)
            
            # Deduplicate by name
            final_results = [r for r in final_results if r["name"].lower() != app_name.lower()]
            final_results.append(result)
            
            with open(RESULTS_PATH, "w") as f:
                json.dump(final_results, f, indent=2)
                
            # Run analysis & compile assets
            import analyze_patterns
            import generate_dashboard_assets
            analyze_patterns.analyze_patterns()
            generate_dashboard_assets.generate_js()
            
            print(f"✅ Custom app {app_name} researched and appended successfully!")
        except Exception as e:
            print(f"❌ Error researching custom app: {e}")
            
    thread = threading.Thread(target=task)
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": f"Started custom research for {app_name} in background. Please refresh in a few seconds."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Server starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port)
