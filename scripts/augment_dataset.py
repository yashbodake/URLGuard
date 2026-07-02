"""Augment PhiUSIIL dataset with diverse legitimate URLs."""

import pandas as pd
import numpy as np

def load_original_dataset():
    """Load the original PhiUSIIL dataset."""
    df = pd.read_csv('data/raw/PhiUSIIL_Dataset.csv')
    print(f"Original dataset: {len(df)} rows")
    print(f"  Legitimate: {len(df[df['label']==0])}")
    print(f"  Phishing: {len(df[df['label']==1])}")
    return df

def generate_diverse_legitimate_urls():
    """Generate diverse legitimate URLs with paths to counter dataset bias."""
    
    # Base domains for legitimate sites
    base_domains = [
        # Search engines
        "google.com",
        "youtube.com", 
        "bing.com",
        "duckduckgo.com",
        
        # Social media
        "facebook.com",
        "twitter.com",
        "instagram.com",
        "linkedin.com",
        "reddit.com",
        "pinterest.com",
        "snapchat.com",
        "tiktok.com",
        
        # E-commerce
        "amazon.com",
        "ebay.com",
        "walmart.com",
        "target.com",
        "bestbuy.com",
        "homedepot.com",
        "lowes.com",
        "costco.com",
        "wayfair.com",
        "etsy.com",
        
        # Technology / Dev / SaaS
        "github.com",
        "gitlab.com",
        "stackoverflow.com",
        "stackoverflow.com",
        "npmjs.com",
        "pypi.org",
        "docker.com",
        "kubernetes.io",
        "aws.amazon.com",
        "azure.microsoft.com",
        "cloud.google.com",
        "github.io",
        "vercel.app",
        "netlify.app",
        "herokuapp.com",
        "slack.com",
        "zoom.us",
        "webex.com",
        "atlassian.com",
        "jira.com",
        "confluence.com",
        "trello.com",
        "asana.com",
        "notion.so",
        "dropbox.com",
        "onedrive.live.com",
        "google.com",
        "drive.google.com",
        "docs.google.com",
        "mail.google.com",
        "calendar.google.com",
        
        # News / Media
        "bbc.com",
        "cnn.com",
        "nytimes.com",
        "washingtonpost.com",
        "theguardian.com",
        "reuters.com",
        "bloomberg.com",
        "foxnews.com",
        "huffpost.com",
        
        # Entertainment / Streaming
        "netflix.com",
        "hulu.com",
        "disneyplus.com",
        "hbomax.com",
        "peacocktv.com",
        "paramountplus.com",
        
        # Finance / Banking
        "chase.com",
        "bankofamerica.com",
        "wellsfargo.com",
        "citibank.com",
        "americanexpress.com",
        "paypal.com",
        "venmo.com",
        "zelle.com",
        "kapitalbank.com",  # This will be filtered out as it's not in brand list but is legitimate
        
        # Education
        "wikipedia.org",
        "arxiv.org",
        "mit.edu",
        "stanford.edu",
        "harvard.edu",
        "yale.edu",
        
        # Government / Org
        "usa.gov",
        "gov.uk",
        "europa.eu",
        "un.org",
        "who.int",
        
        # Miscellaneous popular sites
        "yelp.com",
        "yellowpages.com",
        "yellowpages.ca",
        "tripadvisor.com",
        "airbnb.com",
        "booking.com",
        "expedia.com",
        "hotels.com",
        "investopedia.com",
        "webmd.com",
        "mayoclinic.org",
        "nih.gov",
        "cdc.gov",
        "fda.gov",
        "usps.com",
        "ups.com",
        "fedex.com",
        "amazon.com",
    ]
    
    # Common legitimate paths for each type of site
    path_patterns = [
        # Root/home (should already be in original dataset)
        "",
        "/",
        
        # Search / query
        "/search",
        "/search?q=test",
        "/results",
        "/results?q=test",
        
        # Product / item pages
        "/product/123",
        "/item/456",
        "/dp/B09V3KXJPB",
        "/gp/product/B09V3KXJPB",
        
        # Category / browse
        "/category/electronics",
        "/electronics/laptops",
        "/shop/new-arrivals",
        "/sale",
        "/deals",
        
        # Account / auth
        "/login",
        "/signin",
        "/accounts/Login",
        "/signin",
        "/register",
        "/signup",
        "/create-account",
        "/forgot-password",
        "/reset-password",
        
        # Profile / user
        "/user/johnsmith",
        "/profile/alice",
        "/users/12345",
        "/me",
        "/settings",
        
        # Documentation / help
        "/help",
        "/support",
        "/docs",
        "/documentation",
        "/guide",
        "/tutorial",
        "/faq",
        "/about",
        "/contact",
        
        # Blog / news / media
        "/blog",
        "/news",
        "/articles",
        "/press",
        "/media",
        "/video",
        "/watch",
        "/live",
        
        # API / developer
        "/api",
        "/api/v1",
        "/api/v2/users",
        "/webhook",
        "/widget",
        
        # File / download
        "/download",
        "/download/file.pdf",
        "/assets/css/style.css",
        "/js/app.js",
        "/images/logo.png",
        
        # Special parameters
        "?ref=homepage",
        "?utm_source=newsletter",
        "?campaign=spring_sale",
        "?sessionid=abc123",
        "?token=xyz789",
        
        # Fragments
        "#section1",
        "#comments",
        "#reviews",
        
        # Combined paths
        "/search?q=laptop&category=electronics",
        "/electronics/laptops?price=500-1000&sort=rating",
        "/account/settings/profile",
        "/help/articles/reset-password",
    ]
    
    # Generate legitimate URLs
    legitimate_urls = []
    
    for domain in base_domains:
        # Skip if domain is too short or invalid
        if len(domain) < 4 or '.' not in domain:
            continue
            
        # Add root domain
        legitimate_urls.append(f"https://{domain}")
        legitimate_urls.append(f"http://{domain}")
        
        # Add some path variations
        for path in path_patterns[:15]:  # Limit to avoid explosion
            if path == "" or path == "/":
                continue  # Already added as root
            url = f"https://{domain}{path}"
            legitimate_urls.append(url)
            
            # Also add HTTP version for some
            if len(legitimate_urls) < 2000:  # Prevent too many URLs
                url_http = f"http://{domain}{path}"
                legitimate_urls.append(url_http)
    
    # Remove duplicates
    legitimate_urls = list(set(legitimate_urls))
    
    # Filter out any that might accidentally be phishing-like
    # Remove URLs with suspicious patterns that are too close to phishing
    filtered_urls = []
    suspicious_patterns = [
        "secure-", "-secure", "_secure",
        "verify-", "-verify", "_verify", 
        "login-", "-login", "_login",
        "signin-", "-signin", "_signin",
        "account-", "-account", "_account",
        "update-", "-update", "_update",
        "bonus-", "-bonus", "_bonus",
        "free-", "-free", "_free",
        "prize-", "-prize", "_prize",
        "winner-", "-winner", "_winner",
        "confirm-", "-confirm", "_confirm",
        "alert-", "-alert", "_alert",
        "warning-", "-warning", "_warning",
        "suspend-", "-suspend", "_suspend",
        "lock-", "-lock", "_lock",
        "disabled-", "-disabled", "_disabled",
        "limited-", "-limited", "_limited",
        "urgent-", "-urgent", "_urgent",
        "immediately-", "-immediately", "_immediately",
        "expires-", "-expires", "_expires",
        "todayonly-", "-todayonly", "_todayonly",
        "actnow-", "-actnow", "_actnow",
        "donotreply-", "-donotreply", "_donotreply",
    ]
    
    for url in legitimate_urls:
        url_lower = url.lower()
        # Skip if contains suspicious patterns that are typical of phishing
        if any(pattern in url_lower for pattern in suspicious_patterns):
            continue
        # Skip if has @ symbol in weird places (common in phishing)
        if url.count('@') > 1 or (url.count('@') == 1 and not url.startswith('http://') and not url.startswith('https://')):
            continue
        filtered_urls.append(url)
    
    print(f"Generated {len(filtered_urls)} diverse legitimate URLs")
    return filtered_urls

def main():
    """Main augmentation function."""
    # Load original dataset
    df_original = load_original_dataset()
    
    # Generate diverse legitimate URLs
    diverse_legitimate_urls = generate_diverse_legitimate_urls()
    
    # Create DataFrame for new legitimate URLs (label=0)
    df_new = pd.DataFrame({
        'URL': diverse_legitimate_urls,
        'label': 0  # legitimate
    })
    
    # Combine datasets
    df_combined = pd.concat([df_original, df_new], ignore_index=True)
    
    # Remove duplicates based on URL (keep first occurrence)
    df_combined = df_combined.drop_duplicates(subset=['URL'], keep='first')
    
    print(f"Combined dataset: {len(df_combined)} rows")
    print(f"  Legitimate: {len(df_combined[df_combined['label']==0])}")
    print(f"  Phishing: {len(df_combined[df_combined['label']==1])}")
    print(f"  Legitimate percentage: {len(df_combined[df_combined['label']==0])/len(df_combined)*100:.1f}%")
    
    # Save augmented dataset
    output_path = 'data/raw/PhiUSIIL_Dataset_Augmented.csv'
    df_combined.to_csv(output_path, index=False)
    print(f"Augmented dataset saved to: {output_path}")
    
    # Show some examples of the new URLs
    print("\nExamples of new legitimate URLs added:")
    new_urls_df = df_combined[df_combined['label']==0].tail(10)
    for i, (_, row) in enumerate(new_urls_df.iterrows(), 1):
        print(f"  {i}. {row['URL']}")

if __name__ == "__main__":
    main()
