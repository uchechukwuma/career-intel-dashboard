# ============================================
# CONFIGURATION CONSTANTS
# ============================================

# Quality threshold - only articles above this are considered "signals"
QUALITY_THRESHOLD = 40  # percentage

# Premium pricing
PREMIUM_PRICE_MONTHLY = 49  # euros

# Common acronyms that should stay uppercase
ACRONYMS = [
    # German labor market specific
    'AI', 'HR', 'ML', 'CEO', 'CTO', 'CFO', 'COO', 'CIO', 'CTO',
    'API', 'SaaS', 'IAB', 'BMAS', 'DGB', 'FAZ', 'MDR', 'RND', 'DPA',
    'EU', 'USA', 'UK', 'IT', 'KI', 'AG', 'GMBH', 'SE', 'PLC',
    
    # Companies
    'SAP', 'IBM', 'BMW', 'VW', 'DB', 'DHL', 'Lufthansa', 'Siemens',
    'BASF', 'Bayer', 'Mercedes', 'Audi', 'Porsche', 'Adidas', 'Puma',
    'Deutsche Telekom', 'Telekom', 'Vodafone', 'O2', 'E.ON', 'RWE',
    
    # Tech
    'AWS', 'GCP', 'Azure', 'OpenAI', 'Anthropic', 'Meta', 'Google',
    'Microsoft', 'Apple', 'Amazon', 'Netflix', 'Oracle', 'Salesforce',
    'Adobe', 'Intel', 'Nvidia', 'AMD', 'TSMC', 'Samsung',
    
    # Media
    'ARD', 'ZDF', 'RTL', 'ProSieben', 'Sat.1', 'Axel Springer',
    
    # Organizations
    'IG Metall', 'Verdi', 'IG BCE', 'DGB', 'BDA', 'DIHK', 'ZDH',
    'Ifo', 'IAB', 'DIW', 'RWI', 'ZEW', 'IW', 'KOF'
]

# Color schemes
COLORS = {
    'primary': '#00C2FF',
    'secondary': '#667eea',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'danger': '#FF6B6B',
    'gold': '#FFD700',
    'dark': '#0A0F1F'
}

# Badge thresholds
BADGE_THRESHOLDS = {
    'hot': 70,
    'trending': 50
}