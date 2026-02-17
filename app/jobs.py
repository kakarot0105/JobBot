"""Job scraping and search module."""
import aiohttp
import asyncio
from typing import List, Dict
from datetime import datetime
import re
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

    async def search_github_jobs(self, keywords: List[str], location: str = None) -> List[Dict]:
        """Search GitHub Jobs."""
        jobs = []
        try:
            # GitHub Jobs API (note: may be deprecated, using alternative)
            async with aiohttp.ClientSession() as session:
                for keyword in keywords:
                    url = "https://api.github.com/search/repositories"
                    params = {
                        "q": f"language:python jobs {keyword}",
                        "sort": "stars",
                        "per_page": 5
                    }
                    
                    async with session.get(url, params=params, timeout=10, headers={"User-Agent": "JobBot"}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for repo in data.get('items', [])[:10]:
                                jobs.append({
                                    "title": f"{keyword} Developer",
                                    "company": repo.get('owner', {}).get('login', 'N/A'),
                                    "location": "Remote",
                                    "salary": "Competitive",
                                    "job_type": "Full-time",
                                    "source": "github",
                                    "url": repo.get('html_url', ''),
                                    "description": repo.get('description', '')[:200]
                                })
        except Exception as e:
            print(f"GitHub search error: {e}")
        
        return jobs

    async def search_all(self, keywords: List[str], location: str, salary_min: int = None, level: str = None, job_type: str = None) -> List[Dict]:
        """Search all sources concurrently."""
        tasks = [
            self.search_remoteok(keywords, location),
            self.search_justjoinit(keywords, location),
            self.search_github_jobs(keywords, location),
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
