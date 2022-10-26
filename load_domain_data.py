import os
import csv
import argparse

import pyrkbun

def generate_csvs(domain):
    domain_records = pyrkbun.dns.get_records(domain)

    records = [record for record in domain_records if record.record_type != 'NS']
    names_servers = [record for record in domain_records if record.record_type == 'NS']

    keys = ['record_type','content','name','ttl','prio','record_id']

    if not os.path.isdir(f'./domains/{domain}'):
        os.mkdir(f'./domains/{domain}')

    with open(f'./domains/{domain}/records.csv', 'w') as output:
        writer = csv.DictWriter(output, fieldnames=keys, restval='', extrasaction='ignore')
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)
            
    with open(f'./domains/{domain}/name_servers.csv', 'w') as output:
        writer = csv.DictWriter(output, fieldnames=keys, restval='', extrasaction='ignore')
        writer.writeheader()
        for record in names_servers:
            writer.writerow(record.__dict__)


def main():
    parser = argparse.ArgumentParser(description='Prep csv data for domain management')
    parser.add_argument('domain', type=str, help='Domain name to extract data from')
    parser.set_defaults(func=generate_csvs)
    args = parser.parse_args()
    args.func(args.domain)
            
if __name__ == "__main__":
    main()