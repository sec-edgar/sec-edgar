import re
import json
import os.path
import logging
import uu

# RE PRIMER
# (?!...)
# Matches if ... doesn’t match next.
# This is a negative lookahead assertion. For example, Isaac (?!Asimov) will match 'Isaac ' only if it’s not followed by 'Asimov'.

class EDGARExtractor():

    # Compile regular expressions
    # Note that re.search() does not have a starting position argument
    # but the search() method of a Pattern object (a compiled regex) has a pos argument
    re_doc = re.compile("<DOCUMENT>(.*?)</DOCUMENT>", flags=re.DOTALL)
    re_sec_header =  re.compile("<SEC-HEADER>.*?\n(.*?)</SEC-HEADER>", flags=re.DOTALL)
    re_sec_doc = re.compile("<SEC-DOCUMENT>(.*?)</SEC-DOCUMENT>", flags=re.DOTALL)
    re_text = re.compile("<TEXT>(.*?)</TEXT>", flags=re.DOTALL)

    def __init__(self, in_file, out_dir=None, metadata_debug=False):
        """
        Extract the embedded documents and their respective metadata from an EDGAR txt file
        """
        self.metadata_debug = metadata_debug
        if out_dir is None:
            out_dir = os.path.dirname(os.path.abspath(in_file))
        self.procTxtFile(in_file, out_dir)

    def procTxtFile(self, in_file, out_dir):

        if os.path.splitext(in_file)[1] != ".txt":
            raise Exception("ERROR: " + in_file + " is not a .txt file")

        in_filename = os.path.splitext(os.path.basename(in_file))[0]

        # Read input txt file
        with open(in_file, encoding="utf8") as intxtfh:
            intxt = intxtfh.read()

        # Loop for every "<SEC-DOCUMENT>" in the file
        sec_doc_cursor = 0
        sec_doc_count = intxt.count("<SEC-DOCUMENT>")
        for sec_doc_num in range(sec_doc_count):

            #print("sec_doc_num {}, sec_doc_cursor {}".format(sec_doc_num, sec_doc_cursor))

            # Extract the <SEC-DOCUMENT> part
            sec_doc_m = self.re_sec_doc.search(intxt, pos=sec_doc_cursor)
            if not sec_doc_m:
                break
            sec_doc_cursor = sec_doc_m.span()[1]
            sec_document = sec_doc_m.group(1)

            # Process metadata
            metadata_txt_match = self.re_sec_header.search(sec_document)
            metadata_txt = metadata_txt_match.group(1)
            metadata_file = os.path.join(out_dir, in_filename + "." + str(sec_doc_num) + ".json")
            metadata = self.processMetadata(metadata_txt)
            logging.info("Metadata written into {}".format(metadata_file))

            # Loop through every document
            metadata["documents"] = list()
            documents = sec_document[metadata_txt_match.span()[1]:].strip()
            doc_count = documents.count("<DOCUMENT>")
            doc_cursor = 0
            for doc_num in range(doc_count):

                #print("doc num {}, doc_cursor {}".format(doc_num, doc_cursor))

                #Pattern.search(string[, pos[, endpos]])
                doc_m = self.re_doc.search(documents, pos=doc_cursor)
                doc = doc_m.group(1)
                doc_cursor = doc_m.span()[1]
                doc_metadata = self.procDocMetadata(doc)
                metadata["documents"].append(doc_metadata)

                # Get file type
                filetype = os.path.splitext(metadata["documents"][doc_num]["filename"])[1][1:]
                filedata = self.re_text.search(doc).group(1).strip()
                outfn = os.path.join(out_dir, in_filename + "." + str(sec_doc_num) + "." + str(doc_num) + "." + filetype)

                # DEBUG ONLY: Write filedata to file
                #filedata_filename = os.path.join(out_dir, in_filename + "." + str(doc_num) + ".data_" + filetype)
                #with open(filedata_filename, "w", encoding="utf8") as outfh:
                #    outfh.write(filedata)

                #is the file uuencoded?
                is_uuencoded = filedata.find("begin 644 ") != -1

                # File is uu-encoded
                if is_uuencoded:
                    #print("UU-ENCODED")
                    logging.info("{} contains an uu-encoded file".format(in_file))
                    encfn = os.path.join(out_dir, in_filename + "." + str(doc_num) + ".txt_" + filetype)
                    with open(encfn, "w", encoding="utf8") as encfh:
                        encfh.write(filedata)
                    uu.decode(encfn, outfn)
                    os.remove(encfn)

                # Plain file (no conversion needed)
                else:
                    #print("NOT ENCODED")
                    logging.info("{} contains an non uu-encoded file".format(in_file))
                    with open(outfn, "w", encoding="utf8") as outfh:
                        outfh.write(filedata)

            # Save SEC-DOCUMENT metadata to file
            with open(metadata_file, "w", encoding="utf8") as fileh:
                fileh.write(self.jsonPretty(metadata))

    @staticmethod
    def procKeyStr(s):
        return s.replace(" ","_")

    @staticmethod
    def jsonPretty(dict_data):
        return json.dumps(dict_data, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    def procDocMetadata(self, doc):
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
        metadata_doc["filename"] = fn_m.group(1)

        return metadata_doc

    # Process the metadata of the focal document
    def processMetadata(self, curr_doc):
        out_dict = dict()
        levels = [None, None]

        for line in curr_doc.split("\n"):

            if self.metadata_debug:
                logging.debug("Line: '{}'".format(line))

            if "<ACCEPTANCE-DATETIME>" in line:
                out_dict["acceptance-datetime"] = line[len("<ACCEPTANCE-DATETIME>"):]
                continue

            if "<DESCRIPTION>" in line:
                out_dict["description"] = line[len("<DESCRIPTION>"):]
                continue

            # e.g. "CONFORMED SUBMISSION TYPE:	8-K"
            # *+ -> possessive quantifier
            m = re.match("^(\w.*):\t*([^\t]+)$", line)
            if m:
                if self.metadata_debug:
                    logging.debug("Match A:B")
                out_dict[self.procKeyStr(m.group(1))] = m.group(2)
                continue

            # Level 1 header
            # Headers have 1 initial tab less than data
            m = re.match("^(?!\t)(.+):\t*$", line)
            if m:
                levels[0] = self.procKeyStr(m.group(1))
                levels[1] = None
                if levels[0] not in out_dict:
                    out_dict[levels[0]] = dict()
                    if self.metadata_debug:
                        logging.debug("Creating level 1 header {}".format(levels[0]))
                continue

            # Level 2 header (must be before the data for correct matching)
            # In fact "level 1 data" match this too
            m = re.match("^\t(.+):\t*$", line)
            if m:
                levels[1] = self.procKeyStr(m.group(1))
                if levels[1] not in out_dict[levels[0]]:
                    out_dict[levels[0]][levels[1]] = dict()
                    if self.metadata_debug:
                        logging.debug("Creating level 2 header {}".format(levels[1]))
                continue

            # Level 1 data
            m = re.match("^\t(?!\t)(.+):\t*(.+)$", line)
            if m:
                out_dict[levels[0]][m.group(1)] = m.group(2)
                if self.metadata_debug:
                    logging.debug("Level 1 data. Levels[0]={}; group={}".format(levels[0], m.group(1)))
                continue

            # Level 2 data
            m = re.match("^\t\t(.+):\t*(.+)$", line)
            if m:
                if self.metadata_debug:
                    logging.debug("Level 2 data")
                out_dict[levels[0]][levels[1]][self.procKeyStr(m.group(1))] = m.group(2)
                continue

        # Return metadata dict
        return out_dict
