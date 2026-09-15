
# Multi-node Enterprise DevSecOps Lab Framework
### Lead System ENgineer: NYAGAKA RENEE
### Organizational Target : Nyagaka Enterprise 

## Summary and Overview

THis repository contains the complete engineering baseline , config files and stateful security blueprints for the stage 0 deployment of Nyagaka Enterprises
what started as a single hardened linux server has been systematically expanded into a multi-node network, This environment safely bridges both linux and windows operating systems across private, segregated network pathways, Every piece of configuration is managed entirely as code under version control tomatch real word DevSecOPs standards 

# What We built

1. Repository pipeline Blueprint
 Established a secure , centralized version control reposirtory linked to github (NyagakaRenee/nyagaka-homelab)

Imlemented strict administrative tracking procotols , including standard 'gitignore' rules to prevent runtime offset files or temporary editor swapdata from polluting corporate logs 

Unified the entire deployment workflow so that all infrastructure files from external nodes are centrally tracked on the primary management node

2. Multi-node Private Network Switch deployment
Discovered real-world hypervisor network properties and intentionally split network interfaces logic intodual-NIC setups on all machines 
  **Adapter 1(NAT mode ) = left DHCP with a custom route metric 100 routing overrides 
  **Adapter 2(Internal NEtwork) = configured a completely private virtual switch named 'nyagaka-internal-net' direcly inside the virtual box motherboard settings

Manually assigned static ,persistent IP space across this private internal switch to prevemt communivatin drops 
   ***NYAGAKA-SRV01 = 192.168.50.10/24
   ***NYAGAKA-WEB01 = 192.168.50.20/24
   ***NYAGAKA-WKS01 = 192.168.50.30/24

3. Server-side hardening and key autentication (SSH Security)
Shut down all default remote password acess lines across the linux endpoints (PasswordAuthentication no)

Preventeddirect external root account breaches by blocking administrative login access (PermitRootLogin no)

Deployed modern ultra-secure asymmetric cryptographic key pairs using the high-performance **Ed25519** cpher algorithm

Resolved host-to-guest connection challenges by generaring fresh passphrase-inckuded key pairs on windows 


4. Active Automated defense -Fail2Ban Integration
Deployed Fail2Ban to act as an automated behavioural security guard scanning the live server authenticaton logs 

Fixed initial sockets crases and option duplication errors by enguineering a pristine streamlined override fileusing advanced tee pipe writing shortcuts 

configured automated runtime blocking rules : any host that triggers 0 bad password attempts within a 10-minute window is instantly lokced out by the firewall for 1hour 

added a proactive whitelist ('igonreip') to cover loval host-only ranges to ensure administrative tools never experience lockouts

5. custom system safety rails
overrode standard terminal command behaviours inside the user shell environment profikles - ~/.bashrc

deployes cp -i=cp , mv -i=mv 
created a custom bash function for rm , the tool automatically verifies if a target file exists ,if posostive forces a mandatory sudopassword authentication check before any real file can be pernmanently removed from the system

6. Edge-to-edge cross network verification
Conducted a deep test to prove all virtual communication paths are active 

