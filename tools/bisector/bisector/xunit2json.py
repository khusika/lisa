#! /usr/bin/env python3

import argparse
import collections
import functools
import itertools
import json
import operator
import sys

import pandas as pd
import scipy.stats

def error(msg):
    print('Error: ' + str(msg), file=sys.stderr)

def read_json(path):
    try:
        return pd.read_json(path, orient='index')
    except ValueError as e:
        raise FileNotFoundError("Unable to find or parse " + path) from e

def correlate_df(events_df, threshold=0.0):
    # Convert booleans to integers by multplying by 1
    events_df *= 1
    events_df = events_df.transpose().astype(float)

    # Compute the correlation between tests failures
    corr_df = events_df.corr()

    # Rename the columns for better readability
    corr_df.rename(
        {name: i for i, name in enumerate(corr_df.index)},
        axis = 'columns',
        inplace = True,
    )
    corr_df.rename(
        {
            name: '({i}) {name}'.format(name=name, i=i)
            for i, name in enumerate(corr_df.index)
        },
        axis = 'rows',
        inplace = True,
    )

    # Replace values below a given threshold by dots to improve readability
    corr_df = corr_df.applymap((lambda x: x if abs(x) >= threshold else '.'))
    return corr_df

def compare_df(json_df1, json_df2, alpha, alternative='two-sided', non_significant=True, sort='name'):
    # Use an inner-join to only consider tests that are present on both sides
    merged_df = pd.merge(json_df1, json_df2, how='inner', right_index=True,
            left_index=True, suffixes=('_old','_new'))

    if merged_df.empty:
        raise ValueError("Merged dataframe is empty, there was no test in common")

    # Apply the Fisher exact test to all tests failures.
    regression_map = collections.defaultdict(dict)
    for row in merged_df.itertuples(index=True):
        testcase = row[0]
        failure_old = row.counters_old['failure']
        failure_new = row.counters_new['failure']
        passed_old = row.counters_old['passed']
        passed_new = row.counters_new['passed']

        odds_ratio, p_val = scipy.stats.fisher_exact(
            [
                # Ignore errors and skipped tests
                [failure_old, passed_old],
                [failure_new, passed_new],
            ],
            alternative = alternative
        )

        # Ignore errors and skipped tests
        meaningful_total_old = failure_old + passed_old
        meaningful_total_new = failure_new + passed_new
        # If no meaningful iterations are available, return NaN
        if not meaningful_total_old:
            failure_old_pc = float('Inf')
        else:
            failure_old_pc = 100 * failure_old / (failure_old + passed_old)
        if not meaningful_total_new:
            failure_new_pc = float('Inf')
        else:
            failure_new_pc = 100 * failure_new / (failure_new + passed_new)

        delta = failure_new_pc - failure_old_pc

        regression_map[testcase] = {
            'failure_old': failure_old_pc,
            'failure_new': failure_new_pc,
            'delta': delta,
            'p-value': p_val,
            # If the p-value is smaller than alpha, the regression or
            # improvement is statistically significant
            'significant': (p_val <= alpha),
        }

    regression_df = pd.DataFrame.from_dict(regression_map, orient='index')
    if not non_significant:
        regression_df = regression_df.loc[regression_df['significant']]
        regression_df.drop('significant', axis=1, inplace=True)

    if sort == 'name':
        regression_df.sort_index(inplace=True)
    else:
        regression_df.sort_values(by=[sort], ascending=False, inplace=True)

    return regression_df

def _main(argv):
    parser = argparse.ArgumentParser(description="""
    Compare tests failure rate using Fisher exact test.
    """,
    formatter_class=argparse.RawTextHelpFormatter)

    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')

    compare_parser = subparsers.add_parser('compare',
        description="""Compare two JSON files."""
    )

    analyze_parser = subparsers.add_parser('analyze',
        description="""Analyze a given JSON file."""
    )

    # Options for compare subcommand
    compare_parser.add_argument('json', nargs=2,
        help="""JSON files to compare.""")

    compare_parser.add_argument('--alpha', type=float,
        default=5,
        help="""Alpha risk for Fisher exact test in percents.""")

    compare_parser.add_argument('--non-significant', action='store_true',
        help="""Also show non-significant changes of failure rate.""")

    compare_parser.add_argument('--sort', metavar='COL',
        default='name',
        help="""Sort the results by test name ("name") or by a column name.""")

    compare_parser.add_argument('--regression', action='store_true',
        help="""Only look for regressions (one-sided Fisher exact test).""")

    # Options for analyze subcommand
    analyze_parser.add_argument('json', nargs='+',
        help="""JSON files to analyze.""")

    analyze_parser.add_argument('--corr', action='store_true',
        help="""Show the correlation matrix between the tests' failures.  High
        correlation between tests that are always failing or passing are
        usually not significant and should be filtered-out with --hide-const.
        """)

    analyze_parser.add_argument('--failure-rate-csv', action='store_true',
        help="""Show the failure rates in CSV.""")

    analyze_parser.add_argument('--corr-thresh', type=float,
        default = 0.0,
        help="""Hide correlation factors smaller than this threshold in absolute value.""")

    analyze_parser.add_argument('--hide-const', action='store_true',
        help="""Remove columns and rows filled with NaN. This happens when the
        variance of the failures is 0, which means correlation cannot be
        defined.""")

    args = parser.parse_args(argv)

    # Do not crop any output
    pd.set_option('display.width', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', -1)
    pd.set_option('display.colheader_justify', 'center')

    if args.subcommand == 'compare':
        json_df1 = read_json(args.json[0])
        json_df2 = read_json(args.json[1])

        alpha = args.alpha / 100
        show_non_significant = args.non_significant
        sort = args.sort
        only_regression = args.regression
        alternative = 'less' if only_regression else 'two-sided'

        try:
            regression_df = compare_df(
                json_df1, json_df2,
                alpha, alternative,
                show_non_significant, sort
            )
        except KeyError as e:
            error('Unknown column "{}"'.format(e))
            return 1

        if not regression_df.empty:
            print(regression_df.to_string(
                formatters = {
                    'failure_old':'{:5.2f}%'.format,
                    'failure_new':'{:5.2f}%'.format,
                    'delta':'{:6.2f}%'.format,
                    'p-value':'{:4.2e}'.format,
                }
            ))

    if args.subcommand == 'analyze':
        show_correlation = args.corr
        correlation_thresh = args.corr_thresh
        hide_const = args.hide_const
        show_failure_rate = args.failure_rate_csv

        for json_path in args.json:
            json_df = read_json(json_path)

            if show_correlation:
                # Filter-out tests that never passed or never failed. They may
                # have a 0 variance if they are also never skipped and are
                # never erroring, which will result in NaN. Even if they don't
                # have zero variance, they would be highly correlated which is
                # usually not helpful.
                if hide_const:
                    json_df = json_df[(json_df.failure != 0) & (json_df.passed != 0)]

                # Create a dataframe out of the failure events, one column per
                # iteration.
                failure_events_df = pd.DataFrame(json_df.events.apply(pd.Series).failure.values.tolist(), index=json_df.index)
                # Fill the missing iteration using "false", since the event could not
                # have happened on iteration where the test was not executed.
                failure_events_df.fillna(value=False, inplace=True)
                corr_df = correlate_df(failure_events_df, correlation_thresh)
                print(corr_df.to_string(float_format=lambda x: "{:.2f}".format(x)))

            if show_failure_rate:
                failure_df= json_df['failure']/(json_df['passed'] + json_df['failure'])
                print(failure_df.to_csv(), end='')

def main(argv=sys.argv[1:]):
    try:
        return_code = _main(argv=argv)
    except FileNotFoundError as e:
        error(e)
        return_code = 1

    sys.exit(return_code)

if __name__ == '__main__':
    main()

# vim :set tabstop=4 shiftwidth=4 expandtab textwidth=80
