import os
import csv

import pyrkbun

from datetime import datetime, timezone

from load_domain_data import generate_csvs

DOMAINS = os.listdir('./domains')

def get_target_record_state(domain: str) -> list[pyrkbun.dns]:
    """Get target record state for domain excluding NS records"""
    records = []
    with open(f'./domains/{domain}/records.csv', newline='') as input:
        input_reader = csv.DictReader(input)
        for record in input_reader:
            dns_record = pyrkbun.dns(domain, **record)
            records.append(dns_record)
    return records

def get_target_name_server_state(domain: str) -> list[pyrkbun.dns]:
    """Get target record state for domain NS records"""
    records = []
    with open(f'./domains/{domain}/name_servers.csv', newline='') as input:
        input_reader = csv.DictReader(input)
        for record in input_reader:
            dns_record = pyrkbun.dns(domain, **record)
            records.append(dns_record)
    return records

def get_current_record_state(domain: str) -> list[pyrkbun.dns]:
    """Get all current domain records excluding NS records"""
    domain_records = pyrkbun.dns.get_records(domain)
    records = [record for record in domain_records if record.record_type != 'NS']
    return records

def get_current_name_server_state(domain: str) -> list[pyrkbun.dns]:
    """Get all current domain NS records"""
    domain_records = pyrkbun.dns.get_records(domain)
    records = [record for record in domain_records if record.record_type == 'NS']
    return records

def create_records(target_record_state: list[pyrkbun.dns]) -> list[pyrkbun.dns]:
    """Create new records as required"""
    # records_to_create captures new additions to the domain record list
    # by identifying missing record ID's. Deals with variations based on
    # trailing commas in list entry
    records_to_create: list [pyrkbun.dns] = [record for record in target_record_state if record.record_id == '' or record.record_id == 'None']
    for record in records_to_create:
        result: dict = record.create()
        #print(f'CREATE [{record.record_type}, {record.content}, {record.name}, {record.record_id}] RESULT: {result}')
    return records_to_create

def delete_records(target_record_state: list[pyrkbun.dns], current_record_state: list[pyrkbun.dns]) -> list[pyrkbun.dns]:
    """Delete records as required"""
    ## retain_record_ids is determined by all records that are remaining in the list of records that have an existing id
    retain_record_ids: list [int] = [record.record_id for record in target_record_state if record.record_id != '' or record.record_id != 'None']
    ## For each record in the current list of records, if the record id is not in the retain list it should go
    records_to_delete: list[pyrkbun.dns] = [record for record in current_record_state if record.record_id not in retain_record_ids]
    for record in records_to_delete:
        result = record.delete()
        #print(f'DELETE [{record.record_type}, {record.content}, {record.name}, {record.record_id}] RESULT: {result}')
    return records_to_delete

def edit_records(target_record_state: list[pyrkbun.dns], current_record_state: list[pyrkbun.dns]) -> list[pyrkbun.dns]:
    """Edit records as required"""
    records_to_edit: list[pyrkbun.dns] = []
    for current_record in current_record_state:
        for target_record in target_record_state:
            if target_record.record_id == current_record.record_id:
                if target_record != current_record:
                    records_to_edit.append(target_record)
    for record in records_to_edit:
        result = record.update()
        #print(f'EDIT [{record.record_type}, {record.content}, {record.name}, {record.record_id}] RESULT: {result}')
    return records_to_edit

def write_results(domain: str, created: list[pyrkbun.dns], deleted: list[pyrkbun.dns], edited: list[pyrkbun.dns], current: list[pyrkbun.dns]) -> None:
    """Write back current domain state and generate audit log"""
    generate_csvs(domain)
    with open(f'./domains/{domain}/audit.log', 'a') as results:
        results.write(f'RESULTS OF OPERATION COMPLETED AT: {str(datetime.now(timezone.utc))}\n')
        results.write('__CREATED__\n') if len(created) != 0 else results.write('__CREATED__\nNo Records Created\n')
        for record in created:
            results.write(f'{record.record_type},{record.content},{record.name},{record.ttl},{record.prio},{record.record_id}\n')
        results.write('__DELETED__\n') if len(deleted) != 0 else results.write('__DELETED__\nNo Records Deleted\n')
        for record in deleted:
            results.write(f'{record.record_type},{record.content},{record.name},{record.ttl},{record.prio},{record.record_id}\n')
        results.write('__EDITED__\n') if len(edited) != 0 else results.write('__EDITED__\nNo Records Edited\n')
        for edit_record in edited:
            for original_record in current:
                if original_record.record_id == edit_record.record_id:
                    results.write(f'Pre-edit of record id {original_record.record_id}: ')
                    results.write(f'{original_record.record_type},{original_record.content},{original_record.name},{original_record.ttl},{original_record.prio},{original_record.record_id}\n')
                    results.write(f'Post-edit of record id {edit_record.record_id}: ')
                    results.write(f'{edit_record.record_type},{edit_record.content},{edit_record.name},{edit_record.ttl},{edit_record.prio},{edit_record.record_id}\n')

def main():
    up_to_date_count = 0
    
    for domain in DOMAINS:
        target_record_state: list[pyrkbun.dns] = get_target_record_state(domain)
        current_record_state: list[pyrkbun.dns] = get_current_record_state(domain)
        
        target_name_server_state: list[pyrkbun.dns] = get_target_name_server_state(domain)
        current_name_server_state: list[pyrkbun.dns] = get_current_name_server_state(domain)
        
        # Exit loop and stop any changes if there are no updates detected to DNS records.
        if target_record_state == current_record_state and target_name_server_state == current_name_server_state:
            #print(f'No Changes To DNS Records Detected for Domain {domain}')
            with open(f'./domains/{domain}/no-dns-change.txt', 'w') as file:
                file.write(f'{str(datetime.now(timezone.utc))}')
            continue
        
        target_record_state.extend(target_name_server_state)
        current_record_state.extend(current_name_server_state)
        
        created_records: list[pyrkbun.dns] = create_records(target_record_state)
        deleted_records: list[pyrkbun.dns] = delete_records(target_record_state, current_record_state)
        edited_records:  list[pyrkbun.dns] = edit_records(target_record_state, current_record_state)
        write_results(domain, created_records, deleted_records, edited_records, current_record_state)

    for domain in DOMAINS:
        up_to_date_count += 1 if os.path.exists(f'./domains/{domain}/no-dns-change.txt') else 0
        if os.path.exists(f'./domains/{domain}/no-dns-change.txt'):
         os.remove(f'./domains/{domain}/no-dns-change.txt')
        
    if len(os.listdir('./domains')) == up_to_date_count:
        print('NO_COMMIT')
    else:
        print('COMMIT_REQUIRED')
        
if __name__ == "__main__":
    main()
    