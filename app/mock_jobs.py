"""Mock job data for testing without external APIs."""

MOCK_JOBS = [
    {
        "title": "Senior Data Engineer",
        "company": "Stripe",
        "location": "Remote (USA)",
        "salary": "$180,000 - $250,000",
        "job_type": "Full-time",
        "source": "remoteok",
        "url": "https://stripe.com/jobs/listing/senior-data-engineer",
        "description": "Join Stripe's data team. Build scalable data pipelines and analytics infrastructure."
    },
    {
        "title": "Data Engineer (Mid-Level)",
        "company": "Databricks",
        "location": "San Francisco, CA (Remote options)",
        "salary": "$160,000 - $210,000",
        "job_type": "Full-time",
        "source": "remoteok",
        "url": "https://databricks.com/careers/data-engineer-mid",
        "description": "Work with Apache Spark and Delta Lake. Design and optimize data workflows."
    },
    {
        "title": "Data Engineer - Contract",
        "company": "Shopify",
        "location": "Remote",
        "salary": "$120 - $160/hour",
        "job_type": "Contract",
        "source": "justjoinit",
        "url": "https://shopify.jobs/data-engineer-contract",
        "description": "6-month contract. Build real-time data processing systems for e-commerce."
    },
    {
        "title": "Data Engineer (Mid)",
        "company": "Airbnb",
        "location": "Remote",
        "salary": "$165,000 - $225,000",
        "job_type": "Full-time",
        "source": "remoteok",
        "url": "https://airbnb.com/careers/data-engineer",
        "description": "Design and maintain ETL pipelines. Work with petabyte-scale datasets."
    },
    {
        "title": "Analytics Data Engineer",
        "company": "Figma",
        "location": "Remote (USA)",
        "salary": "$170,000 - $240,000",
        "job_type": "Full-time",
        "source": "remoteok",
        "url": "https://figma.com/jobs/data-engineer",
        "description": "Build analytics infrastructure. Help product teams make data-driven decisions."
    },
    {
        "title": "Contract Data Engineer",
        "company": "AWS",
        "location": "Remote",
        "salary": "$130 - $170/hour",
        "job_type": "Contract",
        "source": "himalayas",
        "url": "https://aws.amazon.com/careers/data-engineer-contract",
        "description": "3-month contract. Work on AWS data migration projects."
    },
    {
        "title": "Mid-Level Data Engineer",
        "company": "Notion",
        "location": "Remote",
        "salary": "$155,000 - $200,000",
        "job_type": "Full-time",
        "source": "remoteok",
        "url": "https://notion.so/careers/data-engineer",
        "description": "Scale Notion's data infrastructure. Work with distributed systems."
    },
    {
        "title": "Data Pipeline Engineer",
        "company": "Canva",
        "location": "Remote (USA friendly)",
        "salary": "$160,000 - $220,000",
        "job_type": "Full-time",
        "source": "remoteok",
        "url": "https://canva.com/careers/data-pipeline-engineer",
        "description": "Build resilient data pipelines. Optimize for performance at scale."
    },
    {
        "title": "Contract: ETL Developer",
        "company": "Microsoft",
        "location": "Remote",
        "salary": "$125 - $165/hour",
        "job_type": "Contract",
        "source": "justjoinit",
        "url": "https://microsoft.com/careers/etl-contract",
        "description": "4-month contract. Azure data platform experience required."
    },
    {
        "title": "Data Engineer II",
        "company": "Uber",
        "location": "Remote",
        "salary": "$170,000 - $230,000",
        "job_type": "Full-time",
        "source": "remoteok",
        "url": "https://uber.com/careers/data-engineer-ii",
        "description": "Build and maintain real-time data systems. Work with billions of events daily."
    },
    {
        "title": "Data Engineer - Mid Level",
        "company": "Google",
        "location": "Remote, USA",
        "salary": "$175,000 - $240,000",
        "job_type": "Full-time",
        "source": "indeed",
        "url": "https://www.indeed.com/viewjob?jk=data-engineer-google",
        "description": "Join Google's data infrastructure team. Work on distributed systems and data pipelines."
    },
    {
        "title": "Senior Data Engineer",
        "company": "Meta",
        "location": "Remote",
        "salary": "$185,000 - $260,000",
        "job_type": "Full-time",
        "source": "linkedin",
        "url": "https://www.linkedin.com/jobs/view/data-engineer-meta",
        "description": "Build scalable data systems. Lead data engineering initiatives at Meta."
    },
]


def get_mock_jobs() -> list:
    """Return mock jobs for testing."""
    return MOCK_JOBS.copy()
