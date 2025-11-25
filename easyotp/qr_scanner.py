"""QR code scanning module."""
from typing import Optional

PYZBAR_AVAILABLE = None  # Will be set on first use

import io


class QRScanner:
    """Scans QR codes for OTP secrets."""
    
    @staticmethod
    def scan_from_file(filepath: str) -> Optional[str]:
        """Scan a QR code from an image file."""
        global PYZBAR_AVAILABLE
        if PYZBAR_AVAILABLE is False:
            print("QR scanning not available: pyzbar library not installed properly or DLL missing")
            return None
        try:
            from PIL import Image
            from pyzbar.pyzbar import decode
            PYZBAR_AVAILABLE = True
        except (ImportError, OSError) as e:
            PYZBAR_AVAILABLE = False
            print(f"Warning: pyzbar or dependency not available ({e}). QR code scanning will be disabled.")
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
        global PYZBAR_AVAILABLE
        if PYZBAR_AVAILABLE is False:
            print("QR scanning not available: pyzbar library not installed properly or DLL missing")
            return None
        try:
            from PIL import Image
            from pyzbar.pyzbar import decode
            PYZBAR_AVAILABLE = True
        except (ImportError, OSError) as e:
            PYZBAR_AVAILABLE = False
            print(f"Warning: pyzbar or dependency not available ({e}). QR code scanning will be disabled.")
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
