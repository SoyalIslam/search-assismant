// Client-Side Application UI Logic for Composio API Research Dashboard

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    setupFilters();
    setupPipelineControls();
    renderAppTable(RESEARCH_DATA);
});

function initDashboard() {
    // Set Summary Counters
    document.getElementById('stat-total-apps').textContent = PATTERNS_DATA.summary.total_apps;
    document.getElementById('stat-buildable').textContent = PATTERNS_DATA.summary.buildable_percent.toFixed(0) + '%';
    document.getElementById('stat-self-serve').textContent = PATTERNS_DATA.summary.self_serve_percent.toFixed(0) + '%';
    
    // Render Auth Chart
    const authList = document.getElementById('auth-chart-list');
    authList.innerHTML = '';
    const totalAuths = Object.values(PATTERNS_DATA.auth_distribution).reduce((a, b) => a + b, 0);
    Object.entries(PATTERNS_DATA.auth_distribution)
        .sort((a, b) => b[1] - a[1])
        .forEach(([auth, count]) => {
            const percentage = (count / 100) * 100; // out of 100 apps
            const row = document.createElement('div');
            row.className = 'chart-row';
            row.innerHTML = `
                <span class="chart-label">${auth}</span>
                <div class="chart-bar-container">
                    <div class="chart-bar" style="width: ${percentage}%"></div>
                </div>
                <span class="chart-value">${count}%</span>
            `;
            authList.appendChild(row);
        });

    // Render Access Chart
    const accessList = document.getElementById('access-chart-list');
    accessList.innerHTML = '';
    Object.entries(PATTERNS_DATA.access_gate_distribution)
        .sort((a, b) => b[1] - a[1])
        .forEach(([gate, count]) => {
            const percentage = (count / 100) * 100;
            const row = document.createElement('div');
            row.className = 'chart-row';
            row.innerHTML = `
                <span class="chart-label">${gate}</span>
                <div class="chart-bar-container">
                    <div class="chart-bar access-bar" style="width: ${percentage}%"></div>
                </div>
                <span class="chart-value">${count}%</span>
            `;
            accessList.appendChild(row);
        });
        
    // Render Easy Wins List
    const easyWinsList = document.getElementById('easy-wins-list');
    easyWinsList.innerHTML = PATTERNS_DATA.easy_wins.map(app => `<span class="tag tag-success">${app}</span>`).join(' ');

    // Render Hard Obstacles List
    const hardObstaclesList = document.getElementById('hard-obstacles-list');
    hardObstaclesList.innerHTML = PATTERNS_DATA.hard_obstacles.map(app => `<span class="tag tag-danger">${app}</span>`).join(' ');
}

function setupFilters() {
    const searchInput = document.getElementById('search-input');
    const categorySelect = document.getElementById('category-filter');
    const authSelect = document.getElementById('auth-filter');
    const buildableSelect = document.getElementById('buildable-filter');
    
    // Populate Categories in filter
    const categories = [...new Set(RESEARCH_DATA.map(item => item.category))];
    categorySelect.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.textContent = cat;
        categorySelect.appendChild(opt);
    });

    const filterHandler = () => {
        const query = searchInput.value.toLowerCase().trim();
        const selectedCat = categorySelect.value;
        const selectedAuth = authSelect.value;
        const selectedBuild = buildableSelect.value;
        
        const filtered = RESEARCH_DATA.filter(item => {
            const nameMatch = item.name.toLowerCase().includes(query) || 
                              item.category_what_it_does.toLowerCase().includes(query);
            const catMatch = !selectedCat || item.category === selectedCat;
            
            // Check auth intersection
            const itemAuths = item.auth_methods.map(a => a.toLowerCase());
            const authMatch = !selectedAuth || itemAuths.some(a => a.includes(selectedAuth.toLowerCase()));
            
            const buildMatch = !selectedBuild || 
                               (selectedBuild === 'yes' && item.buildability_verdict.toLowerCase() === 'yes') ||
                               (selectedBuild === 'no' && item.buildability_verdict.toLowerCase() === 'no');
                               
            return nameMatch && catMatch && authMatch && buildMatch;
        });
        
        renderAppTable(filtered);
    };

    searchInput.addEventListener('input', filterHandler);
    categorySelect.addEventListener('change', filterHandler);
    authSelect.addEventListener('change', filterHandler);
    buildableSelect.addEventListener('change', filterHandler);
}

function setupPipelineControls() {
    const btnSeed = document.getElementById('btn-run-seed');
    const btnAgent = document.getElementById('btn-run-agent');
    const btnCustom = document.getElementById('btn-run-custom');
    const consoleBox = document.getElementById('pipeline-console');
    const statusBadge = document.getElementById('pipeline-status-badge');
    
    let pollInterval = null;

    const startPolling = () => {
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(async () => {
            try {
                const res = await fetch('/api/status');
                const status = await res.json();
                
                statusBadge.textContent = status.running ? `Running: ${status.current_step}` : 'Idle';
                statusBadge.className = status.running ? 'tag tag-info' : 'tag tag-secondary';
                
                // Fetch logs
                const logRes = await fetch('/api/logs');
                const logs = await logRes.text();
                consoleBox.textContent = logs || "Console logs will appear here when you run a pipeline script.";
                consoleBox.scrollTop = consoleBox.scrollHeight;
                
                if (!status.running) {
                    clearInterval(pollInterval);
                    pollInterval = null;
                    if (status.current_step === 'completed') {
                        consoleBox.textContent += "\n\n🎉 Done! Reloading dashboard in 3 seconds...";
                        setTimeout(() => location.reload(), 3000);
                    }
                }
            } catch (err) {
                console.error("Error polling server:", err);
            }
        }, 1000);
    };

    // Check status on load
    fetch('/api/status')
        .then(res => res.json())
        .then(status => {
            if (status.running) startPolling();
        });

    btnSeed.addEventListener('click', async () => {
        if (confirm("Run seed pipeline? This will overwrite the final dataset with seeded values and run the analysis (takes ~5s).")) {
            consoleBox.textContent = "Starting Seed Pipeline...";
            try {
                const res = await fetch('/api/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ seed: true })
                });
                const data = await res.json();
                if (data.success) startPolling();
                else alert(data.message);
            } catch (err) {
                alert("Server error: " + err);
            }
        }
    });

    btnAgent.addEventListener('click', async () => {
        const apiKeyInput = document.getElementById('gemini-api-key');
        const apiKey = apiKeyInput.value.trim();
        if (confirm("Run LLM Research Agent? This will scrape and call Gemini API for all 100 apps (takes ~15 minutes).")) {
            consoleBox.textContent = "Starting Live Agent Pipeline...";
            try {
                const res = await fetch('/api/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ seed: false, api_key: apiKey })
                });
                const data = await res.json();
                if (data.success) startPolling();
                else alert(data.message);
            } catch (err) {
                alert("Server error: " + err);
            }
        }
    });

    btnCustom.addEventListener('click', async () => {
        const nameInput = document.getElementById('custom-app-name');
        const hintInput = document.getElementById('custom-app-hint');
        const apiKeyInput = document.getElementById('gemini-api-key');
        const name = nameInput.value.trim();
        const hint = hintInput.value.trim();
        const apiKey = apiKeyInput.value.trim();

        if (!name) {
            alert("Please provide an app name.");
            return;
        }

        btnCustom.textContent = "🔍 Researching...";
        btnCustom.disabled = true;
        consoleBox.textContent = `Triggering live agent research for custom app: ${name} (Hint: ${hint})...`;

        try {
            const res = await fetch('/api/research-single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, website_hint: hint, api_key: apiKey })
            });
            const data = await res.json();
            
            if (data.success) {
                startPolling();
                btnCustom.textContent = "🔍 Run Custom Agent";
                btnCustom.disabled = false;
            } else {
                alert(data.message);
                btnCustom.textContent = "🔍 Run Custom Agent";
                btnCustom.disabled = false;
            }
        } catch (err) {
            alert("Server error: " + err);
            btnCustom.textContent = "🔍 Run Custom Agent";
            btnCustom.disabled = false;
        }
    });
}

function renderAppTable(data) {
    const tbody = document.getElementById('apps-table-body');
    tbody.innerHTML = '';
    
    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="no-results">No apps found matching the filter criteria.</td></tr>`;
        return;
    }
    
    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.id = `app-row-${item.id}`;
        tr.className = 'app-row-header';
        
        const authBadges = item.auth_methods.map(auth => {
            let typeClass = 'tag-secondary';
            if (auth.includes('OAuth2')) typeClass = 'tag-primary';
            else if (auth.includes('API Key')) typeClass = 'tag-success';
            else if (auth.includes('Token')) typeClass = 'tag-info';
            return `<span class="tag ${typeClass}">${auth}</span>`;
        }).join(' ');

        const buildClass = item.buildability_verdict.toLowerCase() === 'yes' ? 'verdict-yes' : 'verdict-no';
        const buildIcon = item.buildability_verdict.toLowerCase() === 'yes' ? '✓' : '✗';
        
        tr.innerHTML = `
            <td>#${item.id}</td>
            <td class="app-name-cell"><strong>${item.name}</strong></td>
            <td><span class="category-text">${item.category}</span></td>
            <td>${authBadges}</td>
            <td><span class="verdict ${buildClass}">${buildIcon} ${item.buildability_verdict}</span></td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="toggleDetails(${item.id})">View Details</button>
            </td>
        `;
        
        const detailTr = document.createElement('tr');
        detailTr.id = `details-row-${item.id}`;
        detailTr.className = 'app-row-details hidden';
        detailTr.innerHTML = `
            <td colspan="6">
                <div class="details-expanded">
                    <div class="details-grid">
                        <div>
                            <h4>Description</h4>
                            <p>${item.category_what_it_does}</p>
                        </div>
                        <div>
                            <h4>API Surface</h4>
                            <p>${item.api_surface}</p>
                        </div>
                        <div>
                            <h4>Access model</h4>
                            <p><strong>${item.self_serve_vs_gated}</strong></p>
                        </div>
                        <div>
                            <h4>Evidence & Documentation</h4>
                            <p><a href="${item.evidence_url}" target="_blank" class="evidence-link">${item.evidence_url} ↗</a></p>
                        </div>
                    </div>
                </div>
            </td>
        `;
        
        tbody.appendChild(tr);
        tbody.appendChild(detailTr);
    });
}

window.toggleDetails = function(id) {
    const detailsRow = document.getElementById(`details-row-${id}`);
    const btn = document.querySelector(`#app-row-${id} button`);
    if (detailsRow.classList.contains('hidden')) {
        detailsRow.classList.remove('hidden');
        btn.textContent = 'Hide Details';
        btn.classList.add('btn-active');
    } else {
        detailsRow.classList.add('hidden');
        btn.textContent = 'View Details';
        btn.classList.remove('btn-active');
    }
};
