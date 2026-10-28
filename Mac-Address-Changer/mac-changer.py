#!/usr/bin/python3

import subprocess
import argparse
import textwrap
import re
import sys

#Function for Handling Command-line Arguments
def get_arguments():
    
    #Creating Argument Parser
    parser = argparse.ArgumentParser(description= "Mac address Changer",
            formatter_class = argparse.RawDescriptionHelpFormatter,
            epilog = textwrap.dedent(""" Example:
            sudo ./mac-changer -i wlan0 -m 00:11:22:33:44:55
            """))
    
    #Adding arguments to the parser
    parser.add_argument("-i", "--interface", dest="interface", help="Interface")
    parser.add_argument("-m", "--mac", dest="new_mac", help="New mac address")
    
    #Parsing the command line argument
    options = parser.parse_args()
    if not options.interface:
        parser.error("[-] Interface not specified, use --help for more info.")
    if not options.new_mac:
        parser.error("[-] Mac address not specified, use --help for more info.")
    return options


#Function for changing MAC address
def change_mac(interface, new_mac):
    #Removing delimeter (:) from the mac address
    new_mac = re.sub(":", "", new_mac)
    #Removing white spaces in between
    new_mac = "".join(new_mac.split())
    #Checking length of the provided mac address
    if len(new_mac) == 12:
        subprocess.call(["ifconfig", interface, "down"])
        subprocess.call(["ifconfig", interface, "hw", "ether", new_mac])
        subprocess.call(["ifconfig", interface, "up"])
    else:
        print("[-] Error: Please enter valid MAC address. Use --help for more info.")
        sys.exit()


#Function for getting old MAC address
def get_current_mac(interface):
    try:
        ifconfig_result = subprocess.check_output(["ifconfig", options.interface]).decode("utf-8")

        old_mac = re.search(r"\w\w:\w\w:\w\w:\w\w:\w\w:\w\w", ifconfig_result)
        if old_mac:
            return old_mac.group(0)
        else:
            #Print when the interface exist but has no mac address e.g. lo
            print ("[-] Error: Please enter valid interface. Use --help for more info.")
            sys.exit()
    except subprocess.CalledProcessError:
        #Print when the interface or device doesn't exist at all
        print ("[-] Error: Please enter valid interface. Use --help for more info.")
        sys.exit()


options = get_arguments()
current_mac = get_current_mac(options.interface)
old_mac = current_mac
change_mac(options.interface, options.new_mac)

#verifying whether MAC has changed or not
current_mac = get_current_mac(options.interface)
if old_mac == options.new_mac:
    print(f"[-] MAC address did not get changed. It's the same old MAC address.")
elif current_mac == options.new_mac:
    print(f"[+] MAC Address of {options.interface} was successfully changed to {options.new_mac}")
else:
    print("[-] Error: Please enter valid MAC address. Use --help for more info.")
