"""
Gemini AI Client for Voice Assistant
Handles communication with Google's Gemini AI model
"""

import os
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
from response_formatter import ResponseFormatter

# Load environment variables
load_dotenv()

class GeminiClient:
    """
    Client for interacting with Google's Gemini AI model.
    """
    
    def __init__(self, api_key: Optional[str] = None, format_responses: bool = True, format_type: str = "auto", use_rules: bool = True):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Google Gemini API key. If not provided, will try to load from environment.
            format_responses: Whether to format responses using the ResponseFormatter
            format_type: Type of formatting to apply ("auto", "bullet", "structured", "raw")
            use_rules: Whether to append rules from rule.txt to every request
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize the model - using gemini-2.5-flash for best performance and free tier compatibility
        # Available models: gemini-2.5-flash (stable), gemini-2.5-pro, gemini-flash-latest
        # gemini-2.5-flash is the latest stable Flash model with excellent rate limits
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Initialize chat session
        self.chat_session = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Conversation history
        self.conversation_history = []
        
        # Response formatting
        self.format_responses = format_responses
        self.format_type = format_type
        self.response_formatter = ResponseFormatter() if format_responses else None
        
        # Load rules
        self.use_rules = use_rules
        self.response_rules = self._load_response_rules() if use_rules else ""
        
        self.logger.info("Gemini client initialized successfully")
    
    def _load_response_rules(self) -> str:
        """
        Load response rules from rule.txt file.
        
        Returns:
            Rules content as string, or empty string if file not found
        """
        try:
            rules_file = "rule.txt"
            if os.path.exists(rules_file):
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_content = f.read().strip()
                self.logger.info(f"Loaded response rules from {rules_file}")
                return rules_content
            else:
                self.logger.warning(f"Rules file {rules_file} not found")
                return ""
        except Exception as e:
            self.logger.error(f"Error loading response rules: {e}")
            return ""
    
    def start_chat(self) -> None:
        """Start a new chat session."""
        self.chat_session = self.model.start_chat(history=[])
        self.conversation_history = []
        self.logger.info("New chat session started")
    
    def send_message(self, message: str, context: Optional[str] = None, format_type: Optional[str] = None) -> str:
        """
        Send a message to Gemini and get a response.
        
        Args:
            message: The user's message
            context: Optional context to include with the message
            format_type: Override the default format type for this response
            
        Returns:
            Gemini's response text (formatted if enabled)
        """
        try:
            # Prepare the full message with context and rules
            full_message = message
            
            # Add context if provided
            if context:
                full_message = f"Context: {context}\n\nUser: {message}"
            
            # Add response rules if enabled
            if self.use_rules and self.response_rules:
                rules_prefix = f"Response Rules:\n{self.response_rules}\n\n"
                full_message = f"{rules_prefix}User Question: {message}"
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": message})
            
            # Send to Gemini
            if self.chat_session:
                response = self.chat_session.send_message(full_message)
            else:
                response = self.model.generate_content(full_message)
            
            # Extract response text
            if response.text:
                response_text = response.text.strip()
                
                # Format the response if enabled
                if self.format_responses and self.response_formatter:
                    format_to_use = format_type or self.format_type
                    formatted_response = self.response_formatter.format_response(response_text, format_to_use)
                    self.logger.info(f"Formatted response using '{format_to_use}' format")
                else:
                    formatted_response = response_text
                
                # Add to conversation history (store original response)
                self.conversation_history.append({"role": "assistant", "content": response_text})
                
                self.logger.info(f"Received response from Gemini: {len(response_text)} characters")
                return formatted_response
            else:
                error_msg = "No response generated from Gemini"
                self.logger.error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error communicating with Gemini: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def get_conversation_summary(self) -> str:
        """
        Get a summary of the current conversation.
        
        Returns:
            Summary of the conversation
        """
        if not self.conversation_history:
            return "No conversation history available."
        
        summary_parts = []
        for i, entry in enumerate(self.conversation_history, 1):
            role = entry["role"]
            content = entry["content"][:100] + "..." if len(entry["content"]) > 100 else entry["content"]
            summary_parts.append(f"{i}. {role.title()}: {content}")
        
        return "\n".join(summary_parts)
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        if self.chat_session:
            self.chat_session = self.model.start_chat(history=[])
        self.logger.info("Conversation history cleared")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": "gemini-2.5-flash",
            "conversation_length": len(self.conversation_history),
            "chat_session_active": self.chat_session is not None,
            "format_responses": self.format_responses,
            "format_type": self.format_type
        }
    
    def is_healthy(self) -> bool:
        """
        Check if the Gemini client is healthy and can communicate.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a simple test message
            test_response = self.model.generate_content("Hello")
            return test_response.text is not None
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def get_formatting_options(self) -> Dict[str, str]:
        """
        Get available formatting options.
        
        Returns:
            Dictionary of formatting options
        """
        if self.response_formatter:
            return self.response_formatter.get_formatting_options()
        return {}
    
    def set_format_type(self, format_type: str) -> bool:
        """
        Set the default format type for responses.
        
        Args:
            format_type: The format type to use
            
        Returns:
            True if format type is valid, False otherwise
        """
        if self.response_formatter:
            options = self.response_formatter.get_formatting_options()
            if format_type in options:
                self.format_type = format_type
                self.logger.info(f"Format type set to: {format_type}")
                return True
            else:
                self.logger.warning(f"Invalid format type: {format_type}")
                return False
        return False
