#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: boto3 
short_description: Polls the status of an AWS resource and suspend execution until the AWS resource reaches the state that the waiter is polling for.
description:
    - This is a generic module to make AWS "wait" API calls using boto3 client instead of using the CLI.
    - This module will always yield an unchanged state.
version_added: 2.2
requirements:
    - boto3
options:
  service:
    description:
      - The name of the service (ie. 's3', 'ec2', 'rds', 'emr', etc.)
    required: true
    default: null 
    aliases: ['name']
  until:
    description:
      - Waiter name. See boto3 documentation.
    required: true
    default: null
    aliases: []
  parameters:
    description:
      - A hash/dictionary representing operations parameters. See boto3 documentation.
    required: false
    default: null
    aliases: []
  delay:
    description:
      - Seconds between each attempt.
    required: false
    default: null
    aliases: []
  max_attempts:
    description:
      - Maximum number of polling attempts before giving up.
    required: false
    default: null
    aliases: []
  region:
    description:
      - AWS region.
    required: false
    default: present
    aliases: []
  aws_access_key:
    description:
      - AWS access key.
    required: false
    default: null
    aliases: ['ec2_access_key', 'access_key']
  aws_secret_key:
    description:
      - AWS secret key.
    required: false
    default: null
    aliases: ['ec2_secret_key', 'secret_key']
author: "Eric Citaire"
'''

EXAMPLES = '''
- name: Wait for EMR Cluster to be running
  boto3_wait:
    name: emr
    region: us-east-1
    until: cluster_running
    parameters:
      ClusterId: j-XXXXXXXXXXXXXXX
    delay: 30
    max_attempts: 50
'''

RETURN = '''
'''

from time import sleep
try:
  import boto3
  from botocore.exceptions import *
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

def main():
  module = AnsibleModule(
    argument_spec = dict(
      service=dict(required=True, type='str', aliases=['name']),
      until=dict(required=True, type='str'),
      parameters=dict(default={}, type='dict'),
      delay=dict(default=None, type='int'),
      max_attempts=dict(default=None, type='int'),
      region=dict(type='str'),
      aws_access_key=dict(type='str', aliases=['ec2_access_key', 'access_key']),
      aws_secret_key=dict(type='str', aliases=['ec2_secret_key', 'secret_key'])
    ),
    supports_check_mode=False
  )

  if not HAS_BOTO3:
    module.fail_json(msg='boto3 is required for this module')

  service = module.params.get('service')
  until = module.params.get('until')
  parameters = module.params.get('parameters')
  delay = module.params.get('delay')
  max_attempts = module.params.get('max_attempts')
  region = module.params.get('region')
  aws_access_key = module.params.get('aws_access_key')
  aws_secret_key = module.params.get('aws_secret_key')

  try:
    client = boto3.client(service, region_name=region, aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    if until not in client.waiter_names:
      module.fail_json(msg='Waiter "{}" does not exist in "{}" client.'.format(until, service))
    waiter = client.get_waiter(until)
    if delay is not None:
      waiter.config.delay = delay
    if max_attempts is not None:
      waiter.config.max_attempts = max_attempts
    response = waiter.wait(**parameters)
  except Exception as e:
    module.fail_json(msg=e.message)
  
  module.exit_json(changed=False)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
  main()