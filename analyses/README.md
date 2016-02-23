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
   * SEI CERT VU#615808 tracks affected Netgear devices
   * SEI CERT VU#548680 tracks affected D-Link devices

   * Netgear:
      * Use CVE-2016-1555 for issues 200, 201, 204, 205, and 206.
      * Use CVE-2016-1556 for issue 207.
      * Use CVE-2016-1557 for issues 211, 212, 213, and 214.

   * D-Link
      * Use CVE-2016-1558 for issue 203.
      * Use CVE-2016-1559 for issues 209 and 210.
