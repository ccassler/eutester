#!/usr/bin/python

import time
import threading
from eucaops import Eucaops
from eutester.eutestcase import EutesterTestCase
import os
import random
import string


class LogTracking(EutesterTestCase):
    def __init__(self):
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

    def clean_method(self):
        self.tester.cleanup_artifacts()

    def MyTest(self, emi=None):
        """
        Test features of the Log Tracking feature
        """
        for machine in self.tester.get_component_machines("clc"):
            #tester = Eucaops(credpath="/home/ccassler/.euca")
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
            self.tester.run_image(**self.run_instance_params)
            instanceid = self.tester.get_instances("running")
            requestid = machine.sys("source /root/eucarc && /root/logtrackers/euca-req-history eucalyptus -l30 | grep RunInstance | grep RunInstance | awk '{ print $8 }'")
            instanceid = str(instanceid).translate(string.maketrans('', ''), "[']")
            instanceid = str(instanceid).replace('Instance:', '')
            requestid = str(requestid).translate(string.maketrans('', ''), "[']")
            logcheck = machine.sys("grep " + requestid + " /var/log/eucalyptus/*tracking.log | grep -c " + instanceid)
            logcheck = str(logcheck).translate(string.maketrans('', ''), "[']")
            trackcheck = machine.sys("source /root/eucarc && /root/logtrackers/euca-req-track --ssh " + requestid + " | grep -v == | grep -v LOG | grep -v info: | wc -l")
            trackcheck = str(trackcheck).translate(string.maketrans('', ''), "[']")
            print "Instance: " + instanceid
            print "RequestID: " + requestid
            print "Logcheck: " + logcheck
            print "TrackCheck: " + trackcheck


if __name__ == "__main__":
    testcase = LogTracking()
    ### Use the list of tests passed from config/command line to determine what subset of tests to run
    ### or use a predefined list
    list = testcase.args.tests or ["MyTest"]

    ### Convert test suite methods to EutesterUnitTest objects
    unit_list = [ ]
    for test in list:
        unit_list.append( testcase.create_testunit_by_name(test) )

    ### Run the EutesterUnitTest objects
    result = testcase.run_test_case_list(unit_list,clean_on_exit=True)
    exit(result)