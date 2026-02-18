"""Job scraping and search module — v2 with working APIs."""
import aiohttp
import asyncio
import os
import json
from typing import List, Dict
from datetime import datetime
import re
from .db import add_job, get_filters


# RapidAPI key for JSearch (LinkedIn/Indeed/Glassdoor aggregator)
# Free tier: 500 requests/month — more than enough for daily searches
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "2674038040msh80b5aa28db6af96p12a98fjsna87eb2ecb093")


class JobScraper:
    """Scrape jobs from multiple sources."""

    # ─── 1. RemoteOK (free, no key needed) ───────────────────────
    async def search_remoteok(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search RemoteOK jobs via free public API."""
        jobs = []
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://remoteok.com/api"
                headers = {"User-Agent": "JobBot/1.0"}
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        for item in data:
                            if not isinstance(item, dict) or 'position' not in item:
                                continue
                            title = item.get('position', '')
                            # Filter by keywords
                            if any(kw.lower() in title.lower() or
                                   kw.lower() in ' '.join(item.get('tags', [])).lower()
                                   for kw in keywords):
                                salary = ""
                                if item.get('salary_min') and item.get('salary_max'):
                                    salary = f"${item['salary_min']:,} - ${item['salary_max']:,}"
                                elif item.get('salary_min'):
                                    salary = f"${item['salary_min']:,}+"
                                else:
                                    salary = "Not listed"

                                jobs.append({
                                    "title": title,
                                    "company": item.get('company', 'N/A'),
                                    "location": item.get('location', 'Remote'),
                                    "salary": salary,
                                    "job_type": "Full-time",
                                    "source": "RemoteOK",
                                    "url": item.get('url', f"https://remoteok.com/remote-jobs/{item.get('slug', '')}"),
                                    "description": (item.get('description', '') or '')[:200]
                                })
            print(f"  RemoteOK: found {len(jobs)} jobs")
        except Exception as e:
            print(f"  RemoteOK error: {e}")
        return jobs

    # ─── 2. JSearch (RapidAPI) — LinkedIn + Indeed + Glassdoor ────
    async def search_jsearch(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search via JSearch API (aggregates LinkedIn, Indeed, Glassdoor).
        Free tier: 500 requests/month.
        Sign up: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
        """
        jobs = []
        if not RAPIDAPI_KEY:
            print("  JSearch: skipped (no RAPIDAPI_KEY set)")
            return jobs

        try:
            async with aiohttp.ClientSession() as session:
                query = f"{' '.join(keywords)} {location or 'remote'}"
                url = "https://jsearch.p.rapidapi.com/search"
                params = {
                    "query": query,
                    "page": "1",
                    "num_pages": "1",
                    "date_posted": "week",
                    "remote_jobs_only": "true" if "remote" in (location or "").lower() else "false"
                }
                headers = {
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
                }

                async with session.get(url, params=params, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("data", []):
                            salary = "Not listed"
                            if item.get("job_min_salary") and item.get("job_max_salary"):
                                salary = f"${int(item['job_min_salary']):,} - ${int(item['job_max_salary']):,}"
                            elif item.get("job_min_salary"):
                                salary = f"${int(item['job_min_salary']):,}+"

                            source = "LinkedIn"
                            publisher = (item.get("job_publisher") or "").lower()
                            if "indeed" in publisher:
                                source = "Indeed"
                            elif "glassdoor" in publisher:
                                source = "Glassdoor"
                            elif "linkedin" in publisher:
                                source = "LinkedIn"
                            elif "ziprecruiter" in publisher:
                                source = "ZipRecruiter"
                            else:
                                source = item.get("job_publisher", "JSearch")

                            jobs.append({
                                "title": item.get("job_title", "Job"),
                                "company": item.get("employer_name", "N/A"),
                                "location": ((item.get("job_city") or "") + (", " + item["job_state"] if item.get("job_state") else "")).strip(", ") or "Remote",
                                "salary": salary,
                                "job_type": item.get("job_employment_type", "FULLTIME").replace("FULLTIME", "Full-time").replace("CONTRACTOR", "Contract").replace("PARTTIME", "Part-time"),
                                "source": source,
                                "url": item.get("job_apply_link") or item.get("job_google_link", ""),
                                "description": (item.get("job_description", "") or "")[:200]
                            })
                    else:
                        body = await resp.text()
                        print(f"  JSearch: HTTP {resp.status} — {body[:200]}")
            print(f"  JSearch (LinkedIn/Indeed/Glassdoor): found {len(jobs)} jobs")
        except Exception as e:
            print(f"  JSearch error: {e}")
        return jobs

    # ─── 3. Arbeitnow (free, no key needed) ──────────────────────
    async def search_arbeitnow(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search Arbeitnow free job API."""
        jobs = []
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.arbeitnow.com/api/job-board-api"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("data", []):
                            title = item.get("title", "")
                            tags = " ".join(item.get("tags", []))
                            # Filter by keywords
                            if any(kw.lower() in title.lower() or kw.lower() in tags.lower()
                                   for kw in keywords):
                                jobs.append({
                                    "title": title,
                                    "company": item.get("company_name", "N/A"),
                                    "location": item.get("location", "Remote"),
                                    "salary": "Not listed",
                                    "job_type": "Full-time" if not item.get("remote") else "Remote",
                                    "source": "Arbeitnow",
                                    "url": item.get("url", ""),
                                    "description": (item.get("description", "") or "")[:200]
                                })
            print(f"  Arbeitnow: found {len(jobs)} jobs")
        except Exception as e:
            print(f"  Arbeitnow error: {e}")
        return jobs

    # ─── 4. LinkedIn public job search (no key, scraping) ────────
    async def search_linkedin_public(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Scrape LinkedIn public job listings (no login required)."""
        jobs = []
        try:
            async with aiohttp.ClientSession() as session:
                keyword = "%20".join(keywords)
                # LinkedIn public job search URL (no auth needed)
                url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location or 'United States'}&f_WT=2&position=1&pageNum=0"
                headers = {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                async with session.get(url, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        # Parse job cards from HTML
                        # LinkedIn public pages have structured data we can extract
                        import re
                        # Find job titles and links
                        title_pattern = r'<a[^>]*class="[^"]*base-card__full-link[^"]*"[^>]*href="([^"]*)"[^>]*>\s*<span[^>]*>([^<]*)</span>'
                        company_pattern = r'<h4[^>]*class="[^"]*base-search-card__subtitle[^"]*"[^>]*>\s*<a[^>]*>([^<]*)</a>'
                        location_pattern = r'<span[^>]*class="[^"]*job-search-card__location[^"]*"[^>]*>([^<]*)</span>'

                        titles = re.findall(title_pattern, html)
                        companies = re.findall(company_pattern, html)
                        locations = re.findall(location_pattern, html)

                        for i, (link, title) in enumerate(titles[:15]):
                            company = companies[i].strip() if i < len(companies) else "N/A"
                            loc = locations[i].strip() if i < len(locations) else "Remote"
                            jobs.append({
                                "title": title.strip(),
                                "company": company,
                                "location": loc,
                                "salary": "Not listed",
                                "job_type": "Full-time",
                                "source": "LinkedIn",
                                "url": link.split("?")[0],  # Clean URL
                                "description": ""
                            })
            print(f"  LinkedIn (public): found {len(jobs)} jobs")
        except Exception as e:
            print(f"  LinkedIn public error: {e}")
        return jobs

    # ─── 5. Indeed RSS Feed (free, no key) ───────────────────────
    async def search_indeed_rss(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search Indeed via RSS feed (free, no API key)."""
        jobs = []
        try:
            import xml.etree.ElementTree as ET
            async with aiohttp.ClientSession() as session:
                keyword = "+".join(keywords)
                loc = location.replace(",", "+") if location else "Remote"
                url = f"https://www.indeed.com/rss?q={keyword}&l={loc}&sort=date&limit=20"
                headers = {"User-Agent": "JobBot/1.0"}

                async with session.get(url, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        root = ET.fromstring(content)
                        for item in root.findall('.//item'):
                            title_el = item.find('title')
                            link_el = item.find('link')
                            desc_el = item.find('description')

                            if title_el is not None and link_el is not None:
                                title = title_el.text or ""
                                link = link_el.text or ""
                                desc = desc_el.text or "" if desc_el is not None else ""

                                # Extract company from title (format: "Title - Company")
                                company = "Indeed Job"
                                if " - " in title:
                                    parts = title.rsplit(" - ", 1)
                                    title = parts[0]
                                    company = parts[1] if len(parts) > 1 else company

                                jobs.append({
                                    "title": title.strip(),
                                    "company": company.strip(),
                                    "location": loc,
                                    "salary": "Not listed",
                                    "job_type": "Full-time",
                                    "source": "Indeed",
                                    "url": link,
                                    "description": desc[:200]
                                })
            print(f"  Indeed RSS: found {len(jobs)} jobs")
        except Exception as e:
            print(f"  Indeed RSS error: {e}")
        return jobs

    # ─── 6. FindWork.dev (free API for dev jobs) ─────────────────
    async def search_findwork(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search FindWork.dev API (free, dev/data jobs)."""
        jobs = []
        try:
            async with aiohttp.ClientSession() as session:
                keyword = " ".join(keywords)
                url = f"https://findwork.dev/api/jobs/?search={keyword}&sort_by=relevance"
                headers = {"User-Agent": "JobBot/1.0"}

                async with session.get(url, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("results", []):
                            jobs.append({
                                "title": item.get("role", "Job"),
                                "company": item.get("company_name", "N/A"),
                                "location": item.get("location", "Remote"),
                                "salary": "Not listed",
                                "job_type": item.get("employment_type", "Full-time"),
                                "source": "FindWork",
                                "url": item.get("url", ""),
                                "description": (item.get("text", "") or "")[:200]
                            })
            print(f"  FindWork: found {len(jobs)} jobs")
        except Exception as e:
            print(f"  FindWork error: {e}")
        return jobs

    # ─── Orchestrator ────────────────────────────────────────────
    async def search_all(self, keywords: List[str], location: str, salary_min: int = None,
                         level: str = None, job_type: str = None) -> List[Dict]:
        """Search all sources concurrently."""
        print("\n📡 Searching job sources...")
        tasks = [
            self.search_remoteok(keywords, location),
            self.search_jsearch(keywords, location),
            self.search_arbeitnow(keywords, location),
            self.search_linkedin_public(keywords, location),
            self.search_indeed_rss(keywords, location),
            self.search_findwork(keywords, location),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs = []
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                print(f"  Source error: {result}")

        # Filter by salary if specified
        if salary_min:
            all_jobs = [j for j in all_jobs if extract_salary(j.get('salary', '')) >= salary_min]

        # Deduplicate by URL
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            url = job.get('url', '')
            if url and url not in seen:
                seen.add(url)
                unique_jobs.append(job)

        print(f"\n✅ Total unique jobs: {len(unique_jobs)}")
        return unique_jobs


def extract_salary(salary_str: str) -> int:
    """Extract minimum salary from string."""
    if not salary_str or salary_str in ("Negotiable", "Not listed", ""):
        return 0
    numbers = re.findall(r'[\d,]+', salary_str.replace(',', ''))
    if numbers:
        try:
            return int(numbers[0])
        except ValueError:
            return 0
    return 0


async def search_jobs_for_user(user_id: int) -> List[Dict]:
    """Search jobs based on user filters."""
    filters = get_filters(user_id)
    if not filters:
        return []

    scraper = JobScraper()
    jobs = await scraper.search_all(
        keywords=filters['keywords'],
        location=filters['location'],
        salary_min=filters.get('salary_min'),
        level=filters.get('level'),
        job_type=filters.get('job_type')
    )

    # Store jobs in database
    for job in jobs:
        add_job(
            title=job['title'],
            company=job['company'],
            location=job['location'],
            salary=job['salary'],
            job_type=job['job_type'],
            source=job['source'],
            url=job['url'],
            description=job.get('description')
        )

    return jobs
