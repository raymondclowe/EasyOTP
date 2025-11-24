"""QR code scanning module."""
from typing import Optional

try:
    from PIL import Image
    from pyzbar.pyzbar import decode
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    print("Warning: pyzbar not available. QR code scanning will be disabled.")

import io


class QRScanner:
    """Scans QR codes for OTP secrets."""
    
    @staticmethod
    def scan_from_file(filepath: str) -> Optional[str]:
        """Scan a QR code from an image file."""
        if not PYZBAR_AVAILABLE:
            print("QR scanning not available: pyzbar library not installed properly")
            return None
        
        try:
            image = Image.open(filepath)
            decoded_objects = decode(image)
            
            for obj in decoded_objects:
                data = obj.data.decode('utf-8')
                if data.startswith('otpauth://'):
                    return data
            
            return None
        except Exception as e:
            print(f"Error scanning QR code: {e}")
            return None
    
    @staticmethod
    def scan_from_bytes(image_bytes: bytes) -> Optional[str]:
        """Scan a QR code from image bytes."""
        if not PYZBAR_AVAILABLE:
            print("QR scanning not available: pyzbar library not installed properly")
            return None
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            decoded_objects = decode(image)
            
            for obj in decoded_objects:
                data = obj.data.decode('utf-8')
                if data.startswith('otpauth://'):
                    return data
            
            return None
        except Exception as e:
            print(f"Error scanning QR code: {e}")
            return None
