"""OTP generation module."""
import pyotp
from typing import Optional
import re


class OTPGenerator:
    """Generates TOTP codes."""
    
    @staticmethod
    def generate_code(secret: str) -> str:
        """Generate a TOTP code from a secret."""
        try:
            totp = pyotp.TOTP(secret)
            return totp.now()
        except Exception:
            return "ERROR"
    
    @staticmethod
    def get_remaining_seconds() -> int:
        """Get remaining seconds until the next code."""
        import time
        return 30 - (int(time.time()) % 30)
    
    @staticmethod
    def normalize_secret(secret: str) -> str:
        """Normalize a secret by removing spaces and converting to uppercase."""
        secret = secret.replace(" ", "").replace("-", "").upper()
        return secret
    
    @staticmethod
    def parse_otpauth_uri(uri: str) -> Optional[dict]:
        """Parse an otpauth:// URI and extract information."""
        # Example: otpauth://totp/Example:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Example
        if not uri.startswith("otpauth://totp/"):
            return None
        
        try:
            # Split URI
            parts = uri.split("?")
            path_part = parts[0].replace("otpauth://totp/", "")
            
            # Parse label (issuer:account or just account)
            label = path_part
            if ":" in label:
                issuer, account = label.split(":", 1)
            else:
                issuer = ""
                account = label
            
            # Parse query parameters
            if len(parts) > 1:
                query_params = {}
                for param in parts[1].split("&"):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        query_params[key] = value
                
                secret = query_params.get("secret", "")
                if "issuer" in query_params:
                    issuer = query_params["issuer"]
                
                return {
                    "name": account,
                    "secret": secret,
                    "issuer": issuer
                }
        except Exception:
            pass
        
        return None
