#!/usr/bin/env python3
"""
Simple Firecrawl Crawler - Streamlit App
Just input a URL and crawl it
"""

import os
import streamlit as st
import json
import time
import requests
from urllib.parse import urljoin
import pandas as pd
from typing import List, Dict
from phi.agent import Agent
from phi.model.google import Gemini

# Configuration
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "fc-ec217ffcb33f4e3999f27a62e1405c4b")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyA3Xj2t9nZlPe3CJengXDVRp-TAq2sZrQo")


def firecrawl_crawl_with_logs(url: str, max_pages: int) -> List[Dict]:
    """
    Crawl with real-time log display in Streamlit
    """
    with st.status("Crawling website...", expanded=True) as status:
        st.write(f"🕷️ Starting crawl of: {url}")
        st.write(f"🎯 Focusing on team, about, people, and leadership pages")
        
        try:
            # Start the crawl
            response = requests.post(
                "https://api.firecrawl.dev/v1/crawl",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": url,
                    "limit": max_pages,
                    "scrapeOptions": {
                        "formats": ["markdown", "html"]
                    },
                    # Firecrawl expects regular expressions here, not glob patterns
                    "includePaths": [
                        ".*/team.*",
                        ".*/about.*",
                        ".*/people.*",
                        ".*/leadership.*",
                        ".*/staff.*",
                        ".*/founder.*",
                        ".*/contact.*",
                        ".*/our-team.*",
                        ".*/meet-the-team.*"
                    ]
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if it's async (crawl job created)
                if data.get("success") and "id" in data:
                    job_id = data["id"]
                    st.write(f"📋 Crawl job created: {job_id}")
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    
                    # Poll for results
                    max_wait = 600  # 10 minutes max
                    wait_time = 0
                    
                    while wait_time < max_wait:
                        time.sleep(3)
                        wait_time += 3
                        
                        # Check status
                        status_response = requests.get(
                            f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                            headers={
                                "Authorization": f"Bearer {FIRECRAWL_API_KEY}"
                            },
                            timeout=30
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if status_data.get("status") == "completed":
                                pages = status_data.get("data", [])
                                st.write(f"✅ Crawl complete! Got {len(pages)} pages")
                                progress_bar.progress(1.0)
                                status.update(label="✅ Crawl complete!", state="complete")
                                return pages
                            elif status_data.get("status") == "failed":
                                st.error("❌ Crawl failed")
                                status.update(label="❌ Crawl failed", state="error")
                                return []
                            else:
                                # Still in progress
                                completed = status_data.get("completed", 0)
                                total = status_data.get("total", max_pages)
                                progress = completed / total if total > 0 else 0
                                progress_bar.progress(min(progress, 0.99))
                                st.write(f"⏳ Crawling... {completed}/{total} pages")
                        else:
                            st.warning(f"Status check returned {status_response.status_code}")
                    
                    st.warning("⏰ Timeout waiting for crawl")
                    status.update(label="⏰ Timeout", state="error")
                    return []
                
                # If sync response with data
                elif data.get("success") and "data" in data:
                    pages = data.get("data", [])
                    st.write(f"✅ Got {len(pages)} pages")
                    status.update(label="✅ Complete!", state="complete")
                    return pages
                    
            else:
                st.error(f"❌ Crawl returned status {response.status_code}")
                st.code(response.text[:500])
                status.update(label="❌ Failed", state="error")
                
        except Exception as e:
            st.error(f"❌ Crawl error: {e}")
            status.update(label="❌ Error", state="error")
        
        return []


# =========================
# URL routing and scraping
# =========================

TEAM_PATTERNS = [
    '/team', '/about/team', '/people', '/partners', '/leadership', '/our-team', '/meet-the-team',
    '/professionals', '/investment-team', '/management', '/advisors', '/board', '/who-we-are', '/about-us'
]
PORTFOLIO_PATTERNS = [
    '/portfolio', '/companies', '/investments', '/portfolio-companies', '/startups', '/ventures', '/projects'
]

def route_pages(base_domain: str, timeout: float = 2.0):
    if not base_domain:
        return None, None
    base = base_domain
    if not base.startswith('http'):
        base = 'https://' + base
    def first_hit(patterns):
        for p in patterns:
            test_url = urljoin(base.rstrip('/')+'/', p.lstrip('/'))
            try:
                r = requests.head(test_url, timeout=timeout, allow_redirects=True)
                if r.status_code < 400:
                    return r.url
            except:
                continue
        return None
    # Try static patterns first
    team_url = first_hit(TEAM_PATTERNS)
    portfolio_url = first_hit(PORTFOLIO_PATTERNS)
    # If not found, try discovering candidates from homepage nav/text
    if not (team_url and portfolio_url):
        cand_team, cand_port = discover_candidates_from_homepage(base)
        if not team_url and cand_team:
            team_url = first_hit(cand_team)
        if not portfolio_url and cand_port:
            portfolio_url = first_hit(cand_port)
    return team_url, portfolio_url

def discover_candidates_from_homepage(base: str, timeout: float = 5.0):
    team_keywords = [
        'team', 'people', 'leadership', 'partners', 'professionals', 'investment-team',
        'management', 'advisors', 'board', 'who-we-are', 'our-team', 'meet-the-team', 'about'
    ]
    portfolio_keywords = [
        'portfolio', 'companies', 'investments', 'portfolio-companies', 'startups', 'ventures', 'projects'
    ]
    cand_team = []
    cand_port = []
    try:
        if not base.startswith('http'):
            base = 'https://' + base
        resp = requests.get(base, timeout=timeout)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = (a.get_text() or '').strip().lower()
            # Build absolute URL within same site
            if href.startswith('#'):
                continue
            if href.startswith('http') and urljoin(base, '/') not in href:
                # external link
                continue
            full = urljoin(base, href)
            path = '/' + full.split('/', 3)[-1] if full.count('/') >= 3 else '/'
            path_lower = path.lower()
            if any(k in path_lower for k in team_keywords) or any(k in text for k in team_keywords):
                cand_team.append(path)
            if any(k in path_lower for k in portfolio_keywords) or any(k in text for k in portfolio_keywords):
                cand_port.append(path)
        # de-duplicate and keep short paths first
        cand_team = sorted(set(cand_team), key=lambda p: (len(p), p))[:15]
        cand_port = sorted(set(cand_port), key=lambda p: (len(p), p))[:15]
    except:
        pass
    return cand_team, cand_port

def firecrawl_scrape_page(url: str) -> tuple[str, str]:
    """Return (markdown, html) for a URL."""
    try:
        r = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"},
            json={"url": url, "formats": ["markdown", "html"]},
            timeout=60
        )
        r.raise_for_status()
        data = r.json()
        md = data.get("data", {}).get("markdown", "")
        html = data.get("data", {}).get("html", "")
        return md or "", html or ""
    except Exception:
        return "", ""

def discover_pagination_urls(html: str, base_url: str, max_pages: int = 10) -> List[str]:
    try:
        from bs4 import BeautifulSoup
    except Exception:
        return [base_url]
    urls = [base_url]
    if not html:
        return urls
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    links += soup.select('.pagination a')
    links += soup.select('a[rel="next"]')
    for a in links:
        href = a.get('href')
        if not href:
            continue
        if href.startswith('/'):
            href = urljoin(base_url, href)
        if href.startswith('http') and href not in urls:
            urls.append(href)
        if len(urls) >= max_pages:
            break
    return urls

def _html_to_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        # remove script/style
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text("\n")
        # normalize short lines
        lines = [ln.strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if len(ln) > 0]
        return "\n".join(lines)
    except Exception:
        return ""

def scrape_with_pagination(seed_url: str, max_pages: int = 10) -> List[str]:
    if not seed_url:
        return []
    # scrape first page to discover
    first_md, first_html = firecrawl_scrape_page(seed_url)
    page_urls = discover_pagination_urls(first_html, seed_url, max_pages=max_pages)
    contents: List[str] = []
    # include first content if present
    if first_md:
        contents.append(first_md)
    elif first_html:
        contents.append(_html_to_text(first_html))
    for u in page_urls[1:]:
        md, html = firecrawl_scrape_page(u)
        if md:
            contents.append(md)
        elif html:
            contents.append(_html_to_text(html))
    return contents


def clean_content_for_llm(markdown: str) -> str:
    """
    Clean markdown content to remove buttons, navigation, and metadata.
    Keep only the main text content.
    """
    if not markdown:
        return ""
    
    # Split into lines
    lines = markdown.split('\n')
    cleaned_lines = []
    
    # Filter out common non-content patterns
    skip_patterns = [
        'button', 'click', 'menu', 'nav', 'navigation', 'footer', 'header',
        'cookie', 'subscribe', 'sign up', 'log in', 'login', 'search',
        '©', 'copyright', 'all rights reserved', 'privacy policy', 'terms',
        'follow us', 'social media', 'share', 'tweet', 'facebook', 'linkedin',
        '---', '***', '===='
    ]
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Skip empty lines
        if not line_lower:
            continue
        
        # Skip lines with skip patterns
        if any(pattern in line_lower for pattern in skip_patterns):
            continue
        
        # Skip lines that are just links or buttons
        if line_lower.startswith('[') and '](' in line_lower:
            continue
        
        # Skip very short lines (likely navigation)
        if len(line_lower) < 10 and not any(c.isdigit() for c in line_lower):
            continue
        
        cleaned_lines.append(line)
    
    # Join and limit to ~3000 chars for token efficiency
    cleaned = '\n'.join(cleaned_lines)
    return cleaned[:3000]


def extract_names_with_llm(pages: List[Dict], signals: str = "") -> List[Dict]:
    """
    Use Google Gemini to extract names from crawled pages
    """
    if not GOOGLE_API_KEY:
        st.error("❌ GOOGLE_API_KEY not set in environment")
        return []
    
    # Initialize Gemini agent
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
        markdown=True
    )
    
    all_names = []
    
    with st.status("Extracting names with AI...", expanded=True) as status:
        st.write(f"🤖 Analyzing {len(pages)} pages with Google Gemini")
        if signals:
            st.write(f"🎯 Looking for: {signals}")
        
        progress_bar = st.progress(0)
        
        for idx, page in enumerate(pages):
            url = page.get('url', 'unknown')
            markdown = page.get('markdown', '')
            
            if not markdown or len(markdown) < 50:
                continue
            
            st.write(f"📄 Analyzing: {url}")
            
            try:
                # Clean content for better LLM processing
                content = clean_content_for_llm(markdown)
                
                if len(content) < 50:
                    st.write(f"   ⏭️  Skipped (no meaningful content)")
                    continue
                
                # Build prompt with optional signals
                signal_text = f"\n\nFocus on finding people who are: {signals}" if signals else ""
                
                # First, get the company name from the page
                company_prompt = f"""What is the company name for this website?

Return ONLY the company name, nothing else.
If you cannot determine the company name, return: "Unknown"

Webpage content:
{content[:1000]}
"""
                company_response = agent.run(company_prompt)
                company_name = company_response.content if hasattr(company_response, 'content') else str(company_response)
                company_name = company_name.strip().replace('**', '').replace('*', '')
                if 'unknown' in company_name.lower():
                    company_name = url.split('/')[2]  # Use domain as fallback
                
                # Now extract names with role/signal info
                prompt = f"""Look at this webpage content and extract all PERSON NAMES you find.

IMPORTANT: Only extract actual human names, NOT:
- Company names
- Product names
- Button text
- Navigation items
- Metadata

For each person, try to identify their role or title.

Return in this exact format:
Name: [full name]
Role: [their job title/role if found, or "Not specified"]
{signal_text}

If no person names are found, respond with: "No names found"

Webpage content:
{content}
"""
                
                response = agent.run(prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                # Parse response
                if "no names found" not in response_text.lower():
                    lines = response_text.strip().split('\n')
                    current_name = None
                    current_role = "Not specified"
                    
                    for line in lines:
                        line = line.strip()
                        if 'name:' in line.lower():
                            # Save previous entry if exists
                            if current_name:
                                all_names.append({
                                    'name': current_name,
                                    'role': current_role,
                                    'signal': signals or "General",
                                    'company': company_name,
                                    'source_url': url
                                })
                                st.write(f"   ✅ Found: {current_name} - {current_role}")
                            
                            # Extract new name
                            name = line.split(':', 1)[-1].strip()
                            name = name.replace('**', '').replace('*', '').strip()
                            if name and len(name) > 2 and len(name.split()) >= 2:
                                current_name = name
                                current_role = "Not specified"
                        
                        elif 'role:' in line.lower() or 'title:' in line.lower():
                            role = line.split(':', 1)[-1].strip()
                            role = role.replace('**', '').replace('*', '').strip()
                            if role and role.lower() != 'not specified':
                                current_role = role
                    
                    # Add the last person
                    if current_name:
                        all_names.append({
                            'name': current_name,
                            'role': current_role,
                            'signal': signals or "General",
                            'company': company_name,
                            'source_url': url
                        })
                        st.write(f"   ✅ Found: {current_name} - {current_role}")
                
            except Exception as e:
                st.warning(f"   ⚠️  Error analyzing {url}: {str(e)[:100]}")
            
            progress_bar.progress((idx + 1) / len(pages))
            time.sleep(0.5)  # Rate limiting
        
        status.update(label=f"✅ Extracted {len(all_names)} names!", state="complete")
    
    return all_names


# =========================
# LLM extractors for VC fund pipeline
# =========================

def gemini_text(agent: Agent, prompt: str) -> str:
    limiter_allow()
    resp = agent.run(prompt)
    txt = resp.content if hasattr(resp, 'content') else str(resp)
    # strip code fences and markdown if any
    txt = txt.strip()
    if txt.startswith('```'):
        # remove first line fence
        lines = txt.splitlines()
        # drop first and last fence if present
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].startswith('```'):
            lines = lines[:-1]
        txt = "\n".join(lines).strip()
    return txt

def extract_vcs_and_companies(agent: Agent, team_pages: List[str], portfolio_pages: List[str]) -> tuple[str, str]:
    team_blob = "\n\n=== PAGE BREAK ===\n\n".join(team_pages)[:900000]
    port_blob = "\n\n=== PAGE BREAK ===\n\n".join(portfolio_pages)[:900000]
    ppl_prompt = f"""
Extract ALL people from the content. Return strict JSON array of objects:
[
  {{"name": "...", "title": "...", "linkedin_url": "..."}}
]

Content:
{team_blob}
"""
    cos_prompt = f"""
Extract ALL portfolio companies (company name + domain if present). Return strict JSON array:
[
  {{"company": "...", "domain": "..."}}
]

Content:
{port_blob}
"""
    ppl = gemini_text(agent, ppl_prompt)
    cos = gemini_text(agent, cos_prompt)
    return ppl, cos

def extract_company_people(agent: Agent, pages: List[str], stage: str, signals: str = "") -> str:
    content = "\n\n=== PAGE BREAK ===\n\n".join(pages)[:900000]
    scope = "founders/co-founders" if stage.lower() in ["seed", "pre-seed", "early"] else "all employees (leadership prioritized)"
    sfx = f"\nFocus on people related to: {signals}" if signals else ""
    prompt = f"""
Extract {scope} from the content. Return strict JSON array:
[
  {{"name":"...","title":"...","linkedin_url":"..."}}
]{sfx}

Content:
{content}
"""
    return gemini_text(agent, prompt)

from collections import deque
_rpm_q = deque()
def limiter_allow(rpm: int = 15):
    import time as _t
    now = _t.time()
    while _rpm_q and now - _rpm_q[0] > 60:
        _rpm_q.popleft()
    if len(_rpm_q) >= rpm:
        sleep_for = 60 - (now - _rpm_q[0])
        _t.sleep(max(0, sleep_for))
        return limiter_allow(rpm)
    _rpm_q.append(_t.time())

st.set_page_config(
    page_title="Firecrawl Crawler",
    page_icon="🕷️",
    layout="wide"
)

st.title("Outbound: find the right people")
st.markdown("Crawl websites, extract VCs/companies/people with single-call LLMs")
st.caption("🎯 Automatically focuses on: team, about, people, leadership, staff, and founder pages")

# Check API keys
if not GOOGLE_API_KEY:
    st.warning("⚠️ GOOGLE_API_KEY not set - name extraction will be disabled")
else:
    st.success("✅ Google Gemini ready for name extraction")

# Input
url = st.text_input(
    "🌐 Website URL",
    placeholder="https://example.com",
    key="url_input"
)

col1, col2 = st.columns([1, 1])

with col1:
    max_pages = st.number_input(
        "📄 Max Pages to Crawl",
        min_value=5,
        max_value=100,
        value=20,
        step=5,
        key="max_pages"
    )

with col2:
    signals = st.text_input(
        "🎯 Signals (optional)",
        placeholder="e.g., recruiter, partnerships, CEO",
        help="Keywords to help find specific types of people",
        key="signals"
    )

# Clay webhook (optional)
with st.expander("📤 Clay Integration (optional)"):
    clay_webhook = st.text_input(
        "Clay Webhook URL",
        placeholder="https://clay.com/api/webhook/...",
        help="Automatically send extracted names to Clay for enrichment",
        key="clay_webhook"
    )
    st.caption("Leave empty to skip Clay integration")

# Crawl button (single site people finder)
if st.button("🚀 Start Crawl", type="primary", use_container_width=True):
    if not url:
        st.error("Please enter a URL")
        st.stop()
    
    if not url.startswith('http'):
        url = 'https://' + url
    
    # Run crawl with real-time logs
    pages = firecrawl_crawl_with_logs(url, max_pages)
    
    if pages:
        st.success(f"✅ Crawled {len(pages)} pages!")
        
        # Stats
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Pages Crawled", len(pages))
        with col_b:
            total_chars = sum(len(p.get('markdown', '')) for p in pages)
            st.metric("Total Content", f"{total_chars:,} chars")
        
        # Automatically run name extraction
        st.markdown("---")
        names = extract_names_with_llm(pages, signals=signals or "")
        
        if names:
            st.success(f"✅ Found {len(names)} names!")
            
            # Convert to DataFrame
            df = pd.DataFrame(names)
            
            # Deduplicate
            df = df.drop_duplicates(subset=['name'], keep='first')
            
            # Show table
            st.subheader("📋 Extracted Names")
            st.dataframe(df, use_container_width=True)
            
            # Send to Clay if webhook provided
            if clay_webhook:
                st.markdown("---")
                with st.spinner("📤 Sending to Clay..."):
                    try:
                        response = requests.post(
                            clay_webhook,
                            json=df.to_dict('records'),
                            headers={"Content-Type": "application/json"},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            st.success(f"✅ Successfully sent {len(df)} contacts to Clay!")
                        else:
                            st.error(f"❌ Clay webhook returned {response.status_code}: {response.text[:200]}")
                    except Exception as e:
                        st.error(f"❌ Error sending to Clay: {e}")
            
            # Download CSV
            st.markdown("---")
            csv = df.to_csv(index=False)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"names_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )
            with col_dl2:
                # Also offer JSON download
                json_data = df.to_json(orient='records', indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"names_{timestamp}.json",
                    mime="application/json",
                    use_container_width=True
                )
        else:
            st.warning("⚠️ No names found on any pages")
        
        # Show page list (collapsed)
        with st.expander("📄 View Crawled Pages"):
            for i, page in enumerate(pages, 1):
                url = page.get('url', 'unknown')
                markdown_len = len(page.get('markdown', ''))
                st.write(f"{i}. {url} ({markdown_len:,} chars)")
        
        # Download raw JSON
        with st.expander("💾 Download Raw Data"):
            json_str = json.dumps(pages, indent=2)
            st.download_button(
                label="📥 Download Full JSON",
                data=json_str,
                file_name="crawl_results.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.error("❌ Crawl failed")


# =========================
# VC Fund Pipeline (Layer 1)
# =========================
st.markdown("---")
st.subheader("💼 VC Fund Pipeline (Layer 1)")
st.caption("Enter fund domains (one per line). We route to team/portfolio, scrape with pagination, then call Gemini once per fund.")

col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    fund_domains = st.text_area(
        "Fund domains (one per line)",
        placeholder="a16z.com\nsequoiacap.com\nbenchmark.com",
        height=120,
        key="fund_domains"
    )
with col_f2:
    fund_max_pages = st.number_input(
        "Max pages per section",
        min_value=2,
        max_value=20,
        value=8,
        step=1,
        key="fund_max_pages"
    )

run_fund = st.button("🚀 Run Fund Pipeline", use_container_width=True)

if run_fund:
    domains = [d.strip() for d in fund_domains.split('\n') if d.strip()]
    if not domains:
        st.error("Please enter at least one fund domain")
    else:
        agent = Agent(model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY), markdown=True)
        all_vcs = []
        all_companies = []
        with st.status("Processing funds...", expanded=True) as s:
            for d in domains:
                st.write(f"🔎 Routing pages for {d}...")
                team_url, portfolio_url = route_pages(d)
                st.write(f"   team={team_url or '-'} portfolio={portfolio_url or '-'}")
                team_pages = scrape_with_pagination(team_url, max_pages=fund_max_pages) if team_url else []
                port_pages = scrape_with_pagination(portfolio_url, max_pages=fund_max_pages) if portfolio_url else []
                ppl_json, cos_json = extract_vcs_and_companies(agent, team_pages, port_pages)
                import json as _json
                try:
                    vcs = _json.loads(ppl_json)
                except Exception:
                    vcs = []
                try:
                    pcs = _json.loads(cos_json)
                except Exception:
                    pcs = []
                # add source domain
                for v in vcs:
                    v["source_domain"] = d
                for c in pcs:
                    c["source_domain"] = d
                all_vcs.extend(vcs)
                all_companies.extend(pcs)
                st.write(f"   ✅ {len(vcs)} VCs, {len(pcs)} companies")
            s.update(label="✅ Fund pipeline complete", state="complete")
        # Export
        if all_vcs:
            import pandas as _pd
            df_v = _pd.DataFrame(all_vcs)
            csv_v = df_v.to_csv(index=False)
            st.download_button("📥 Download VCs CSV", csv_v, file_name="vcs.csv", mime="text/csv", use_container_width=True)
        if all_companies:
            import pandas as _pd
            df_c = _pd.DataFrame(all_companies)
            csv_c = df_c.to_csv(index=False)
            st.download_button("📥 Download Portfolio Companies CSV", csv_c, file_name="portfolio_companies.csv", mime="text/csv", use_container_width=True)
