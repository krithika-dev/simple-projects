#!/usr/bin/env python
#
# SDX Platform Definition description (in XML format)
#
# This is the master copy on which software relies upon to change
# the behavior of SDX based on platform (if applicable)
#
# Any new feature/TAG that gets introduced needs a corresponding interface to expose
# in parser (available below).
#

import os, sys
import re
import optparse
import subprocess
import xml.dom.minidom
from xml.dom.minidom import Node


#
# Exported Helper Functions
def socket_count():
    return int(dom.getElementsByTagName('SOCKET')[0].firstChild.data)

def hyperthread_count():
    return int(dom.getElementsByTagName('HYPER-THREADS')[0].firstChild.data)

def cores_count():
    return int(dom.getElementsByTagName('CORES')[0].firstChild.data)

def dmidecodeid():
    return (dom.getElementsByTagName('HARDWARE')[0].attributes['DMIDECODEID'].value)

def sysfamily(arg):
    return (dom.getElementsByTagName('HARDWARE')[0].attributes['SYSFAMILY'].value)

def sysid(arg):
    return (dom.getElementsByTagName('HARDWARE')[0].attributes['SYSID'].value)

def vpxsysid(arg):
    return  dom.getElementsByTagName('HARDWARE')[0].attributes['VPXSYSID'].value

def svm_vcpu_affinity(arg):
    return int(dom.getElementsByTagName('SVM_VCPU_AFFINITY')[0].firstChild.data)

def productname(arg):
    return str(dom.getElementsByTagName('PRODUCTNAME')[0].firstChild.data)

def mgmtintfs(arg):
    return (dom.getElementsByTagName('MGMT_INTFS')[0].firstChild.data)

def pcibackhide(arg):
    try:
        return (dom.getElementsByTagName('PCIBACK_HIDE')[0].firstChild.data)
    except:
        return ""

def bayinfo(arg):
    try:
        return (dom.getElementsByTagName('BAYINFO')[0].firstChild.data)
    except:
        return ""

def diskassemble(arg):
    try:
        return (dom.getElementsByTagName('DISKASSEMBLE')[0].firstChild.data)
    except:
        return ""

def diskdata(arg, name):
    if not arg:
        return ""
    slot=arg[0]
    tag = name+slot
    try:
        return dom.getElementsByTagName(tag)[0].firstChild.data
    except:
        return ""

def contains_fortville(arg):
    try:
        return  dom.getElementsByTagName('CONTAINS_FORTVILLE')[0].firstChild.data
    except:
        return "0"

def contains_mnx(arg):
    try:
        return  dom.getElementsByTagName('MNX_DRIVER')[0].firstChild.data
    except:
        return "0"

def contains_coleto(arg):
    try:
        return  dom.getElementsByTagName('CONTAINS_COLETO')[0].firstChild.data
    except:
        return "0"

def contains_cavium(arg):
    try:
        return  dom.getElementsByTagName('CONTAINS_CAVIUM')[0].firstChild.data
    except:
        return "0"

def diskmem(arg):
    return diskdata(arg, 'DISKSLOT')

def diskdev(arg):
    return diskdata(arg, 'DISKDEVICE')

def diskname(arg):
    return diskdata(arg, 'DISKNAME')

def disk_slot_count(arg):
    count=0
    for elem in dom.getElementsByTagName('DISKS'):
        for x in elem.childNodes:
            if x.nodeType == Node.ELEMENT_NODE and x.tagName[0:10] == "DISKDEVICE":
                count += 1
    return count

def platform(arg):
    plat={}
    for elem in dom.getElementsByTagName('PRODUCT'):
        for x in elem.childNodes:
            if x.nodeType == Node.ELEMENT_NODE:
                if plat.has_key(x.tagName):
                    plat[x.tagName] = [ plat[x.tagName], x.childNodes[0].data ]
                else:
                    plat[x.tagName] = x.childNodes[0].data
    return repr(plat)

def get_features():
    features = {}
    for elem in dom.getElementsByTagName('FEATURE'):
        for x in elem.childNodes:
            if x.nodeType == Node.ELEMENT_NODE:
                features[x.tagName] = x.childNodes[0].data
    return features    

#Return 1 - if feature is supported and present
def get_features():
    features = {}
    for elem in dom.getElementsByTagName('FEATURE'):
        for x in elem.childNodes:
            if x.nodeType == Node.ELEMENT_NODE:
                features[x.tagName] = x.childNodes[0].data
    return features    

#Return 1 - if feature is supported and present
#Return 0 - otherwise
def swraid(arg):
    f = get_features()
    if f and f.has_key('SWRAID'):
        return int(f['SWRAID'])
    return 0

def l2mode(arg):
    f = get_features()
    if f and f.has_key('L2MODE'):
        return int(f['L2MODE'])
    return 0

def get_cmds(tag):
    for elem in dom.getElementsByTagName(tag):
        alist=elem.getElementsByTagName('BASH_ACTIONS')
        cmds = re.split(";|\n", alist[0].firstChild.data)
        for i in reversed(cmds):
            if not i and not i.strip():
                cmds.remove(i)
                continue
    return cmds
    
def do_postinst(arg):
    cmds = get_cmds("POSTINSTALL")
    for cmd in cmds:
        os.system(cmd)

def do_lcd(arg):
    cmds = get_cmds("LCD")
    for cmd in cmds:
        os.system(cmd)

def determineProduct():
    cmd = "dmidecode -s system-serial-number| sed  '/^[@#]/ d' | tr -d '\n'"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output,error = p.communicate()

    cmd = "/opt/xensource/packages/files/fvt/sernov3d -d %s -D" % output
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output,error = p.communicate()
    if "error" in output:
        type = str(0)
    else:
        type = output.split(" ")[2].upper()
    return type

def verify():
    return (determineProduct() == dmidecodeid())

if __name__ == '__main__':
    try:
        # Not This platform
        #if not verify():
            #sys.exit(0)

        parser = optparse.OptionParser()
        parser.add_option('-f', '--file', help="sdx definition file in xml format")
        options, remainder = parser.parse_args()

        if (len(remainder) < 1):
            sys.exit(0)
        act = remainder[0]
        param=None
        if (len(remainder) > 1):
            param = remainder[1:] 

        sdx_xml = os.path.dirname(os.path.realpath(__file__)) + "/sdx-def.xml"
        if options.file:
            sdx_xml = options.file
        dom = xml.dom.minidom.parse(sdx_xml)
        
        # Dispatch Table for Query to help with Bash calls
        action = \
            {'svmaffinity': (svm_vcpu_affinity, None),
             'setlcd': (do_lcd, None),
             'swraid': (swraid, None),
             'l2mode': (l2mode, None),
             'productname': (productname, None),
             'platform': (platform, None),
             'sysid': (sysid, None),
             'vpxsysid': (vpxsysid, None),
             'sysfamily': (sysfamily, None),
             'mgmtintfs': (mgmtintfs, None),
             'diskmembers': (diskmem, param),
             'diskdevice': (diskdev, param),
             'diskname': (diskname, param),
             'slotcount': (disk_slot_count, None),
             'execpostinstall': (do_postinst, None),
             'pcibackhide': (pcibackhide, None),
             'bayinfo': (bayinfo, None),
             'diskassemble': (diskassemble, None),
             'contains_fortville': (contains_fortville, None),
             'contains_mnx': (contains_mnx, None),
             'contains_coleto': (contains_coleto, None),
             'contains_cavium': (contains_cavium, None) }

        # Call all meaningful actions
        if action.has_key(act):
            handler, param = action.get(act)
            print handler(param)

    except Exception , e:
        raise(e)

