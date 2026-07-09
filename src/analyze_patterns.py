import os
import json
from collections import Counter
from typing import Dict, Any, List

DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(DIR_PATH, "data")
INPUT_FILE = os.path.join(DATA_DIR, "research_results_final.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "patterns.json")

def clean_auth(auth_list: List[str]) -> List[str]:
    cleaned = []
    for a in auth_list:
        a_lower = str(a).lower()
        if "oauth" in a_lower:
            cleaned.append("OAuth2")
        elif "key" in a_lower:
            cleaned.append("API Key")
        elif "token" in a_lower:
            cleaned.append("Token")
        elif "basic" in a_lower:
            cleaned.append("Basic")
        elif "other" in a_lower:
            cleaned.append("Other")
        elif "none" in a_lower or "no api" in a_lower:
            cleaned.append("None")
        else:
            cleaned.append("API Key" if "key" in a_lower else "Other")
    if not cleaned:
        cleaned.append("Other")
    return list(set(cleaned))

def analyze_patterns():
    # If final results don't exist yet, try v1 results
    results_path = INPUT_FILE
    if not os.path.exists(results_path):
        results_path = os.path.join(DATA_DIR, "research_results_v1.json")
        
    if not os.path.exists(results_path):
        print(f"❌ Results file not found at {INPUT_FILE} or v1. Please run research_agent.py first.")
        return
        
    with open(results_path) as f:
        data = json.load(f)
        
    print(f"Analyzing patterns across {len(data)} apps...")
    
    total = len(data)
    
    # 1. Auth Distribution
    auth_counts = Counter()
    for item in data:
        auths = clean_auth(item.get("auth_methods", ["Other"]))
        for a in auths:
            auth_counts[a] += 1
            
    auth_distribution = {k: v for k, v in auth_counts.items()}
    
    # 2. Self-Serve vs Gated Distribution
    gate_counts = Counter()
    for item in data:
        gate = item.get("self_serve_vs_gated", "Unknown")
        if "self-serve" in gate.lower():
            gate_counts["Self-serve"] += 1
        elif "paid" in gate.lower():
            gate_counts["Gated-Paid"] += 1
        elif "admin" in gate.lower():
            gate_counts["Gated-Admin"] += 1
        elif "sales" in gate.lower() or "partner" in gate.lower() or "contact" in gate.lower():
            gate_counts["Gated-Sales/Partner"] += 1
        else:
            gate_counts["Other/Unknown"] += 1
            
    gate_distribution = {k: v for k, v in gate_counts.items()}
    
    # 3. Buildability Verdict
    buildable_counts = Counter()
    blockers = Counter()
    for item in data:
        verdict = item.get("buildability_verdict", "No")
        # Normalize verdict
        if "yes" in verdict.lower():
            buildable_counts["Yes"] += 1
        else:
            buildable_counts["No"] += 1
            # Extract common blocker patterns from text
            gated = item.get("self_serve_vs_gated", "")
            desc = item.get("category_what_it_does", "")
            surface = item.get("api_surface", "")
            
            if "no public api" in surface.lower() or "no api" in desc.lower() or "no developer portal" in gated.lower():
                blockers["No Public API"] += 1
            elif "partner" in gated.lower() or "sales" in gated.lower() or "contact-sales" in gated.lower():
                blockers["Partner/Sales Gate"] += 1
            elif "paid" in gated.lower():
                blockers["Paid Subscription Needed"] += 1
            else:
                blockers["Gated/Restricted Access"] += 1
                
    buildable_distribution = {k: v for k, v in buildable_counts.items()}
    blocker_distribution = {k: v for k, v in blockers.items()}
    
    # 4. Analysis by Category
    category_data = {}
    for item in data:
        cat = item.get("category", "Other")
        if cat not in category_data:
            category_data[cat] = {
                "total": 0,
                "self_serve": 0,
                "gated": 0,
                "buildable": 0,
                "auth_methods": Counter()
            }
        category_data[cat]["total"] += 1
        gate = item.get("self_serve_vs_gated", "")
        if "self-serve" in gate.lower():
            category_data[cat]["self_serve"] += 1
        else:
            category_data[cat]["gated"] += 1
            
        verdict = item.get("buildability_verdict", "No")
        if "yes" in verdict.lower():
            category_data[cat]["buildable"] += 1
            
        auths = clean_auth(item.get("auth_methods", ["Other"]))
        for a in auths:
            category_data[cat]["auth_methods"][a] += 1
            
    # Normalize category data for export
    category_summary = {}
    for cat, stats in category_data.items():
        category_summary[cat] = {
            "total": stats["total"],
            "self_serve_percent": stats["self_serve"] / stats["total"] * 100,
            "gated_percent": stats["gated"] / stats["total"] * 100,
            "buildable_percent": stats["buildable"] / stats["total"] * 100,
            "top_auth": stats["auth_methods"].most_common(1)[0][0] if stats["auth_methods"] else "Other"
        }
        
    # 5. Easy Wins vs Hard Obstacles
    easy_wins = []
    hard_obstacles = []
    
    for item in data:
        name = item.get("name")
        gate = item.get("self_serve_vs_gated", "")
        verdict = item.get("buildability_verdict", "")
        auths = clean_auth(item.get("auth_methods", ["Other"]))
        
        # Easy Win: Buildable, Self-serve, standard Auth (OAuth2 or API key)
        if "yes" in verdict.lower() and "self-serve" in gate.lower() and ("OAuth2" in auths or "API Key" in auths):
            easy_wins.append(name)
        elif "no" in verdict.lower() or "partner" in gate.lower() or "sales" in gate.lower():
            hard_obstacles.append(name)
            
    patterns_report = {
        "summary": {
            "total_apps": total,
            "buildable_percent": buildable_distribution.get("Yes", 0) / total * 100,
            "self_serve_percent": gate_distribution.get("Self-serve", 0) / total * 100
        },
        "auth_distribution": auth_distribution,
        "access_gate_distribution": gate_distribution,
        "buildable_distribution": buildable_distribution,
        "blocker_distribution": blocker_distribution,
        "category_analysis": category_summary,
        "easy_wins": easy_wins[:15],  # Sample first 15
        "hard_obstacles": hard_obstacles[:15]
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(patterns_report, f, indent=2)
        
    print(f"✅ Saved patterns analysis to {OUTPUT_FILE}")
    print("\n📈 Summary Insights:")
    print(f"  - Total Apps: {total}")
    print(f"  - Buildable today: {buildable_distribution.get('Yes', 0)} ({buildable_distribution.get('Yes', 0)/total*100:.1f}%)")
    print(f"  - Self-serve developer access: {gate_distribution.get('Self-serve', 0)} ({gate_distribution.get('Self-serve', 0)/total*100:.1f}%)")
    print(f"  - Dominant Auth: {auth_counts.most_common(1)[0][0]} ({auth_counts.most_common(1)[0][1]} counts)")

if __name__ == "__main__":
    analyze_patterns()
