import asyncio
from edgar_mcp.client import SECClient

async def main():
    client = SECClient("arnavhpd@gmail.com")
    
    # We want to check:
    # 1. Apple (320193) FY24 Net sales (Revenues)
    # 2. Microsoft (789019) FY24 Net income (NetIncomeLoss)
    # 3. Amazon (1018724) FY24 Total assets (Assets)
    # 4. NVIDIA (1045810) FY24 R&D (ResearchAndDevelopmentExpense)
    # 5. Tesla (1318605) FY24 Cash (CashAndCashEquivalentsAtCarryingValue)
    # 6. Apple FY24 Operating income (OperatingIncomeLoss)
    # 7. Microsoft FY24 Total liabilities (Liabilities)
    # 8. Amazon FY22 Total revenue (Revenues)

    queries = [
        ("Apple", "320193", "us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax", "FY", "2024"), # Apple usually uses this
        ("Microsoft", "789019", "us-gaap", "NetIncomeLoss", "FY", "2024"),
        ("Amazon", "1018724", "us-gaap", "Assets", "FY", "2024"),
        ("NVIDIA", "1045810", "us-gaap", "ResearchAndDevelopmentExpense", "FY", "2024"),
        ("Tesla", "1318605", "us-gaap", "CashAndCashEquivalentsAtCarryingValue", "FY", "2024"),
        ("Apple", "320193", "us-gaap", "OperatingIncomeLoss", "FY", "2024"),
        ("Microsoft", "789019", "us-gaap", "Liabilities", "FY", "2024"),
        ("Amazon", "1018724", "us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax", "FY", "2022")
    ]
    
    for name, cik, taxonomy, concept, period, year in queries:
        try:
            res = await client.company_concept(cik.zfill(10), taxonomy, concept)
            for unit, frames in res.get("units", {}).items():
                for frame in frames:
                    if frame.get("fy") == int(year) and frame.get("fp") == period:
                        print(f"{name} {concept} {year}: {frame.get('val')} (accn: {frame.get('accn')})")
        except Exception as e:
            print(f"Error fetching {name} {concept}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
