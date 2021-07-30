from enum import Enum


class FilingType(Enum):
    """Available filing types to be used when creating Filing object.

    .. versionadded:: 0.1.5

    """
    FILING_1A = '1-A'
    FILING_1A_AMEND = '1-A/A'
    FILING_1APOS = '1-A POS'
    FILING_1AW = '1-A-W'
    FILING_1AW_AMEND = '1-A-W/A'
    FILING_1E = '1-E'
    FILING_1E_AMEND = '1-E/A'
    FILING_1EAD = '1-E AD'
    FILING_1EAD_AMEND = '1-E AD/A'
    FILING_1K = '1-K'
    FILING_1K_AMEND = '1-K/A'
    FILING_1SA = '1-SA'
    FILING_1SA_AMEND = '1-SA/A'
    FILING_1U = '1-U'
    FILING_1U_AMEND = '1-U/A'
    FILING_1Z = '1-Z'
    FILING_1Z_AMEND = '1-Z/A'
    FILING_253G1 = '253G1'
    FILING_253G2 = '253G2'
    FILING_253G3 = '253G3'
    FILING_253G4 = '253G4'
    FILING_2E = '2-E'
    FILING_2E_AMEND = '2-E/A'
    FILING_1012B = '10-12B'
    FILING_1012B_AMEND = '10-12B/A'
    FILING_1012G = '10-12G'
    FILING_1012G_AMEND = '10-12G/A'
    FILING_10D = '10-D'
    FILING_10D_AMEND = '10-D/A'
    FILING_10K = '10-K'
    FILING_10K_AMEND = '10-K/A'
    FILING_10KT = '10-KT'
    FILING_10KT_AMEND = '10-KT/A'
    FILING_10Q = '10-Q'
    FILING_10Q_AMEND = '10-Q/A'
    FILING_10QT = '10-QT'
    FILING_10QT_AMEND = '10-QT/A'
    FILING_11K = '11-K'
    FILING_11K_AMEND = '11-K/A'
    FILING_11KT = '11-KT'
    FILING_11KT_AMEND = '11-KT/A'
    FILING_13FHR = '13F-HR'
    FILING_13FHR_AMEND = '13F-HR/A'
    FILING_13FNT = '13F-NT'
    FILING_13FNT_AMEND = '13F-NT/A'
    FILING_13H = '13H'
    FILING_13HQ = '13H-Q'
    FILING_13HA = '13H-A'
    FILING_13HI = '13H-I'
    FILING_13HR = '13H-R'
    FILING_13HT = '13H-T'
    FILING_144 = '144'
    FILING_144_AMEND = '144/A'
    FILING_1512B = '15-12B'
    FILING_1512B_AMEND = '15-12B/A'
    FILING_1512G = '15-12G'
    FILING_1512G_AMEND = '15-12G/A'
    FILING_1515D = '15-15D'
    FILING_1515D_AMEND = '15-15D/A'
    FILING_15F12B = '15F-12B'
    FILING_15F12B_AMEND = '15F-12B/A'
    FILING_15F12G = '15F-12G'
    FILING_15F12G_AMEND = '15F-12G/A'
    FILING_15F15D = '15F-15D'
    FILING_15F15D_AMEND = '15F-15D/A'
    FILING_17HACON = '17HACON'
    FILING_17HACON_AMEND = '17HACON/A'
    FILING_17HQCON = '17HQCON'
    FILING_17HQCON_AMEND = '17HQCON/A'
    FILING_1812B = '18-12B'
    FILING_1812B_AMEND = '18-12B/A'
    FILING_1812G = '18-12G'
    FILING_1812G_AMEND = '18-12G/A'
    FILING_18K = '18-K'
    FILING_18K_AMEND = '18-K/A'
    FILING_20F = '20-F'
    FILING_20F_AMEND = '20-F/A'
    FILING_20FR12G = '20FR12G'
    FILING_20FR12G_AMEND = '20FR12G/A'
    FILING_24F2NT = '24F-2NT'
    FILING_24F2NT_AMEND = '24F-2NT/A'
    FILING_25 = '25'
    FILING_25_AMEND = '25/A'
    FILING_25NSE = '25-NSE'
    FILING_25NSE_AMEND = '25-NSE/A'
    FILING_3 = '3'
    FILING_3_AMEND = '3/A'
    FILING_305B2 = '305B2'
    FILING_305B2_AMEND = '305B2/A'
    FILING_4 = '4'
    FILING_4_AMEND = '4/A'
    FILING_406B = '40-6B'
    FILING_406B_AMEND = '40-6B/A'
    FILING_4017F1 = '40-17F1'
    FILING_4017F1_AMEND = '40-17F1/A'
    FILING_4017F2 = '40-17F2'
    FILING_4017F2_AMEND = '40-17F2/A'
    FILING_4017G = '40-17G'
    FILING_4017G_AMEND = '40-17G/A'
    FILING_4017GCS = '40-17GCS'
    FILING_4017GCS_AMEND = '4017GCS/A'
    FILING_4024B2 = '40-24B2'
    FILING_4024B2_AMEND = '40-24B2/A'
    FILING_4033 = '40-33'
    FILING_4033_AMEND = '40-33/A'
    FILING_408B25 = '40-8B25'
    FILING_408F2 = '40-8F-2'
    FILING_408F2_AMEND = '40-8F-2/A'
    FILING_40APP = '40-APP'
    FILING_40APP_AMEND = '40-APP/A'
    FILING_40F = '40-F'
    FILING_40F_AMEND = '40-F/A'
    FILING_40FR12B = '40FR12B'
    FILING_40FR12B_AMEND = '40FR12B/A'
    FILING_40FR12G = '40FR12G'
    FILING_40FR12G_AMEND = '40FR12G/A'
    FILING_40OIP = '40-OIP'
    FILING_40OIP_AMEND = '40-OIP/A'
    FILING_424A = '424A'
    FILING_424B1 = '424B1'
    FILING_424B2 = '424B2'
    FILING_424B3 = '424B3'
    FILING_424B4 = '424B4'
    FILING_424B5 = '424B5'
    FILING_424B7 = '424B7'
    FILING_424B8 = '424B8'
    FILING_424H = '424H'
    FILING_424H_AMEND = '424H/A'
    FILING_425 = '425'
    FILING_485APOS = '485APOS'
    FILING_485BPOS = '485BPOS'
    FILING_485BXT = '485BXT'
    FILING_486APOS = '486APOS'
    FILING_486BPOS = '486BPOS'
    FILING_486BXT = '486BXT'
    FILING_487 = '487'
    FILING_497 = '497'
    FILING_497AD = '497AD'
    FILING_497H2 = '497H2'
    FILING_497K = '497K'
    FILING_497VPI = '497VPI'
    FILING_497VPU = '497VPU'
    FILING_5 = '5'
    FILING_5_AMEND = '5/A'
    FILING_6K = '6-K'
    FILING_6K_AMEND = '6-K/A'
    FILING_8A12B = '8-A12B'
    FILING_8A12B_AMEND = '8-A12B/A'
    FILING_8A12G = '8-A12G'
    FILING_8A12G_AMEND = '8-A12G/A'
    FILING_8K = '8-K'
    FILING_8K_AMEND = '8-K/A'
    FILING_8K12B = '8-K12B'
    FILING_8K12B_AMEND = '8-K12B/A'
    FILING_8K15D5 = '8-K15D5'
    FILING_8K15D5_AMEND = '8-K15D5/A'
    FILING_ABS15G = 'ABS-15G'
    FILING_ABS15G_AMEND = 'ABS-15G/A'
    FILING_ABSEE = 'ABS-EE'
    FILING_ABSEE_AMEND = 'ABS-EE/A'
    FILING_ANNLRPT = 'ANNLRPT'
    FILING_ANNLRPT_AMEND = 'ANNLRPT/A'
    FILING_APPWD = 'APP WD'
    FILING_APPWD_AMEND = 'APP WD/A'
    FILING_ARS = 'ARS'
    FILING_ARS_AMEND = 'ARS/A'
    FILING_ATSN = 'ATS-N'
    FILING_ATSNCA = 'ATS-N/CA'
    FILING_ATSNMA = 'ATS-N/MA'
    FILING_ATSNOFA = 'ATS-N/OFA'
    FILING_ATSNUA = 'ATS-N/UA'
    FILING_ATSNC = 'ATS-N-C'
    FILING_ATSNW = 'ATS-N-W'
    FILING_AW = 'AW'
    FILING_AWWD = 'AW WD'
    FILING_BULK = 'BULK'
    FILING_C = 'C'
    FILING_C_AMEND = 'C/A'
    FILING_CW = 'C-W'
    FILING_CU = 'C-U'
    FILING_CUW = 'C-U-W'
    FILING_CAR = 'C-AR'
    FILING_CAR_AMEND = 'C-AR/A'
    FILING_CARW = 'C-AR-W'
    FILING_CARAW = 'C-AR/A-W'
    FILING_CTR = 'C-TR'
    FILING_CTRW = 'C-TR-W'
    FILING_CB = 'CB'
    FILING_CB_AMEND = 'CB/A'
    FILING_CERT = 'CERT'
    FILING_CFPORTALW = 'CFPORTAL-W'
    FILING_CORRESP = 'CORRESP'
    FILING_D = 'D'
    FILING_D_AMEND = 'D/A'
    FILING_DEF14A = 'DEF 14A'
    FILING_DEF14C = 'DEF 14C'
    FILING_DEFA14A = 'DEFA14A'
    FILING_DEFA14C = 'DEFA14C'
    FILING_DEFC14A = 'DEFC14A'
    FILING_DEFC14C = 'DEFC14C'
    FILING_DEFM14C = 'DEFM14C'
    FILING_DEFN14A = 'DEFN14A'
    FILING_DEFR14A = 'DEFR14A'
    FILING_DEFR14C = 'DEFR14C'
    FILING_DELAM = 'DEL AM'
    FILING_DFAN14A = 'DFAN14A'
    FILING_DFRN14A = 'DFRN14A'
    FILING_DOS = 'DOS'
    FILING_DOS_AMEND = 'DOS/A'
    FILING_DOSLTR = 'DOSLTR'
    FILING_DRS = 'DRS'
    FILING_DRS_AMEND = 'DRS/A'
    FILING_DRSLTR = 'DRSLTR'
    FILING_F1 = 'F-1'
    FILING_F1_AMEND = 'F-1/A'
    FILING_F10 = 'F-10'
    FILING_F10_AMEND = 'F-10/A'
    FILING_F10EF = 'F-10EF'
    FILING_F10POS = 'F-10POS'
    FILING_F1MEF = 'F-1MEF'
    FILING_F3 = 'F-3'
    FILING_F3_AMEND = 'F-3/A'
    FILING_F3ASR = 'F-3ASR'
    FILING_F3D = 'F-3D'
    FILING_F3DPOS = 'F-3DPOS'
    FILING_F3MEF = 'F-3MEF'
    FILING_F4POS = 'F-4 POS'
    FILING_F4 = 'F-4'
    FILING_F4_AMEND = 'F-4/A'
    FILING_F4EF = 'F-4EF'
    FILING_F4MEF = 'F-4MEF'
    FILING_F6POS = 'F-6 POS'
    FILING_F6 = 'F-6'
    FILING_F6_AMEND = 'F-6/A'
    FILING_F6EF = 'F-6EF'
    FILING_F7POS = 'F-7 POS'
    FILING_F7 = 'F-7'
    FILING_F7_AMEND = 'F-7/A'
    FILING_F8POS = 'F-8 POS'
    FILING_F8 = 'F-8'
    FILING_F8_AMEND = 'F-8/A'
    FILING_F80 = 'F-80'
    FILING_F80_AMEND = 'F-80/A'
    FILING_F80POS = 'F-80POS'
    FILING_FN = 'F-N'
    FILING_FN_AMEND = 'F-N/A'
    FILING_FWP = 'FWP'
    FILING_FX = 'F-X'
    FILING_FX_AMEND = 'F-X/A'
    FILING_IRANNOTICE = 'IRANNOTICE'
    FILING_MA = 'MA'
    FILING_MAA = 'MA-A'
    FILING_MA_AMEND = 'MA/A'
    FILING_MAI = 'MA-I'
    FILING_MAI_AMEND = 'MA-I/A'
    FILING_MAW = 'MA-W'
    FILING_MODULE = 'MODULE'
    FILING_N14 = 'N-14'
    FILING_N14_AMEND = 'N-14/A'
    FILING_N14MEF = 'N-14MEF'
    FILING_N18F1 = 'N-18F1'
    FILING_N18F1_AMEND = 'N-18F1/A'
    FILING_N1A = 'N-1A'
    FILING_N1A_AMEND = 'N-1A/A'
    FILING_N2 = 'N-2'
    FILING_N2_AMEND = 'N-2/A'
    FILING_N23C2 = 'N-23C-2'
    FILING_N23C2_AMEND = 'N-23C-2/A'
    FILING_N23C3A = 'N-23C3A'
    FILING_N23C3A_AMEND = 'N23C3A/A'
    FILING_N23C3B = 'N-23C3B'
    FILING_N23C3B_AMEND = 'N23C3B/A'
    FILING_N23C3C = 'N-23C3C'
    FILING_N23C3C_AMEND = 'N23C3C/A'
    FILING_N27D1 = 'N-27D-1'
    FILING_N27D1_AMEND = 'N-27D-1/A'
    FILING_N2MEF = 'N-2MEF'
    FILING_N3 = 'N-3'
    FILING_N3_AMEND = 'N-3/A'
    FILING_N30B2 = 'N-30B-2'
    FILING_N30D = 'N-30D'
    FILING_N30D_AMEND = 'N-30D/A'
    FILING_N4 = 'N-4'
    FILING_N4_AMEND = 'N-4/A'
    FILING_N5 = 'N-5'
    FILING_N5_AMEND = 'N-5/A'
    FILING_N54A = 'N-54A'
    FILING_N54A_AMEND = 'N-54A/A'
    FILING_N54C = 'N-54C'
    FILING_N54C_AMEND = 'N-54C/A'
    FILING_N6 = 'N-6'
    FILING_N6_AMEND = 'N-6/A'
    FILING_N6F = 'N-6F'
    FILING_N6F_AMEND = 'N-6F/A'
    FILING_N8A = 'N-8A'
    FILING_N8A_AMEND = 'N-8A/A'
    FILING_N8B2 = 'N-8B-2'
    FILING_N8B2_AMEND = 'N-8B-2/A'
    FILING_N8B3 = 'N-8B-3'
    FILING_N8B3_AMEND = 'N-8B-3/A'
    FILING_N8B4 = 'N-8B-4'
    FILING_N8B4_AMEND = 'N-8B-4/A'
    FILING_N8F = 'N-8F'
    FILING_N8F_AMEND = 'N-8F/A'
    FILING_NCEN = 'N-CEN'
    FILING_NCEN_AMEND = 'N-CEN/A'
    FILING_NCR = 'N-CR'
    FILING_NCR_AMEND = 'N-CR/A'
    FILING_NCSR = 'N-CSR'
    FILING_NCSR_AMEND = 'N-CSR/A'
    FILING_NCSRS = 'N-CSRS'
    FILING_NCSRS_AMEND = 'N-CSRS/A'
    FILING_NLIQUID = 'N-LIQUID'
    FILING_NLIQUID_AMEND = 'N-LIQUID/A'
    FILING_NMFP2 = 'N-MFP2'
    FILING_NMFP2_AMEND = 'N-MFP2/A'
    FILING_NPORTNP = 'NPORT-NP'
    FILING_NPORTNP_AMEND = 'NPORT-NP/A'
    FILING_NPORTP = 'NPORT-P'
    FILING_NPORTP_AMEND = 'NPORT-P/A'
    FILING_NPX = 'N-PX'
    FILING_NPX_AMEND = 'N-PX/A'
    FILING_NPXCR = 'N-PX-CR'
    FILING_NPXCR_AMEND = 'N-PX-CR/A'
    FILING_NPXFM = 'N-PX-FM'
    FILING_NPXFM_AMEND = 'N-PX-FM/A'
    FILING_NPXNT = 'N-PX-NT'
    FILING_NPXNT_AMEND = 'N-PX-NT/A'
    FILING_NPXVR = 'N-PX-VR'
    FILING_NPXVR_AMEND = 'N-PX-VR/A'
    FILING_NQ = 'N-Q'
    FILING_NQ_AMEND = 'N-Q/A'
    FILING_NRSROUPD = 'NRSRO-UPD'
    FILING_NRSROFR = 'NRSRO-FR'
    FILING_NRSROFR_AMEND = 'NRSRO-FR/A'
    FILING_NRSROWCLS = 'NRSRO-WCLS'
    FILING_NRSROWREG = 'NRSRO-WREG'
    FILING_NT10K = 'NT 10-K'
    FILING_NT10K_AMEND = 'NT 10-K/A'
    FILING_NT10D = 'NT 10-D'
    FILING_NT10D_AMEND = 'NT 10-D/A'
    FILING_NT10Q = 'NT 10-Q'
    FILING_NT10Q_AMEND = 'NT 10-Q/A'
    FILING_NT11K = 'NT 11-K'
    FILING_NT11K_AMEND = 'NT 11-K/A'
    FILING_NT15D2 = 'NT 15D2'
    FILING_NT15D2_AMEND = 'NT 15D2/A'
    FILING_NT20F = 'NT 20-F'
    FILING_NT20F_AMEND = 'NT 20-F/A'
    FILING_NTNCEN = 'NT-NCEN'
    FILING_NTNCEN_AMEND = 'NT-NCEN/A'
    FILING_NTNCSR = 'NT-NCSR'
    FILING_NTNCSR_AMEND = 'NTNCSR/A'
    FILING_NVP = 'N-VP'
    FILING_NVP_AMEND = 'N-VP/A'
    FILING_NVPFS = 'N-VPFS'
    FILING_NVPFS_AMEND = 'N-VPFS/A'
    FILING_POS8C = 'POS 8C'
    FILING_POSAM = 'POS AM'
    FILING_POSAMI = 'POS AMI'
    FILING_POSASR = 'POSASR'
    FILING_POSEX = 'POS EX'
    FILING_POS462B = 'POS462B'
    FILING_POS462C = 'POS462C'
    FILING_PRE14A = 'PRE 14A'
    FILING_PRE14C = 'PRE 14C'
    FILING_PREC14A = 'PREC14A'
    FILING_PREC14C = 'PREC14C'
    FILING_PREM14A = 'PREM14A'
    FILING_PREM14C = 'PREM14C'
    FILING_PREN14A = 'PREN14A'
    FILING_PRER14A = 'PRER14A'
    FILING_PRER14C = 'PRER14C'
    FILING_PRRN14A = 'PRRN14A'
    FILING_PX14A6G = 'PX14A6G'
    FILING_PX14A6N = 'PX14A6N'
    FILING_QRTLYRPT = 'QRTLYRPT'
    FILING_QRTLYRPT_AMEND = 'QRTLYRPT/A'
    FILING_RW = 'RW'
    FILING_RWWD = 'RW WD'
    FILING_S1 = 'S-1'
    FILING_S1_AMEND = 'S-1/A'
    FILING_S11 = 'S-11'
    FILING_S11_AMEND = 'S-11/A'
    FILING_S11MEF = 'S-11MEF'
    FILING_S1MEF = 'S-1MEF'
    FILING_S20 = 'S-20'
    FILING_S20_AMEND = 'S-20/A'
    FILING_S3 = 'S-3'
    FILING_S3_AMEND = 'S-3/A'
    FILING_S3ASR = 'S-3ASR'
    FILING_S3D = 'S-3D'
    FILING_S3DPOS = 'S-3DPOS'
    FILING_S3MEF = 'S-3MEF'
    FILING_S4POS = 'S-4 POS'
    FILING_S4 = 'S-4'
    FILING_S4_AMEND = 'S-4/A'
    FILING_S4EF = 'S-4EF'
    FILING_S4MEF = 'S-4MEF'
    FILING_S6 = 'S-6'
    FILING_S6_AMEND = 'S-6/A'
    FILING_S8 = 'S-8'
    FILING_S8POS = 'S-8 POS'
    FILING_SB = 'S-B'
    FILING_SB_AMEND = 'S-B/A'
    FILING_SBMEF = 'S-BMEF'
    FILING_SBSE = 'SBSE'
    FILING_SBSE_AMEND = 'SBSE/A'
    FILING_SBSEA = 'SBSE-A'
    FILING_SBSEA_AMEND = 'SBSE-A/A'
    FILING_SBSEBD = 'SBSE-BD'
    FILING_SBSEBD_AMEND = 'SBSE-BD/A'
    FILING_SBSEC = 'SBSE-C'
    FILING_SBSEW = 'SBSE-W'
    FILING_SC13D = 'SC 13D'
    FILING_SC13D_AMEND = 'SC 13D/A'
    FILING_SC13E1 = 'SC 13E1'
    FILING_SC13E1_AMEND = 'SC 13E1/A'
    FILING_SC13E3 = 'SC 13E3'
    FILING_SC13E3_AMEND = 'SC 13E3/A'
    FILING_SC13G = 'SC 13G'
    FILING_SC13G_AMEND = 'SC 13G/A'
    FILING_SC14D9 = 'SC 14D9'
    FILING_SC14D9_AMEND = 'SC 14D9/A'
    FILING_SC14N = 'SC 14N'
    FILING_SC14N_AMEND = 'SC 14N/A'
    FILING_SC14NS = 'SC 14N-S'
    FILING_SC14NS_AMEND = 'SC 14N-S/A'
    FILING_SCTOC = 'SC TO-C'
    FILING_SCTOI = 'SC TO-I'
    FILING_SCTOI_AMEND = 'SC TO-I/A'
    FILING_SCTOT = 'SC TO-T'
    FILING_SCTOT_AMEND = 'SC TO-T/A'
    FILING_SC13E4F = 'SC13E4F'
    FILING_SC13E4F_AMEND = 'SC13E4F/A'
    FILING_SC14D1F = 'SC14D1F'
    FILING_SC14D1F_AMEND = 'SC14D1F/A'
    FILING_SC14D9C = 'SC14D9C'
    FILING_SC14D9F = 'SC14D9F'
    FILING_SC14D9F_AMEND = 'SC14D9F/A'
    FILING_SDR = 'SDR'
    FILING_SDR_AMEND = 'SDR/A'
    FILING_SDRA = 'SDR-A'
    FILING_SDRCCO = 'SDR-CCO'
    FILING_SDRCCO_AMEND = 'SDR-CCO/A'
    FILING_SDRW = 'SDR-W'
    FILING_SF1 = 'SF-1'
    FILING_SF1_AMEND = 'SF-1/A'
    FILING_SF1MEF = 'SF-1MEF'
    FILING_SF3 = 'SF-3'
    FILING_SF3_AMEND = 'SF-3/A'
    FILING_SF3MEF = 'SF-3MEF'
    FILING_SHER = 'SH-ER'
    FILING_SHER_AMEND = 'SH-ER/A'
    FILING_SHNT = 'SH-NT'
    FILING_SHNT_AMEND = 'SH-NT/A'
    FILING_SP15D2 = 'SP 15D2'
    FILING_SP15D2_AMEND = 'SP 15D2/A'
    FILING_SUPPL = 'SUPPL'
    FILING_T1 = 'T-1'
    FILING_T2 = 'T-2'
    FILING_T3 = 'T-3'
    FILING_T3_AMEND = 'T-3/A'
    FILING_T6 = 'T-6'
    FILING_T6_AMEND = 'T-6/A'
    FILING_TA1 = 'TA-1'
    FILING_TA1_AMEND = 'TA-1/A'
    FILING_TA2 = 'TA-2'
    FILING_TA2_AMEND = 'TA-2/A'
    FILING_TAW = 'TA-W'
    FILING_UNDER = 'UNDER'
    FILING_UNDER_AMEND = 'UNDER/A'
    FILING_X17A5 = 'X-17A-5'
    FILING_X17A5_AMEND = 'X-17A-5/A'
    FILING_1ZW = '1-Z-W'
    FILING_1ZW_AMEND = '1-Z-W/A'
    FILING_CAW = 'C/A-W'
    FILING_CFPORTAL = 'CFPORTAL'
    FILING_CFPORTAL_AMEND = 'CFPORTAL/A'
    FILING_DEFM14A = 'DEFM14A'
    FILING_20FR12B = '20FR12B'
    FILING_20FR12B_AMEND = '20FR12B/A'
    FILING_SD = 'SD'
    FILING_SD_AMEND = 'SD/A'
    FILING_8K12G3 = '8-K12G3'
    FILING_8K12G3_AMEND = '8-K12G3/A'
    FILING_NRSROCE = 'NRSRO-CE'
    FILING_NRSROCE_AMEND = 'NRSRO- CE/A'
    FILING_APPWDAPPWD_AMEND = 'APP WD APP WD/A'
    FILING_NMFP2NMFP2_AMEND = 'N-MFP2 N-MFP2/A'
    FILING_SC14F1 = 'SC 14F1'
    FILING_SC14F1_AMEND = 'SC 14F1/A'
    FILING_NOINFOBLANKCELL = 'No info blank cell'
    FILING_497J = '497J'
    FILING_N148C = 'N-14 8C'
    FILING_N148C_AMEND = 'N-14 8C/A'
    FILING_NPORTEX = 'NPORT-EX'
    FILING_DSTRBRPT = 'DSTRBRPT'
    FILING_DSTRBRPT_AMEND = 'DSTRBRPT/A'
