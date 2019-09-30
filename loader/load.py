"""Define report loader class."""
import re
import os

import bioc
import pandas as pd
from negbio.pipeline import text2bioc, ssplit, section_split
from tqdm import tqdm

from constants import *


class Loader(object):
    """Report impression loader."""

    def __init__(self, reports_path, extract_impression=False, extension='txt'):
        self.reports_path = reports_path
        self.extract_impression = extract_impression
        self.punctuation_spacer = str.maketrans({key: f"{key} "
                                                 for key in ".,"})
        self.splitter = ssplit.NegBioSSplitter(newline=False)
        self.extension = extension

        if os.path.isdir(reports_path):
            # load in all radiology reports in a folder
            self.load_files()
        else:
            # load in a single CSV file with all radiology reports
            self.load_csv()

        self.prep_collection()

    def load_files(self):
        """Load and clean many reports stored in a folder"""
        files = os.listdir(self.reports_path)
        files = [f for f in files if f.endswith(self.extension)]
        assert len(files) > 0,\
            ('Folder with reports must contain at '
             f'least one ".{self.extension}" file')

        files.sort()

        # if args.verbose:
        files = tqdm(files)
        print('Collecting reports from files...')

        # assume one report per file
        self.reports = list()
        self.index = list()
        for f in tqdm(files, total=len(files)):
            with open(self.reports_path / f, 'r') as fp:
                self.reports.append(''.join(fp.readlines()))
            self.index.append(f)

    def load_csv(self):
        """Load and clean the reports."""
        reports = pd.read_csv(self.reports_path, header=None)
        # allow users to input
        #  (1) single column CSV or reports
        #  (2) two columns; first is the index, second is the report
        assert reports.shape[1] <= 2,\
            ('A one or two column CSV with no header is expected as input.')
        if reports.shape[1] == 1:
            reports = reports.iloc[:, 0].tolist()
            index = None
        else:
            # reports shape must be 2
            index = reports.iloc[:, 0].tolist()
            reports = reports.iloc[:, 1].tolist()

        self.index = index
        self.reports = reports

    def prep_collection(self):
        """Apply splitter and create bioc collection"""
        collection = bioc.BioCCollection()
        for i, report in enumerate(self.reports):
            clean_report = self.clean(report)
            document = text2bioc.text2document(str(i), clean_report)

            if self.extract_impression:
                document = section_split.split_document(document)
                self.extract_impression_from_passages(document)

            split_document = self.splitter.split_doc(document)

            assert len(split_document.passages) == 1,\
                ('Each document must have a single passage, ' +
                 'the Impression section.')

            collection.add_document(split_document)
        self.collection = collection

    def extract_impression_from_passages(self, document):
        """Extract the Impression section from a Bioc Document."""
        impression_passages = []
        for i, passage in enumerate(document.passages):
            if 'title' in passage.infons:
                if passage.infons['title'] == 'impression':
                    next_passage = document.passages[i+1]
                    assert 'title' not in next_passage.infons,\
                        "Document contains empty impression section."
                    impression_passages.append(next_passage)

        assert len(impression_passages) <= 1,\
            (f"The document contains {len(document.passages)} impression " +
             "passages.")

        assert len(impression_passages) >= 1,\
            "The document contains no explicit impression passage."

        document.passages = impression_passages

    def clean(self, report):
        """Clean the report text."""
        lower_report = report.lower()
        # Change `and/or` to `or`.
        corrected_report = re.sub('and/or',
                                  'or',
                                  lower_report)
        # Change any `XXX/YYY` to `XXX or YYY`.
        corrected_report = re.sub('(?<=[a-zA-Z])/(?=[a-zA-Z])',
                                  ' or ',
                                  corrected_report)
        # Clean double periods
        clean_report = corrected_report.replace("..", ".")
        # Insert space after commas and periods.
        clean_report = clean_report.translate(self.punctuation_spacer)
        # Convert any multi white spaces to single white spaces.
        clean_report = ' '.join(clean_report.split())
        # Remove empty sentences
        clean_report = re.sub(r'\.\s+\.', '.', clean_report)

        return clean_report
