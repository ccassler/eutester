#!/usr/bin/python

import time
import threading
from eucaops import Eucaops
from eutester.eutestcase import EutesterTestCase
import os
import random
import string

class LogTracking(EutesterTestCase):
    def __init__(self, emi=None):
        self.setuptestcase()
        self.setup_parser()
        self.get_args()
        # Setup basic eutester object
 #       self.tester = Eucaops( config_file=self.args.config,password=self.args.password)
        if self.args.region:
            self.tester = EC2ops(credpath=self.args.credpath, region=self.args.region)
        else:
            self.tester = Eucaops(config_file=self.args.config_file,
                                  password=self.args.password,
                                  credpath=self.args.credpath)
        self.instance_timeout = 600
        self.group = self.tester.add_group(group_name="group-" + str(time.time()))
        self.tester.authorize_group_by_name(group_name=self.group.name)
        self.tester.authorize_group_by_name(group_name=self.group.name, port=-1, protocol="icmp")
        ### Generate a keypair for the instance
        self.keypair = self.tester.add_keypair("keypair-" + str(time.time()))
        self.keypath = '%s/%s.pem' % (os.curdir, self.keypair.name)
        if emi:
            self.image = self.tester.get_emi(emi=self.args.emi)
        else:
            self.image = self.tester.get_emi(root_device_type="instance-store", basic_image=True)
        self.address = None
        self.volume = None
        self.private_addressing = False
        if not self.args.zone:
            zones = self.tester.ec2.get_all_zones()
            self.zone = random.choice(zones).name
        else:
            self.zone = self.args.zone
        self.reservation = None
        self.reservation_lock = threading.Lock()
        self.run_instance_params = {'image': self.image,
                                    'user_data': self.args.user_data,
                                    'username': self.args.instance_user,
                                    'keypair': self.keypair.name,
                                    'group': self.group.name,
                                    'zone': self.zone,
                                    'return_reservation': True,
                                    'timeout': self.instance_timeout}
        self.managed_network = True
        self.instance = self.tester.run_image(**self.run_instance_params)
        self.instanceid = self.instance.instances
        self.instanceid = str(self.instanceid[0])
        self.instanceid = self.instanceid.replace('Instance:', '')


    def clean_method(self):
        self.tester.cleanup_artifacts()

    def Functional(self):
        """
        Test functionality of the Log Tracking feature
        """
        reqhistory = "/usr/bin/euca-req-history"
        reqtrack = "/usr/bin/euca-req-track"
        for machine in self.tester.get_component_machines("clc"):
            machine.sys("wget https://raw.githubusercontent.com/eucalyptus/logtrackers/master/euca-req-history -O " + reqhistory + " && chmod 755 " + reqhistory)
            machine.sys("wget https://raw.githubusercontent.com/eucalyptus/logtrackers/master/euca-req-track -O " + reqtrack + " && chmod 755 " + reqtrack)
            check_history_command = machine.sys(reqhistory + " 2>&1 > /dev/null | wc -l")
            check_track_command = machine.sys(reqtrack + " 2>&1 > /dev/null | wc -l")
            if int(check_history_command[0]) > 0:
                raise Exception("Log tracking command: " + reqhistory + " not found or not working properly.  TEST FAILED!")
            if int(check_track_command[0]) > 0:
                raise Exception("Log tracking command: " + reqtrack + " not found or not working properly.  TEST FAILED!")
            requestid = machine.sys("source /root/eucarc && " + reqhistory + " eucalyptus -n RunInstance | grep -v DATE | grep -v \- | head -1 | awk '{ print $9 }'")
            requestid = str(requestid[0])
            logcheck = machine.sys("grep " + requestid + " /var/log/eucalyptus/*tracking.log | grep -c " + self.instanceid)
            logcheck = int(logcheck[0])
            trackcheck = machine.sys("source /root/eucarc && " + reqtrack + " --ssh " + requestid + " | grep -v == | grep -v LOG | grep -v info: | wc -l")
            trackcheck = int(trackcheck[0])
            if not self.instanceid:
                raise Exception("Instance not found: " + self.instanceid + " Test FAILED!")
            if not requestid:
                raise Exception("RequestID not found using euca-req-history: " + requestid + " Test FAILED!")
            if logcheck == 0:
                raise Exception("RequestID, InstanceID " + requestid + " and " + self.instanceid + " were not found in tracking log files.  Test FAILED!")
            if trackcheck == 0:
                raise Exception("RequestID " + requestid + " not found using euca-req-track.  Test FAILED!")
            print "instanceid: " + self.instanceid
            print "requestid: " + requestid
            print "logcheck: " + str(logcheck)
            print "trackcheck: " + str(trackcheck)


if __name__ == "__main__":
    testcase = LogTracking()
    ### Use the list of tests passed from config/command line to determine what subset of tests to run
    ### or use a predefined list
    list = testcase.args.tests or ["Functional"]

    ### Convert test suite methods to EutesterUnitTest objects
    unit_list = [ ]
    for test in list:
        unit_list.append( testcase.create_testunit_by_name(test) )

    ### Run the EutesterUnitTest objects
    result = testcase.run_test_case_list(unit_list,clean_on_exit=True)
    exit(result)