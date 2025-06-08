import re

def escape_markdown(text: str) -> str:
    """Escapa caracteres especiales para MarkdownV2"""
    if text is None:
        return ""
    escape_chars = r'_*[]()~`>#+\-={}.!|:'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

def luhn_checksum(card_number: str) -> int:
    """Calcula el dígito de verificación usando el algoritmo de Luhn"""
    digits = [int(d) for d in card_number if d.isdigit()]
    if not digits:
        return 0
        
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for digit in even_digits:
        total += sum(divmod(digit * 2, 10))
    return (10 - (total % 10)) % 10

def extract_card_data(input_text: str) -> dict:
    """
    Extrae datos de tarjeta de diferentes formatos de entrada.
    Formatos aceptados ahora:
    - 123456789012/01/2025/321 (año de 4 dígitos)
    - 123456789012/01/25/321    (año de 2 dígitos)
    - 123456789012 01/2025 321
    - 123456789012 01/25 321
    - 123456789012|01|2025|321  (nuevo formato con pipe)
    - 123456789012|01|25|321    (nuevo formato con pipe)
    """
    normalized = re.sub(r'\s+', ' ', input_text.strip()).upper()
    
    patterns = [
        # Formato con pipe: número|MM|AAAA|CVV
        (r'^([\dX]{6,19})\|(\d{1,2})\|(\d{4})\|(\d{3,4})$', 'pipe_full'),
        # Formato con pipe: número|MM|AA|CVV
        (r'^([\dX]{6,19})\|(\d{1,2})\|(\d{2})\|(\d{3,4})$', 'pipe_short'),
        # Formato con barras: número/MM/AAAA/CVV
        (r'^([\dX]{6,19})/(\d{1,2})/(\d{4})/(\d{3,4})$', 'barra_4digitos_cvv'),
        # Formato con barras: número/MM/AA/CVV
        (r'^([\dX]{6,19})/(\d{1,2})/(\d{2,4})/(\d{3,4})$', 'barra_cvv'),
        # Formato con barras: número/MM/AAAA
        (r'^([\dX]{6,19})/(\d{1,2})/(\d{4})$', 'barra_4digitos'),
        # Formato con barras: número/MM/AA
        (r'^([\dX]{6,19})/(\d{1,2})/(\d{2,4})$', 'barra_sin_cvv'),
        # Formato con espacios: número MM/AAAA CVV
        (r'^([\dX]{6,19})\s+(\d{1,2}/\d{4})\s+(\d{3,4})$', 'espacio_4digitos'),
        # Formato con espacios: número MM/AA CVV
        (r'^([\dX]{6,19})\s+(\d{1,2}/\d{2,4})\s+(\d{3,4})$', 'espacio_cvv'),
        # Formato con espacios: número MM AA CVV
        (r'^([\dX]{6,19})\s+(\d{1,2})\s+(\d{2,4})\s+(\d{3,4})$', 'espacio_separado'),
        # Solo número
        (r'^([\dX]{6,19})$', 'solo_numero'),
    ]
    
    for pattern, pattern_type in patterns:
        match = re.match(pattern, normalized)
        if match:
            groups = match.groups()
            card_number = groups[0].replace('X', 'x')
            
            if pattern_type in ['barra_4digitos_cvv', 'barra_cvv', 'pipe_full', 'pipe_short']:
                month = groups[1]
                year = groups[2]
                cvv = groups[3]
                
                if len(year) == 4:
                    year = year[2:]
                
                return {
                    "cardNumber": card_number,
                    "monthYear": f"{month.zfill(2)}/{year}",
                    "cvv": cvv
                }
                
            elif pattern_type == 'barra_4digitos':
                month = groups[1]
                year = groups[2]
                return {
                    "cardNumber": card_number,
                    "monthYear": f"{month.zfill(2)}/{year[2:]}",
                    "cvv": "XXX"
                }
                
            elif pattern_type == 'barra_sin_cvv':
                month = groups[1]
                year = groups[2]
                if len(year) == 4:
                    year = year[2:]
                return {
                    "cardNumber": card_number,
                    "monthYear": f"{month.zfill(2)}/{year}",
                    "cvv": "XXX"
                }
                
            elif pattern_type == 'espacio_4digitos':
                date_part = groups[1]
                cvv = groups[2]
                month, year = date_part.split('/')
                return {
                    "cardNumber": card_number,
                    "monthYear": f"{month.zfill(2)}/{year[2:]}",
                    "cvv": cvv
                }
                
            elif pattern_type == 'espacio_cvv':
                date_part = groups[1]
                cvv = groups[2]
                month, year = date_part.split('/')
                if len(year) == 4:
                    year = year[2:]
                return {
                    "cardNumber": card_number,
                    "monthYear": f"{month.zfill(2)}/{year}",
                    "cvv": cvv
                }
                
            elif pattern_type == 'espacio_separado':
                month = groups[1]
                year = groups[2]
                cvv = groups[3]
                if len(year) == 4:
                    year = year[2:]
                return {
                    "cardNumber": card_number,
                    "monthYear": f"{month.zfill(2)}/{year}",
                    "cvv": cvv
                }
                
            elif pattern_type == 'solo_numero':
                return {
                    "cardNumber": card_number,
                    "monthYear": "XX/XX",
                    "cvv": "XXX"
                }
    
    return {
        "cardNumber": "xxxxxxxxxxxxxxxx",
        "monthYear": "XX/XX",
        "cvv": "XXX"
    }