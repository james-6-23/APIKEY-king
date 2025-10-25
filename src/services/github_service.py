"""
GitHub service for API interactions.
"""

import base64
import random
import time
from typing import Dict, List, Optional, Any
import requests

from ..models.config import AppConfig, ProxyConfig


class GitHubService:
    """Service for GitHub API interactions."""
    
    def __init__(self, config: AppConfig, log_callback=None):
        self.config = config
        self.tokens = config.github.tokens
        self.api_url = config.github.api_url
        self.proxies = config.get_proxy_configs()
        self._token_ptr = 0
        self.log_callback = log_callback or print  # Use callback or default to print
    
    def _get_next_token(self) -> Optional[str]:
        """Get next token from rotation."""
        if not self.tokens:
            return None
        
        token = self.tokens[self._token_ptr % len(self.tokens)]
        self._token_ptr += 1
        return token.strip()
    
    def _get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get random proxy configuration."""
        if not self.proxies:
            return None
        
        proxy_config = random.choice(self.proxies)
        return {
            'http': proxy_config.http,
            'https': proxy_config.https
        } if proxy_config.http or proxy_config.https else None
    
    def search_code(self, query: str, max_retries: int = 5) -> Dict[str, Any]:
        """
        Search GitHub code with the given query.
        
        Args:
            query: GitHub search query
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary containing search results
        """
        all_items = []
        total_count = 0
        expected_total = None
        pages_processed = 0
        
        # Statistics
        total_requests = 0
        failed_requests = 0
        rate_limit_hits = 0
        
        for page in range(1, 11):  # Max 10 pages
            page_result = None
            page_success = False
            
            for attempt in range(1, max_retries + 1):
                current_token = self._get_next_token()
                
                headers = {
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
                }
                
                if current_token:
                    headers["Authorization"] = f"token {current_token}"
                
                params = {
                    "q": query,
                    "per_page": 100,
                    "page": page
                }
                
                try:
                    total_requests += 1
                    proxies = self._get_random_proxy()
                    
                    response = requests.get(
                        self.api_url,
                        headers=headers,
                        params=params,
                        timeout=30,
                        proxies=proxies
                    )
                    
                    rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
                    if rate_limit_remaining and int(rate_limit_remaining) < 3:
                        self.log_callback(f"⚠️ Rate limit low: {rate_limit_remaining} remaining")
                    
                    response.raise_for_status()
                    page_result = response.json()
                    page_success = True
                    break
                    
                except requests.exceptions.HTTPError as e:
                    status = e.response.status_code if e.response else None
                    failed_requests += 1
                    
                    if status in (403, 429):
                        rate_limit_hits += 1
                        if rate_limit_remaining and int(rate_limit_remaining) == 0:
                            self.log_callback(f"⚠️ Token exhausted, switching to next token")
                            continue
                        
                        wait = min(2 ** attempt + random.uniform(0, 1), 120)
                        if attempt >= 2:
                            self.log_callback(f"⚠️ Rate limit hit (attempt {attempt}/{max_retries}) - waiting {wait:.1f}s")
                        time.sleep(wait)
                        continue
                    else:
                        if attempt == max_retries:
                            self.log_callback(f"❌ HTTP {status} error after {max_retries} attempts on page {page}")
                        time.sleep(min(2 ** attempt, 30))
                        continue
                        
                except requests.exceptions.RequestException as e:
                    failed_requests += 1
                    wait = min(2 ** attempt, 30)
                    
                    if attempt == max_retries:
                        self.log_callback(f"❌ Network error after {max_retries} attempts on page {page}: {type(e).__name__}")
                    
                    time.sleep(wait)
                    continue
            
            if not page_success or not page_result:
                if page == 1:
                    self.log_callback(f"❌ First page failed for query: {query[:50]}...")
                    break
                continue
            
            pages_processed += 1
            
            if page == 1:
                total_count = page_result.get("total_count", 0)
                expected_total = min(total_count, 1000)
            
            items = page_result.get("items", [])
            current_page_count = len(items)
            
            if current_page_count == 0:
                if expected_total and len(all_items) < expected_total:
                    continue
                else:
                    break
            
            all_items.extend(items)
            
            if expected_total and len(all_items) >= expected_total:
                break
            
            if page < 10:
                sleep_time = random.uniform(0.5, 1.5)
                self.log_callback(f"[WAIT] Processing query page {page}, items: {current_page_count}, sleep: {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        final_count = len(all_items)
        
        # Check data integrity
        if expected_total and final_count < expected_total:
            discrepancy = expected_total - final_count
            if discrepancy > expected_total * 0.1:
                self.log_callback(f"⚠️ Significant data loss: {discrepancy}/{expected_total} items missing")
        
        self.log_callback(f"🔍 Search complete: {final_count}/{expected_total or '?'} items, {pages_processed} pages, {total_requests} requests")
        
        return {
            "total_count": total_count,
            "incomplete_results": final_count < expected_total if expected_total else False,
            "items": all_items,
            "statistics": {
                "pages_processed": pages_processed,
                "total_requests": total_requests,
                "failed_requests": failed_requests,
                "rate_limit_hits": rate_limit_hits
            }
        }
    
    def get_file_content(self, item: Dict[str, Any]) -> Optional[str]:
        """
        Get file content from GitHub API.
        
        Args:
            item: GitHub search result item
            
        Returns:
            File content as string, or None if failed
        """
        repo_full_name = item["repository"]["full_name"]
        file_path = item["path"]
        
        metadata_url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        
        token = self._get_next_token()
        if token:
            headers["Authorization"] = f"token {token}"
        
        try:
            proxies = self._get_random_proxy()
            
            self.log_callback(f"🌐 Fetching: {metadata_url}")
            metadata_response = requests.get(
                metadata_url,
                headers=headers,
                proxies=proxies,
                timeout=30
            )
            
            metadata_response.raise_for_status()
            file_metadata = metadata_response.json()
            
            # Try base64 content first
            encoding = file_metadata.get("encoding")
            content = file_metadata.get("content")
            
            if encoding == "base64" and content:
                try:
                    decoded_content = base64.b64decode(content).decode('utf-8')
                    return decoded_content
                except Exception as e:
                    self.log_callback(f"⚠️ Failed to decode base64 content: {e}")
            
            # Fallback to download_url
            download_url = file_metadata.get("download_url")
            if not download_url:
                self.log_callback(f"⚠️ No download URL found")
                return None
            
            content_response = requests.get(
                download_url,
                headers=headers,
                proxies=proxies,
                timeout=30
            )
            
            content_response.raise_for_status()
            return content_response.text
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch file content: {type(e).__name__}")
            return None