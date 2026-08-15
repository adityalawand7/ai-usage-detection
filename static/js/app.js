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

function formatTimeAgo(dateString) {
    if (!dateString) return "Just now";
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMin = Math.floor(diffMs / 60000);
        const diffHr = Math.floor(diffMin / 60);
        const diffDays = Math.floor(diffHr / 24);

        if (diffMin < 1) return "Just now";
        if (diffMin < 60) return `${diffMin}m ago`;
        if (diffHr < 24) return `${diffHr}h ago`;
        return `${diffDays}d ago`;
    } catch (e) {
        return "Recently";
    }
}

// --------------------------------
// PDF REPORT GENERATOR
// --------------------------------
function generatePDF(result) {
    if (!window.jspdf) {
        alert('PDF library is still loading. Please wait a moment and try again.');
        return;
    }
    try {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

    const pageW = doc.internal.pageSize.getWidth();
    const pageH = doc.internal.pageSize.getHeight();
    const marginL = 18;
    const marginR = 18;
    const contentW = pageW - marginL - marginR;
    let y = 0;

    // ---- Color Palette ----
    const colors = {
        headerBg: [15, 17, 20],
        headerAccent: [91, 138, 240],
        sectionBg: [240, 243, 250],
        primary: [91, 138, 240],
        accent: [91, 138, 240],
        success: [16, 185, 129],
        danger: [239, 68, 68],
        warning: [245, 158, 11],
        textDark: [17, 24, 39],
        textMid: [75, 85, 99],
        textLight: [107, 114, 128],
        white: [255, 255, 255],
        divider: [229, 231, 235],
        cardBg: [249, 250, 251],
        tableBorder: [209, 213, 219],
    };

    function ensureSpace(needed) {
        if (y + needed > pageH - 20) {
            doc.addPage();
            y = 20;
        }
    }

    function drawRoundedRect(x, ry, w, h, r, fillColor) {
        doc.setFillColor(...fillColor);
        doc.roundedRect(x, ry, w, h, r, r, 'F');
    }

    // ================================
    // HEADER BANNER
    // ================================
    doc.setFillColor(...colors.headerBg);
    doc.rect(0, 0, pageW, 52, 'F');

    // Accent bar
    doc.setFillColor(...colors.headerAccent);
    doc.rect(0, 52, pageW, 2, 'F');

    // Title
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(22);
    doc.setTextColor(...colors.white);
    doc.text('AI Usage Detection Report', marginL, 22);

    // Subtitle - company URL
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(11);
    doc.setTextColor(200, 200, 230);
    doc.text(result.url || 'Unknown', marginL, 32);

    // Date
    const dateStr = new Date().toLocaleDateString('en-US', {
        year: 'numeric', month: 'long', day: 'numeric'
    });
    doc.setFontSize(9);
    doc.setTextColor(160, 160, 200);
    doc.text('Generated: ' + dateStr, marginL, 42);

    // Verdict badge on right
    const verdictText = result.verdict ? 'AI ACTIVE' : 'NO AI DETECTED';
    const verdictColor = result.verdict ? colors.success : colors.danger;
    const badgeW = 38;
    const badgeX = pageW - marginR - badgeW;
    drawRoundedRect(badgeX, 17, badgeW, 10, 3, verdictColor);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...colors.white);
    doc.text(verdictText, badgeX + badgeW / 2, 23.5, { align: 'center' });

    y = 62;

    // ================================
    // KEY METRICS PANEL
    // ================================
    const totalScore = result.total_score !== undefined ? result.total_score : (result.maturity_score || 0);
    const roleLabel = roleLabels[result.role] || result.role || 'Unknown';
    const panelH = 26;

    // 1. Draw rounded rectangle background (very light gray background, subtle border)
    drawRoundedRect(marginL, y, contentW, panelH, 4, colors.cardBg);
    doc.setDrawColor(...colors.divider);
    doc.setLineWidth(0.3);
    doc.roundedRect(marginL, y, contentW, panelH, 4, 4, 'S');

    // 2. Metrics configuration
    const metrics = [
        { label: 'AI MATURITY SCORE', value: String(result.maturity_score || 0), color: colors.primary },
        { label: 'CLASSIFICATION', value: roleLabel, color: colors.textDark },
        { label: 'CONFIDENCE', value: result.confidence || 'N/A', color: colors.textDark },
        { label: 'TOTAL SCORE', value: Number(totalScore).toFixed(1) + ' pts', color: colors.textDark }
    ];

    const colW = contentW / 4;

    metrics.forEach((m, i) => {
        const colStartX = marginL + i * colW;
        const colCenterX = colStartX + colW / 2;

        // Draw vertical divider after column (except last column)
        if (i < 3) {
            doc.setDrawColor(...colors.divider);
            doc.setLineWidth(0.3);
            doc.line(colStartX + colW, y + 4, colStartX + colW, y + panelH - 4);
        }

        // Draw Category Label (Uppercase, small, gray)
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7);
        doc.setTextColor(...colors.textLight);
        doc.text(m.label, colCenterX, y + 8, { align: 'center' });

        // Draw Value (wrapped to fit column width)
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11);
        doc.setTextColor(...m.color);
        
        const valLines = doc.splitTextToSize(m.value, colW - 6);
        // Center the value lines vertically within the remaining space
        const startY = y + 11;
        const endY = y + panelH - 3;
        const availableH = endY - startY;
        const textH = valLines.length * 4.5;
        const textY = startY + (availableH - textH) / 2 + 3.5;

        doc.text(valLines, colCenterX, textY, { align: 'center' });
    });

    y += panelH + 12;

    // ================================
    // EXECUTIVE SUMMARY
    // ================================
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(...colors.primary);
    doc.text('Executive AI Summary', marginL, y);
    y += 3;

    // Accent underline
    doc.setDrawColor(...colors.headerAccent);
    doc.setLineWidth(0.8);
    doc.line(marginL, y, marginL + 42, y);
    y += 6;

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(...colors.textMid);
    const summaryLines = doc.splitTextToSize(result.summary || 'No summary available.', contentW);
    doc.text(summaryLines, marginL, y);
    y += summaryLines.length * 5 + 8;

    // ================================
    // CAPABILITIES
    // ================================
    ensureSpace(25);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(...colors.primary);
    doc.text('Detected AI Capabilities', marginL, y);
    y += 3;
    doc.setDrawColor(...colors.headerAccent);
    doc.setLineWidth(0.8);
    doc.line(marginL, y, marginL + 46, y);
    y += 7;

    if (result.capabilities && result.capabilities.length > 0) {
        let capX = marginL;
        result.capabilities.forEach(cap => {
            const label = capabilityLabels[cap] || cap;
            const tw = doc.getTextWidth(label) + 8;
            if (capX + tw > pageW - marginR) {
                capX = marginL;
                y += 10;
            }
            ensureSpace(12);
            drawRoundedRect(capX, y - 4, tw, 8, 2, colors.accent);
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(8);
            doc.setTextColor(...colors.white);
            doc.text(label, capX + 4, y + 1);
            capX += tw + 4;
        });
        y += 14;
    } else {
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(9);
        doc.setTextColor(...colors.textLight);
        doc.text('No specialized AI modules detected.', marginL, y);
        y += 10;
    }

    // ================================
    // SCORE BREAKDOWN TABLE
    // ================================
    ensureSpace(50);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(...colors.primary);
    doc.text('Confidence Score Breakdown', marginL, y);
    y += 3;
    doc.setDrawColor(...colors.headerAccent);
    doc.setLineWidth(0.8);
    doc.line(marginL, y, marginL + 52, y);
    y += 5;

    const sb = result.score_breakdown || {};
    const scoreRows = [
        ['Base Semantic & Tech Evidence', '+' + Math.round(sb.base_score || 0)],
        ['Technical Integrations Bonus', '+' + (sb.technical_bonus || 0)],
        ['Signals Diversity Bonus', '+' + (sb.diversity_bonus || 0)],
        ['Strong Evidence Weightings', '+' + (sb.strong_evidence_bonus || 0)],
        ['False Positive Penalties', String(sb.penalties || 0)],
    ];

    doc.autoTable({
        startY: y,
        margin: { left: marginL, right: marginR },
        head: [['Component', 'Points']],
        body: scoreRows,
        foot: [['Calculated Total', Number(totalScore).toFixed(1)]],
        theme: 'grid',
        headStyles: {
            fillColor: colors.headerBg,
            textColor: colors.white,
            fontStyle: 'bold',
            fontSize: 9,
            cellPadding: 4,
        },
        bodyStyles: {
            textColor: colors.textDark,
            fontSize: 9,
            cellPadding: 3.5,
        },
        footStyles: {
            fillColor: colors.sectionBg,
            textColor: colors.primary,
            fontStyle: 'bold',
            fontSize: 10,
            cellPadding: 4,
        },
        alternateRowStyles: { fillColor: [252, 251, 255] },
        columnStyles: {
            0: { cellWidth: contentW * 0.72 },
            1: { cellWidth: contentW * 0.28, halign: 'right' },
        },
        styles: {
            lineColor: colors.tableBorder,
            lineWidth: 0.3,
        },
    });

    y = doc.lastAutoTable.finalY + 12;

    // ================================
    // EVIDENCE SUMMARY GRID
    // ================================
    ensureSpace(35);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(...colors.primary);
    doc.text('Evidence Summary', marginL, y);
    y += 3;
    doc.setDrawColor(...colors.headerAccent);
    doc.setLineWidth(0.8);
    doc.line(marginL, y, marginL + 36, y);
    y += 7;

    const es = result.evidence_summary || {};
    const summaryItems = [
        { label: 'Semantic Signals', value: es.semantic || 0, color: colors.primary },
        { label: 'Technical Triggers', value: es.technical || 0, color: colors.accent },
        { label: 'Behavioral Events', value: es.behavioral || 0, color: colors.warning },
        { label: 'Organizational', value: es.organizational || 0, color: colors.success },
    ];

    const eCardW = (contentW - 12) / 4;
    const eCardH = 26;
    summaryItems.forEach((item, i) => {
        const cx = marginL + i * (eCardW + 4);

        // Card background (clean rounded rect, no border)
        drawRoundedRect(cx, y, eCardW, eCardH, 3, colors.cardBg);

        // Top bar with rounded top corners
        // 1. Draw rounded rect for the top bar
        doc.setFillColor(...item.color);
        doc.roundedRect(cx, y, eCardW, 2.2, 2.2, 2.2, 'F');
        // 2. Draw normal rect on the bottom half of the top bar to flatten bottom corners
        doc.setFillColor(...item.color);
        doc.rect(cx, y + 1.1, eCardW, 1.1, 'F');

        // Value
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(16);
        doc.setTextColor(...item.color);
        doc.text(String(item.value), cx + eCardW / 2, y + 13.5, { align: 'center' });

        // Label
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(6.5);
        doc.setTextColor(...colors.textLight);
        doc.text(item.label, cx + eCardW / 2, y + 20.5, { align: 'center' });
    });

    y += eCardH + 10;

    // ================================
    // EVIDENCE LOG
    // ================================
    if (result.evidence && result.evidence.length > 0) {
        ensureSpace(20);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(13);
        doc.setTextColor(...colors.primary);
        doc.text('Evidence Log', marginL, y);
        y += 3;
        doc.setDrawColor(...colors.headerAccent);
        doc.setLineWidth(0.8);
        doc.line(marginL, y, marginL + 28, y);
        y += 5;

        const evidenceRows = result.evidence.map(e => [
            e.category || '',
            (e.text || '').substring(0, 120) + ((e.text || '').length > 120 ? '...' : ''),
            e.url || '',
            Number(e.similarity || 0).toFixed(2),
            e.strength || '',
        ]);

        doc.autoTable({
            startY: y,
            margin: { left: marginL, right: marginR },
            head: [['Category', 'Evidence Text', 'Source URL', 'Sim.', 'Strength']],
            body: evidenceRows,
            theme: 'striped',
            headStyles: {
                fillColor: colors.headerBg,
                textColor: colors.white,
                fontStyle: 'bold',
                fontSize: 7.5,
                cellPadding: 3,
            },
            bodyStyles: {
                textColor: colors.textDark,
                fontSize: 7,
                cellPadding: 2.5,
                overflow: 'linebreak',
            },
            alternateRowStyles: { fillColor: [252, 251, 255] },
            columnStyles: {
                0: { cellWidth: 24, fontStyle: 'bold' },
                1: { cellWidth: contentW * 0.42 },
                2: { cellWidth: contentW * 0.24, textColor: colors.primary },
                3: { cellWidth: 14, halign: 'center' },
                4: { cellWidth: 18, halign: 'center' },
            },
            styles: {
                lineColor: colors.tableBorder,
                lineWidth: 0.2,
            },
        });

        y = doc.lastAutoTable.finalY + 10;
    }

    // ================================
    // GLOSSARY & DEFINITIONS
    // ================================
    ensureSpace(40);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(...colors.primary);
    doc.text('Glossary & Definitions', marginL, y);
    y += 3;
    doc.setDrawColor(...colors.headerAccent);
    doc.setLineWidth(0.8);
    doc.line(marginL, y, marginL + 46, y);
    y += 7;

    const definitions = [];
    
    const roleDesc = {
        ai_native: "Develops core AI models or AI-first products.",
        ai_product: "Builds and sells software products featuring major AI capabilities.",
        ai_enabled: "Integrates AI features into operational workflows or product modules.",
        ai_governance: "Focuses on AI compliance, risk management, safety, and policy frameworks.",
        ai_research: "Dedicated to academic/commercial machine learning research and publications.",
        ai_consumer: "Utilizes third-party AI systems to enhance internal productivity.",
        ai_marketing_only: "Showcases AI marketing positioning with limited technical implementation."
    };
    if (result.role && roleDesc[result.role]) {
        definitions.push([roleLabels[result.role] || result.role, roleDesc[result.role]]);
    }

    const capDesc = {
        general_ai: "Core AI capabilities, general reasoning engines, or foundational models.",
        coding_ai: "AI programming assistants, code generation tools, or testing copilots.",
        chatbot_ai: "Interactive conversational agents, support bots, or virtual assistants.",
        marketing_ai: "Generative AI copywriting, SEO optimization, and content creation.",
        image_ai: "Generative image generation, design helpers, or audio/video synthesizers."
    };

    if (result.capabilities && result.capabilities.length > 0) {
        result.capabilities.forEach(cap => {
            if (capDesc[cap]) {
                definitions.push([capabilityLabels[cap] || cap, capDesc[cap]]);
            }
        });
    }

    if (definitions.length > 0) {
        doc.autoTable({
            startY: y,
            margin: { left: marginL, right: marginR },
            head: [['Term / Concept', 'Definition & Context']],
            body: definitions,
            theme: 'grid',
            headStyles: {
                fillColor: colors.headerBg,
                textColor: colors.white,
                fontStyle: 'bold',
                fontSize: 8.5,
                cellPadding: 4,
            },
            bodyStyles: {
                textColor: colors.textDark,
                fontSize: 8,
                cellPadding: 3.5,
            },
            columnStyles: {
                0: { cellWidth: contentW * 0.3, fontStyle: 'bold', textColor: colors.primary },
                1: { cellWidth: contentW * 0.7 },
            },
            styles: {
                lineColor: colors.tableBorder,
                lineWidth: 0.2,
            },
        });
        y = doc.lastAutoTable.finalY + 10;
    }

    // ================================
    // FOOTER on every page
    // ================================
    const totalPages = doc.internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);

        // Footer divider
        doc.setDrawColor(...colors.divider);
        doc.setLineWidth(0.3);
        doc.line(marginL, pageH - 14, pageW - marginR, pageH - 14);

        // Left: branding
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        doc.setTextColor(...colors.textLight);
        doc.text('AI Usage Detection Engine', marginL, pageH - 9);

        // Center: confidential
        doc.setFontSize(6.5);
        doc.text('CONFIDENTIAL', pageW / 2, pageH - 9, { align: 'center' });

        // Right: page number
        doc.text('Page ' + i + ' of ' + totalPages, pageW - marginR, pageH - 9, { align: 'right' });
    }

    // ================================
    // SAVE
    // ================================
    const domain = (result.url || 'report').replace(/https?:\/\//, '').replace(/[\/\\:]/g, '-');
    doc.save('ai-report-' + domain + '.pdf');

    } catch (err) {
        console.error('PDF generation error:', err);
        alert('Failed to generate PDF: ' + err.message);
    }
}

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

    // Store result data globally for PDF download
    window.__lastReportResult = result;

    let html = `
        <div class="result animate-fade-in">
            <div class="result-header">
                <div class="result-header-top">
                    <h2>Analysis Report 
                        <span class="badge badge-${result.confidence.toLowerCase().replace(" ", "-")}">
                            ${result.confidence}
                        </span>
                    </h2>
                    <button class="download-pdf-btn" onclick="generatePDF(window.__lastReportResult)">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        <span>Download PDF</span>
                    </button>
                </div>
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
                    <div class="meta-row">
                        <span class="meta-label">Last Scanned</span>
                        <strong class="meta-val">${formatTimeAgo(result.last_analyzed)}</strong>
                    </div>
                </div>
            </div>

            <!-- EXECUTIVE SUMMARY -->
            <div class="summary-card executive-summary-card">
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
                        ${e.explanation ? `
                            <div class="evidence-explanation">
                                <strong>AI Analysis (${e.explanation_source === 'gemini' ? 'Gemini 2.5' : 'Local Heuristics'}):</strong> ${e.explanation}
                            </div>
                        ` : ""}
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

function updatePipelineSteps(progress) {
    const steps = [
        { id: "step-init", trigger: 0 },
        { id: "step-crawl", trigger: 15 },
        { id: "step-extract", trigger: 35 },
        { id: "step-semantic", trigger: 55 },
        { id: "step-fingerprint", trigger: 75 },
        { id: "step-report", trigger: 90 }
    ];

    steps.forEach((step, idx) => {
        const el = document.getElementById(step.id);
        if (!el) return;

        let isCompleted = false;
        let isActive = false;

        if (idx === steps.length - 1) {
            if (progress >= step.trigger && progress < 100) {
                isActive = true;
            } else if (progress >= 100) {
                isCompleted = true;
            }
        } else {
            const nextStep = steps[idx + 1];
            if (progress >= nextStep.trigger) {
                isCompleted = true;
            } else if (progress >= step.trigger) {
                isActive = true;
            }
        }

        if (isCompleted) {
            el.className = "checklist-item completed";
        } else if (isActive) {
            el.className = "checklist-item active";
        } else {
            el.className = "checklist-item pending";
        }
    });
}

function markErrorOnPipeline() {
    const activeEl = document.querySelector(".checklist-item.active");
    if (activeEl) {
        activeEl.className = "checklist-item error";
    } else {
        const pendingEl = document.querySelector(".checklist-item.pending");
        if (pendingEl) pendingEl.className = "checklist-item error";
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
                markErrorOnPipeline();
            }
        }
        else if (data.status === "running") {
            document.getElementById("progress-step").innerText = data.step;
            document.getElementById("progress-bar").style.width = data.progress + "%";
            document.getElementById("progress-percent").innerText = data.progress + "%";
            
            // Update step statuses in the checklist
            updatePipelineSteps(data.progress);

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
    try {
        const response = await fetch(`/company/${companyId}/`);
        const data = await response.json();

        if (data.status === "completed") {
            renderReport(data.result);
            window.scrollTo({
                top: document.getElementById("live-result").offsetTop - 30,
                behavior: "smooth"
            });
        }
    } catch (e) {
        console.error("Failed to load cached report:", e);
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