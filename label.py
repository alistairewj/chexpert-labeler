"""Entry-point script to label radiology reports."""
from pathlib import Path
import os
import sys
from datetime import datetime
import pandas as pd

from args import ArgParser
from loader import Loader
from stages import Extractor, Classifier, Aggregator
from constants import *


def write(reports, labels, output_path, verbose=False):
    """Write labeled reports to specified path."""
    labeled_reports = pd.DataFrame({REPORTS: reports})
    for index, category in enumerate(CATEGORIES):
        labeled_reports[category] = labels[:, index]

    if verbose:
        print(f"Writing reports and labels to {output_path}.")
    labeled_reports[[REPORTS] + CATEGORIES].to_csv(output_path,
                                                   index=False)


def label(args):
    """Label the provided report(s)."""

    loader = Loader(args.reports_path, args.extract_impression)

    extractor = Extractor(args.mention_phrases_dir,
                          args.unmention_phrases_dir,
                          verbose=args.verbose)
    classifier = Classifier(args.pre_negation_uncertainty_path,
                            args.negation_path,
                            args.post_negation_uncertainty_path,
                            verbose=args.verbose)
    aggregator = Aggregator(CATEGORIES,
                            verbose=args.verbose)
    return extractor, classifier, aggregator


def label(args, extractor, classifier, aggregator):
    """Label the provided report(s)."""
    # Load the reports
    loader = Loader(args.reports_path, args.extract_impression)

    # Load reports in place.
    loader.load()
    # Extract observation mentions in place.
    extractor.extract(loader.collection)
    # Classify mentions in place.
    classifier.classify(loader.collection)
    # Aggregate mentions to obtain one set of labels for each report.
    labels = aggregator.aggregate(loader.collection)

    write(loader.reports, labels, args.output_path, args.verbose)


if __name__ == "__main__":
    parser = ArgParser()
    args = parser.parse_args()

    # check if folder is passed as input
    # in this case parse each text file individually
    if os.path.isdir(args.reports_path):
        base_path = args.reports_path
        if os.path.isdir(args.output_path):
            out_prefix = 'labeled_'
            out_path = args.output_path
        else:
            out_prefix = args.output_path.stem
            out_path = args.output_path.parents[0]

        report_files = os.listdir(base_path)
        report_files = [x for x in report_files if x[-4:] == '.csv']
        N = len(report_files)
        if N == 0:
            print('Empty folder given for parsing. ' +
                  'Input path must be a single CSV, or a folder of CSVs.')
            sys.exit()

        if args.verbose:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            print('{} - Parsing {} files.'.format(now, N))

        extractor, classifier, aggregator = prep_objects(args)
        for i, f in enumerate(report_files):
            f_out = out_prefix + f
            # update output paths for this folder
            args.reports_path = base_path / f
            args.output_path = out_path / f_out
            try:
                label(args, extractor, classifier, aggregator)
            except:
                print('Error on file {}'.format(f))
                with open('error.log', 'a') as fp:
                    fp.write('{}\n'.format(f))

            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            if args.verbose:
                print('{} - Finished {} of {} ({:3.2f}%).'.format(
                      now, i+1, N, float(i+1)/N*100.0))
    else:
        extractor, classifier, aggregator = prep_objects(args)
        label(args, extractor, classifier, aggregator)
