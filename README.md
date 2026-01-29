# 📊 Stock Signal Dashboard

Auto-updating stock signal dashboard with LEAPS call options recommendations.

**Live Dashboard:** [View Dashboard](https://YOUR_USERNAME.github.io/stock-signals/)

## Features

- 📈 Technical analysis for 33 stocks across multiple sectors
- 🎯 Buy/Sell/Hold signals with confidence scores
- 📊 Market regime detection (Bullish/Neutral/Bearish/Crash)
- 💰 LEAPS call options recommendations with optimal strike/expiry
- 🔄 Auto-updates 3x daily (market open, mid-day, pre-close)
- 📱 Works on iPhone, Android, PC, Mac

## How It Works

GitHub Actions automatically runs the Python signal generator 3x daily during market hours:
- 9:35 AM ET (5 min after open)
- 12:30 PM ET (mid-day)
- 3:00 PM ET (1 hour before close)

The dashboard is then published to GitHub Pages.

## Manual Update

To trigger a manual update:
1. Go to **Actions** tab
2. Click **Update Stock Signals**
3. Click **Run workflow**

## Setup Your Own

1. Fork this repository
2. Go to **Settings** → **Pages**
3. Set Source to **Deploy from a branch**
4. Select **main** branch and **/ (root)**
5. Click Save
6. Your dashboard will be live at `https://YOUR_USERNAME.github.io/stock-signals/`

## Stocks Tracked

| Sector | Stocks |
|--------|--------|
| NASDAQ Tech | AMD, AMZN, ANET, GOOG, GOOGL, IONQ, META, MU, NET, NVDA, PLTR, RGTI, SMCI, SNOW, STX, SYM, TSLA, WDC |
| S&P 500 | COIN, HOOD, ISRG, SOFI |
| Biotech | BEAM, CRSP, DNA, RXRX |
| Space | ASTS, IRDM, RKLB |
| Clean Energy | ENPH, FSLR, QS |
| Nuclear | LEU |

## Disclaimer

⚠️ This is not financial advice. Always do your own research before making investment decisions. Options trading involves significant risk and can result in 100% loss of premium.
