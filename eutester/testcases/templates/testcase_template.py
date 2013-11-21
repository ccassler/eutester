#!/usr/bin/python
from eutester.eutestcase import EutesterTestCase

class BaseEc2Testcase(EutesterTestCase):
    def __init__(self, args= None):
        self.admin = super(EutesterTestCase, self).__init__(args)
        self.user = self.admin.gimme_a_user()
        self.user.ec2.run_image
        self.keypair = self.admin.ec2.add_keypair()
        self.group = self.admin.add_group()
        self.image = self.args.emi
        if not self.image:
            self.image = self.admin.get_emi(root_device_type="instance-store")

    def clean_method(self):
        self.admin.cleanup_artifcats()


class MyTest(BaseEc2Testcase):
    def __init__(self):
        super(EutesterTestCase, self).__init__()

    def MyTest(self):
        self.admin.ec2.run_instance()
        self.admin.ec2.reboot_instances

if __name__ == "__main__":
    testcase = MyTest()
    list = testcase.args.tests or ["MyTest"]
    result = testcase.run(list)
    exit(result)