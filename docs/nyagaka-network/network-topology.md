# Nyagaka enterprices - Corporate Network Topology specification 
### Location : Nairobi Kenya | operational Status : Hardened stage 0 production Baseline

# Architectural overview
this document serves as the source of truth for multi-os lab network designed for nyagaka enterprises. The environment is segregated into public-facinginternet path (NAT adapters for patching and updates ) and isolated internal operational paths 

#Virtual Infrastructure Matrix 
virtual private switch= nyagaka-internal-net
network posture: Strict role-based access control wth asymmetric key-only management gateways

## Asset Inventory and Resource Alocation

Hostname:
    NYAGAKA-SRV01
    NYAGAKA-WEB01
    NYAGAKA-WKS01

Primary role:
   SRV01= central gateway
   WEB01= corporate app host node
   WKS01= local administartive host

Operating system:
    SRV01= ubuntu server 24.04
    WEB01= ubuntu server 24.04
    WKS01= windows server 2025 core

Private Internal IP and Network Interface metrics
   SRV01= 192.168.50.10 | Dual NIC (enp0s3, enpos8 'internal')
   WEB01= 192.168.50.20 | Dual NIC (enp0s3, enp0s8 'internal')
   WKS01= 192.168.50.30 | Dual NIC (ethernet'NAT' , ethernet 2 'internal')

## Role based Access Control and Firewall Metrics 
1. NYAGAKA-SRV01

Default= deny all incoming traffic
Rule 1= allow SSH(port 22) from the internal network subnet loop (192.168.50.0/24)
Acive Defence = fail2ban dynamic socket jail monitoring with adnimistrative whitelist(127.0.0.1/8 , 192.168.50.0/24)

2. NYAGAKA-WEB01

Default = deny all incoming traffic
Rule 1 = Allow HTTP (port 80) and HTTPS (PORT 443) globally from internal clients 
Rule 2 = Allow SSH (port 22) management access from the internal administration subnet

3. NYAGAKA-WKS01
 
Default = Windows Advanced Firewall Standard Core Rule Block
Rule 1 = Allow inbound remote desktop (RDP - Port 3389) to the internal network range(192.168.50.0/24)
