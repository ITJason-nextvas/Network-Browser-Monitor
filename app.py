# import psutil
# import time
# import dnslib
# import socket
# import dns.resolver
# from scapy.all import sniff, DNSQR, TCP
# from threading import Thread
# import logging

# # Create a logger
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

# # Create a file handler
# handler = logging.FileHandler('network_usage_and_browsing_activity.log')
# handler.setLevel(logging.INFO)

# # Create a formatter and set it for the handler
# formatter = logging.Formatter('%(asctime)s - %(message)s')
# handler.setFormatter(formatter)

# # Add the handler to the logger
# logger.addHandler(handler)

# def track_network_usage_and_log_browsing_activity():
#     # Network usage tracking
#     net_io = psutil.net_io_counters()
#     bytes_sent = net_io.bytes_sent
#     bytes_recv = net_io.bytes_recv

#     def packet_sniffer(packet):
#         if packet.haslayer(DNSQR):
#             domain = packet.qd.qname.decode('utf-8')
#             logger.info(f"DNS Query: {domain}")
#             print(f"DNS Query: {domain}")
#         elif packet.haslayer(TCP):
#             if packet[TCP].dport == 80 or packet[TCP].dport == 443:
#                 try:
#                     url = packet[TCP].payload.decode('utf-8')
#                     logger.info(f"HTTP Request: {url}")
#                     print(f"HTTP Request: {url}")
#                 except:
#                     pass

#     # Run the packet sniffer in a separate thread
#     sniffer_thread = Thread(target=lambda: sniff(prn=packet_sniffer, store=0))
#     sniffer_thread.daemon = True  # Allow the main thread to exit even if the sniffer_thread is still running
#     sniffer_thread.start()

#     while True:
#         # Network usage tracking
#         time.sleep(1)
#         net_io = psutil.net_io_counters()
#         bytes_sent_diff = net_io.bytes_sent - bytes_sent
#         bytes_recv_diff = net_io.bytes_recv - bytes_recv
#         bytes_sent = net_io.bytes_sent
#         bytes_recv = net_io.bytes_recv
#         logger.info(f"Bytes Sent: {bytes_sent_diff}, Bytes Received: {bytes_recv_diff}")

# track_network_usage_and_log_browsing_activity()

###

import psutil
import time
import dnslib
import socket
import dns.resolver
from scapy.all import sniff, DNSQR, TCP, get_if_list, get_working_if
from threading import Thread
import logging
import netifaces

interfaces = get_if_list()
print("Available interfaces:", interfaces)

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a file handler
handler = logging.FileHandler('network_usage_and_browsing_activity.log')
handler.setLevel(logging.INFO)

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

def track_network_usage_and_log_browsing_activity():
    # Network usage tracking
    net_io = psutil.net_io_counters()
    bytes_sent = net_io.bytes_sent
    bytes_recv = net_io.bytes_recv

    def packet_sniffer(packet):
        if packet.haslayer(DNSQR):
            domain = packet[DNSQR].qname.decode('utf-8')
            logger.info(f"DNS Query: {domain}")
            print(f"DNS Query: {domain}")
        elif packet.haslayer(TCP):
            if packet[TCP].dport == 80 or packet[TCP].dport == 443:
                try:
                    url = packet[TCP].payload.decode('utf-8')
                    logger.info(f"HTTP Request: {url}")
                    print(f"HTTP Request: {url}")
                except:
                    pass
        
    # # Get all network interfaces
    # all_interfaces = netifaces.interfaces()
    # print(f"netifaces asdasdas{all_interfaces}")
    # # Sniff on all available network interfaces
    # for iface in all_interfaces:
    #     try:
    #         # Start sniffing on each interface in a separate thread
    #         sniffer_thread = Thread(target=lambda: sniff(prn=packet_sniffer, store=0, iface=iface))
    #         sniffer_thread.daemon = True  # Allow the main thread to exit even if sniffer_thread is still running
    #         sniffer_thread.start()
    #     except Exception as e:
    #         logger.error(f"Failed to sniff on interface {iface}: {str(e)}")

    try:
    # Try sniffing on the best working interface first
        iface = get_working_if()  
        print(f"Sniffing on the best interface: {iface}")
        sniff(prn=packet_sniffer, store=0, iface=iface)
    except Exception as e:
        logging.error(f"Failed to sniff on best interface: {str(e)}")
        # Fall back to sniffing on all available interfaces
        print("Falling back to sniffing on all interfaces.")
        all_interfaces = netifaces.interfaces()
        for iface in all_interfaces:
            try:
                sniffer_thread = Thread(target=lambda: sniff(prn=packet_sniffer, store=0, iface=iface))
                sniffer_thread.daemon = True
                sniffer_thread.start()
            except Exception as e:
                logging.error(f"Failed to sniff on interface {iface}: {str(e)}")
    
    while True:
        # Network usage tracking
        time.sleep(1)
        net_io = psutil.net_io_counters()
        bytes_sent_diff = net_io.bytes_sent - bytes_sent
        bytes_recv_diff = net_io.bytes_recv - bytes_recv
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv
        logger.info(f"Bytes Sent: {bytes_sent_diff}, Bytes Received: {bytes_recv_diff}")

track_network_usage_and_log_browsing_activity()
