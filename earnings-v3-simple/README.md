# Earnings Script Analyzer

Analyze earnings call scripts for sentiment, confidence, and legal compliance.

## Features
- Loughran-McDonald sentiment analysis
- Hedging/confidence detection
- PSLRA-aware legal mode
- PDF and Word export with track changes
- Historical comparison to public companies

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Research basis
- Loughran & McDonald (2011) - Financial sentiment dictionary
- Larcker & Zakolyukina (2012) - Deception detection
- Price et al. (2012) - Tone and stock returns
