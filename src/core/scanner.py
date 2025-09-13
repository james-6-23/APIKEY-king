"""
Main scanner implementation with orchestration logic.
"""

from typing import List, Dict, Any


class APIKeyScanner:
    """Main scanner implementation that orchestrates extraction and validation."""
    
    def __init__(self, extractors: List, validators: List):
        self.extractors = extractors
        self.validators = validators
        self._extractor_map = {ext.name: ext for ext in extractors}
        self._validator_map = {val.name: val for val in validators}
    
    def scan_content(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan content using all applicable extractors and validators.
        
        Returns:
            Dictionary with structure:
            {
                'extracted_keys': {extractor_name: ExtractionResult},
                'validation_results': {key: ValidationResult},
                'summary': {
                    'total_keys_found': int,
                    'total_valid_keys': int,
                    'extractors_used': List[str]
                }
            }
        """
        results = {
            'extracted_keys': {},
            'validation_results': {},
            'summary': {
                'total_keys_found': 0,
                'total_valid_keys': 0,
                'extractors_used': []
            }
        }
        
        # Run extraction
        all_keys = set()
        for extractor in self.extractors:
            if extractor.should_process(content, context):
                extraction_result = extractor.extract(content, context)
                if extraction_result.keys:
                    results['extracted_keys'][extractor.name] = extraction_result
                    results['summary']['extractors_used'].append(extractor.name)
                    all_keys.update(extraction_result.keys)
        
        results['summary']['total_keys_found'] = len(all_keys)
        
        # Run validation for each unique key
        for key in all_keys:
            validator = self._find_validator_for_key(key)
            if validator:
                validation_result = validator.validate(key, context)
                results['validation_results'][key] = validation_result
                if validation_result.is_valid:
                    results['summary']['total_valid_keys'] += 1
        
        return results
    
    def _find_validator_for_key(self, key: str):
        """Find the appropriate validator for a given key."""
        for validator in self.validators:
            if validator.can_validate(key):
                return validator
        return None
    
    def get_extractor(self, name: str):
        """Get extractor by name."""
        return self._extractor_map.get(name)
    
    def get_validator(self, name: str):
        """Get validator by name."""
        return self._validator_map.get(name)