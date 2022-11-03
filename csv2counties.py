#!/usr/bin/env python3
"""Create a report for counties found in the first column of supplied CSV file."""
import csv
import re
import sys

import requests

ADDRESS_REGEX = re.compile(r'.*[,\s]([a-zA-Z]{1,2}[0-9]{1,2})\s?([0-9]{1,2}[a-zA-Z]{1,2})')


def read_csv(file_name):
    with open(file_name) as fh:
        return list(csv.reader(fh.readlines()))


def api_query_county(result):
    county = result['admin_county']
    if county is None:
        county = result['admin_district']
    return county


def get_api_data(data, query):
    api_data = {}
    with requests.Session() as session:
        for entry in data:
            match = ADDRESS_REGEX.match(entry[0])
            if match:
                postcode = "".join(match.groups())
                response = session.get(f'https://api.postcodes.io/postcodes/{postcode}')
                response.raise_for_status()
                try:
                    result = response.json()['result']
                    key = query(result)
                    api_data.setdefault(key, 0)
                    api_data[key] += 1
                except KeyError:
                    pass
    return api_data


def percent(part, whole):
    try:
        return 100 * float(part) / float(whole)
    except ZeroDivisionError:
        return 0


def report_line(lead, total, num):
    print(f'{lead}: {num} ({percent(num, total):.2f}%)')


def report(total, api_data):
    [report_line(county, total, num) for county, num in api_data.items()]
    print()

    report_line('No data', total, total - sum(api_data.values()))
    report_line('Total', total, total)


def main():
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} file-name.csv', file=sys.stderr)
        exit(1)
    csv_data = read_csv(sys.argv[1])
    api_data = get_api_data(csv_data, api_query_county)
    report(len(csv_data), api_data)


if __name__ == '__main__':
    main()
