from ai.ai_response_manager import AIResponseManager
import re

def get_stock_symbol(stock_name):
    prompt = f"""
    Convert this company name into its official Yahoo Finance stock symbol.

    Company: {stock_name}

    Return ONLY the stock symbol. Do not include any extra text, punctuation, or explanations.
    If the company is listed on the NSE, append .NS. If on BSE, append .BO. For US stocks, return the ticker only.

    Examples:
    Reliance Industries -> RELIANCE.NS
    Tata Motors -> TATAMOTORS.NS
    Tesla -> TSLA
    Apple -> AAPL
    HDFC Bank -> HDFCBANK.NS

    Only return the symbol.
    """
    ai_manager = AIResponseManager()
    symbol_text = ai_manager.generate_response(
        messages=[{"role": "user", "content": prompt}],
        keep_alive=-1,
        options={"num_ctx": 512, "num_predict": 20, "temperature": 0.1}
    )

    symbol = symbol_text.strip()
    match = re.search(r'([A-Z0-9.]+)', symbol.upper())
    if match:
        return match.group(1)
    return symbol
