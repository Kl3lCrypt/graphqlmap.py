#!/usr/bin/env python3

import requests
from termcolor import colored
import signal
import sys
import argparse


def def_handler(sig, frame):
    print(colored("\n[!] Saliendo del programa...\n", "red"))
    sys.exit(1)

signal.signal(signal.SIGINT, def_handler)



DEFAULT_ROUTES = [
"/graphql/v1",
"/api/v1",
"/api/graphql/v1",
"/graphql/api/v1",
"/graphql/graphql/v1",
"/graphql/",
"/api/",
"/api/graphql/",
"/graphql/api",
"/graphql/graphql",
]


BYPASS = "\n\n\t"*10

PAYLOAD = {
    "query":"query {__typename}"
}

HEADERS = {
    "Content-Type":"application/json"
}

RESPONSE = '''{
  "data": {
    "__typename": "query"
  }
}'''

RESPONSE_INTROSPECTION = '''{
  "data": {
    "__schema": {
      "queryType": {
        "name": "query"
      }
    }
  }
}'''

INTROSPECTION_PROOF = {
    "query":"{__schema{queryType{name}}}"
}

INTROSPECTION_PROOF_BYPASS = {
    "query": f"{{__schema{BYPASS}{{queryType{BYPASS}{{name{BYPASS}}}}}}}"
}


def getArguments():
    parser = argparse.ArgumentParser(description="Script para detectar enpoints GraphQL")
    parser.add_argument("--url", required=True, help="URL a scanear. Ex: --url https://ejemplo.com")
    parser.add_argument("--wordlist", help="Specific wordlist for endpoint. Ex: --wordlist my_endpoint.txt")
    args = parser.parse_args()
    return args.url, args.wordlist

def send_scan(line, url):
    line = line.strip()
    url_complete = url+line
    r = requests.post(url_complete, headers=HEADERS, json=PAYLOAD)

    endpoint_found_get = False
    endpoint_found_post = False

    if r.status_code == 405 or r.text == '"Method Not Allowed"':
        r_get = requests.get(url_complete, params=PAYLOAD)
        if r_get.text == RESPONSE and r_get.status_code == 200:
            print(colored(f"[+] Graphql Endpoint localizado GET Methods ==> {url_complete}\n", "green"))
            endpoint_found_get = True
    elif r.status_code == 200:
        print(colored(f"Graphql Endpoint localizado POST Methods ==> {url_complete}", "green"))
        endpoint_found_post = True

    if endpoint_found_get:
        r_get = requests.get(url_complete, params=INTROSPECTION_PROOF)
        if "errors" in r_get.text or "introspection is not allowed" in r_get.text:
            print(colored("[!] Introspeccion desabilitada", "red"))
            r_get = requests.get(url_complete, params=INTROSPECTION_PROOF_BYPASS)
            if r_get.text == RESPONSE_INTROSPECTION: 
                print(colored("[+] Bypass Exitoso\n", "green"))
            else:
                print(colored("[!] Bypass Fallido\n", "red"))
        else:
            print(colored("[+] Introspeccion habilitada", "green"))
        return True

    if endpoint_found_post:
        r_post = requests.post(url_complete, headers=HEADERS, json=INTROSPECTION_PROOF)
        if "errors" in r_post.text or "introspection is not allowed" in r_post.text:
            print(colored("[!] Introspeccion desabilitada", "red"))
            r_post = requests.get(url_complete, headers=HEADERS, json=INTROSPECTION_PROOF_BYPASS)
            if r_post.text == RESPONSE_INTROSPECTION: 
                print(colored("[+] Bypass Exitoso\n", "green"))
            else:
                print(colored("[!] Bypass Fallido\n", "red"))
        else:
            print(colored("[+] Introspeccion habilitada", "green"))
        return True
    return False
 

def main():
    url, wordlist = getArguments()
    print(colored(f"\nIniciando graphqlScan hacia {url}\n", "yellow"))
    found = False
    if wordlist:
        try:
            with open(wordlist, "r") as f:
                for line in f:
                    if send_scan(line, url):
                        found = True
        except Exception as e:
            print(f"Error: {e}")
    else:
        for line in DEFAULT_ROUTES:
            if send_scan(line, url):
                found = True
    if not found:
        print(colored("[-] No se encontraron endpoints GraphQL", "red"))

if __name__ == "__main__":
    main()

