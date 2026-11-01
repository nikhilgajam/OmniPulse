# 🔔 OmniPulse

> Automated 6-hour intelligence pulse running via GitHub Actions.  
> Delivers **10 curated feeds** — precious metals, financial markets, crypto, local & national news, viral discussions, trending AI models, open-source repos, and cosmic wonders — directly to your **Telegram**.

![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Scheduled-2088FF?logo=github-actions&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?logo=telegram&logoColor=white)

---

## 📦 What You Get Every 6 Hours (10 Curated Feeds)

| # | Feed | Category | What's Extracted |
|:---:|---|---|---|
| 1 | 🪙 **Gold & Silver (Hyderabad)** | Commodities | 24K, 22K, 18K gold per **10 grams** + Silver (10g & 1 Kg) |
| 2 | 📊 **Indian Market Snapshot** | Finance | **NIFTY 50**, **SENSEX** (with % change) & **USD / INR** rate |
| 3 | ₿ **Crypto Pulse** | Crypto Assets | **Bitcoin (BTC)**, **Ethereum (ETH)**, **Solana (SOL)** in ₹ and $ + 24h % change + `[🔗]` links |
| 4 | 📰 **Top India News** | National News | Top 3 verified headlines + news sources + `[🔗]` links |
| 5 | 🏙️ **Hyderabad City News** | Local News | Top 3 local Hyderabad/Telangana developments + `[🔗]` links |
| 6 | 🔥 **Reddit Popular Topics** | Viral Trends | Top 3 trending discussions across Reddit + `[🔗]` links |
| 7 | ⚡ **Tech & AI Pulse** | Tech News | **Top 10** Hacker News stories + points + comments + `[🔗]` links |
| 8 | 🤖 **Hugging Face Trending AI** | AI & Machine Learning | Top 3 breakout AI models + likes + pipeline task + `[🔗]` links |
| 9 | ⭐ **GitHub Trending Repos** | Open Source | Top 3 breakout repositories created this week + stars + `[🔗]` links |
| 10 | 🌌 **NASA Picture of the Day** | Astronomy | Daily deep-space photography title + explanation + `[🔗]` link |

---

## 💡 Key Features & Things You Should Know

### 1. What does `pts` mean in Tech & AI News?
In the **Tech & AI Pulse** feed, each item displays a point count and comment count:
```text
1. Backdoor in Claude Code extension [🔗](https://...)
   ↳ 941 pts • 537 comments
```
* **`pts` stands for Points (Upvotes)** on **Hacker News** (operated by Y Combinator).
* Hacker News is one of the most respected tech communities for software engineers, AI researchers, and founders. Each upvote from a member awards **1 point**.
* **How to interpret the score**:
  * **50 – 150 pts**: Good niche discussion or interesting utility.
  * **200 – 400 pts**: Solid front-page trending article.
  * **500+ to 1,000+ pts**: 🔥 **Major breaking story**, critical zero-day vulnerability, or milestone AI release.
* **`comments`**: Indicates active community debate, developer feedback, and analysis.

### 2. Interactive `[🔗]` Links
Every headline across news, tech, Reddit, GitHub repos, and AI models features an inline `[🔗]` link icon. Tapping the icon in Telegram opens the full article, repository, or discussion thread directly in your browser.

### 3. Gold Prices are per 10 Grams
In line with Indian retail standards, all gold prices (24K, 22K, 18K) for Hyderabad are explicitly extracted and formatted for **10 grams**, alongside silver for both 10 grams and 1 kilogram.

### 4. Zero Cloud Blocking (Reliable Scrapers)
Reddit and various APIs aggressively block cloud runners (like GitHub Actions IPs) with HTTP 403 / 429 errors. This project routes through public syndication endpoints and RSS bridges, ensuring **100% uptime and no IP blocks** during scheduled runs.

---

## 📱 Sample Telegram Message Previews

```text
🪙 *Gold & Silver Prices - Hyderabad*

🥇 *Gold 24K (10g):* ₹1,38,880(-3,380)
🥇 *Gold 22K (10g):* ₹1,27,300(-3,100)
🥇 *Gold 18K (10g):* ₹1,04,160(-2,530)

🥈 *Silver (10g):* ₹2,000
🥈 *Silver (1 Kg):* ₹2,00,000
```

```text
📊 *Indian Market Snapshot*

• *NIFTY 50:* 23,053.10 (+0.51%)

• *SENSEX:* 74,459.53 (+0.42%)

• *USD / INR:* ₹95.07
```

```text
₿ *Crypto Pulse*

• 🟠 *Bitcoin (BTC):* ₹7,359,914 ($77,544.00) • 🟢 +0.03% [🔗](https://...)

• 🔹 *Ethereum (ETH):* ₹213,531 ($2,249.76) • 🟢 +0.86% [🔗](https://...)

• 🟣 *Solana (SOL):* ₹9,105 ($95.93) • 🟢 +0.94% [🔗](https://...)
```

```text
⚡ *Tech & AI Pulse*

1. *Backdoor in Claude Code for VS Code extension on Cursor Marketplace* [🔗](https://...)
   ↳ 941 pts • 537 comments

2. *Serbia just elected the world's brainiest parliament* [🔗](https://...)
   ↳ 582 pts • 338 comments

3. *The $6.3B Binance hack was pulled off in just 20 minutes* [🔗](https://...)
   ↳ 531 pts • 376 comments

... (Top 10 total)
```

```text
🤖 *Hugging Face Trending AI*

1. *Nanbeige/Nanbeige4.3-33B* [🔗](https://huggingface.co/Nanbeige/Nanbeige4.3-33B)
   ↳ ❤️ 840 likes • Text Generation

2. *deepseek-ai/DeepSeek-V4.1-Flash-1017* [🔗](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017)
   ↳ ❤️ 4,072 likes • Image Text To Text

3. *LiquidAI/LFM3-1.7B* [🔗](https://huggingface.co/LiquidAI/LFM3-1.7B)
   ↳ ❤️ 606 likes • Text Generation
```

```text
🌌 *NASA Astronomy Picture*

🔭 *Haunting the Cepheus Flare* [🔗](https://science.nasa.gov/...)
_Spooky shapes seem to haunt this dusty expanse, drifting through the night in the royal constellation Cepheus_
```

---

## 🚀 Setup Guide (Step-by-Step)

### Step 1 — Create a Telegram Bot

1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot`.
3. Choose a friendly name (e.g., `My Daily Monitor`).
4. Choose a username ending in `bot` (e.g., `hyd_daily_monitor_bot`).
5. BotFather will provide your **HTTP API Token**:
   ```
   7123456789:AAH1bGciOiJSUzI1NiIsInR5cCI6Ikp...
   ```
6. ✅ Save this as your `TELEGRAM_BOT_TOKEN`.

---

### Step 2 — Set Up Your Telegram Channel (Recommended)

A **Telegram Channel** is the best delivery method for OmniPulse — it works like a one-way broadcast newsletter. Anyone who joins your channel automatically receives every update, with no ID management needed.

#### 2a — Create the Channel
1. Open Telegram → tap the **pencil / compose** icon → **New Channel**.
2. Give it a name and optional description (e.g., `OmniPulse Daily Feed`).
3. Choose **Public** (gives it a shareable `@username`) or **Private**.
4. ✅ Your channel is ready.

#### 2b — Add Your Bot as Admin
1. Open the channel → tap the channel name at the top → **Administrators** → **Add Administrator**.
2. Search for your bot's username and select it.
3. Enable the **"Post Messages"** permission.
4. Tap **Save**.

#### 2c — Get the Channel ID

**Option 1 — Public channel** (easiest): Use the `@username` directly as the chat ID.
```
@YourChannelName
```

**Option 2 — Numeric ID** (works for both public & private, and never changes even if you rename the channel):
1. Send any message in the channel.
2. Open this URL in your browser (replace with your actual token):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. Find your channel in the response and copy the `id` value — it will be a **negative number**:
   ```json
   "chat": {
     "id": -1001234567890,
     "title": "OmniPulse Daily Feed",
     "type": "channel"
   }
   ```

> **Tip:** If `getUpdates` returns an empty result, forward any message from your channel to **[@userinfobot](https://t.me/userinfobot)** on Telegram — it will instantly reply with the channel's numeric ID.

> **Note:** The numeric ID is the more robust choice — if you ever rename your channel's `@username`, the numeric ID stays the same forever.

#### Alternative — Personal Chat or Group
If you prefer to receive messages privately or in a group instead of a channel:

- **Personal chat**: Search for **[@userinfobot](https://t.me/userinfobot)** → send `/start` → note your numeric **Id** (e.g., `123456789`). Then send `/start` to your own bot to activate it.
- **Group**: Add the bot as admin, send a message in the group, then use `getUpdates` to find the group's negative chat ID.

---

### Step 3 — Push to GitHub

```bash
cd omnipulse
git add .
git commit -m "Configure OmniPulse with 10 monitoring feeds and Telegram alerts"
git push -u origin main
```

### Step 4 — Add Repository Secrets

In your GitHub repository:
1. Navigate to **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret** and add:

| Secret Name | Value | Example |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather | `7123456789:AAH1bG...` |
| `TELEGRAM_CHAT_ID` | Channel `@username` or numeric ID | `@mychannel` or `-1001234567890` |

> **Multiple recipients?** If you want to send to several individual chats, set `TELEGRAM_CHAT_IDS` (note the **S**) as a comma-separated list of chat IDs instead:
> ```
> 123456789,987654321,111222333
> ```
> The bot will send to each ID individually. `TELEGRAM_CHAT_ID` (single) is used as a fallback if `TELEGRAM_CHAT_IDS` is not set.

### Step 5 — Test & Run

1. Go to the **Actions** tab in your repository.
2. Select **OmniPulse** from the workflow list.
3. Click **Run workflow** → **Run workflow**.
4. Check your Telegram channel in ~30 seconds!

---

## ⚙️ Configuration & Customization

All jobs are configured in [`config.json`](config.json). You can adjust any job without altering Python code.

### Built-in Extractor Types

| Type | Used For | Key Fields |
|---|---|---|
| `gold_silver` | Hyderabad 10g Gold & Silver rates | `silver_url` |
| `markets` | Nifty 50, Sensex & USD/INR | Automatically tracked |
| `rss` | Google News India & Hyderabad News | `count` (number of headlines) |
| `reddit` | Reddit Popular discussions | `count` (number of posts) |
| `hackernews` | Top Hacker News tech & AI stories | `count` (default: 10) |
| `huggingface` | Trending AI Models & Weights | `count` (default: 3) |
| `github_trending`| Breakout repositories created this week | `count` (default: 3), `days` |
| `crypto` | Live crypto prices (BTC/ETH/SOL) | Automatically tracked |
| `nasa_apod` | NASA Astronomy Picture of the Day | Automatically tracked |
| `json` | Generic REST APIs | JSONPath field mapping |
| `css` | Generic HTML web scraping | CSS selectors |
| `regex` | Raw text pattern extraction | Regex with capture groups |

---

## 🕐 Execution Schedule

The workflow runs on a cron schedule in [`.github/workflows/monitor.yml`](.github/workflows/monitor.yml):

```yaml
schedule:
  - cron: "0 */6 * * *"   # Runs at 00:00, 06:00, 12:00, 18:00 UTC
```

In Indian Standard Time (IST, UTC+5:30), this corresponds to:
* **05:30 AM IST** (Morning Briefing)
* **11:30 AM IST** (Midday Market Update)
* **05:30 PM IST** (Evening Wrap-up)
* **11:30 PM IST** (Night Tech & Trends Digest)

---

## 🛠️ Local Testing

Run locally on your machine at any time:

```bash
# On Linux / macOS
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="@yourchannel"   # or the numeric ID
python scraper.py

# On Windows (PowerShell)
$env:TELEGRAM_BOT_TOKEN = "your_bot_token"
$env:TELEGRAM_CHAT_ID = "@yourchannel"   # or the numeric ID
python scraper.py
```

Console output prints the exact payload and visual banners for every job.

---

## 📂 Project Structure

```
omnipulse/
├── .github/
│   └── workflows/
│       └── monitor.yml        # GitHub Actions workflow (runs every 6 hours)
├── config.json                # Job definitions, endpoints, extraction rules
├── scraper.py                 # Core scraping engine & Telegram notifier
├── requirements.txt           # Python dependencies
├── .gitignore
└── README.md                  # Documentation & configuration guide
```

---

## 📄 License

MIT License — free for personal, educational, and commercial use.
