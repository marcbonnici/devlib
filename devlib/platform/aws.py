#    Copyright 2015-2018 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import division
import os
import json
import sys
import tempfile
import time
import pexpect
import requests

try:
    import boto3
except ImportError:
    boto3 = None

from json.decoder import JSONDecodeError

from devlib.exception import HostError, TargetStableError, TargetTransientError
from devlib.host import PACKAGE_BIN_DIRECTORY
from devlib.instrument import (Instrument, InstrumentChannel, MeasurementsCsv,
                               Measurement, CONTINUOUS, INSTANTANEOUS)
from devlib.platform import Platform



class AWSPlatform(Platform):

    def __init__(self, name,  # pylint: disable=too-many-locals
            core_names=None,
            core_clusters=None,
            big_core=None,
            model=None,
            modules=None,
            stop_instance=False,
            aws_credentials='~/.aws/credentials',
            region='us-east-2',
            launch_new=False,
            terminate_instance=False,
            image_id=None,
            instance_type=None,
            key_name=None,
            security_groups=None,
            subnet_id=None
            ):

        super(AWSPlatform, self).__init__(name,
                                        core_names,
                                        core_clusters,
                                        big_core,
                                        model,
                                        modules)
        if boto3 is None:
            raise HostError('boto3 not found, please install')
        self.ec2 = boto3.client('ec2')

        if not os.path.exists(aws_credentials):
            raise ValueError('Cannot find AWS credentials file "{}"'.format(aws_credentials))
        if launch_new:
            if not image_id:
                raise ValueError('Please provide an image_id to launch.')
            if not instance_type:
                raise ValueError('Please provide an instance_type to launch.')
            if not image_id:
                raise ValueError('Please provide an image_id to launch.')

        self.stop_instance = stop_instance

        self.aws_credentials = aws_credentials
        self.launch_new = launch_new
        self.image_id = image_id
        self.instance_type = instance_type
        self.key_name = key_name
        self.security_groups = security_groups
        self.subnet_id = subnet_id
        self.region = region
        self.terminate_instance = terminate_instance

        self.machine_details = {}


        self.ec2_session = boto3.Session(region_name=self.region)
        self.ec2_resource = self.ec2_session.resource('ec2')


    def get_host_public_ip(self):
        host_public_ip = requests.get('https://checkip.amazonaws.com').text.strip()

    def init_target_connection(self, target):
        if self.launch_new:
            self._launch_instance(target)


    def teardown_target_connection(self, target):
        if not self.stop_instance or self.terminate_instance:
            return

        # Do a dryrun first to verify permissions
        try:
            self.ec2.stop_instances(InstanceIds=[self.instance_id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = self.ec2.stop_instances(InstanceIds=[self.instance_id], DryRun=False)
            print(response)
        except ClientError as e:
            print(e)


    def stop_instance(self):
        self.ec2_resource.instances.filter(InstanceIds=self.resource_id).stop()

    def terminate_instance(self):
        self.ec2_resource.instances.filter(InstanceIds=self.resource_id).terminate()

    def create_key_pair(self):
        self.keypair_filepath = 'ec2-keypair.pem'
        # create a file to store the key locally
        with open(self.keypair_filepath,'w') as outfile:
            # call the boto ec2 function to create a key pair
            key_pair = self.ec2.create_key_pair(KeyName='ec2-keypair')
            # capture the key and store it in a file
            KeyPairOut = str(key_pair.key_material)
            outfile.write(KeyPairOut)
        os.chmod(self.keypair_filepath, '0o400')


    def _launch_instance(self, target):
        self.instance = self.ec2_resource.create_instances(
                                                            ImageId=self.image_id,
                                                            MinCount=1,
                                                            MaxCount=1,
                                                            InstanceType=self.instance_type,
                                                            KeyName=self.keypair
                                                        )




        launch_args_string = 'aws ec2 run-instances'
        for k, v in self.args:
            if v:
                launch_args_string += ' --{} {}'.format(k, v)

        # output = ''
        #output = execute('aws ec2 run-instances {}'.format(args)

        try:
            self.machine_details = json.loads(output)
        except JSONDecodeError:
            # Something went wront
            raise TargetStableError('Could not initialise instance due to: {}'.format(output))

        address = self.machine_details['Instances'].get('PublicIDAddress')
        if not address:
            self.logger.debug('Failed to find Pulib IP Address, trying PrivateIP Address')
            address = self.machine_details['Instances'].get('PrivateIPAddress')
        if not address:
            raise TargetStableError('Could not detect instance IP Address')
        target.connection_settings['host'] = address



        self.instance_id = self.machine_details['Instances'].get('InstanceId')
        self.image_id = self.machine_details['Instances'].get('ImageId')
        self.security_group_name = self.machine_details['Instances']['SecurityGroups'].get('GroupName')
        self.security_group_id = self.machine_details['Instances']['SecurityGroups'].get('GroupId')

    #     if target.os == 'android':
    #         self._init_android_target(target)
    #     else:
    #         self._init_linux_target(target)

    # def _init_android_target(self, target):
    #     if target.connection_settings.get('device') is None:
    #         addr = self._get_target_ip_address(target)
    #         target.connection_settings['device'] = addr + ':5555'

    # def _init_linux_target(self, target):
    #     if target.connection_settings.get('host') is None:
    #         addr = self._get_target_ip_address(target)
    #         target.connection_settings['host'] = addr

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None

class AWSInstanceHardReset(HardRestModule):

    name = 'aws-restart'
    # stage = 'early'

    @staticmethod
    def probe(target):
        if not boto3:
            return False
        return isinstance(target.platform, AWSPlatform)

    def __init__(self, target):
        super(AWSInstanceHardReset, self).__init__(target)
        self.ec2 = boto3.client('ec2')

    def __call__(self):
        try:
            self.ec2.reboot_instances(InstanceIds=[self.target.platform.instance_id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise TargetStableError("You don't have permission to reboot instances.")

        try:
            response = self.ec2.reboot_instances(InstanceIds=[self.target.platform.instance_id], DryRun=False)
            self.log.info('AWS instance "{}" rebooting'.format(self.target.platform.instance_id))
            self.log.debug(response)
        except ClientError as e:
            self.log.error('Error rebooting AWS instance "{}"'.format(e))