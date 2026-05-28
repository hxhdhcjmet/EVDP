# EVDP - Easy & Visual Data Processor

[中文说明](README.md)

EVDP is a Streamlit-based application for public-opinion data processing and safety analysis. It provides local workflows for multi-platform data collection, unified cleaning, sentiment analysis, IP location analysis, user profiling, anomaly detection, risk scoring, and report archiving.

The project is designed for coursework, open-source demos, local analysis prototypes, and public-opinion monitoring experiments.

## Key Features

- Multi-platform collectors: Bilibili, Douyin, Baidu Tieba, and Zhihu entry points with cookie or QR-code login flows.
- Unified data cleaning: normalizes comments, replies, user fields, timestamps, IP locations, and content metadata.
- Safety analysis pipeline: combines sentiment, sensitive words, regional concentration, suspicious users, and anomaly detection.
- AI-assisted analysis: supports user-configured OpenAI-compatible APIs for summaries, risk review, and Q&A.
- Interactive dashboard: Streamlit UI for file preview, configurable analysis, visual charts, and report downloads.
- Report center: summarizes local datasets, platform distribution, empty files, and exported safety reports.
- Multi-format reports: exports Markdown, JSON, HTML, and TXT reports.

## Pages

| Page | Description |
| --- | --- |
| `01_bilibili_page` | Bilibili video comment collection, basic analysis, word cloud, and location charts |
| `02_douyin_page` | Douyin video comment collection, cookie validation, and comment visualization |
| `03_tieba_page` | Baidu Tieba post/reply collection with optional image download |
| `04_zhihu_page` | Zhihu question/answer comment collection with login support |
| `05_file_page` | Local data browser for JSON, JSONL, and image files |
| `06_security_dashboard` | Full public-opinion safety pipeline with cleaning, sentiment, IP, user, anomaly, risk scoring, and export |
| `07_sentiment_analysis` | Standalone sentiment analysis and high-risk comment export |
| `08_data_cleaning` | Standalone data cleaning and quality statistics |
| `09_report_center` | Dataset summary, platform distribution, report archive, and quality overview |
| `10_ai_analysis` | AI summaries, risk review, response recommendations, and custom Q&A |

## Quick Start

### Docker recommended

Linux / macOS / WSL:

```bash
bash ./run.sh
```

Windows PowerShell:

```powershell
.\run.ps1
```

Manual Docker run:

```bash
docker build -t evdp .
docker run -d -p 8501:8501 -v ./data:/home/EVDP/data -v ./assets:/home/EVDP/assets evdp
```

Open `http://localhost:8501` after startup.

### Local Python

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
streamlit run app.py
```

Windows activation:

```powershell
.\venv\Scripts\activate
```

You can also use `setup.sh` or `setup.ps1` for dependency installation.

## Recommended Workflow

1. Collect data from one of the platform pages. Results are stored under `data/`.
2. Preview JSONL, JSON, or image files in `05_file_page`.
3. Clean data in `08_data_cleaning`, or run the full pipeline directly in `06_security_dashboard`.
4. Enable or disable IP analysis, user profiling, and anomaly detection as needed.
5. Export reports and review local archives in `09_report_center`.
6. Configure an API provider in `10_ai_analysis` when AI-assisted review is needed.

## Data And Reports

- Collected data is stored in `data/`.
- Uploaded files are temporarily stored under `evdp_uploads/` in the system temp directory.
- Reports are saved next to the analyzed source file by default.
- Sensitive word lists live in `assets/sensitive_words/`.
- Stopword lists live in `assets/stopwords/`.
- AI analysis sends only statistics and sampled comments to the user-configured model service by default. API keys are kept in the current session unless the user chooses otherwise.

## Project Structure

```text
EVDP/
├── app.py                    # Streamlit home page
├── pages/                    # Streamlit feature pages
├── core/
│   ├── analysis/             # Main analysis modules: cleaning, sentiment, IP, user profiling, pipeline, reports
│   ├── security/             # Safety modules such as anomaly detection and bot detection
│   ├── spider/               # Platform collectors
│   └── paths.py              # Shared path utilities
├── assets/                   # Fonts, sensitive words, stopwords
├── data/                     # Local datasets and exported reports
├── Dockerfile
├── requirements.txt
├── run.sh / run.ps1
└── setup.sh / setup.ps1
```

## Analysis Notes

EVDP produces local heuristic risk scores for triage and demonstration. They are not a replacement for human review.

- Sentiment risk: based on SnowNLP or a fallback dictionary, sensitive words, and text features.
- IP location: coverage ratio, Gini coefficient, top-region concentration, and spread pattern.
- User profiling: comment count, repeated content, short-comment ratio, timing regularity, and platform-specific metadata.
- Anomaly detection: volume spikes, location concentration, negative sentiment spikes, repeated content, and sensitive keyword concentration.
- AI-assisted review: natural-language analysis based on local statistics and sampled comments. Human review is still required.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `ModuleNotFoundError` | Activate the virtual environment and rerun `pip install -r requirements.txt` |
| Playwright browser fails to start | Run `python -m playwright install chromium` |
| Port 8501 is occupied | Stop the process using the port or run Streamlit on another port |
| Chinese text is garbled in charts | Ensure `assets/fonts/simhei.ttf` exists |
| Platform login expired | Refresh cookies or scan the QR code again on the related page |

## Roadmap

- Add a database synchronization page.
- Add a sensitive-word management page.
- Add multi-file comparison analysis.
- Improve task status tracking and retry handling.
- Add more standard automated tests.

## Disclaimer

This project is for learning, research, local analysis, and demos only. Please follow the target platforms' terms of service, robots policies, and applicable laws. Do not use it for commercial scraping, access-control bypassing, or high-pressure crawling.
