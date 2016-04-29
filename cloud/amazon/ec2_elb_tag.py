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
module: ec2_elb_tag 
short_description: create and remove tag(s) to ELBs.
description:
    - Creates, removes and lists tags from any ELB. The ELB is referenced by its name.  This module has a dependency on boto3.
version_added: 2.2
options:
  name:
    description:
      - The name of the ELB
    required: true
    default: null 
    aliases: []
  state:
    description:
      - Whether the tags should be present or absent on the ELB. Use list to interrogate the tags of an ELB.
    required: false
    default: present
    choices: ['present', 'absent', 'list']
    aliases: []
  aws_access_key:
    description:
      - AWS access key.
    required: false
    default: present
    aliases: ['ec2_access_key', 'access_key']
  aws_secret_key:
    description:
      - AWS secret key.
    required: false
    default: present
    aliases: ['ec2_secret_key', 'secret_key']
  tags:
    description:
      - A hash/dictionary of tags to add to the resource; '{"key":"value"}' and '{"key":"value","key":"value"}'
    required: true
    default: null
    aliases: []
author: "Eric Citaire"
'''

EXAMPLES = '''
- name: list tags on ELB
  ec2_lb_tag: 
    name: my-lb
    state: list
  register: result

- name: remove tags on ELB
  ec2_lb_tag: 
    name: my-lb
    state: absent
    tags: "{{ result.tags }}"

- name: add tags on ELB
  ec2_lb_tag: 
    name: my-lb
    tags:
      Name: uberlb
      env: prod
'''

RETURN = '''
tags:
    description: ELB tags, after the changes are made.
    returned: success
    type: dict
    sample: {"Name": "uberlb", "foo": "bar", "env": "prod"}
'''

try:
  import boto3
  from botocore.exceptions import NoRegionError, ClientError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

def get_lb_tags(module, elb, name):
  try:
    response = elb.describe_tags(LoadBalancerNames=[name])
  except ClientError as e:
    module.fail_json(msg=e.response['Error']['Message'])

  return dict((tag['Key'], tag['Value']) for tag in response['TagDescriptions'][0]['Tags'])

def main():
  module = AnsibleModule(
    argument_spec = dict(
      state=dict(default='present', choices=['present', 'absent', 'list'], type='str'),
      name=dict(required=True, type='str'),
      region=dict(type='str'),
      aws_access_key=dict(type='str', aliases=['ec2_access_key', 'access_key']),
      aws_secret_key=dict(type='str', aliases=['ec2_secret_key', 'secret_key']),
      tags=dict(type='dict')
    ),
    supports_check_mode=True
  )

  if not HAS_BOTO3:
    module.fail_json(msg='boto3 is required for this module')

  changed = False

  name = module.params.get('name')
  state = module.params.get('state')
  region = module.params.get('region')
  aws_access_key = module.params.get('aws_access_key')
  aws_secret_key = module.params.get('aws_secret_key')
  tags = module.params.get('tags')

  try:
    elb = boto3.client('elb', region_name=region, aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
  except NoRegionError:
    module.fail_json(msg='You must specify a region. You can also configure your region by running "aws configure".')

  actual_tags = get_lb_tags(module, elb, name)

  if state == 'present':
    tag_keys_to_add = [ key for key in tags if key not in actual_tags or actual_tags[key] != str(tags[key]) ]
    if tag_keys_to_add:
      tags_to_add = [ { 'Key': key, 'Value': str(tags[key]) } for key in tag_keys_to_add ]
      if not module.check_mode:
        elb.add_tags(LoadBalancerNames=[name], Tags=tags_to_add)
        actual_tags = get_lb_tags(module, elb, name)
      else:
        actual_tags.update(tags_to_add)
      changed = True

  elif state == 'absent':
    tag_keys_to_remove = [ key for key in actual_tags if key in tags and actual_tags[key] == str(tags[key]) ]
    if tag_keys_to_remove:
      if not module.check_mode:
        elb.remove_tags(LoadBalancerNames=[name], Tags=[ { 'Key': key } for key in tag_keys_to_remove ])
        actual_tags = get_lb_tags(module, elb, name)
      else:
        actual_tags = [ { 'Key': key, 'Value': str(actual_tags[key]) } for key in actual_tags if key not in tag_keys_to_remove ]
      changed = True

  module.exit_json(changed=changed, tags=actual_tags)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
  main()
