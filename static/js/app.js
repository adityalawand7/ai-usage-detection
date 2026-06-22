const roleLabels = {
    ai_native: "AI-Native Company",
    ai_product: "AI Product Company",
    ai_enabled: "AI-Enabled Organization",
    ai_governance: "AI Governance & Advisory",
    ai_research: "AI Research Organization",
    ai_consumer: "AI Consumer",
    ai_marketing_only: "AI Marketing Presence",
    unknown: "Unknown"
};

const capabilityLabels = {
    general_ai: "General AI Core",
    coding_ai: "AI Coding Systems",
    chatbot_ai: "Conversational Chatbot",
    marketing_ai: "AI Writing & SEO",
    image_ai: "Image & Creative AI"
};

// --------------------------------
// DISPLAY SCAN REPORT
// --------------------------------
function renderReport(result) {
    // Hide history grid if visible
    const historySec = document.getElementById("history-section");
    if (historySec) {
        historySec.style.display = "none";
    }

    const totalScore = result.total_score !== undefined ? result.total_score : (result.maturity_score || 0);

    let capabilitiesHtml = "";
    if (result.capabilities && result.capabilities.length > 0) {
        capabilitiesHtml = `
            <div class="capabilities-box">
                <h4>Detected AI Capabilities</h4>
                <div class="tags-container">
                    ${result.capabilities.map(cap => `
                        <span class="cap-tag tag-${cap}">
                            ${capabilityLabels[cap] || cap}
                        </span>
                    `).join("")}
                </div>
            </div>
        `;
    } else {
        capabilitiesHtml = `
            <div class="capabilities-box">
                <h4>Detected AI Capabilities</h4>
                <p class="no-capabilities">No specialized AI modules detected (e.g. Chatbots, Code Gen).</p>
            </div>
        `;
    }

    let html = `
        <div class="result animate-fade-in">
            <div class="result-header">
                <h2>Analysis Report 
                    <span class="badge badge-${result.confidence.toLowerCase().replace(" ", "-")}">
                        ${result.confidence}
                    </span>
                </h2>
                <span class="target-url-subtitle">${result.url}</span>
            </div>

            <!-- KEY INFORMATION METRICS -->
            <div class="metrics-row">
                <div class="maturity-card">
                    <div class="maturity-card-inner">
                        <div class="maturity-number">${result.maturity_score}</div>
                        <div class="maturity-label">AI Maturity Score</div>
                    </div>
                </div>

                <div class="info-meta-card">
                    <div class="meta-row">
                        <span class="meta-label">Uses AI Verdict</span>
                        <strong class="meta-val val-${result.verdict}">
                            ${result.verdict ? "ACTIVE AI ADOPTER" : "NO SIGNIFICANT AI"}
                        </strong>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Classification Role</span>
                        <strong class="meta-val val-role">${roleLabels[result.role] || result.role}</strong>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Confidence Score</span>
                        <strong class="meta-val">${Number(totalScore).toFixed(1)} pts</strong>
                    </div>
                </div>
            </div>

            <!-- EXECUTIVE SUMMARY -->
            <div class="summary-card executive-summary-card">
                <div class="executive-sparkle"></div>
                <h4>Executive AI Summary</h4>
                <p>${result.summary}</p>
            </div>

            <!-- CAPABILITIES & SCORE BREAKDOWN -->
            <div class="features-grid">
                ${capabilitiesHtml}

                <div class="summary-card scores-breakdown-card">
                    <h4>Confidence Breakdown</h4>
                    <div class="score-breakdown">
                        <div class="score-row">
                            <span>Base Semantic & Tech Evidence</span>
                            <strong>+${Math.round(result.score_breakdown.base_score || 0)}</strong>
                        </div>
                        <div class="score-row">
                            <span>Technical Integrations Bonus</span>
                            <strong>+${result.score_breakdown.technical_bonus || 0}</strong>
                        </div>
                        <div class="score-row">
                            <span>Signals Diversity Bonus</span>
                            <strong>+${result.score_breakdown.diversity_bonus || 0}</strong>
                        </div>
                        <div class="score-row">
                            <span>Strong Evidence Weightings</span>
                            <strong>+${result.score_breakdown.strong_evidence_bonus || 0}</strong>
                        </div>
                        <div class="score-row penalty">
                            <span>False Positive Penalties</span>
                            <strong>${result.score_breakdown.penalties || 0}</strong>
                        </div>
                        <div class="score-row total-row">
                            <span>Calculated Score</span>
                            <strong>${Number(totalScore).toFixed(1)}</strong>
                        </div>
                    </div>
                </div>
            </div>

            <!-- QUANTITATIVE SUMMARY GRID -->
            <div class="summary-grid">
                <div class="metric-card">
                    <div class="metric-value color-semantic">${result.evidence_summary.semantic}</div>
                    <h4>Semantic Signals</h4>
                    <p class="metric-description">AI product, service, or strategy statements discovered across textual content.</p>
                </div>
                <div class="metric-card">
                    <div class="metric-value color-technical">${result.evidence_summary.technical}</div>
                    <h4>Technical Triggers</h4>
                    <p class="metric-description">AI libraries, APIs, SDK scripts, or infrastructure code signatures identified.</p>
                </div>
                <div class="metric-card">
                    <div class="metric-value color-behavioral">${result.evidence_summary.behavioral}</div>
                    <h4>Behavioral Events</h4>
                    <p class="metric-description">Active runtime network calls or connections to AI endpoint services.</p>
                </div>
                <div class="metric-card">
                    <div class="metric-value color-organizational">${result.evidence_summary.organizational}</div>
                    <h4>Organizational Indicators</h4>
                    <p class="metric-description">Advisory, corporate governance, or compliance positioning statements.</p>
                </div>
            </div>

            <!-- EVIDENCE EXPLORER -->
            <h3 class="section-title">Evidence Log Explorer</h3>
            
            <div class="filter-bar">
                <button class="filter-btn active" id="btn-all" onclick="filterEvidence('all')">All Evidence</button>
                <button class="filter-btn" id="btn-tech" onclick="filterEvidence('technical_ai')">Technical</button>
                <button class="filter-btn" id="btn-org" onclick="filterEvidence('organizational')">Organizational</button>
                <button class="filter-btn" id="btn-sem" onclick="filterEvidence('semantic')">Semantic & Careers</button>
            </div>

            <div id="evidence-container">
    `;

    const groupedEvidence = {
        technical: [],
        semantic: [],
        organizational: []
    };

    result.evidence.forEach(e => {
        if (e.category === "technical_ai" || e.page_type === "technical") {
            groupedEvidence.technical.push(e);
        } else if (
            e.category.includes("governance") ||
            e.category.includes("consulting")
        ) {
            groupedEvidence.organizational.push(e);
        } else {
            groupedEvidence.semantic.push(e);
        }
    });

    function renderEvidenceGroup(title, evidenceList, id) {
        let section = `
            <div class="evidence-group" id="group-container-${id}">
                <div class="evidence-header" onclick="toggleEvidence('${id}')">
                    <span>${title} (${evidenceList.length})</span>
                    <span class="chevron" id="chevron-${id}">▼</span>
                </div>
                <div class="evidence-content" id="${id}">
        `;

        if (evidenceList.length === 0) {
            section += `<p class="no-evidence-message">No collected signals in this category.</p>`;
        } else {
            evidenceList.forEach(e => {
                let badgeClass = e.strength || "medium";
                section += `
                    <div class="evidence" data-category="${e.category}">
                        <div class="evidence-top">
                            <span class="evidence-badge badge-${badgeClass}">${e.category}</span>
                            <span class="evidence-sim">Sim: ${Number(e.similarity).toFixed(2)}</span>
                        </div>
                        <p class="evidence-url">URL: <a href="${e.url}" target="_blank">${e.url}</a></p>
                        <blockquote class="evidence-text">"${e.text}"</blockquote>
                    </div>
                `;
            });
        }

        section += `
                </div>
            </div>
        `;
        return section;
    }

    html += renderEvidenceGroup("Technical & Behavioral Signatures", groupedEvidence.technical, "technical-group");
    html += renderEvidenceGroup("Semantic Web Content & Job Openings", groupedEvidence.semantic, "semantic-group");
    html += renderEvidenceGroup("Organizational Strategy & Governance Indicators", groupedEvidence.organizational, "organizational-group");

    html += `
            </div>
        </div>
    `;

    document.getElementById("live-result").innerHTML = html;
    
    // Auto-open technical group if it has entries, else open semantic
    if (groupedEvidence.technical.length > 0) {
        toggleEvidence("technical-group");
    } else {
        toggleEvidence("semantic-group");
    }
}

// --------------------------------
// TASK POLLING & LOADER
// --------------------------------
async function checkStatus() {
    if (!taskId) return;

    try {
        const response = await fetch(`/task/${taskId}/`);
        const data = await response.json();

        if (data.status === "completed") {
            const statusBox = document.getElementById("status-box");
            if (statusBox) statusBox.style.display = "none";
            renderReport(data.result);
        } 
        else if (data.status === "failed") {
            const statusBox = document.getElementById("status-box");
            if (statusBox) {
                document.getElementById("progress-step").innerText = "Pipeline error: " + data.message;
                document.getElementById("progress-bar").style.width = "100%";
                document.getElementById("progress-bar").style.background = "var(--danger)";
                document.getElementById("progress-percent").innerText = "Error";
                const indicator = document.querySelector(".progress-indicator");
                if (indicator) indicator.innerText = "Check Celery worker trace logs for details.";
            }
        }
        else if (data.status === "running") {
            document.getElementById("progress-step").innerText = data.step;
            document.getElementById("progress-bar").style.width = data.progress + "%";
            document.getElementById("progress-percent").innerText = data.progress + "%";
            
            // Adjust loading helper text
            const indicator = document.querySelector(".progress-indicator");
            if (indicator) {
                if (data.progress < 35) indicator.innerText = "Launching headless browser...";
                else if (data.progress < 55) indicator.innerText = "Analyzing page DOM tree nodes...";
                else if (data.progress < 75) indicator.innerText = "Running GPU/CPU Transformer Embeddings...";
                else if (data.progress < 90) indicator.innerText = "Evaluating evidence caps & bonuses...";
                else indicator.innerText = "Compiling report metrics...";
            }

            setTimeout(checkStatus, 1500);
        } 
        else {
            setTimeout(checkStatus, 1500);
        }
    } catch (e) {
        console.error("Poller encountered an error:", e);
        setTimeout(checkStatus, 2000);
    }
}

// --------------------------------
// HISTORICAL DB LOADER
// --------------------------------
async function loadCachedReport(companyId) {
    const statusBox = document.getElementById("status-box");
    
    // Render dynamic fake loaders to make it feel smooth
    if (statusBox) {
        statusBox.style.display = "block";
        document.getElementById("progress-step").innerText = "Loading cached intelligence report...";
        document.getElementById("progress-bar").style.width = "100%";
        document.getElementById("progress-percent").innerText = "100%";
    }

    try {
        const response = await fetch(`/company/${companyId}/`);
        const data = await response.json();

        if (data.status === "completed") {
            if (statusBox) statusBox.style.display = "none";
            renderReport(data.result);
            window.scrollTo({
                top: document.getElementById("live-result").offsetTop - 30,
                behavior: "smooth"
            });
        }
    } catch (e) {
        console.error("Failed to load cached report:", e);
        if (statusBox) statusBox.style.display = "none";
    }
}

// --------------------------------
// INTERACTIVE FUNCTIONS
// --------------------------------
function toggleEvidence(id) {
    const section = document.getElementById(id);
    const chevron = document.getElementById(`chevron-${id}`);
    
    if (section) {
        section.classList.toggle("active");
        if (section.classList.contains("active")) {
            section.style.display = "block";
            if (chevron) chevron.innerText = "▲";
        } else {
            section.style.display = "none";
            if (chevron) chevron.innerText = "▼";
        }
    }
}

function filterEvidence(type) {
    // Manage active states of tab buttons
    document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.remove("active"));
    
    if (type === "all") {
        document.getElementById("btn-all").classList.add("active");
        document.querySelectorAll(".evidence-group").forEach(el => el.style.display = "block");
        document.querySelectorAll(".evidence").forEach(card => card.style.display = "block");
    } 
    else if (type === "technical_ai") {
        document.getElementById("btn-tech").classList.add("active");
        document.getElementById("group-container-technical-group").style.display = "block";
        document.getElementById("group-container-semantic-group").style.display = "none";
        document.getElementById("group-container-organizational-group").style.display = "none";
        
        // Show technical cards
        document.querySelectorAll("#technical-group .evidence").forEach(c => c.style.display = "block");
    } 
    else if (type === "organizational") {
        document.getElementById("btn-org").classList.add("active");
        document.getElementById("group-container-technical-group").style.display = "none";
        document.getElementById("group-container-semantic-group").style.display = "none";
        document.getElementById("group-container-organizational-group").style.display = "block";
        
        // Show organizational cards
        document.querySelectorAll("#organizational-group .evidence").forEach(c => c.style.display = "block");
    } 
    else if (type === "semantic") {
        document.getElementById("btn-sem").classList.add("active");
        document.getElementById("group-container-technical-group").style.display = "none";
        document.getElementById("group-container-semantic-group").style.display = "block";
        document.getElementById("group-container-organizational-group").style.display = "none";
        
        // Show semantic cards
        document.querySelectorAll("#semantic-group .evidence").forEach(c => c.style.display = "block");
    }
}

// --------------------------------
// INITIALIZATION ON LOAD
// --------------------------------
window.addEventListener("DOMContentLoaded", () => {
    // Setup target URL scanning title on loader
    const urlInput = document.getElementById("url-input");
    const scanningUrlSpan = document.getElementById("scanning-url");
    
    if (urlInput && scanningUrlSpan) {
        const form = document.getElementById("analysis-form");
        form.addEventListener("submit", () => {
            scanningUrlSpan.innerText = urlInput.value;
        });
    }

    // Trigger instant cached DB fetch or begin Celery polling
    if (typeof cachedCompanyId !== "undefined" && cachedCompanyId) {
        loadCachedReport(cachedCompanyId);
    } else if (typeof taskId !== "undefined" && taskId) {
        checkStatus();
    }
});