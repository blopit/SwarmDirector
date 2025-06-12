"""
DiffGenerator component for SwarmDirector
Provides sophisticated JSON diff generation between text versions with change detection and metadata
"""

import difflib
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class DiffGenerator:
    """
    Specialized component for generating structured JSON diffs between text versions
    Detects additions, deletions, modifications, and moves with confidence scoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize DiffGenerator with optional configuration
        
        Args:
            config: Configuration dictionary for diff generation parameters
        """
        self.config = config or {}
        
        # Default configuration
        self.min_confidence = self.config.get('min_confidence', 0.3)
        self.max_diffs = self.config.get('max_diffs', 50)
        self.context_lines = self.config.get('context_lines', 2)
        self.word_diff_threshold = self.config.get('word_diff_threshold', 0.6)
        
        logger.debug(f"DiffGenerator initialized with config: {self.config}")
    
    def generate_diff(self, original: str, modified: str = None, 
                     suggestions: Optional[List[Dict]] = None,
                     context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate structured JSON diff between original and modified text or from suggestions
        
        Args:
            original: Original text content
            modified: Modified text content (optional if using suggestions)
            suggestions: List of review suggestions to convert to diffs
            context: Additional context for diff generation
            
        Returns:
            List of structured diff entries with metadata
        """
        logger.info(f"Generating diff for content ({len(original)} chars)")
        
        if not original:
            return self._create_empty_diff_result("No original content provided")
        
        try:
            diffs = []
            
            # Generate diffs from text comparison if modified version provided
            if modified and modified != original:
                text_diffs = self._generate_text_diffs(original, modified, context)
                diffs.extend(text_diffs)
            
            # Generate diffs from suggestions if provided
            if suggestions:
                suggestion_diffs = self._generate_suggestion_diffs(original, suggestions, context)
                diffs.extend(suggestion_diffs)
            
            # If no modified text or suggestions, create informational diff
            if not diffs and not modified and not suggestions:
                diffs = self._create_informational_diff(original, context)
            
            # Sort by confidence and line number, limit results
            diffs = self._sort_and_limit_diffs(diffs)
            
            logger.info(f"Generated {len(diffs)} diff entries")
            return diffs
            
        except Exception as e:
            logger.error(f"Error generating diff: {str(e)}")
            return self._create_error_diff_result(str(e))
    
    def _generate_text_diffs(self, original: str, modified: str, 
                            context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate diffs by comparing original and modified text"""
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        # Use difflib for sequence matching
        matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)
        diffs = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
                
            diff_entry = self._create_diff_entry_from_opcode(
                tag, original_lines, modified_lines, i1, i2, j1, j2, context
            )
            if diff_entry:
                diffs.append(diff_entry)
        
        return diffs
    
    def _create_diff_entry_from_opcode(self, tag: str, original_lines: List[str], 
                                      modified_lines: List[str], i1: int, i2: int, 
                                      j1: int, j2: int, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a structured diff entry from difflib opcode"""
        
        # Calculate confidence based on change type and content similarity
        confidence = self._calculate_confidence(tag, original_lines[i1:i2] if i1 < len(original_lines) else [], 
                                               modified_lines[j1:j2] if j1 < len(modified_lines) else [])
        
        if confidence < self.min_confidence:
            return None
        
        diff_entry = {
            'type': self._map_opcode_to_type(tag),
            'line': i1 + 1,  # 1-indexed line numbers
            'confidence': round(confidence, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'category': 'text_comparison'
        }
        
        # Add type-specific fields
        if tag == 'delete':
            diff_entry.update({
                'original': '\n'.join(original_lines[i1:i2]),
                'reason': f"Content removed at line {i1 + 1}"
            })
        elif tag == 'insert':
            diff_entry.update({
                'suggested': '\n'.join(modified_lines[j1:j2]),
                'reason': f"Content added at line {i1 + 1}"
            })
        elif tag == 'replace':
            diff_entry.update({
                'original': '\n'.join(original_lines[i1:i2]),
                'suggested': '\n'.join(modified_lines[j1:j2]),
                'reason': f"Content modified at line {i1 + 1}"
            })
        
        # Add word-level diff for replace operations
        if tag == 'replace' and len(original_lines[i1:i2]) == 1 and len(modified_lines[j1:j2]) == 1:
            word_diff = self._generate_word_diff(original_lines[i1], modified_lines[j1])
            if word_diff:
                diff_entry['word_changes'] = word_diff
        
        return diff_entry
    
    def _generate_word_diff(self, original_line: str, modified_line: str) -> Optional[List[Dict[str, Any]]]:
        """Generate word-level differences within a line"""
        original_words = original_line.split()
        modified_words = modified_line.split()
        
        matcher = difflib.SequenceMatcher(None, original_words, modified_words)
        word_changes = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                change = {
                    'type': self._map_opcode_to_type(tag),
                    'position': i1,
                    'original_words': original_words[i1:i2] if tag in ['delete', 'replace'] else [],
                    'modified_words': modified_words[j1:j2] if tag in ['insert', 'replace'] else []
                }
                word_changes.append(change)
        
        return word_changes if word_changes else None
    
    def _generate_suggestion_diffs(self, original: str, suggestions: List[Dict],
                                  context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate diffs from review suggestions with enhanced intelligence"""
        diffs = []
        lines = original.splitlines()
        
        for i, suggestion in enumerate(suggestions[:self.max_diffs]):
            try:
                diff_entry = self._create_diff_from_suggestion(original, lines, suggestion, context)
                if diff_entry and diff_entry.get('confidence', 0) >= self.min_confidence:
                    diffs.append(diff_entry)
            except Exception as e:
                logger.warning(f"Error processing suggestion {i}: {str(e)}")
                continue
        
        return diffs
    
    def _create_diff_from_suggestion(self, original: str, lines: List[str], 
                                   suggestion: Dict, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a diff entry from a review suggestion with intelligent targeting"""
        issue = suggestion.get('issue', suggestion.get('reason', ''))
        category = suggestion.get('category', 'general')
        priority = suggestion.get('priority', 'medium')
        
        # Base diff entry
        diff_entry = {
            'type': self._determine_suggestion_type(suggestion),
            'category': category,
            'priority': priority,
            'reason': issue,
            'confidence': self._calculate_suggestion_confidence(suggestion, original),
            'timestamp': datetime.utcnow().isoformat(),
            'suggestion_id': suggestion.get('id', f"suggestion_{hash(issue) % 10000}")
        }
        
        # Intelligent targeting based on issue content
        target_info = self._find_target_location(original, lines, issue, suggestion)
        diff_entry.update(target_info)
        
        return diff_entry
    
    def _find_target_location(self, original: str, lines: List[str], issue: str, 
                             suggestion: Dict) -> Dict[str, Any]:
        """Intelligently find the target location for a suggestion"""
        issue_lower = issue.lower()
        
        # Punctuation issues
        if any(word in issue_lower for word in ['punctuation', 'period', 'comma', 'semicolon']):
            return self._target_punctuation_issues(lines, issue)
        
        # Paragraph and structure issues  
        elif any(word in issue_lower for word in ['paragraph', 'break', 'structure']):
            return self._target_structure_issues(lines, issue)
        
        # Grammar and style issues
        elif any(word in issue_lower for word in ['grammar', 'tense', 'voice', 'style']):
            return self._target_grammar_issues(lines, issue)
        
        # Header and organization issues
        elif any(word in issue_lower for word in ['header', 'title', 'section', 'organization']):
            return self._target_organization_issues(lines, issue)
        
        # Length issues
        elif any(word in issue_lower for word in ['length', 'brief', 'long', 'verbose']):
            return self._target_length_issues(lines, issue)
        
        # Default: general suggestion
        else:
            return self._create_general_suggestion(lines, issue, suggestion)
    
    def _target_punctuation_issues(self, lines: List[str], issue: str) -> Dict[str, Any]:
        """Target punctuation-related issues"""
        for line_num, line in enumerate(lines):
            if line.strip() and not line.strip().endswith(('.', '!', '?', ':', ';')):
                return {
                    'line': line_num + 1,
                    'type': 'modification',
                    'original': line,
                    'suggested': line.rstrip() + '.',
                    'reason': f"Add proper ending punctuation: {issue}"
                }
        
        # If no specific target found, suggest general punctuation review
        return {
            'line': 1,
            'type': 'general',
            'reason': f"Review punctuation throughout document: {issue}",
            'suggestion': "Check all sentences for proper ending punctuation"
        }
    
    def _target_structure_issues(self, lines: List[str], issue: str) -> Dict[str, Any]:
        """Target structure and paragraph issues"""
        # Look for long lines that could be split
        for line_num, line in enumerate(lines):
            if len(line) > 200 and '. ' in line:
                sentences = re.split(r'\. ', line)
                if len(sentences) > 1:
                    split_point = line.find('. ') + 2
                    return {
                        'line': line_num + 1,
                        'type': 'split',
                        'original': line,
                        'suggested': [line[:split_point].strip(), line[split_point:].strip()],
                        'reason': f"Break into separate paragraphs: {issue}"
                    }
        
        # Suggest adding paragraph breaks after certain patterns
        content = '\n'.join(lines)
        if len(content) > 300 and '\n\n' not in content:
            return {
                'line': max(1, len(lines) // 2),
                'type': 'insertion',
                'suggested': '\n',
                'reason': f"Add paragraph break for better structure: {issue}"
            }
        
        return {
            'line': 1,
            'type': 'general',
            'reason': f"Review document structure: {issue}",
            'suggestion': "Consider reorganizing content into clear sections"
        }
    
    def _target_grammar_issues(self, lines: List[str], issue: str) -> Dict[str, Any]:
        """Target grammar and style issues"""
        # Look for common grammar patterns
        content = '\n'.join(lines)
        
        # Check for passive voice
        if 'passive' in issue.lower():
            passive_patterns = [r'\bwas\s+\w+ed\b', r'\bwere\s+\w+ed\b', r'\bbeen\s+\w+ed\b']
            for pattern in passive_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    return {
                        'line': line_num,
                        'type': 'modification',
                        'original': match.group(),
                        'reason': f"Consider active voice: {issue}",
                        'suggestion': "Rewrite in active voice"
                    }
        
        # Default grammar suggestion
        return {
            'line': 1,
            'type': 'general',
            'reason': f"Grammar review needed: {issue}",
            'suggestion': "Review grammar and style throughout document"
        }
    
    def _target_organization_issues(self, lines: List[str], issue: str) -> Dict[str, Any]:
        """Target organization and header issues"""
        # Check if document lacks headers
        has_headers = any(line.strip().endswith(':') or line.strip().startswith('#') 
                         for line in lines)
        
        if not has_headers and 'header' in issue.lower():
            return {
                'line': 1,
                'type': 'insertion',
                'suggested': '# Document Title\n\n',
                'reason': f"Add document header: {issue}"
            }
        
        return {
            'line': 1,
            'type': 'general',
            'reason': f"Improve organization: {issue}",
            'suggestion': "Add clear section headers and improve organization"
        }
    
    def _target_length_issues(self, lines: List[str], issue: str) -> Dict[str, Any]:
        """Target length-related issues"""
        content = '\n'.join(lines)
        word_count = len(content.split())
        
        if 'brief' in issue.lower() or 'short' in issue.lower():
            return {
                'line': len(lines),
                'type': 'insertion',
                'suggested': '\n\nAdd more detail here.',
                'reason': f"Expand content: {issue}"
            }
        
        elif 'long' in issue.lower() or 'verbose' in issue.lower():
            # Find the longest line/paragraph
            longest_line_num = max(range(len(lines)), key=lambda i: len(lines[i]))
            return {
                'line': longest_line_num + 1,
                'type': 'modification',
                'original': lines[longest_line_num],
                'reason': f"Condense content: {issue}",
                'suggestion': "Consider shortening this section"
            }
        
        return {
            'line': 1,
            'type': 'general',
            'reason': f"Adjust length: {issue}",
            'suggestion': f"Current length: {word_count} words"
        }
    
    def _create_general_suggestion(self, lines: List[str], issue: str, 
                                  suggestion: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a general suggestion entry"""
        priority = suggestion.get('priority', 'low') if suggestion else 'low'
        return {
            'line': 1,
            'type': 'general',
            'reason': issue,
            'suggestion': f"Consider addressing: {issue}",
            'priority': priority
        }
    
    def _determine_suggestion_type(self, suggestion: Dict) -> str:
        """Determine the type of diff based on suggestion content"""
        suggestion_type = suggestion.get('suggestion_type', '')
        issue = suggestion.get('issue', suggestion.get('reason', '')).lower()
        
        if suggestion_type == 'improvement':
            if any(word in issue for word in ['add', 'insert', 'include']):
                return 'insertion'
            elif any(word in issue for word in ['remove', 'delete', 'eliminate']):
                return 'deletion'
            elif any(word in issue for word in ['change', 'modify', 'replace', 'update']):
                return 'modification'
            elif any(word in issue for word in ['split', 'break', 'divide']):
                return 'split'
            else:
                return 'modification'
        
        return 'general'
    
    def _calculate_confidence(self, tag: str, original_lines: List[str], 
                            modified_lines: List[str]) -> float:
        """Calculate confidence score for a diff operation"""
        base_confidence = {
            'insert': 0.9,
            'delete': 0.8,
            'replace': 0.7
        }.get(tag, 0.5)
        
        # Adjust based on content similarity for replace operations
        if tag == 'replace' and original_lines and modified_lines:
            original_text = ' '.join(original_lines)
            modified_text = ' '.join(modified_lines)
            similarity = difflib.SequenceMatcher(None, original_text, modified_text).ratio()
            
            # Higher similarity in replace operations suggests more confident changes
            confidence_adjustment = similarity * 0.3
            base_confidence = min(1.0, base_confidence + confidence_adjustment)
        
        return base_confidence
    
    def _calculate_suggestion_confidence(self, suggestion: Dict, original: str) -> float:
        """Calculate confidence score for a suggestion-based diff"""
        priority = suggestion.get('priority', 'medium')
        category = suggestion.get('category', 'general')
        issue = suggestion.get('issue', suggestion.get('reason', ''))
        
        # Base confidence by priority
        priority_confidence = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5
        }.get(priority, 0.5)
        
        # Adjust by category
        category_confidence = {
            'grammar': 0.8,
            'style': 0.7,
            'structure': 0.8,
            'content': 0.9,
            'technical': 0.6
        }.get(category, 0.6)
        
        # Adjust by specificity of issue
        specificity_bonus = 0.1 if len(issue.split()) > 5 else 0
        
        return min(1.0, (priority_confidence + category_confidence) / 2 + specificity_bonus)
    
    def _map_opcode_to_type(self, opcode: str) -> str:
        """Map difflib opcodes to diff types"""
        mapping = {
            'insert': 'insertion',
            'delete': 'deletion', 
            'replace': 'modification'
        }
        return mapping.get(opcode, 'general')
    
    def _sort_and_limit_diffs(self, diffs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort diffs by confidence and line number, limit to max_diffs"""
        # Sort by confidence (descending) then by line number (ascending)
        sorted_diffs = sorted(diffs, key=lambda d: (-d.get('confidence', 0), d.get('line', 0)))
        
        # Limit results
        return sorted_diffs[:self.max_diffs]
    
    def _create_empty_diff_result(self, reason: str) -> List[Dict[str, Any]]:
        """Create an empty diff result with explanation"""
        return [{
            'type': 'info',
            'line': 1,
            'reason': reason,
            'confidence': 1.0,
            'timestamp': datetime.utcnow().isoformat()
        }]
    
    def _create_error_diff_result(self, error_msg: str) -> List[Dict[str, Any]]:
        """Create an error diff result"""
        return [{
            'type': 'error',
            'line': 1,
            'reason': f"Error generating diff: {error_msg}",
            'confidence': 0.0,
            'timestamp': datetime.utcnow().isoformat()
        }]
    
    def _create_informational_diff(self, original: str, context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create informational diff when no changes or suggestions provided"""
        word_count = len(original.split())
        line_count = len(original.splitlines())
        
        return [{
            'type': 'info',
            'line': 1,
            'reason': f"Document analyzed: {word_count} words, {line_count} lines",
            'confidence': 1.0,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': {
                'word_count': word_count,
                'line_count': line_count,
                'char_count': len(original)
            }
        }]
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update diff generation configuration"""
        try:
            self.config.update(new_config)
            
            # Update derived settings
            self.min_confidence = self.config.get('min_confidence', 0.3)
            self.max_diffs = self.config.get('max_diffs', 50)
            self.context_lines = self.config.get('context_lines', 2)
            self.word_diff_threshold = self.config.get('word_diff_threshold', 0.6)
            
            logger.info(f"Updated DiffGenerator config: {new_config}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating config: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            'min_confidence': self.min_confidence,
            'max_diffs': self.max_diffs,
            'context_lines': self.context_lines,
            'word_diff_threshold': self.word_diff_threshold,
            **self.config
        } 