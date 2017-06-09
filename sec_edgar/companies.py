"""Data for some big companies."""
from collections import namedtuple

Company = namedtuple("Company", ["name", "code", "cik"])

COMPANIES = {
    "Apple": Company(name="Apple", code="AAPL", cik="0000320193"),
    "Accenture Plc": Company(
        name="Accenture Plc", code="ACN", cik="00001467373"),
    "Adobe": Company(name="Adobe", code="ADBE", cik="0000796343"),
    "AMD": Company(name="AMD", code="AMD", cik="0000002488"),
    "Akamai Technologies": Company(
        name="Akamai Technologies", code="AKAM", cik="0001086222"),
    "Altera": Company(name="Altera", code="ALTR", cik="0000768251"),
    "Analog Devices": Company(
        name="Analog Devices", code="ADI", cik="0000006281"),
    "Autodesk": Company(name="Autodesk", code="ADSK", cik="0000769397"),
    "Automatic Data Processing": Company(
        name="Automatic Data Processing", code="ADP", cik="0000008670"),
    "Broadcom": Company(name="Broadcom", code="BRCM", cik="0001054374"),
    "CA": Company(name="CA", code="CA", cik="0001314355"),
    "Cisco Systems": Company(
        name="Cisco Systems", code="CSCO", cik="0000858877"),
    "Citrix Systems": Company(
        name="Citrix Systems", code="CTXS", cik="0000877890"),
    "Ebay": Company(name="Ebay", code="EBAY", cik="0001065088"),
    "Electronic Arts": Company(
        name="Electronic Arts", code="EA", cik="0000712515"),
    "Emblem Corp": Company(name="Emblem Corp", code="EMC", cik="0000790070"),
    "First Solar": Company(name="First Solar", code="FSLR", cik="0001274494"),
    "Facebook": Company(name="Facebook", code="FCBK", cik="0001326801"),
    "Google": Company(name="Google", code="GOOG", cik="0001288776"),
    "HP": Company(name="HP", code="HPQ", cik="0001370414"),
    "Intel": Company(name="Intel", code="INTC", cik="0000050863"),
    "IBM": Company(name="IBM", code="IBM", cik="0000051143"),
    "Intuit": Company(name="Intuit", code="INTU", cik="0000896878"),
    "Juniper Networks": Company(
        name="Juniper Networks", code="JNPR", cik="0001043604"),
    "microsoft": Company(name="microsoft", code="MSFT", cik="0000789019"),
    "Motorola Solutions Inc": Company(
        name="Motorola Solutions Inc", code="MSI", cik="0000068505"),
    "NetApp": Company(name="NetApp", code="NTAP", cik="0001133469"),
    "NVidia": Company(name="NVidia", code="NVDA", cik="0001045810"),
    "Oracle": Company(name="Oracle", code="ORCL", cik="0000727632"),
    "QUALCOMM": Company(name="QUALCOMM", code="QCOM", cik="0000804328"),
    "SalesForce": Company(name="SalesForce", code="CRM", cik="0001108524"),
    "SanDisk": Company(name="SanDisk", code="SNDK", cik="0001000180"),
    "Seagate Technology PLC": Company(
        name="Seagate Technology PLC", code="STX", cik="0000354952"),
    "Symantec Corporation": Company(
        name="Symantec Corporation", code="SYMC", cik="0000849399"),
    "DC A/S": Company(name="DC A/S", code="TDC", cik="0000816761"),
    "Texas Instruments Incorporated": Company(
        name="Texas Instruments Incorporated", code="TXN", cik="0000097476"),
    "Verisign": Company(name="Verisign", code="VRSN", cik="0001014473"),
    "Waldron Energy Corp": Company(
        name="Waldron Energy Corp", code="WDN", cik="0001168332"),
    "Xerox": Company(name="Xerox", code="XRX", cik="0000108772"),
    "Xilinx": Company(name="Xilinx", code="XLNX", cik="0000743988"),
    "Yahoo": Company(name="Yahoo", code="YHOO", cik="0001011006"),
    "Amazon": Company(name="Amazon", code="AMZN", cik="0001018724"),
    "Linkedin": Company(name="Linkedin", code="LNKD", cik="0001271024"),
    "Verizon": Company(name="Verizon", code="VZ", cik="0000071428"),
    "VMware": Company(name="VMware", code="VMW", cik="0001124610"),
    "Zynga": Company(name="Zynga", code="ZNGA", cik="0001439404"),
}
