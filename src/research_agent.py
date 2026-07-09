import os
import sys
import json
import time
import re
from typing import List, Dict, Any
from duckduckgo_search import DDGS
import google.generativeai as genai

# Setup directories
DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(DIR_PATH, "data")
INPUT_FILE = os.path.join(DATA_DIR, "apps.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "research_results_v1.json")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)

# Gemini client will be initialized dynamically inside the research function to prevent import side-effects.

def search_ddg(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Query DuckDuckGo for search results."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                }
                for r in results
            ]
    except Exception as e:
        print(f"⚠️ Search error for query '{query}': {e}")
        time.sleep(2)  # Back off
        return []

def research_app(app: Dict[str, Any]) -> Dict[str, Any]:
    """Perform research for a single app using DDG search and Gemini."""
    app_name = app["name"]
    hint = app["website_hint"]
    category = app["category"]
    
    # Configure Gemini dynamically
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable is not set inside research_app.")
        return {
            "id": app["id"],
            "name": app_name,
            "category": category,
            "website_hint": hint,
            "category_what_it_does": "Error: GEMINI_API_KEY is not configured.",
            "auth_methods": ["Unknown"],
            "self_serve_vs_gated": "Unknown",
            "api_surface": "Unknown",
            "buildability_verdict": "No",
            "evidence_url": hint
        }
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )
    except Exception as e:
        print(f"❌ Error configuring Gemini model: {e}")
        return {
            "id": app["id"],
            "name": app_name,
            "category": category,
            "website_hint": hint,
            "category_what_it_does": f"Error: Failed to initialize model ({e})",
            "auth_methods": ["Unknown"],
            "self_serve_vs_gated": "Unknown",
            "api_surface": "Unknown",
            "buildability_verdict": "No",
            "evidence_url": hint
        }
    
    print(f"\n🔍 Researching: {app_name} (Hint: {hint})")
    
    # Construct search queries
    queries = [
        f"{app_name} API developer documentation authentication developer portal",
        f"{app_name} developer account pricing sign up gated self-serve"
    ]
    
    search_context = []
    for q in queries:
        print(f"  Searching: {q}")
        results = search_ddg(q, max_results=3)
        search_context.extend(results)
        time.sleep(1)  # Sleep between searches to avoid DDG block
        
    # Deduplicate search context by URL
    seen_urls = set()
    deduped_context = []
    for res in search_context:
        url = res["url"]
        if url not in seen_urls:
            seen_urls.add(url)
            deduped_context.append(res)
            
    # Formulate prompt
    prompt = f"""
You are a Product Operations Researcher at Composio. Your job is to analyze the API details of '{app_name}' (website/hint: '{hint}').
Below is the search context retrieved from the web:

{json.dumps(deduped_context, indent=2)}

Please research and provide details in the following JSON format:
{{
  "category_what_it_does": "One-line description of the app category and its core function.",
  "auth_methods": ["OAuth2" and/or "API Key" and/or "Basic" and/or "Token" and/or "Other" - list all that apply],
  "self_serve_vs_gated": "Identify if access is 'Self-serve' (anyone can sign up for free/trial), 'Gated-Paid' (needs subscription to access API), 'Gated-Admin' (needs workspace admin approval), or 'Gated-Sales/Partner' (needs manual approval/partnership). Add a brief sentence of context.",
  "api_surface": "Specify if it is REST, GraphQL, gRPC, and whether it has an existing MCP (Model Context Protocol) server or SDK.",
  "buildability_verdict": "Identify if we can build an agent toolkit today. Select 'Yes' or 'No'. If 'No', explain the primary blocker (e.g. requires partnership, paid subscription wall, no API available).",
  "evidence_url": "Provide the exact documentation URL or article URL from the search context backing your research. Make sure this URL is real, from the context, and links directly to developer docs."
}}

Only respond with a valid JSON block, conforming strictly to the schema. Do not add any conversational text.
"""
    
    # Query Gemini
    retries = 3
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            data = json.loads(response.text.strip())
            # Ensure the structure contains app metadata
            data["id"] = app["id"]
            data["name"] = app_name
            data["category"] = category
            data["website_hint"] = hint
            return data
        except Exception as e:
            last_err = e
            print(f"  ⚠️ LLM error (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(3)
            
    # Raise exception if all retries fail
    raise Exception(f"Gemini LLM error: {last_err}")

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable is not set.")
        print("Please set it using: export GEMINI_API_KEY='your-key'")
        sys.exit(1)
        
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found at {INPUT_FILE}. Please run parse_apps.py first.")
        sys.exit(1)
        
    with open(INPUT_FILE) as f:
        apps = json.load(f)
        
    # Read existing results to support resuming
    results = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE) as f:
                existing_data = json.load(f)
                results = {item["id"]: item for item in existing_data}
                print(f"ℹ️ Found {len(results)} existing results. Resuming research...")
        except Exception as e:
            print(f"⚠️ Could not load existing results: {e}. Starting fresh.")
            
    completed_count = len(results)
    
    for app in apps:
        app_id = app["id"]
        if app_id in results:
            continue
            
        try:
            result = research_app(app)
            results[app_id] = result
        except Exception as e:
            print(f"❌ Failed to research {app['name']}: {e}")
            results[app_id] = {
                "id": app["id"],
                "name": app["name"],
                "category": app["category"],
                "website_hint": app["website_hint"],
                "category_what_it_does": f"Failed to retrieve data: {e}",
                "auth_methods": ["Unknown"],
                "self_serve_vs_gated": "Unknown",
                "api_surface": "Unknown",
                "buildability_verdict": "No",
                "evidence_url": app["website_hint"]
            }
        
        # Write back to file after each app
        with open(OUTPUT_FILE, "w") as f:
            json.dump(list(results.values()), f, indent=2)
            
        completed_count += 1
        print(f"✅ Processed {completed_count}/100 apps.")
        
        # Sleep for Gemini free tier rate limit spacing (15 RPM -> 4 seconds per request)
        # We also made 2 DDG search requests, so we need some delay
        time.sleep(4)

if __name__ == "__main__":
    main()
