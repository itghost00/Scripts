#!/usr/bin/python3

import scapy.all as scapy
import argparse
import textwrap
import sys

def get_arguments():
    
    #Creating Argument Parser
    parser = argparse.ArgumentParser(description= "Network Scanner",
            formatter_class = argparse.RawDescriptionHelpFormatter,
            epilog = textwrap.dedent(""" Example:
            sudo ./network-scanner.py -t 10.10.10.10/24
            """))
    
    #Adding arguments to the parser
    parser.add_argument("-t", "--target", dest="target", help="Target IP / IP range")
    
    #Parsing the command line argument
    options = parser.parse_args()
    return options

def scan(ip):
    #creating arp request using the given ip address
    arp_request = scapy.ARP(pdst=ip)
    
    #Setting custom destination address which is broadcast address here 
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    
    #Joining two packets into single packet using "/" 
    arp_request_broadcast = broadcast/arp_request

    #Sending and recieving packets; srp returns two set of values answered and unaswered, [0] captures only the first element
    answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]
    
    
    clients_list = []
    #Parsing response
    for element in answered_list:
        clients_dict = {"IP": element[1].psrc, "MAC": element[1].hwsrc}
        clients_list.append(clients_dict)

    return clients_list

def print_result(result_list):
    print("-" * 42)
    print("IP\t\t\tMAC Address")
    print("-" * 42)
    for client in result_list:
        print(client["IP"] + "\t\t" + client["MAC"])

options = get_arguments()
if not options.target:
    print("[-] Please enter IP address. Use --help for more info.")
    sys.exit()
scan_result = scan(options.target)
if not scan_result:
    print("[-] Please enter valid IP address. Use --help for more info.")
    sys.exit()
print_result(scan_result)
