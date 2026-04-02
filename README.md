# Scrapyard

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A visual web scraping desktop application built with Python. Create scraping workflows through a GUI, extract data from websites, and export results to Excel.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Workflow Nodes](#workflow-nodes)
  - [Extract](#extract)
  - [Loop](#loop)
  - [Visit](#visit)
  - [Click](#click)
  - [Scroll](#scroll)
  - [Repeat](#repeat)
  - [Ensure Auth](#ensure-auth)
- [Browser Features](#browser-features)
  - [Headless Mode](#headless-mode)
  - [Stealth Browsing](#stealth-browsing)
  - [Cookie Management](#cookie-management)
- [Authentication](#authentication)
- [Data Export](#data-export)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)

## Overview

Scrapyard is a general-purpose web crawler/scraper application that provides a visual, no-code interface for building web scraping workflows. The application uses a tree-based workflow builder where each step is a "node" that performs a specific action.

## Features

- **Visual Workflow Builder**: Build scraping workflows by dragging and configuring nodes
- **Multiple Node Types**: Extract data, loop through elements, click buttons, scroll pages, and more
- **Stealth Browsing**: Uses undetected-chromedriver to avoid bot detection
- **Cookie Persistence**: Save and reload authentication sessions
- **Headless/Visible Modes**: Switch between headless for speed and visible for debugging
- **Real-time Logging**: See scraping progress in the built-in console
- **Excel Export**: Export scraped data to `.xlsx` format
- **Deduplication**: Built-in option to skip duplicate data during extraction
- **Thread-Safe Execution**: Runs scraping in background thread, UI remains responsive

## Requirements

- **Python 3.x** (3.8 or higher recommended)
- **Google Chrome** browser installed on your system
- **Windows/Linux/macOS**

## Installation

1. Clone or download this repository
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate   # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Quick Start

1. **Enter a Starting URL**: Enter the website URL you want to scrape in the "Starting URL" field
2. **Build Your Workflow**: Click the action buttons to add nodes to your workflow
3. **Configure Nodes**: Select a node in the tree and fill in its properties (CSS selectors, etc.)
4. **Run the Scraper**: Click "Run Scraper" to start
5. **Export Data**: After scraping, click "Export to Excel" to save results

### Example Workflow

```
START
├── Ensure Auth (if login required)
│   └── Login URL: https://example.com/login
├── Loop (For Each Element)
│   └── Selector: .item
│   ├── Extract (Title)
│   │   └── Selector: .title, Name: Title
│   └── Visit (Open Details)
│       └── Selector: a.detail
│           └── Extract (Price)
│               └── Selector: .price, Name: Price
└── Export to Excel
```

## Workflow Nodes

### Extract

Extract data from the current page or element.

| Property | Description |
|----------|-------------|
| `selector` | CSS selector for the target element |
| `name` | Column name for the extracted data |
| `attr` | HTML attribute to extract (e.g., `href`, `src`) - leave empty for text |
| `multi` | Extract multiple values instead of just the first |
| `sep` | Separator for multi-mode (default: comma) |
| `formatting` | Preserve newlines in extracted text |
| `discard_duplicates` | Skip extracting duplicate content (text) or URLs (links) |

### Loop

Iterate over multiple elements and execute child steps for each.

| Property | Description |
|----------|-------------|
| `selector` | CSS selector to find multiple elements |
| `limit` | Maximum number of items to process (0 = unlimited) |
| `children` | Steps to execute for each item |

### Visit

Navigate to a link and execute child steps, then return to the original page.

| Property | Description |
|----------|-------------|
| `selector` | CSS selector for the link |
| `children` | Steps to execute on the visited page |

### Click

Click a button or link and optionally wait for a result.

| Property | Description |
|----------|-------------|
| `selector` | CSS selector for the clickable element |
| `wait_strategy` | How to wait after clicking |
| `wait_selector` | Selector to watch for (for element_appears/disappears) |
| `wait_timeout` | Timeout for wait strategy in seconds |
| `delay_after` | Delay after click completes |
| `optional` | Don't fail if element not found |

**Wait Strategies:**
- `none`: No waiting
- `dom_change`: Wait for HTML to change
- `url_change`: Wait for URL to change
- `element_appears`: Wait for selector to appear
- `element_disappears`: Wait for selector to disappear

### Scroll

Scroll the page to load lazy content.

| Property | Description |
|----------|-------------|
| `mode` | Scroll direction: `bottom`, `top`, or `selector` |
| `wait_strategy` | `dom_change`, `height_change`, or `none` |
| `wait_timeout` | Timeout for wait in seconds |

### Repeat

Repeat actions multiple times or until a condition is met.

| Property | Description |
|----------|-------------|
| `mode` | Type of repeat condition |
| `max_iter` | Maximum iterations (for fixed/count_lt modes) |
| `count_value` | Value for count_lt mode |
| `children` | Steps to execute in each iteration |

**Repeat Modes:**
- `fixed`: Run a fixed number of times
- `exists`: Repeat while selector exists
- `not_exists`: Repeat while selector does not exist
- `count_lt`: Repeat while count is less than value

### Ensure Auth

Handle authentication via cookies or manual login.

| Property | Description |
|----------|-------------|
| `login_url` | URL to use for login (defaults to current page) |
| `success_selector` | CSS selector that indicates successful login |
| `cookie_name` | Custom name for cookie file (defaults to domain) |
| `stay_visible` | Keep browser visible after auth (debug mode) |

## Browser Features

### Headless Mode

By default, Scrapyard runs in headless mode (no visible browser window) for better performance. You can switch to visible mode for debugging.

**Automatic Switching:**
- EnsureAuth automatically switches to visible during login
- After login, it can switch back to headless

### Stealth Browsing

Scrapyard uses `undetected-chromedriver` to:
- Avoid bot detection
- Mimic real browser behavior
- Bypass common anti-scraping measures

### Cookie Management

- Cookies are automatically saved after login
- Saved cookies are reloaded on subsequent runs
- Cookie files are stored in the `cookies/` directory
- Each domain gets its own cookie file (`{domain}.pkl`)

## Authentication

The EnsureAuth node handles website authentication:

### Flow

1. Load existing cookies from file (if any)
2. Visit the login page
3. If `success_selector` configured: Check if already logged in
4. If no selector: Ask user to verify login status
5. If not logged in: Show visible browser for manual login
6. Save cookies after successful login
7. Switch back to headless mode (if configured)

### Tips for Authentication

- Set a `success_selector` for automatic login detection (e.g., a profile avatar element that only appears when logged in)
- Use `stay_visible` for debugging auth issues
- Cookies are domain-specific, so test on the same domain

## Data Export

Scraped data is exported to Excel format (.xlsx):

1. Click "Export to Excel" after scraping completes
2. Choose a save location in the file dialog
3. Data is exported with columns: `Source URL`, `Extracted Data`

### Handling Infinite Scroll

For pages with infinite scroll (loading more content as you scroll), use the `Repeat` node with `Scroll` and `Extract` nodes:

```
START
└── Repeat (mode: exists or fixed)
    ├── Scroll (mode: bottom)
    └── Extract (Discard Duplicates: checked)
```

**How it works:**
- The `Discard Duplicates` option tracks extracted content using content hashes (for text) or URLs (for links)
- Each unique item is extracted once; duplicates are silently skipped
- Empty rows (from duplicates) are automatically filtered out from the final results
- Each Extract node has independent deduplication tracking

**Tips:**
- Use `multi` mode to extract multiple values at once
- Check the console log for `[duplicate skipped]` messages to verify deduplication is working

## Architecture

Scrapyard follows the MVC (Model-View-Controller) pattern:

```
Scrapyard/
├── main.py                 # Application entry point
├── controller/
│   └── app_controller.py  # Main controller
├── model/
│   ├── app_model.py       # Main model
│   ├── engine.py           # Workflow execution engine
│   ├── browser.py          # Selenium driver wrapper
│   ├── context.py          # Thread-safe context
│   ├── xls_exporter.py     # Excel export
│   └── nodes/              # Workflow node implementations
│       ├── base.py         # Base node class
│       ├── registry.py     # Node registry
│       ├── extract.py      # Extract node
│       ├── loop.py         # Loop node
│       ├── visit.py        # Visit node
│       ├── click.py        # Click node
│       ├── scroll.py       # Scroll node
│       ├── repeat.py       # Repeat node
│       └── auth.py         # Auth node
├── view/
│   └── app_view.py         # GUI view
└── cookies/                # Stored cookies
```

## Troubleshooting

### ChromeDriver Version Mismatch

If you see an error like "ChromeDriver only supports Chrome version X", run:
```bash
pip install --upgrade webdriver-manager
```

Or manually download the correct ChromeDriver version from [ChromeDriver Downloads](https://sites.google.com/chromium.org/driver/).

### Elements Not Found

- **Headless vs Visible**: Some sites behave differently in headless mode. Use `Stay Visible` or manual login to debug.
- **JavaScript Required**: Ensure the site loads properly with JavaScript enabled
- **Dynamic Content**: Add Scroll nodes to load lazy content
- **Wrong Selector**: Verify CSS selectors in browser DevTools

### Authentication Issues

- Cookies may expire - delete the `.pkl` file in `cookies/` and login again
- Sites may require additional headers or user-agent rotation
- Some sites detect and block automation tools

### Bot Detection

Scrapyard uses stealth measures, but:
- Some sites have aggressive anti-bot systems
- Consider using proxies for sensitive scraping
- Add delays between requests

## License

MIT License
