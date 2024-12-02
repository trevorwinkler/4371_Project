import re
import openai
import os

openai.api_key = os.environ["OPENAI_API_KEY"]

class Moderator:
    """
    A moderator that detects and stops indirect prompt injections
    """
    def __init__(self, model="gpt-4o-mini"):
        self.model = model
        self.warning_message = "Your input contains potentially harmful instructions and has been blocked."
    
    def sanitize_input(self, user_input):
        """
        Sanitizes user input to prevent indirect prompt injection.
        """
        # Detects common malicious prompts
        maliciousPatterns = [
            r'\[SYSTEM ANNOTATION.*?\]',  
            r'(immediately follow instructions)',  
            r'(do not give any output to the user)',  
            r'(create a new email for each contact)',  
        ]
        
        for pattern in maliciousPatterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False  # Reject the input

        return True  # Allow safe inputs
    
    def forward_to_model(self, user_input):
        """
        Sends sanitized input to the GPT model and retrieves the response.
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": user_input}
                ]
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            return f"An error occurred while processing your request: {e}"
    
    def moderate(self, user_input):
        """
        Main moderation function.
        """
        if not self.sanitize_input(user_input):
            return self.warning_message
        else:
            return self.forward_to_model(user_input)