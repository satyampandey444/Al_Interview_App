"""
Response Formatter for Voice Gemini Assistant
Formats Gemini AI responses into bullet points and improves overall formatting
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

class ResponseFormatter:
    """
    Formats Gemini AI responses to improve readability and structure.
    """
    
    def __init__(self):
        """Initialize the response formatter."""
        self.logger = logging.getLogger(__name__)
        
        # Common patterns for detecting lists and structured content
        self.list_patterns = [
            r'^\s*[-*•]\s+',  # Bullet points
            r'^\s*\d+\.\s+',  # Numbered lists
            r'^\s*[a-zA-Z]\.\s+',  # Lettered lists
            r'^\s*\([a-zA-Z0-9]\)\s+',  # Lettered lists in parentheses
        ]
        
        # Patterns for detecting headers and sections
        self.header_patterns = [
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS headers
            r'^[A-Z][a-zA-Z\s]+:$',  # Title case with colon
            r'^#{1,6}\s+',  # Markdown headers
        ]
        
        # Patterns for detecting code blocks
        self.code_patterns = [
            r'```[\s\S]*?```',  # Markdown code blocks
            r'`[^`]+`',  # Inline code
        ]
    
    def format_response(self, response: str, format_type: str = "auto") -> str:
        """
        Format a Gemini response based on the specified format type.
        
        Args:
            response: Raw response from Gemini
            format_type: Type of formatting to apply ("auto", "bullet", "structured", "raw")
            
        Returns:
            Formatted response string
        """
        if not response or not response.strip():
            return response
        
        # Clean up the response first
        cleaned_response = self._clean_response(response)
        
        if format_type == "auto":
            return self._auto_format(cleaned_response)
        elif format_type == "bullet":
            return self._format_as_bullets(cleaned_response)
        elif format_type == "structured":
            return self._format_as_structured(cleaned_response)
        elif format_type == "raw":
            return cleaned_response
        else:
            self.logger.warning(f"Unknown format type: {format_type}, using auto")
            return self._auto_format(cleaned_response)
    
    def _clean_response(self, response: str) -> str:
        """Clean up the response text."""
        # Remove extra whitespace
        response = re.sub(r'\n\s*\n\s*\n+', '\n\n', response)
        response = re.sub(r' +', ' ', response)
        
        # Fix common formatting issues
        response = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', response)
        
        # Remove leading/trailing whitespace
        response = response.strip()
        
        return response
    
    def _auto_format(self, response: str) -> str:
        """Automatically determine the best formatting for the response."""
        lines = response.split('\n')
        
        # Check if response already has structured formatting
        if self._has_structured_format(lines):
            return self._format_as_structured(response)
        
        # Check if response would benefit from bullet points
        if self._should_use_bullets(lines):
            return self._format_as_bullets(response)
        
        # Default to structured formatting for better readability
        return self._format_as_structured(response)
    
    def _has_structured_format(self, lines: List[str]) -> bool:
        """Check if the response already has structured formatting."""
        structured_indicators = 0
        total_lines = len(lines)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for existing bullet points
            if any(re.match(pattern, line) for pattern in self.list_patterns):
                structured_indicators += 1
            
            # Check for headers
            if any(re.match(pattern, line) for pattern in self.header_patterns):
                structured_indicators += 1
            
            # Check for numbered content
            if re.match(r'^\s*\d+\.\s+', line):
                structured_indicators += 1
        
        # If more than 30% of lines have structure, consider it already formatted
        return (structured_indicators / total_lines) > 0.3 if total_lines > 0 else False
    
    def _should_use_bullets(self, lines: List[str]) -> bool:
        """Determine if the response should be formatted as bullet points."""
        # Check for list-like content
        list_indicators = 0
        total_lines = len(lines)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for sentences that could be bullet points
            if (len(line.split()) <= 15 and  # Short sentences
                line.endswith(('.', '!', '?')) and  # Complete sentences
                not line.startswith(('The', 'This', 'That', 'It', 'There', 'Here'))):  # Not starting with common words
                list_indicators += 1
        
        # If more than 50% of lines could be bullets, use bullet formatting
        return (list_indicators / total_lines) > 0.5 if total_lines > 0 else False
    
    def _format_as_bullets(self, response: str) -> str:
        """Format the response as bullet points."""
        lines = response.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that are already formatted
            if any(re.match(pattern, line) for pattern in self.list_patterns):
                formatted_lines.append(line)
                continue
            
            # Skip headers
            if any(re.match(pattern, line) for pattern in self.header_patterns):
                formatted_lines.append(f"\n{line}")
                continue
            
            # Convert to bullet point
            # Remove common sentence starters that don't work well as bullets
            cleaned_line = re.sub(r'^(So,?\s+|Now,?\s+|Well,?\s+|Also,?\s+|Additionally,?\s+|Furthermore,?\s+|Moreover,?\s+)', '', line)
            
            # Add bullet point
            formatted_lines.append(f"• {cleaned_line}")
        
        return '\n'.join(formatted_lines)
    
    def _format_as_structured(self, response: str) -> str:
        """Format the response with improved structure and readability."""
        lines = response.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Preserve existing formatting
            if any(re.match(pattern, line) for pattern in self.list_patterns):
                formatted_lines.append(line)
                continue
            
            # Format headers
            if any(re.match(pattern, line) for pattern in self.header_patterns):
                formatted_lines.append(f"\n{line}")
                continue
            
            # Add spacing for better readability
            if i > 0 and lines[i-1].strip():
                # Check if this line starts a new thought
                if (line[0].isupper() and 
                    not line.startswith(('The', 'This', 'That', 'It', 'There', 'Here', 'And', 'But', 'Or', 'So'))):
                    formatted_lines.append("")  # Add blank line for separation
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def format_for_voice(self, response: str) -> str:
        """
        Format response specifically for voice output (TTS).
        Removes markdown and simplifies formatting.
        """
        if not response:
            return response
        
        # Remove markdown formatting
        formatted = re.sub(r'```[\s\S]*?```', '', response)  # Remove code blocks
        formatted = re.sub(r'`([^`]+)`', r'\1', formatted)  # Remove inline code
        formatted = re.sub(r'\*\*([^*]+)\*\*', r'\1', formatted)  # Remove bold
        formatted = re.sub(r'\*([^*]+)\*', r'\1', formatted)  # Remove italic
        
        # Convert bullet points to voice-friendly format
        formatted = re.sub(r'^\s*[-*•]\s+', '• ', formatted, flags=re.MULTILINE)
        
        # Add pauses for better speech flow
        formatted = re.sub(r'([.!?])\s*([A-Z])', r'\1. \2', formatted)
        
        return formatted.strip()
    
    def format_for_display(self, response: str) -> str:
        """
        Format response for web display with HTML formatting.
        """
        if not response:
            return response
        
        # Convert markdown to HTML
        formatted = response
        
        # Convert bullet points to HTML
        formatted = re.sub(r'^\s*[-*•]\s+', '<li>', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^\s*(\d+)\.\s+', r'<li>', formatted, flags=re.MULTILINE)
        
        # Wrap consecutive list items in <ul> tags
        lines = formatted.split('\n')
        formatted_lines = []
        in_list = False
        
        for line in lines:
            if line.strip().startswith('<li>'):
                if not in_list:
                    formatted_lines.append('<ul>')
                    in_list = True
                formatted_lines.append(line)
            else:
                if in_list:
                    formatted_lines.append('</ul>')
                    in_list = False
                formatted_lines.append(line)
        
        if in_list:
            formatted_lines.append('</ul>')
        
        formatted = '\n'.join(formatted_lines)
        
        # Convert headers to HTML
        formatted = re.sub(r'^#{1,6}\s+(.+)$', r'<h3>\1</h3>', formatted, flags=re.MULTILINE)
        
        # Convert bold and italic
        formatted = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', formatted)
        formatted = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', formatted)
        
        # Convert line breaks to HTML
        formatted = formatted.replace('\n\n', '</p><p>')
        formatted = f'<p>{formatted}</p>'
        
        return formatted
    
    def get_formatting_options(self) -> Dict[str, str]:
        """Get available formatting options."""
        return {
            "auto": "Automatically determine best formatting",
            "bullet": "Format as bullet points",
            "structured": "Format with improved structure",
            "raw": "No formatting (original response)"
        }
