"""Career sweep configuration - IT Manager and Sr IT Manager only."""

# SMTP
SMTP_HOST = "smtp.mail.me.com"
SMTP_PORT = 587
SMTP_USER = "fihassistant@icloud.com"
SMTP_PASS = "oqta-eehk-twjn-ycpk"
EMAIL_FROM = "fihassistant@icloud.com"
EMAIL_TO = "freemancurtisd@gmail.com"

# Target roles: IT Manager and Sr IT Manager ONLY
EXACT_PHRASES = [
    "it manager",
    "sr it manager",
    "sr. it manager",
    "senior it manager",
    "it operations manager",
    "infrastructure manager",
]

# Leadership + Domain combos (for titles like "Senior Manager, IT Operations")
LEADERSHIP_TERMS = [
    "senior manager", "sr manager", "sr. manager", "manager",
]

DOMAIN_TERMS = [
    "it", "it operations", "information technology",
    "infrastructure", "technology operations",
    "workplace technology", "enterprise technology",
    "service delivery", "endpoint", "desktop",
]

# Negative title signals - reject these
TITLE_NEGATIVES = [
    "intern", "entry level", "junior", "associate", "co-op",
    "sales", "marketing", "account executive", "account manager",
    "finance", "tax", "accounting", "revenue", "pricing",
    "frontend", "ios", "android",
    "software engineer", "backend engineer", "frontend engineer",
    "product marketing", "customer success", "partner",
    "nurse", "cook", "dealer", "bartender", "security officer",
    "restaurant", "retail", "warehouse", "driver",
    "recruiting", "recruiter", "talent acquisition",
    "payroll", "compensation", "benefits",
    "campaign", "events", "sustainability", "esg",
    "people", "hr", "human resources",
    "product manager", "program manager",
    "legal counsel", "attorney", "paralegal",
    "data engineer", "data scientist", "ml engineer",
    "research engineer", "research scientist",
    "art director", "creative director", "design director",
    "growth", "business development",
    "engineering manager",
    "applied ai", "machine learning",
    "solutions architect",
    "director", "head", "vp", "vice president",
]

# Top tech companies (bonus points)
TOP_COMPANIES = {
    "google", "microsoft", "amazon", "apple", "meta", "netflix",
    "salesforce", "adobe", "nvidia", "openai", "anthropic", "stripe",
    "figma", "vercel", "cloudflare", "datadog", "snowflake", "databricks",
    "mongodb", "elastic", "confluent", "doordash", "airtable", "servicenow",
    "palo alto networks", "crowdstrike", "zscaler", "hashicorp",
    "twilio", "samsara", "liveperson", "talkdesk", "dialpad",
}

# Location filtering
US_CITIES = [
    "new york", "boston", "seattle", "san francisco", "los angeles", "chicago",
    "austin", "denver", "miami", "atlanta", "washington", "phoenix", "dallas",
    "houston", "richmond", "nashville", "portland", "philadelphia", "detroit",
    "minneapolis", "las vegas", "reno", "henderson", "north las vegas",
    "sparks", "salt lake", "raleigh", "charlotte", "pittsburgh",
    "san diego", "tampa", "orlando",
]

US_SIGNALS = [
    "united states", "usa", "u.s.", "us-remote", "us remote",
    "remote - us", "remote, us", "north america",
]

REMOTE_KEYWORDS = ["remote", "anywhere", "work from home", "remote-friendly"]

INTERNATIONAL_ONLY = [
    "london", "berlin", "germany", "uk only", "australia", "singapore",
    "sydney", "canada", "toronto", "vancouver", "paris", "amsterdam",
    "tokyo", "india", "bengaluru", "bangalore", "japan", "china",
    "brazil", "mexico", "berlin office", "remotely in germany",
    "remotely in the uk", "london office", "dublin", "ireland",
    "netherlands", "poland", "philippines", "manila", "spain",
    "barcelona", "madrid", "portugal", "lisbon", "zurich", "switzerland",
    "apac", "europe", "eu", "middle east", "africa",
]

# Scoring
SCORING = {
    "remote_bonus": 3,
    "vegas_bonus": 5,
    "top_company_bonus": 3,
    "junior_penalty": -15,
}

TITLE_SCORES = {
    "senior it manager": 9,
    "sr it manager": 9,
    "sr. it manager": 9,
    "senior manager": 9,
    "sr manager": 9,
    "sr. manager": 9,
    "it manager": 8,
    "it operations manager": 8,
    "infrastructure manager": 8,
    "manager": 8,
}

# ATS companies to scan (Greenhouse/Ashby/Lever/Workday slugs)
ATS_COMPANIES = [
    ("Anthropic", "greenhouse", "anthropic"),
    ("OpenAI", "greenhouse", "openai"),
    ("Stripe", "greenhouse", "stripe"),
    ("Cloudflare", "greenhouse", "cloudflare"),
    ("Datadog", "greenhouse", "datadog"),
    ("Snowflake", "greenhouse", "snowflake"),
    ("Confluent", "greenhouse", "confluent"),
    ("Airtable", "greenhouse", "airtable"),
    ("Samsara", "greenhouse", "samsara"),
    ("LivePerson", "greenhouse", "liveperson"),
    ("Talkdesk", "greenhouse", "talkdesk2"),
    ("Twilio", "greenhouse", "twilio"),
    ("Dialpad", "greenhouse", "dialpad"),
    ("Clarity AI", "greenhouse", "clarityai"),
    ("MongoDB", "greenhouse", "mongodb"),
    ("Elastic", "greenhouse", "elastic"),
    ("HashiCorp", "greenhouse", "hashicorp"),
    ("CrowdStrike", "greenhouse", "crowdstrike"),
    ("ServiceNow", "greenhouse", "servicenow"),
    ("Palo Alto Networks", "greenhouse", "paloaltonetworks"),
    ("DoorDash", "greenhouse", "doordash"),
    ("Langfuse", "ashby", "langfuse"),
    ("Runway", "ashby", "runway-ml"),
    ("Figma", "ashby", "figma"),
    ("Vercel", "ashby", "vercel"),
    ("Databricks", "ashby", "databricks"),
    ("Tinybird", "lever", "tinybird"),
    ("Retool", "lever", "retool"),
    ("Genesys", "workday", "genesys.wd1.myworkdayjobs.com:genesys:Genesys"),
    ("Salesforce", "workday", "salesforce.wd1.myworkdayjobs.com:salesforce:Salesforce"),
    ("MGM Resorts", "html", "https://careers.mgmresorts.com"),
]

# Data paths
DATA_DIR = "/home/fihadmin/career-sweep/data"
SEEN_FILE = f"{DATA_DIR}/seen.json"
APPLIED_FILE = f"{DATA_DIR}/applied.json"
