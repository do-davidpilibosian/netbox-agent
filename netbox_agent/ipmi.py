import logging
import subprocess

from netaddr import IPNetwork


class IPMI():
    """
    Parse IPMI output
    ie:

    Set in Progress         : Set Complete
    Auth Type Support       :
    Auth Type Enable        : Callback :
                            : User     :
                            : Operator :
                            : Admin    :
                            : OEM      :
    IP Address Source       : DHCP Address
    IP Address              : 10.192.2.1
    Subnet Mask             : 255.255.240.0
    MAC Address             : 98:f2:b3:f0:ee:1e
    SNMP Community String   :
    BMC ARP Control         : ARP Responses Enabled, Gratuitous ARP Disabled
    Default Gateway IP      : 10.192.2.254
    802.1q VLAN ID          : Disabled
    802.1q VLAN Priority    : 0
    RMCP+ Cipher Suites     : 0,1,2,3
    Cipher Suite Priv Max   : XuuaXXXXXXXXXXX
                            :     X=Cipher Suite Unused
                            :     c=CALLBACK
                            :     u=USER
                            :     o=OPERATOR
                            :     a=ADMIN
                            :     O=OEM
    Bad Password Threshold  : Not Available
    """

    def __init__(self):
        result = subprocess.run(['ipmitool', 'lan', 'print'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.ret = result.returncode
        self.output = result.stdout.decode('utf-8')
        self.error_output = result.stderr.decode('utf-8')
        
        if self.ret != 0 and "IP Address" not in self.output:
            logging.info("Returned error code and IP Address not defined")
            logging.info('Cannot get ipmi info: {}'.format(self.error_output))
        else:
            logging.info('IPMI info retrieved successfully')
            logging.info(self.output)

    def parse(self):
        _ipmi = {}
        if self.ret != 0 and "IP Address" not in self.output:
            return _ipmi

        for line in self.output.splitlines():
            key = line.split(':')[0].strip()
            if key not in ['802.1q VLAN ID', 'IP Address', 'Subnet Mask', 'MAC Address']:
                continue
            value = ':'.join(line.split(':')[1:]).strip()
            _ipmi[key] = value

        ret = {}
        ret['name'] = 'IPMI'
        ret["mtu"] = 1500
        ret['bonding'] = False
        ret['mac'] = _ipmi['MAC Address']
        if 'vlan' not in _ipmi:
            ret['vlan'] = None

        if '802.1q VLAN ID' in _ipmi:
            ret['vlan'] = int(_ipmi['802.1q VLAN ID']) \
                if _ipmi['802.1q VLAN ID'] != 'Disabled' else None
            
        ip = _ipmi['IP Address']
        netmask = _ipmi['Subnet Mask']
        address = str(IPNetwork('{}/{}'.format(ip, netmask)))

        ret['ip'] = [address]
        ret['ipmi'] = True
        return ret
