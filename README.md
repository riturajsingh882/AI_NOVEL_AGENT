## AI-Powered Novel Writing Assistant 🤖📖

![GitHub](https://img.shields.io/github/license/riturasingh882/AI_NOVEL)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![AI](https://img.shields.io/badge/AI-Kluster%20API-orange)

An automated system for generating fiction novels using AI, with built-in version control and progress tracking.

## Features ✨

- **AI-Powered Writing**: Integrated with Kluster AI API for continuous story generation
- **GitHub Automation**: Daily commits with version control
- **Progress Tracking**: JSON-based progress monitoring
- **Chapter Management**: Automatic chapter transitions every 10 pages
- **Context Awareness**: Maintains story continuity using previous 2000 characters
- **Scheduling**: 24-hour automated writing cycles
- **Error Handling**: Comprehensive logging and recovery system

## Project Structure 🗂️

```plaintext
AI_AGENT_FICT1/
│
├── AI_Novel/
│   ├── assets/          # Empty directory
│   ├── chapters/        # Contains generated chapters
│   │   └── chapter_01.md
│   ├── config/
│   │   ├── api_config.yaml
│   │   └── book_config.yaml
│   ├── novel_env/       # Virtual environment
│   └── scripts/
│       ├── __pycache__/
│       ├── __init__.py
│       ├── github_ops.py
│       └── writer_agent.py
│
├── book_progress.json
├── diag.py
├── README.md
├── requirements.txt
├── scheduler.log
└── test_run.py


## Installation 💻
Prerequisites
Python 3.10+
Git
Kluster AI API key


