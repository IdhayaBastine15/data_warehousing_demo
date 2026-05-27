"""Shared constants for the entire pipeline. Import from here — never duplicate."""
from __future__ import annotations
import os

STATE_ABBREV: dict[str, str] = {
    'AL': 'Alabama',        'AK': 'Alaska',         'AZ': 'Arizona',       'AR': 'Arkansas',
    'CA': 'California',     'CO': 'Colorado',        'CT': 'Connecticut',   'DE': 'Delaware',
    'DC': 'District of Columbia', 'FL': 'Florida',   'GA': 'Georgia',       'HI': 'Hawaii',
    'ID': 'Idaho',          'IL': 'Illinois',        'IN': 'Indiana',       'IA': 'Iowa',
    'KS': 'Kansas',         'KY': 'Kentucky',        'LA': 'Louisiana',     'ME': 'Maine',
    'MD': 'Maryland',       'MA': 'Massachusetts',   'MI': 'Michigan',      'MN': 'Minnesota',
    'MS': 'Mississippi',    'MO': 'Missouri',        'MT': 'Montana',       'NE': 'Nebraska',
    'NV': 'Nevada',         'NH': 'New Hampshire',   'NJ': 'New Jersey',    'NM': 'New Mexico',
    'NY': 'New York',       'NC': 'North Carolina',  'ND': 'North Dakota',  'OH': 'Ohio',
    'OK': 'Oklahoma',       'OR': 'Oregon',          'PA': 'Pennsylvania',  'RI': 'Rhode Island',
    'SC': 'South Carolina', 'SD': 'South Dakota',    'TN': 'Tennessee',     'TX': 'Texas',
    'UT': 'Utah',           'VT': 'Vermont',         'VA': 'Virginia',      'WA': 'Washington',
    'WV': 'West Virginia',  'WI': 'Wisconsin',       'WY': 'Wyoming',
    'PR': 'Puerto Rico',    'VI': 'Virgin Islands',  'GU': 'Guam',
    'AS': 'American Samoa', 'MP': 'Northern Marianas',
}

REGION_MAP: dict[str, list[str]] = {
    'Northeast': [
        'Maine', 'New Hampshire', 'Vermont', 'Massachusetts', 'Rhode Island',
        'Connecticut', 'New York', 'New Jersey', 'Pennsylvania',
    ],
    'Southeast': [
        'Maryland', 'Delaware', 'Virginia', 'West Virginia', 'North Carolina',
        'South Carolina', 'Georgia', 'Florida', 'Alabama', 'Mississippi',
        'Tennessee', 'Kentucky',
    ],
    'Midwest': [
        'Ohio', 'Michigan', 'Indiana', 'Wisconsin', 'Illinois', 'Minnesota',
        'Iowa', 'Missouri', 'North Dakota', 'South Dakota', 'Nebraska', 'Kansas',
    ],
    'Southwest': ['Texas', 'Oklahoma', 'New Mexico', 'Arizona'],
    'West': [
        'Colorado', 'Wyoming', 'Montana', 'Idaho', 'Washington', 'Oregon',
        'Utah', 'Nevada', 'California', 'Alaska', 'Hawaii',
    ],
}

# Derived reverse-lookup: state name → region
STATE_TO_REGION: dict[str, str] = {
    state: region for region, states in REGION_MAP.items() for state in states
}

VALID_REGIONS: frozenset[str] = frozenset(REGION_MAP.keys())

VALID_METRICS: frozenset[str] = frozenset({
    "total_cost", "housing_cost", "food_cost",
    "healthcare_cost", "childcare_cost", "transportation_cost",
    "affordability_ratio",
})

# Column order expected in the raw source file
RAW_COLUMNS: tuple[str, ...] = (
    "case_id", "state", "areaname", "county", "isMetro",
    "housing_cost", "food_cost", "transportation_cost", "healthcare_cost",
    "other_necessities_cost", "childcare_cost", "taxes",
    "total_cost", "median_family_income",
)

# Environment-configurable defaults
DEFAULT_DB_URL         = os.getenv("DATABASE_URL",    "postgresql://dap:dap@127.0.0.1:5432/dap")
DEFAULT_SOURCE_PATH    = os.getenv("SOURCE_PATH",     "cost_of_living_us_dap2.xls")
DEFAULT_STAGING_PATH   = os.getenv("STAGING_PATH",   "data/staging")
DEFAULT_PROCESSED_PATH = os.getenv("PROCESSED_PATH", "data/processed")
