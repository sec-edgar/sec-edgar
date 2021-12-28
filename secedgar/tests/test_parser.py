import pytest
from secedgar.parser import F4Parser, MetaParser


class TestParser:
    parser = MetaParser()

    def test_process_document_metadata(self):
        doc = """<TYPE>10-K
        <SEQUENCE>123
        <FILENAME>test-filename.txt
        """
        metadata = self.parser.process_document_metadata(doc)
        assert metadata == {"type": "10-K", "sequence": "123", "filename": "test-filename.txt"}

    @pytest.mark.parametrize(
        "bad_filetype",
        [
            "xml",
            "json",
            "html",
            "txt.gz",
            "zip"
        ]
    )
    def test_bad_filetypes_raises_error(self, bad_filetype):
        with pytest.raises(ValueError):
            self.parser.process(infile="test.{0}".format(bad_filetype))


class TestF4Parser:

    parser = F4Parser()

    def test_process_document_metadata_form_4(self):
        doc = """<TYPE>4
        <SEQUENCE>123
        <FILENAME>test-filename.txt
        <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
            <transactionDate>
                <value>2021-05-14</value>
            </transactionDate>
            <transactionCoding>
                <transactionFormType>5</transactionFormType>
                <transactionCode>G</transactionCode>
                <equitySwapInvolved>0</equitySwapInvolved>
            </transactionCoding>
            <transactionTimeliness>
                <value>E</value>
            </transactionTimeliness>
            <transactionAmounts>
                <transactionShares>
                    <value>4010</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>0</value>
                </transactionPricePerShare>
                <transactionAcquiredDisposedCode>
                    <value>D</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction>
                    <value>324164</value>
                </sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership>
                    <value>D</value>
                </directOrIndirectOwnership>
            </ownershipNature>
        </nonDerivativeTransaction>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
                <footnoteId id="F1"/>
            </securityTitle>
            <transactionDate>
                <value>2021-08-02</value>
            </transactionDate>
            <transactionCoding>
                <transactionFormType>4</transactionFormType>
                <transactionCode>S</transactionCode>
                <equitySwapInvolved>0</equitySwapInvolved>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>15600</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>145.83</value>
                    <footnoteId id="F2"/>
                </transactionPricePerShare>
                <transactionAcquiredDisposedCode>
                    <value>D</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction>
                    <value>308564</value>
                </sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership>
                    <value>D</value>
                </directOrIndirectOwnership>
            </ownershipNature>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
        """
        data = self.parser.process(doc)
        assert data == {
            "nonDerivativeTable": {
                "nonDerivativeTransaction": [
                    {
                        "securityTitle": "Common Stock",
                        "transactionDate": "2021-05-14",
                        "transactionCoding": {
                            "transactionFormType": "5",
                            "transactionCode": "G",
                            "equitySwapInvolved": "0"
                        },
                        "transactionAmounts": {
                            "transactionShares": "4010",
                            "transactionPricePerShare": "0",
                            "transactionAcquiredDisposedCode": "D"
                        },
                        "postTransactionAmounts": {
                            "sharesOwnedFollowingTransaction": "324164"
                        },
                        "ownershipNature": {
                            "directOrIndirectOwnership": "D"
                        }
                    },
                    {
                        "securityTitle": "Common Stock",
                        "transactionDate": "2021-08-02",
                        "transactionCoding": {
                            "transactionFormType": "4",
                            "transactionCode": "S",
                            "equitySwapInvolved": "0"
                        },
                        "transactionAmounts": {
                            "transactionShares": "15600",
                            "transactionPricePerShare": "145.83",
                            "transactionAcquiredDisposedCode": "D"
                        },
                        "postTransactionAmounts": {
                            "sharesOwnedFollowingTransaction": "308564"
                        },
                        "ownershipNature": {
                            "directOrIndirectOwnership": "D"
                        }
                    }
                ]
            }
        }
