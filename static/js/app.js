

const roleLabels = {

    ai_native:
        "AI-Native Company",

    ai_product:
        "AI Product Company",

    ai_enabled:
        "AI-Enabled Organization",

    ai_governance:
        "AI Governance & Advisory",

    ai_research:
        "AI Research Organization",

    ai_consumer:
        "AI Consumer",

    ai_marketing_only:
        "AI Marketing Presence",

    unknown:
        "Unknown"
};

async function checkStatus() {

    const response = await fetch(
        `/task/${taskId}/`
    );

    const data = await response.json();

    if (data.status === "completed") {

        // remove loading state
        document.getElementById(
            "status-box"
        ).style.display = "none";

        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: "smooth"
        });

        let html = `

                <div class="result">

                    <hr>

                    <h2>
                        Analysis Complete
                        <span class="badge">
                            ${data.result.confidence}
                        </span>
                    </h2>

                    <p>
                        <strong>Company:</strong>
                        ${data.result.url}
                    </p>

                    <p>
                        <strong>Uses AI:</strong>
                        ${data.result.verdict}
                    </p>

                    <p>
                        <strong>Classification:</strong>
                        ${roleLabels[data.result.role]}
                    </p>

                    <div class="summary-card">

                        <h4>
                            AI Intelligence Summary
                        </h4>

                        <p>
                            ${data.result.summary}
                        </p>

                    </div>

                    <div class="summary-grid">

                        <div class="summary-card">
                            <h4>
                                Website AI Signals
                            </h4>
                            <p>
                                ${data.result.evidence_summary.semantic}
                                AI-related product or service indicators detected across website content.
                            </p>
                        </div>

                        <div class="summary-card">
                            <h4>
                                Technical AI Integrations
                            </h4>
                            <p>
                                ${data.result.evidence_summary.technical}
                                AI SDKs, APIs, scripts, or model integrations identified.
                            </p>
                        </div>

                        <div class="summary-card">
                            <h4>
                                Live AI Activity
                            </h4>
                            <p>
                                ${data.result.evidence_summary.behavioral}
                                runtime AI-related network behaviors observed during analysis.
                            </p>
                        </div>

                        <div class="summary-card">
                            <h4>
                                Organizational Indicators
                            </h4>
                            <p>
                                ${data.result.evidence_summary.organizational}
                                strategic or operational AI positioning indicators detected.
                            </p>
                        </div>

                    </div>

                    <h3 class="section-title">
                        Evidence Collected
                    </h3>
            `;

        data.result.evidence.forEach(e => {

            html += `

                    <div class="evidence">

                        <p>
                            <strong>Evidence Type:</strong>
                            ${e.category}
                        </p>

                        <p>
                            <strong>Source URL:</strong>
                            ${e.url}
                        </p>

                        <p class="score">
                            Relevance Score:
                            ${Number(e.similarity).toFixed(2)}
                        </p>

                        <p>
                            ${e.text}
                        </p>

                    </div>
                `;
        });

        html += `</div>`;

        document.getElementById(
            "live-result"
        ).innerHTML = html;

    }

    else if (data.status === "running") {

        document.getElementById(
            "progress-step"
        ).innerText = data.step;

        document.getElementById(
            "progress-bar"
        ).style.width = data.progress + "%";

        document.getElementById(
            "progress-percent"
        ).innerText = data.progress + "%";

        setTimeout(
            checkStatus,
            1500
        );
    }

    else {

        setTimeout(
            checkStatus,
            1500
        );
    }
}

checkStatus();