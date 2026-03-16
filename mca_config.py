"""Configuration for Montana Code Annotated (MCA) scraper."""

# Titles to scrape: number -> human-readable name
TITLES_TO_SCRAPE = {
    0: "Montana Constitution",
    1: "General Laws & Definitions",
    2: "Government Structure & Administration",
    3: "Judiciary, Courts",
    5: "Legislative Branch",
    7: "Local Government",
    18: "Public Contracts",
    25: "Civil Procedure",
    26: "Evidence",
    27: "Civil Liability, Remedies & Limitations",
    28: "Contracts & Other Obligations",
    33: "Insurance",
    39: "Labor",
    40: "Family Law",
    41: "Minors",
    44: "Law Enforcement",
    45: "Crimes",
    46: "Criminal Procedure",
    49: "Human Rights",
    50: "Health & Safety",
    52: "Family Services",
    69: "Public Utilities",
    70: "Property",
    71: "Mortgages, Pledges & Liens",
    72: "Estates, Trusts & Fiduciary Relationships",
    75: "Environmental Protection",
    76: "Land Resources & Use",
    77: "State Lands",
    85: "Water Use",
    87: "Fish & Wildlife",
}

BASE_URL = "https://leg.mt.gov/bills/mca"
DATA_DIR = "data/mca"

# Politeness settings
REQUEST_DELAY_SECONDS = 1.0
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 5.0
REQUEST_TIMEOUT_SECONDS = 30

USER_AGENT = (
    "Mozilla/5.0 (compatible; MCA-Research-Scraper/1.0; "
    "educational/legal-research)"
)


def title_dir(n):
    """Title number -> directory URL component. Title 45 -> 'title_0450'."""
    return f"title_{n * 10:04d}"


def title_url(n):
    """Full URL to a title's chapters index page."""
    return f"{BASE_URL}/{title_dir(n)}/chapters_index.html"
