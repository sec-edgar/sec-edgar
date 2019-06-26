import re
import json
import os.path
import logging
import codecs
import uu
import io
import binascii

# Utilities
class FilingsExtractorUtils():

    @staticmethod
    def proc_key_str(s):
        return s.replace(" ", "_")

    @staticmethod
    def json_pretty(dict_data):
        return json.dumps(dict_data, sort_keys=True,
                          indent=4, separators=(',', ': '),
                          ensure_ascii=False)


# Data containeers
class SECDocument():
    def __init__(self):
        self.metadata = dict()
        self.docslist = list()

    def add_document(self, in_doc):
        if not isinstance(in_doc, EmbeddedDocument):
            raise Exception("Trying to add a document which is not a SECDocument")
        self.docslist.append(in_doc)

class EmbeddedDocument():
    def __init__(self):
        self.metadata = dict()
        self.contents = ""

# Parsers
class FilingsExtracted():
    def __init__(self):
        self.in_file = None
        self.sec_documents = list()

    def add_document(self, in_doc):
        if not isinstance(in_doc, SECDocument):
            raise Exception("Trying to add a document which is not a SECDocument")
        self.sec_documents.append(in_doc)

    def save(self, out_dir):
        """
        Save the extracted files to disk
        out_dir: The output directory. Can be None, in which case a sub-directory with the same name of the input .txt file will be created
        """

        # Create output dir
        if out_dir is None:
            out_dir = os.path.dirname(os.path.abspath(self.in_txt_file))
            out_dir = os.path.join(out_dir, self.in_txt_file)
        os.makedirs(out_dir, exist_ok=True)

        # Loop through <SEC-DOCUMENT>
        for sec_doc_num, sec_doc in enumerate(self.sec_documents):

            # Loop through <DOCUMENT>
            for doc_num, doc in enumerate(sec_doc.docslist):
                # Build filename
                if "filename" in doc.metadata:
                    doc_filename = doc.metadata["filename"]
                else:
                    in_filename = os.path.splitext(os.path.basename(self.in_file))[0]
                    doc_filename = in_filename + "." + str(sec_doc_num) + "." + str(doc_num) + ".txt"

                # Check whether a file with this name already exist
                outfn = os.path.join(out_dir, doc_filename)
                if os.path.isfile(outfn):
                    doc_filename_split = os.path.splitext(doc_filename)
                    outfn = os.path.join(out_dir, doc_filename_split[0]
                                         + "." + str(sec_doc_num)
                                         + "." + str(doc_num)
                                         + "." + doc_filename_split[1][1:])

                # Write embedded document to file
                if(type(doc.contents)==str):
                    with open(outfn, "w", encoding="utf8") as fh:
                        fh.write(doc.contents)
                elif(type(doc.contents)==bytearray):
                    with open(outfn, "wb") as fh:
                        fh.write(doc.contents)
                else:
                    raise Exception("Unrecognized doc.contents type")

                # Append file metadata to sec-document metadata
                if "documents" not in sec_doc.metadata:
                    sec_doc.metadata["documents"] = list()
                sec_doc.metadata["documents"].append(doc.metadata)

            # Save <SEC-DOCUMENT> metadata to file
            metadata_filename = "secdoc" + str(sec_doc_num) + ".metadata.json"
            metadata_file = os.path.join(out_dir, metadata_filename)
            with open(metadata_file, "w", encoding="utf8") as fileh:
                fileh.write(FilingsExtractorUtils.json_pretty(sec_doc.metadata))

    def rm_infile(self):
        if os.path.isfile(self.in_file):
            os.unlink(self.in_file)

class FilingsExtractor():

    def __init__(self):
        self.re_dict = self.compile_regex()
        pass

    @staticmethod
    def compile_regex():
        """
        Compile the regular expression needed to extract contents from a .txt file
        """
        re_sec_doc = re.compile("<SEC-DOCUMENT>(.*?)</SEC-DOCUMENT>", flags=re.DOTALL)
        re_sec_header = re.compile("<SEC-HEADER>.*?\n(.*?)</SEC-HEADER>", flags=re.DOTALL)
        re_doc = re.compile("<DOCUMENT>(.*?)</DOCUMENT>", flags=re.DOTALL)
        re_text = re.compile("<TEXT>(.*?)</TEXT>", flags=re.DOTALL)
        re_uu_cont = re.compile("begin 644 .*\n(.*?)\nend", flags=re.DOTALL)
        re_dict = {
            "doc" : re_doc,
            "sec_header" : re_sec_header,
            "sec_doc" : re_sec_doc,
            "text" : re_text,
            "uu_cont" : re_uu_cont,
        }
        return re_dict


    def extract(self, in_file):
        """
        Extract the contents of a txt file.
        in_file: The input .txt file
        return: A SECDocument object
        """
        filing_extracted = FilingsExtracted()
        filing_extracted.in_file = in_file

        # Read input txt file
        if os.path.splitext(in_file)[1] != ".txt":
            raise Exception("ERROR: " + in_file + " is not a .txt file")
        with open(in_file, encoding="utf8") as intxtfh:
            intxt = intxtfh.read()

        # Loop for every "<SEC-DOCUMENT>" in the file
        for sec_doc_m in self.re_dict["sec_doc"].finditer(intxt):

            logging.info("New SEC-DOCUMENT found")

            # Extract the <SEC-DOCUMENT> part
            sec_document_txt = sec_doc_m.group(1)
            sec_document = SECDocument()

            # Process metadata
            metadata_txt_match = self.re_dict["sec_header"].search(sec_document_txt)
            metadata_txt = metadata_txt_match.group(1)
            sec_document.metadata = self.extract_metadata_secdoc(metadata_txt)

            # Get the text of the documents, by removing sec-document metadata we already processed
            documents = sec_document_txt[metadata_txt_match.span()[1]:].strip()
            # Loop through <DOCUMENT>
            for doc_m in self.re_dict["doc"].finditer(documents):

                logging.info("New <DOCUMENT> found")

                doc_txt = doc_m.group(1)
                document = EmbeddedDocument()
                document.metadata = self.extract_metadata_doc(doc_txt)

                # Get file data and output filename
                document.contents = self.re_dict["text"].search(doc_txt).group(1).strip()

                # Is the file uuencoded?
                is_uuencoded = document.contents.find("begin 644 ") != -1

                # File is uu-encoded
                if is_uuencoded:
                    purified = self.re_dict["uu_cont"].match(document.contents).group(1)
                    outbytes = bytearray()
                    for line in purified.split("\n"):
                        outbytes += binascii.a2b_uu(line)
                    document.contents = outbytes

                # Save <DOCUMENT> to the <SEC-DOCUMENT> object
                sec_document.add_document(document)

            # <DOCUMENT> loop end

            filing_extracted.add_document(sec_document)
        # <SEC-DOCUMENT> loop end

        return filing_extracted

    def extract_metadata_doc(self, doc):
        """
        Extract metadata of a <DOCUMENT> tag
        return: a dictionary containing the metadata
        """
        metadata_doc = dict()
        # Document type
        type_m = re.search("<TYPE>(.*?)\n", doc)
        if type_m:
            metadata_doc["type"] = type_m.group(1)
        # Document sequence
        seq_m = re.search("<SEQUENCE>(.*?)\n", doc)
        if seq_m:
            metadata_doc["sequence"] = seq_m.group(1)
        # Document filename
        fn_m = re.search("<FILENAME>(.*?)\n", doc)
        if fn_m:
            metadata_doc["filename"] = fn_m.group(1)
        return metadata_doc


    # Process the metadata of the focal sec-document
    def extract_metadata_secdoc(self, curr_doc):
        """
        Extract metadata of a <SEC-DOCUMENT> tag
        return: a dictionary containing the metadata
        """
        out_dict = dict()
        levels = [None, None]
        self.metadata_debug = False

        for line in curr_doc.split("\n"):

            if self.metadata_debug:
                logging.debug("Line: '{}'".format(line))

            if "<ACCEPTANCE-DATETIME>" in line:
                out_dict["acceptance-datetime"] = \
                    line[len("<ACCEPTANCE-DATETIME>"):]
                continue

            if "<DESCRIPTION>" in line:
                out_dict["description"] = line[len("<DESCRIPTION>"):]
                continue

            # e.g. "CONFORMED SUBMISSION TYPE:	8-K"
            # *+ -> possessive quantifier
            m = re.match(r"^(\w.*):\t*([^\t]+)$", line)
            if m:
                if self.metadata_debug:
                    logging.debug("Match A:B")
                metakey = FilingsExtractorUtils.proc_key_str(m.group(1))
                out_dict[metakey] = m.group(2)
                continue

            # Level 1 header
            # Headers have 1 initial tab less than data
            m = re.match("^(?!\t)(.+):\t*$", line)
            if m:
                levels[0] = FilingsExtractorUtils.proc_key_str(m.group(1))
                levels[1] = None
                if levels[0] not in out_dict:
                    out_dict[levels[0]] = dict()
                    if self.metadata_debug:
                        logging.debug("Creating level 1 header {}"
                                      .format(levels[0]))
                continue

            # Level 2 header (must be before the data for correct matching)
            # In fact "level 1 data" match this too
            m = re.match("^\t(.+):\t*$", line)
            if m:
                levels[1] = FilingsExtractorUtils.proc_key_str(m.group(1))
                if levels[1] not in out_dict[levels[0]]:
                    out_dict[levels[0]][levels[1]] = dict()
                    if self.metadata_debug:
                        logging.debug("Creating level 2 header {}"
                                      .format(levels[1]))
                continue

            # Level 1 data
            m = re.match("^\t(?!\t)(.+):\t*(.+)$", line)
            if m:
                out_dict[levels[0]][m.group(1)] = m.group(2)
                if self.metadata_debug:
                    logging.debug("Level 1 data. Levels[0]={}; group={}"
                                  .format(levels[0], m.group(1)))
                continue

            # Level 2 data
            m = re.match("^\t\t(.+):\t*(.+)$", line)
            if m:
                if self.metadata_debug:
                    logging.debug("Level 2 data")
                metakey = FilingsExtractorUtils.proc_key_str(m.group(1))
                out_dict[levels[0]][levels[1]][metakey] = m.group(2)
                continue

        # Return metadata dict
        return out_dict
