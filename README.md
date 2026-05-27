# AI Usage Detection Engine

An intelligent web analysis platform that detects and classifies how organizations use Artificial Intelligence across their products, infrastructure, operations, and public-facing platforms.

The engine performs semantic analysis, technical fingerprinting, behavioral inspection, and organizational reasoning to determine whether a company is:

* AI-Native
* AI Product Company
* AI-Enabled Organization
* AI Governance / Advisory Firm
* AI Research Organization
* AI Marketing Presence

---

# Features

## Intelligent AI Detection

Detects AI adoption signals from:

* Website content
* Product pages
* Technical scripts
* Network requests
* Public AI terminology
* AI infrastructure fingerprints

---

## Semantic Intelligence Engine

Uses transformer-based embeddings to:

* Understand AI-related language
* Detect contextual AI usage
* Reduce keyword-only false positives
* Analyze company positioning

---

## Technical Fingerprinting

Detects:

* OpenAI integrations
* Anthropic usage
* Hugging Face references
* LangChain
* AI SDKs
* AI APIs
* AI model infrastructure

---

## Behavioral Analysis

Inspects runtime browser activity including:

* XHR requests
* Fetch requests
* Websocket activity
* AI endpoint interactions

---

## Organizational Classification

Classifies organizations into categories such as:

* AI-Native
* AI Product Company
* AI Governance / Advisory
* AI-Enabled Enterprise
* AI Research Organization

---

## Async Distributed Scanning

Built with Celery + Redis for:

* Background analysis
* Scalable task execution
* Non-blocking frontend experience
* Real-time polling

---

## Dynamic Crawling Engine

Powered by Playwright:

* Crawls internal pages
* Executes JavaScript-heavy websites
* Extracts rendered content
* Collects scripts and runtime signals

---

## AI Intelligence Summary

Generates executive-style summaries explaining:

* How the organization uses AI
* Whether AI is operational or marketing-oriented
* The confidence level of the analysis

---

# Tech Stack

| Layer               | Technology            |
| ------------------- | --------------------- |
| Backend             | Django                |
| Task Queue          | Celery                |
| Broker              | Redis                 |
| Crawling Engine     | Playwright            |
| AI / NLP            | Sentence Transformers |
| ML Framework        | PyTorch               |
| Semantic Similarity | scikit-learn          |
| HTML Parsing        | BeautifulSoup         |
| Frontend            | HTML, CSS, JavaScript |
| Containerization    | Docker                |

---

# System Architecture

```text
                ┌─────────────────────┐
                │  User Submits URL   │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Django Frontend/API │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Celery Task Queue   │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Playwright Crawler  │
                └──────────┬──────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
   ┌────────────────┐ ┌──────────────┐ ┌─────────────────┐
   │ Semantic NLP   │ │ Fingerprints │ │ Behavioral Scan │
   └────────────────┘ └──────────────┘ └─────────────────┘
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                ┌─────────────────────┐
                │ Reasoning Engine    │
                └──────────┬──────────┘
                           ▼
                ┌─────────────────────┐
                │ Classification +    │
                │ Evidence Summary    │
                └──────────┬──────────┘
                           ▼
                ┌─────────────────────┐
                │ Frontend Dashboard  │
                └─────────────────────┘
```

---

# Detection Pipeline

## Step 1 — Dynamic Crawling

The crawler visits internal company pages using Playwright and collects:

* Rendered HTML
* Scripts
* Network activity
* Internal links

---

## Step 2 — Semantic Analysis

Website content is chunked and analyzed using sentence-transformer embeddings.

The engine compares semantic meaning instead of relying only on keywords.

---

## Step 3 — Technical Fingerprinting

The engine scans:

* Scripts
* API calls
* SDK references
* AI providers

for known AI technologies.

---

## Step 4 — Behavioral Detection

Runtime browser activity is inspected to identify:

* AI API calls
* Model interactions
* Streaming endpoints
* AI-driven workflows

---

## Step 5 — Organizational Reasoning

The reasoning engine:

* Scores evidence
* Removes weak signals
* Reduces false positives
* Determines organizational AI role
* Generates confidence levels

---

# Example Output

```json
{
  "url": "https://www.coderabbit.ai",
  "verdict": true,
  "confidence": "HIGH CONFIDENCE",
  "role": "ai_native",
  "summary": "This organization appears deeply AI-native with strong evidence of AI-powered products and technical AI integrations.",
  "evidence_summary": {
    "semantic": 49,
    "technical": 21,
    "behavioral": 4,
    "organizational": 2
  }
}
```

---

# Screenshots

## Homepage

<img width="1919" height="1018" alt="image" src="https://github.com/user-attachments/assets/27b47e6f-2f18-4561-954c-4eeabed985b7" />


---

## Live Analysis

<img width="1919" height="718" alt="image" src="https://github.com/user-attachments/assets/e16c2fc5-2868-44fe-bcac-426eea202cf3" />


---

## Results

<img width="1919" height="1015" alt="image" src="https://github.com/user-attachments/assets/e388d38b-4b26-48fd-b75e-e55b98ed66c9" />


---
## Evidence Breakdown

<img width="1919" height="1017" alt="image" src="https://github.com/user-attachments/assets/6a22180d-78df-4768-a2c3-10abc0f519d8" />


---

# Local Setup

## Clone Repository

```bash
git clone <your-repo-url>
cd ai-usage-detection
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

---

## Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Install Playwright Browsers

```bash
playwright install
```

---

## Start Redis

```bash
docker run -d -p 6379:6379 redis
```

---

## Start Celery Worker

```bash
celery -A config worker --pool=solo -l info
```

---

## Start Django Server

```bash
python manage.py runserver
```

---

# Future Enhancements

* Smart crawl prioritization
* AI-generated intelligence summaries
* Company comparison engine
* PDF export reports
* Scan history persistence
* Real-time crawl visualization
* Industry benchmarking
* Risk scoring
* Enterprise API mode
* Dashboard analytics

---

# Challenges Solved

* Crawling JavaScript-heavy websites
* Async distributed processing
* Reducing AI false positives
* Semantic reasoning over keyword matching
* Evidence normalization
* Dynamic link discovery
* Technical fingerprint detection
* Runtime behavior analysis

---

# Project Goals

This project was built to explore:

* AI adoption intelligence
* Web-scale semantic analysis
* Automated company profiling
* AI infrastructure detection
* Distributed crawling systems
* Evidence-driven reasoning engines

---

# License

MIT License

---

# Author

Aditya Dadasaheb Lawand
