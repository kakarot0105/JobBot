"""Job scraping and search module."""
import aiohttp
import asyncio
from typing import List, Dict
from datetime import datetime
import re
import xml.etree.ElementTree as ET
from .db import add_job, get_filters


class JobScraper:
    """Scrape jobs from multiple sources."""

    async def search_indeed(self, keywords: List[str], location: str, job_type: str = None) -> List[Dict]:
        """Search Indeed jobs."""
        jobs = []
        try:
            # Indeed doesn't have official free API, so we use web scraping approach
            # This is a simplified version - for production use Indeed API (paid) or their RSS feed
            keyword_str = " ".join(keywords)
            url = f"https://www.indeed.com/jobs?q={keyword_str}&l={location}&jt={'contract' if job_type == 'Contract' else 'fulltime'}"
            
            # Note: Indeed actively blocks scrapers, so this may not work
            # Better approach: use Indeed's RSS feed or job listing APIs
            jobs.append({
                "title": f"{' '.join(keywords)} Position",
                "company": "Indeed Job",
                "location": location,
                "salary": "Negotiable",
                "job_type": job_type or "Full-time",
                "source": "indeed",
                "url": url,
                "description": "View on Indeed"
            })
        except Exception as e:
            print(f"Indeed search error: {e}")
        
        return jobs

    async def search_remoteok(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search RemoteOK jobs via API."""
        jobs = []
        try:
            # RemoteOK has a free public API
            async with aiohttp.ClientSession() as session:
                url = "https://remoteok.com/api"
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for job in data[:50]:  # Get first 50
                            if job.get('type') == 'job':
                                title = job.get('title', '')
                                # Filter by keywords
                                if any(kw.lower() in title.lower() for kw in keywords):
                                    jobs.append({
                                        "title": title,
                                        "company": job.get('company', 'N/A'),
                                        "location": job.get('location', 'Remote'),
                                        "salary": f"${job.get('salary_min', 'N/A')}-${job.get('salary_max', 'N/A')}",
                                        "job_type": "Full-time",
                                        "source": "remoteok",
                                        "url": f"https://remoteok.com/remote-jobs/{job.get('id', '')}",
                                        "description": job.get('description', '')[:200]
                                    })
        except Exception as e:
            print(f"RemoteOK search error: {e}")
        
        return jobs

    async def search_justjoinit(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search JustJoinIt jobs via API."""
        jobs = []
        try:
            # JustJoinIt has a public API
            async with aiohttp.ClientSession() as session:
                url = "https://api.justjoinit.eu/offers"
                params = {
                    "limit": 100,
                    "sort_by": "publish_date",
                    "order_by": "desc"
                }
                
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for job in data.get('data', [])[:50]:
                            title = job.get('title', '')
                            # Filter by keywords
                            if any(kw.lower() in title.lower() for kw in keywords):
                                # Filter by location if specified (USA or Remote)
                                loc = job.get('city', 'Remote')
                                if location and location.lower() == 'usa' and 'usa' not in loc.lower() and 'remote' not in loc.lower():
                                    continue
                                
                                salary_range = "Negotiable"
                                if job.get('salary_from'):
                                    salary_range = f"${job.get('salary_from')}-${job.get('salary_to')}"
                                
                                jobs.append({
                                    "title": title,
                                    "company": job.get('company_name', 'N/A'),
                                    "location": loc,
                                    "salary": salary_range,
                                    "job_type": "Full-time",
                                    "source": "justjoinit",
                                    "url": f"https://justjoinit.eu/jobs/{job.get('id', '')}",
                                    "description": job.get('description', '')[:200]
                                })
        except Exception as e:
            print(f"JustJoinIt search error: {e}")
        
        return jobs

    async def search_indeed(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search Indeed via RSS feeds."""
        jobs = []
        try:
            async with aiohttp.ClientSession() as session:
                keyword = keywords[0] if keywords else "Data Engineer"
                # Indeed RSS feed format
                url = f"https://www.indeed.com/rss?q={keyword}&l={location or 'Remote'}&filter=1"
                
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        root = ET.fromstring(content)
                        
                        # Parse RSS items
                        for item in root.findall('.//item')[:20]:
                            title_elem = item.find('title')
                            desc_elem = item.find('description')
                            link_elem = item.find('link')
                            
                            if title_elem is not None and link_elem is not None:
                                title = title_elem.text or "Job"
                                link = link_elem.text or ""
                                description = desc_elem.text or "" if desc_elem is not None else ""
                                
                                # Extract company name from description
                                company = "Indeed Job"
                                if "Company" in description:
                                    try:
                                        company = description.split("Company")[1].split("<")[0].strip() or "Indeed Job"
                                    except:
                                        pass
                                
                                jobs.append({
                                    "title": title,
                                    "company": company,
                                    "location": location or "Remote",
                                    "salary": "Negotiable",
                                    "job_type": "Full-time",
                                    "source": "indeed",
                                    "url": link,
                                    "description": description[:200]
                                })
        except Exception as e:
            print(f"Indeed RSS error: {e}")
        
        return jobs

    async def search_linkedin(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search LinkedIn via RSS feeds (job board RSS)."""
        jobs = []
        try:
            async with aiohttp.ClientSession() as session:
                keyword = keywords[0] if keywords else "Data Engineer"
                # LinkedIn job board RSS
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting?keywords={keyword}&location={location or 'Remote'}&count=20"
                
                async with session.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                            
                            if "elements" in data:
                                for job in data["elements"][:20]:
                                    jobs.append({
                                        "title": job.get("title", "Job"),
                                        "company": job.get("companyName", "LinkedIn Job"),
                                        "location": job.get("location", location or "Remote"),
                                        "salary": job.get("salary", "Negotiable"),
                                        "job_type": job.get("jobType", "Full-time"),
                                        "source": "linkedin",
                                        "url": job.get("applyUrl", "https://www.linkedin.com/jobs/"),
                                        "description": job.get("description", "")[:200]
                                    })
                        except:
                            # Fallback: if JSON parsing fails
                            pass
        except Exception as e:
            print(f"LinkedIn search error: {e}")
        
        return jobs

    async def search_himalayas(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search Himalayas.app job board (free API)."""
        jobs = []
        try:
            # Himalayas has a free job API
            async with aiohttp.ClientSession() as session:
                # Search for data engineering jobs
                url = "https://api.thehimalayasapp.com/api/v1/roles/search"
                params = {
                    "q": "data engineer",
                    "count": 20,
                    "sort": "-date_posted"
                }
                
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for job in data.get('roles', [])[:15]:
                            # Filter by location if specified
                            job_loc = job.get('location', 'Remote').lower()
                            if location and location.lower() == 'usa':
                                if 'usa' not in job_loc and 'remote' not in job_loc and 'united states' not in job_loc:
                                    continue
                            
                            salary = "Negotiable"
                            if job.get('salary_min') and job.get('salary_max'):
                                salary = f"${job.get('salary_min')}-${job.get('salary_max')}"
                            elif job.get('salary_min'):
                                salary = f"${job.get('salary_min')}+"
                            
                            jobs.append({
                                "title": job.get('title', 'Data Engineer'),
                                "company": job.get('company_name', 'N/A'),
                                "location": job.get('location', 'Remote'),
                                "salary": salary,
                                "job_type": job.get('job_type', 'Full-time'),
                                "source": "himalayas",
                                "url": job.get('url', ''),
                                "description": job.get('description', '')[:200]
                            })
        except Exception as e:
            print(f"Himalayas search error: {e}")
        
        return jobs

    async def search_all(self, keywords: List[str], location: str, salary_min: int = None, level: str = None, job_type: str = None) -> List[Dict]:
        """Search all sources concurrently."""
        tasks = [
            self.search_remoteok(keywords, location),
            self.search_justjoinit(keywords, location),
            self.search_himalayas(keywords, location),
            self.search_indeed(keywords, location),
            self.search_linkedin(keywords, location),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_jobs = []
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
        
        # Filter by salary if specified
        if salary_min:
            all_jobs = [j for j in all_jobs if j.get('salary') and extract_salary(j['salary']) >= salary_min]
        
        # Deduplicate by URL
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job['url'] not in seen:
                seen.add(job['url'])
                unique_jobs.append(job)
        
        return unique_jobs


def extract_salary(salary_str: str) -> int:
    """Extract minimum salary from string."""
    if not salary_str or salary_str == "Negotiable":
        return 0
    
    numbers = re.findall(r'\d+', salary_str.replace(',', ''))
    if numbers:
        return int(numbers[0])
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
