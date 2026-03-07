#!/usr/bin/env python3
"""
Earnings Transcript Fetcher
Scrapes transcripts from The Motley Fool (free, no API key required)
"""

import re
import json
import sys
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import quote
from html.parser import HTMLParser

# ============================================================
# HTML PARSING
# ============================================================

class TranscriptParser(HTMLParser):
    """Extract transcript text from Motley Fool article HTML"""
    def __init__(self):
        super().__init__()
        self.in_article = False
        self.text_parts = []
        self.current_tag = None
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attrs_dict = dict(attrs)
        # Look for article content
        if tag == 'article' or (tag == 'div' and 'article' in attrs_dict.get('class', '')):
            self.in_article = True
            
    def handle_endtag(self, tag):
        if tag == 'article':
            self.in_article = False
        self.current_tag = None
        
    def handle_data(self, data):
        if self.in_article and self.current_tag in ('p', 'h2', 'h3', 'strong', None):
            text = data.strip()
            if text:
                self.text_parts.append(text)
    
    def get_text(self):
        return '\n'.join(self.text_parts)


def clean_transcript(html):
    """Extract readable text from HTML"""
    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Try parser first
    parser = TranscriptParser()
    try:
        parser.feed(html)
        text = parser.get_text()
        if len(text) > 1000:
            return text
    except:
        pass
    
    # Fallback: regex extraction
    # Find main content between "Prepared Remarks" and end markers
    patterns = [
        r'Prepared Remarks.*?(?:Duration:|Call participants:|More \w+ analysis)',
        r'Contents:.*?(?:Duration:|Call participants:|More \w+ analysis)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(0)
            # Strip HTML tags
            content = re.sub(r'<[^>]+>', ' ', content)
            # Clean whitespace
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'\n\s*\n', '\n\n', content)
            return content.strip()
    
    # Last resort: strip all HTML
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    return text[:50000]  # Limit length

# ============================================================
# MOTLEY FOOL TRANSCRIPT FETCHING  
# ============================================================

def search_fool_transcripts(ticker):
    """Search Motley Fool for earnings call transcripts via company quote page"""
    import subprocess
    
    ticker_lower = ticker.lower()
    
    # Try the company's quote page which lists recent transcripts
    quote_url = f"https://www.fool.com/quote/nasdaq/{ticker_lower}/"
    
    try:
        result = subprocess.run(
            ['curl', '-sL', '-m', '15', quote_url],
            capture_output=True,
            text=True,
            timeout=20
        )
        
        if result.returncode != 0:
            return []
        
        html = result.stdout
        
        # Find transcript URLs
        pattern = r'/earnings/call-transcripts/\d{4}/\d{2}/\d{2}/[^"\'>\s\\]+-earnings-call-transcript[^"\'>\s\\]*'
        urls = re.findall(pattern, html)
        
        # Also try NYSE for some tickers
        if not urls:
            quote_url = f"https://www.fool.com/quote/nyse/{ticker_lower}/"
            result = subprocess.run(
                ['curl', '-sL', '-m', '15', quote_url],
                capture_output=True,
                text=True,
                timeout=20
            )
            if result.returncode == 0:
                urls = re.findall(pattern, result.stdout)
        
        # Get company name for matching
        company_names = {
            'aapl': 'apple', 'msft': 'microsoft', 'googl': 'alphabet', 'goog': 'alphabet',
            'amzn': 'amazon', 'meta': 'meta', 'nvda': 'nvidia', 'tsla': 'tesla',
            'nflx': 'netflix', 'amd': 'amd', 'intc': 'intel', 'crm': 'salesforce',
            'orcl': 'oracle', 'csco': 'cisco', 'ibm': 'ibm', 'qcom': 'qualcomm',
            'dis': 'disney', 'v': 'visa', 'ma': 'mastercard', 'jpm': 'jpmorgan',
            'bac': 'bank-of-america', 'wfc': 'wells-fargo', 'wmt': 'walmart',
            'cost': 'costco', 'hd': 'home-depot', 'nke': 'nike', 'sbux': 'starbucks',
        }
        company = company_names.get(ticker_lower, ticker_lower)
        
        # Deduplicate and filter
        unique_urls = []
        seen = set()
        for url in urls:
            # Clean up URL
            url = url.rstrip('\\/')
            if url not in seen:
                seen.add(url)
                full_url = 'https://www.fool.com' + url
                # Filter for this ticker OR company name
                url_lower = url.lower()
                if ticker_lower in url_lower or company in url_lower:
                    unique_urls.append(full_url)
        
        return unique_urls[:10]
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)
        return []


def fetch_transcript_url(url):
    """Fetch and parse a single transcript using curl for reliability"""
    import subprocess
    
    try:
        # Use curl for more reliable fetching
        result = subprocess.run(
            ['curl', '-sL', '-m', '20', url],
            capture_output=True,
            text=True,
            timeout=25
        )
        
        if result.returncode != 0:
            return None
            
        html = result.stdout
        
        if len(html) < 1000:
            return None
        
        # Extract title for quarter info
        title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
        title = title_match.group(1) if title_match else url
        
        # Parse quarter from title (e.g., "Apple (AAPL) Q1 2025 Earnings Call Transcript")
        quarter_match = re.search(r'Q(\d)\s*(\d{4})', title)
        if quarter_match:
            quarter = f"Q{quarter_match.group(1)} {quarter_match.group(2)}"
        else:
            # Try to extract from URL date
            date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
            if date_match:
                year, month, day = date_match.groups()
                quarter = f"{year}-{month}"
            else:
                quarter = "Unknown"
        
        # Extract transcript text
        text = clean_transcript(html)
        
        return {
            'quarter': quarter,
            'url': url,
            'title': title.replace(' | The Motley Fool', '').strip(),
            'text': text,
            'length': len(text),
        }
    except Exception as e:
        print(f"Fetch error for {url}: {e}", file=sys.stderr)
        return None


def fetch_transcripts(ticker, num_quarters=4):
    """
    Fetch the last N earnings transcripts for a ticker from Motley Fool
    Returns list of transcript dicts with quarter, text, url
    """
    print(f"Searching for {ticker} transcripts...", file=sys.stderr)
    
    urls = search_fool_transcripts(ticker)
    
    if not urls:
        # Try direct URL construction for common companies
        print("No search results, trying direct URLs...", file=sys.stderr)
        urls = construct_likely_urls(ticker)
    
    print(f"Found {len(urls)} potential transcripts", file=sys.stderr)
    
    transcripts = []
    for url in urls[:num_quarters + 2]:  # Fetch a few extra in case some fail
        print(f"Fetching: {url}", file=sys.stderr)
        result = fetch_transcript_url(url)
        if result and result['length'] > 5000:  # Minimum length for valid transcript
            transcripts.append(result)
            print(f"  ✓ {result['quarter']} ({result['length']} chars)", file=sys.stderr)
            if len(transcripts) >= num_quarters:
                break
        else:
            print(f"  ✗ Too short or failed", file=sys.stderr)
    
    return transcripts


def construct_likely_urls(ticker):
    """Construct likely transcript URLs based on common patterns"""
    from datetime import datetime
    
    ticker_lower = ticker.lower()
    ticker_upper = ticker.upper()
    
    # Company name mappings
    company_names = {
        'AAPL': 'apple',
        'MSFT': 'microsoft',
        'GOOGL': 'alphabet',
        'GOOG': 'alphabet',
        'AMZN': 'amazon',
        'META': 'meta-platforms',
        'NVDA': 'nvidia',
        'TSLA': 'tesla',
        'NFLX': 'netflix',
        'AMD': 'amd',
        'INTC': 'intel',
        'CRM': 'salesforce',
        'ORCL': 'oracle',
        'CSCO': 'cisco-systems',
        'IBM': 'ibm',
        'QCOM': 'qualcomm',
        'TXN': 'texas-instruments',
        'AVGO': 'broadcom',
        'NOW': 'servicenow',
        'ADBE': 'adobe',
        'PYPL': 'paypal',
        'SQ': 'block',
        'SHOP': 'shopify',
        'SNOW': 'snowflake',
        'UBER': 'uber-technologies',
        'LYFT': 'lyft',
        'ABNB': 'airbnb',
        'COIN': 'coinbase-global',
        'PLTR': 'palantir-technologies',
        'JPM': 'jpmorgan-chase',
        'BAC': 'bank-of-america',
        'WFC': 'wells-fargo',
        'GS': 'goldman-sachs',
        'MS': 'morgan-stanley',
        'C': 'citigroup',
        'V': 'visa',
        'MA': 'mastercard',
        'DIS': 'walt-disney',
        'CMCSA': 'comcast',
        'T': 'att',
        'VZ': 'verizon-communications',
        'WMT': 'walmart',
        'COST': 'costco-wholesale',
        'TGT': 'target',
        'HD': 'home-depot',
        'LOW': 'lowes-companies',
        'NKE': 'nike',
        'SBUX': 'starbucks',
        'MCD': 'mcdonalds',
        'KO': 'coca-cola',
        'PEP': 'pepsico',
        'PG': 'procter-gamble',
        'JNJ': 'johnson-johnson',
        'PFE': 'pfizer',
        'MRK': 'merck',
        'UNH': 'unitedhealth-group',
        'CVS': 'cvs-health',
        'XOM': 'exxon-mobil',
        'CVX': 'chevron',
    }
    
    company = company_names.get(ticker_upper, ticker_lower)
    
    urls = []
    
    # Typical earnings dates - most companies report within these windows
    # Apple fiscal year ends in Sept, reports Q1 in late Jan, Q2 in late Apr, Q3 in late Jul, Q4 in late Oct
    
    earnings_windows = [
        # (year, month, days, fiscal_quarter, fiscal_year)
        # 2025 Q4 results (reported Oct/Nov 2025)
        (2025, 10, range(28, 32), 'q4', 2025),
        (2025, 11, range(1, 5), 'q4', 2025),
        # 2025 Q3 results (reported Jul/Aug 2025)
        (2025, 8, range(1, 8), 'q3', 2025),
        (2025, 7, range(28, 32), 'q3', 2025),
        # 2025 Q2 results (reported Apr/May 2025)
        (2025, 5, range(1, 8), 'q2', 2025),
        (2025, 4, range(28, 32), 'q2', 2025),
        # 2025 Q1 results (reported Jan/Feb 2025)
        (2025, 1, range(28, 32), 'q1', 2025),
        (2025, 2, range(1, 5), 'q1', 2025),
        # 2024 results
        (2024, 10, range(28, 32), 'q4', 2024),
        (2024, 11, range(1, 8), 'q4', 2024),
        (2024, 8, range(1, 8), 'q3', 2024),
        (2024, 7, range(25, 32), 'q3', 2024),
        (2024, 5, range(1, 8), 'q2', 2024),
        (2024, 4, range(25, 32), 'q2', 2024),
        (2024, 2, range(1, 8), 'q1', 2024),
        (2024, 1, range(25, 32), 'q1', 2024),
    ]
    
    for year, month, days, quarter, fy in earnings_windows:
        for day in days:
            # Try multiple URL patterns that Motley Fool uses (they're inconsistent)
            patterns = [
                # Pattern 1: company-ticker-quarter-year (most common)
                f"https://www.fool.com/earnings/call-transcripts/{year}/{month:02d}/{day:02d}/{company}-{ticker_lower}-{quarter}-{fy}-earnings-call-transcript/",
                # Pattern 2: company-quarter-year (no ticker)
                f"https://www.fool.com/earnings/call-transcripts/{year}/{month:02d}/{day:02d}/{company}-{quarter}-{fy}-earnings-call-transcript/",
                # Pattern 3: just company-ticker
                f"https://www.fool.com/earnings/call-transcripts/{year}/{month:02d}/{day:02d}/{company}-{ticker_lower}-earnings-call-transcript/",
            ]
            urls.extend(patterns)
    
    # Also add 2026 dates
    for month, days, quarter, fy in [
        (1, range(27, 32), 'q1', 2026),
        (2, range(1, 5), 'q1', 2026),
    ]:
        for day in days:
            patterns = [
                f"https://www.fool.com/earnings/call-transcripts/2026/{month:02d}/{day:02d}/{company}-{ticker_lower}-{quarter}-{fy}-earnings-call-transcript/",
                f"https://www.fool.com/earnings/call-transcripts/2026/{month:02d}/{day:02d}/{company}-{quarter}-{fy}-earnings-call-transcript/",
            ]
            urls.extend(patterns)
    
    return urls[:50]


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetcher.py TICKER [--quarters N] [--save DIR]")
        print("Example: python fetcher.py AAPL --quarters 4 --save ./transcripts")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    quarters = 4
    save_dir = None
    
    # Parse args
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--quarters' and i + 1 < len(sys.argv):
            quarters = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--save' and i + 1 < len(sys.argv):
            save_dir = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # Fetch transcripts
    transcripts = fetch_transcripts(ticker, quarters)
    
    if not transcripts:
        print(f"No transcripts found for {ticker}", file=sys.stderr)
        sys.exit(1)
    
    print(f"\nFound {len(transcripts)} transcripts for {ticker}:", file=sys.stderr)
    for t in transcripts:
        print(f"  - {t['quarter']}: {t['length']} chars", file=sys.stderr)
    
    # Save if requested
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        for t in transcripts:
            filename = f"{ticker}_{t['quarter'].replace(' ', '_')}.txt"
            filepath = os.path.join(save_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f"# {t['title']}\n")
                f.write(f"# URL: {t['url']}\n\n")
                f.write(t['text'])
            print(f"Saved: {filepath}", file=sys.stderr)
    
    # Output JSON summary
    output = []
    for t in transcripts:
        output.append({
            'ticker': ticker,
            'quarter': t['quarter'],
            'url': t['url'],
            'title': t['title'],
            'length': t['length'],
        })
    
    print(json.dumps(output, indent=2))
