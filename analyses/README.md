This directory contains analyses for the FIRMADYNE system. The public release
of our system includes the following analyses.

* `webAccess.py`: This script iterates through each file within the filesystem of a firmware image that appears to be served by a webserver, and aggregates the results based on whether they appear to required
authentication.
* `snmpwalk.sh`: This script dumps the contents of the public and private SNMP
v2c communities to disk using no credentials.
* `runExploits.py`: This script tests for the presence of 60 known
vulnerabilities using exploits from Metasploit, and 14 previously-unknown
vunlerabilities that we developed. These unknown vulnerabilities are tracked
as follows.
   * SEI CERT VU#615808 tracks affected Netgear devices.
   * SEI CERT VU#548680 tracks affected D-Link devices.

   * Netgear: Fixes for WN604 [now available (v3.3.3)](http://files.netgear-support.com/go/?a=d&i=giUL1cgnWF), others except WN802T v2 and WN802T v3 expected by mid-March, remainder no details.
      * Use CVE-2016-1555 for issues 200, 201, 204, 205, and 206.

> WN604 v2.0.1  
> WN604 v2.0.2  
> WN604 v2.1  
> WN604 v2.3.1  
> WN604 v2.3.2  
> WN604 v3.0.0  
> WN604 v3.0.2  
> WN802Tv2 v3.1.1  
> WN802Tv2 v3.1.12  
> WN802Tv2 v3.1.3  
> WN802Tv2 v3.1.9  
> WNAP210 v2.1.1  
> WNAP210 v2.1.4  
> WNAP210 v2.17.5.0  
> WNAP320 v2.0  
> WNAP320 v2.0.3  
> WNAP320 v2.1.1  
> WNAP320 v2.17.5.0  
> WNAP320JP v2.1.4  
> WNDAP350 v2.0.27  
> WNDAP350 v2.0.9  
> WNDAP350 v2.1.2  
> WNDAP350 v2.1.6  
> WNDAP350 v2.1.7  
> WNDAP350 v2.17.5.0  
> WNDAP360 v2.0.0  
> WNDAP360 v2.0.4  
> WNDAP360 v2.0.7  
> WNDAP360 v2.1.1  
> WNDAP360 v2.1.5  
> WNDAP360 v2.1.6  
> WNDAP360 v2.1.7  
> WNDAP360 v2.1.8  
> WNDAP360 v2.17.5.0

      * Use CVE-2016-1556 for issue 207.
> WN604 v2.0.1  
> WN604 v2.0.2  
> WN604 v2.1  
> WN604 v2.3.1  
> WN604 v2.3.2  
> WN604 v3.0.0  
> WN604 v3.0.2  
> WNAP210 v2.1.1  
> WNAP210 v2.1.4  
> WNAP210 v2.17.5.0  
> WNAP320 v2.1.1  
> WNAP320 v2.17.5.0  
> WNAP320JP V2.1.4  
> WND930 v2.0.3  
> WNDAP350 v2.1.2  
> WNDAP350 v2.1.6  
> WNDAP350 v2.1.7  
> WNDAP350 v2.17.5.0  
> WNDAP360 v2.1.1  
> WNDAP360 v2.1.5  
> WNDAP360 v2.1.6  
> WNDAP360 v2.1.7  
> WNDAP360 v2.1.8  
> WNDAP360 v2.17.5.0

      * Use CVE-2016-1557 for issues 211, 212, 213, and 214.
> WNAP320 v2.0  
> WNAP320 v2.0.3  
> WNDAP350 v2.0.9  
> WNDAP360 v2.0.0  
> WNDAP360 v2.0.0  
> WNDAP360 v2.0.4  
> WNDAP360 v2.0.7

   * D-Link: Fix expected by mid-April
      * Use CVE-2016-1558 for issue 203.
> DAP-2230 v1.02  
> DAP-2310 v2.06  
> DAP-2330 v1.06  
> DAP-2360 v2.06  
> DAP-2553 v3.05  
> DAP-2660 v1.11  
> DAP-2690 v3.15  
> DAP-2695 v1.16  
> DAP-3662 v1.01/v1.01EU  
> DAP-3320 v1.00  
> DWP-2360 v2.05

      * Use CVE-2016-1559 for issues 209 and 210.
> DAP-1353 v3.15  
> DAP-2553 v1.31  
> DAP-3520 v1.16
