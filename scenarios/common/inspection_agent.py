"""
*******************************************************
Name:   InspectionAgent
Date:   December 1, 2024
Author: Jose Reyes San Miguel 
Description:
    This module provides an InspectionAgent class designed
    to sanitize and spotlight potentially harmful content
    from inputs processed by a ChatML-based application. 
    It detects malicious instructions, removes harmful 
    payloads, and ensures transparency by flagging sanitized 
    content with a note.

    The agent also integrates Base64 encoding/decoding 
    functionality to support spotlighting techniques, 
    ensuring consistent handling of encoded inputs.

Key Features:
    - Content Sanitization: Removes harmful elements while 
      retaining benign content.
    - Spotlighting: Highlights sanitized portions with 
      explanatory notes.
    - Base64 Encoding/Decoding: Automatically decodes 
      inputs for inspection and re-encodes them after 
      sanitization.
    - Logging: Tracks all sanitized content for auditing 
      purposes.
    
Usage:
    Instantiate the InspectionAgent and call its inspect() 
    method on incoming content before passing it to the 
    ChatML-based application.

*******************************************************
"""
import re
import base64
import logging

#Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InspectionAgent")

class InspectionAgent:
    def __init__(self):
        """
        Initialize the InspectionAgent with encoding as the spotlighting technique.
        """
        self.keywords = [
            "ignore",
            "override",
            "reset instructions",
            "fetch",
            "bypass",
            "https://",  # Watch for URL-based commands
            "STRICTLY FOLLOW THE INSTRUCTIONS",
            "[SYSTEM ANNOTATION:",
            "Create a new email",
            "Send the details of new email",
        ]
        self.html_tags = re.compile(r"<[^>]+>")  # Matches HTML tags
        self.markdown_comments = re.compile(r"<!--.*?-->", re.DOTALL)  # Matches hidden comments
        self.system_instructions = re.compile(r"<\|im_start\|>.*?<\|im_end\|>", re.DOTALL)  # Matches system-level tags

    def sanitize(self, input_text, source="unknown"):
        """
        Sanitize input text by removing harmful instructions, HTML tags, Markdown comments,
        system-level instructions, and any specific patterns such as between <|im_start|> and <|im_end|>.
        :param input_text: str - The text to sanitize.
        :param source: str - The source of the input (e.g., "email", "view").
        :return: str - Sanitized text.
        """
        sanitized_text = input_text

        if source == "email":
            # Remove SYSTEM ANNOTATIONS
            sanitized_text = re.sub(r'\[SYSTEM ANNOTATION:.*?\]', '', sanitized_text, flags=re.DOTALL)

            # Remove harmful instructions
            sanitized_text = re.sub(r'\d+\..*?MUST.*?\n', '', sanitized_text, flags=re.DOTALL)

            # Remove the malicious payload
            sanitized_text = re.sub(r'Dear Friend,.*?{duplicated message body}.*?\n', '', sanitized_text, flags=re.DOTALL)
        
        if source == "view":
            # Remove content between <|im_start|> and <|im_end|>
            sanitized_text = re.sub(r"<\|im_start\|>.*?<\|im_end\|>", "[NOTE: Potentially harmful content has been removed.]", sanitized_text, flags=re.DOTALL)
        
        # Remove HTML tags
        sanitized_text = self.html_tags.sub("", sanitized_text)
        
        # Remove Markdown comments
        sanitized_text = self.markdown_comments.sub("", sanitized_text)
        
        #Remove system-level instructions
        sanitized_text = self.system_instructions.sub("", sanitized_text)
        
        # Strip any extra whitespace or unwanted artifacts
        sanitized_text = sanitized_text.strip()
        
        # Add a note if sanitization altered the content
        if sanitized_text != input_text:
            sanitized_text += "\n\n[NOTE: Potentially harmful content has been removed.]"

        return sanitized_text

    def inspect(self, input_text, source="unknown"):
        """
        Inspect the input text for harmful content. If flagged, sanitize it.
        :param input_text: str - The input text to inspect.
        :param source: str - The source of the input (e.g., "view", "fetch", "email").
        :return: str - Base64-encoded sanitized text or the original text if no sanitization is needed.
        """
        # Decode if input is Base64-encoded
        try:
            decoded_text = base64.b64decode(input_text).decode("utf-8")
            logger.info(f"Input detected as Base64-encoded from {source}. Decoding for inspection.")
        except (base64.binascii.Error, UnicodeDecodeError):
            decoded_text = input_text

        # Flag for sanitization
        flagged = False

        # Check for risky keywords
        for keyword in self.keywords:
            if keyword.lower() in decoded_text.lower():
                flagged = True
                #logger.warning(f"Risky keyword detected ({source}): {keyword}")

        # Check for HTML tags, Markdown comments, and system-level instructions
        if self.html_tags.search(decoded_text):
            flagged = True
            #logger.warning(f"HTML tags detected in {source}.")
        if self.markdown_comments.search(decoded_text):
            flagged = True
            #logger.warning(f"Markdown comments detected in {source}.")
        if self.system_instructions.search(decoded_text):
            flagged = True
            #logger.warning(f"System-level instructions detected in {source}.")

        # Sanitize if flagged
        if flagged:
            sanitized_text = self.sanitize(decoded_text)
            sanitized_text += " [NOTE: Potentially harmful content removed.]"
            encoded_input = base64.b64encode(sanitized_text.encode()).decode()
            #logger.info(f"Sanitized and encoded input from {source}: {encoded_input}")
            return encoded_input

        # If no issue is detected, return the original input (re-encoded if necessary)
        #logger.info(f"No harmful content detected in {source}. Returning original input.")
        return base64.b64encode(decoded_text.encode()).decode()
