# dns-manager

Simple text based updates to DNS domains hosted on porkbun.com via git commits using Github actions.

Create a directory under `./domains/<domain-name>` and populate:
 - records.csv: with all records except name server records
 - name_servers.csv: with all name server records
 
 Pushing a commit to any file in the `./domains` hierarchy will trigger an action to update the domain records as represented in these files utilising the `dns_execute.py` script
 
 To initilise these files in the correct syntax you can run `load_domain_data.py` with the target domain name given as the only argument.
 
```
 ./load_domain.data.py mydomain.com
```
 
 The utility requires [Pyrkbun](https://pypi.org/project/pyrkbun/) to perfrom the domain operations. As such you will need to set the following environment variables to your Porkbun API Key and Secret
```
PYRK_API_SECRET_KEY='sk_abcdef123456789abcdef123456789abcdef'
PYRK_API_KEY = 'sk_abcdef123456789abcdef123456789abcdef'
```

