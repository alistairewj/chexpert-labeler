# This script prepares MIMIC-CXR reports for CheXpert labeling.
import sys
import os
import argparse
import csv
import re
from pathlib import Path

import numpy as np
from tqdm import tqdm

# local folder import
import section_parser as sp

parser = argparse.ArgumentParser()

# Input report parameters.
parser.add_argument('--reports_path',
                    required=True,
                    help='Path to file with radiology reports.')
parser.add_argument('--output_path',
                    required=True,
                    help='Path to output CSV files.')


def main(args):
    args = parser.parse_args(args)

    reports_path = Path(args.reports_path)
    output_path = Path(args.output_path)

    # get all the folders in MIMIC-CXR
    p_folders = os.listdir(reports_path)
    p_folders = [p for p in p_folders if p.startswith('p')]
    p_folders.sort()

    # For each patient
    for p in tqdm(p_folders):
        patient_path = reports_path / p
        studies = os.listdir(patient_path)
        studies = [s for s in studies
                   if s.endswith('.txt') and s.startswith('s')]

        patient_studies = []
        for s in studies:
            with open(patient_path / s, 'r') as fp:
                text = ''.join(fp.readlines())

            # split text into sections
            sections, section_names, section_idx = sp.split_report_into_sections(
                text
            )

            # grab the *first* section with the given title
            if 'impression' in section_names:
                idx = section_names.index('impression')
            elif 'findings' in section_names:
                # If impression not found, extract findings
                idx = section_names.index('findings')
            elif 'last_paragraph' in section_names:
                idx = section_names.index('last_paragraph')
            else:
                # If neither found, we do not output anything
                patient_studies.append([s[0:-4], ''])
                print(patient_path / s)
                # sys.exit(0)
                continue

            # Output into CSV files, one per patient
            patient_studies.append([s[0:-4], sections[idx].strip()])

        if len(patient_studies) > 0:
            with open(output_path / f'{p}.csv', 'w') as fp:
                csvwriter = csv.writer(fp)
                for row in patient_studies:
                    csvwriter.writerow(row)


if __name__ == '__main__':
    main(sys.argv[1:])
