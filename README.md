# Steam Deal Finder

A lightweight web application for discovering discounted games on the Steam Store. Search by title, narrow results by genre and price, and compare current discounts using Indonesian rupiah (IDR).

## Project Overview

Steam Deal Finder retrieves current store search results and helps you find games within a budget—for example, games priced below **Rp30,000**. You can also set a **minimum discount percentage** to focus on deeper deals, such as discounts of 50% or more.

The application uses Steam Store's web search endpoint to retrieve regional Indonesian pricing and sale information. It does not use the official Steam Web API and does not require an API key.

## Core Features

- Search Steam games by title.
- Filter by Steam genre or tag, loaded dynamically with fallback tags if the request fails.
- Set minimum and maximum prices in IDR.
- Set a minimum discount percentage.
- View game titles, current and original prices, discount percentages, and cover images.
- Open a game's Steam Store page from its result.
- Cache responses locally to reduce repeated requests.
- Retry transient network failures and return readable errors to the interface.
- Provide a responsive browser-based interface backed by Flask JSON endpoints.

## Technology Stack

- **Python** — application logic and HTTP server.
- **Flask** — web application and JSON endpoints.
- **Requests** — HTTP requests to Steam Store.
- **Beautiful Soup 4** — parsing Steam search result markup.
- **HTML, CSS, and JavaScript** — browser interface.

Python dependencies are listed in [`requirements.txt`](requirements.txt).

## AI-Assisted Development Workflow

This personal project was developed using a **Multi-LLM Development Pipeline**:

1. **ChatGPT — Prompt Architect:** helped design instruction structure and plan the application logic.
2. **Claude — Core Logic Executor:** helped produce the main code structure.
3. **VS Code Codex/Copilot — Modular Feature Development and Debugging:** helped add modular features and troubleshoot implementation issues.

This workflow reflects a modern **Product Owner and System Analyst** approach: defining the product needs, translating them into a system plan, and orchestrating AI tools to support an efficient development process.

## Prerequisites

- Python 3.9 or newer.
- Internet access to retrieve Steam Store data.

### API key and environment file

No Steam Web API key is needed for the current implementation. The application uses Steam Store search and tag endpoints directly; it does not read credentials from a `.env` file. You do not need to create a `.env` file to run this project.

## Setup

### Windows quick start

Double-click `run.bat`. On its first run, it creates a local `.venv`, installs dependencies from `requirements.txt`, and starts the application.

### Manual setup

From the project directory, create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Run the Application

Start the Flask server from the project directory:

```bash
python main.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Project Structure

```text
SteamDealFinder/
├── main.py                  # Flask application and API routes
├── requirements.txt         # Python dependencies
├── run.bat                  # Windows setup and launch script
├── templates/
│   └── index.html           # Main page
├── static/
│   ├── app.js               # Browser interactions
│   └── styles.css           # Application styles
└── app/
    ├── api/                 # Steam HTTP client and response parser
    ├── core/                # Search, filtering, models, and file cache
    ├── gui/                 # Earlier desktop interface components
    └── workers/             # Earlier desktop worker components
```

## Data Source and Limitations

The application queries Steam Store web endpoints that are used by the store's own search experience. These endpoints are not documented as a stable public API and may change without notice. If Steam changes its response format, the parser may need an update. Availability and displayed prices depend on Steam's regional store data and network access.
