"""
DeepSeek API key validator.

Unlike chat-based validators, DeepSeek ships a lightweight ``/user/balance``
endpoint that doubles as both authentication check and balance lookup, so
validation is one HTTP round-trip with no model call cost.
"""

import re
import requests
from typing import Dict, Any, List

from .base import BaseValidator
from ..core import ValidationResult
from ..models.config import ValidatorConfig
from ..utils.logger import logger


class DeepSeekValidator(BaseValidator):
    """Validator for DeepSeek API keys."""

    def __init__(self, config: ValidatorConfig):
        super().__init__(config)
        self.base_url = "https://api.deepseek.com"
        self._key_pattern = re.compile(r'^sk-[a-f0-9]{32}$', re.IGNORECASE)

    @property
    def supported_key_types(self) -> List[str]:
        """Return list of supported key types."""
        return ['deepseek']

    def can_validate(self, key: str) -> bool:
        """Check if this validator can validate the given key."""
        return bool(self._key_pattern.match(key))

    def validate(self, key: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate DeepSeek API key by querying /user/balance."""
        if not self.config.enabled:
            return self._create_error_result('disabled', 'DeepSeek validator is disabled')

        # Throttle a little; balance endpoint is cheap but still rate-limited.
        self._add_delay()

        # Optional proxy from scanner context
        proxies = None
        proxy_config = context.get('proxy_config') if context else None
        if proxy_config:
            proxies = {
                'http': proxy_config.get('http'),
                'https': proxy_config.get('https'),
            }

        url = f"{self.base_url}/user/balance"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {key}",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.config.timeout,
                proxies=proxies,
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError:
                    return self._create_error_result('bad_response', 'Invalid JSON from balance endpoint')

                # DeepSeek treats `is_available=false` as "authenticated but no
                # credit". We surface that as invalid so the UI's valid-count
                # stays meaningful.
                if not data.get('is_available', False):
                    return self._create_error_result('no_balance', 'Key authenticated but has no usable balance')

                metadata: Dict[str, Any] = {
                    'response_time': response.elapsed.total_seconds(),
                    'is_available': True,
                }

                balance_infos = data.get('balance_infos') or []
                if isinstance(balance_infos, list) and balance_infos:
                    primary = balance_infos[0]
                    currency = primary.get('currency', '')
                    total = primary.get('total_balance')
                    if total is not None:
                        # Surface a human-readable string for the UI's "余额" column.
                        metadata['total_balance'] = f"{total} {currency}".strip()
                    metadata['granted_balance'] = primary.get('granted_balance')
                    metadata['topped_up_balance'] = primary.get('topped_up_balance')
                    metadata['currency'] = currency
                    metadata['balance_infos'] = balance_infos

                return self._create_success_result(metadata)

            if response.status_code == 401:
                return self._create_error_result('unauthorized', 'Invalid API key')
            if response.status_code == 403:
                return self._create_error_result('forbidden', 'Access forbidden')
            if response.status_code == 429:
                return self._create_error_result('rate_limited', 'Rate limit exceeded')

            return self._create_error_result('unknown', f"HTTP {response.status_code}: {response.text[:200]}")

        except requests.exceptions.Timeout:
            return self._create_error_result('timeout', f"Request timeout after {self.config.timeout}s")
        except requests.exceptions.ConnectionError:
            return self._create_error_result('network_error', 'Connection error')
        except requests.exceptions.RequestException as e:
            return self._create_error_result('network_error', f"Request error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error validating DeepSeek key: {e}")
            return self._create_error_result('unknown', f"Unexpected error: {e}")
