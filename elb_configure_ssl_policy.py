#!/usr/bin/env python
# Copyright (c) 2013 Eugene Zhuk.
# Use of this source code is governed by the MIT license that can be found
# in the LICENSE file.

"""Configures AWS Elastic Load Balancer (ELB) SSL settings.

A tool to properly configure SSL settings for AWS load balancers. Even
though ELB supports TLS v1.2 and v1.1 protocols and certain recommended
ciphers, they are not enabled by default.

This script creates a new SSL policy with the correct TLS versions and
ciphers enabled and applies it to the default HTTPS listener (port 443)
on the load balancer.

Usage:
    ./elb_configure_ssl_policy <load_balancer>
"""

import optparse
import subprocess
import sys
import time


def create_policy(load_balancer, policy_name):
    """Creates a new SSL policy for the specified load balancer.

    Enables the most recent and more secure TLS v1.2 and v1.1 protocols
    and strong ciphersuite by default. Since AWS ELB does not seem to
    support ECDHE ciphers at this time, forward secrecy is provided by
    the DHE suite.

    Args:
        load_balancer: The name of the load balancer to associate the
            newly created policy with.
        policy_name: The name of the policy to create.

    Returns:
        The status code that is set to 0 on success and 1 otherwise.
    """
    proc = subprocess.Popen(['aws',
        'elb',
        'create-load-balancer-policy',
        '--load-balancer-name', load_balancer,
        '--policy-name', policy_name,
        '--policy-type-name', 'SSLNegotiationPolicyType',
        '--policy-attributes', '['
            '{"AttributeName":"Protocol-SSLv2","AttributeValue":"false"},'
            '{"AttributeName":"Protocol-TLSv1","AttributeValue":"true"},'
            '{"AttributeName":"Protocol-SSLv3","AttributeValue":"true"},'
            '{"AttributeName":"Protocol-TLSv1.1","AttributeValue":"true"},'
            '{"AttributeName":"Protocol-TLSv1.2","AttributeValue":"true"},'
            '{"AttributeName":"DHE-RSA-AES128-GCM-SHA256","AttributeValue":"true"},'
            '{"AttributeName":"DHE-RSA-AES256-GCM-SHA384","AttributeValue":"true"},'
            '{"AttributeName":"AES128-GCM-SHA256","AttributeValue":"true"},'
            '{"AttributeName":"AES256-GCM-SHA384","AttributeValue":"true"},'
            '{"AttributeName":"AES128-SHA","AttributeValue":"true"},'
            '{"AttributeName":"AES256-SHA","AttributeValue":"true"},'
            '{"AttributeName":"DHE-RSA-AES128-SHA","AttributeValue":"true"},'
            '{"AttributeName":"DHE-RSA-AES256-SHA","AttributeValue":"true"},'
            '{"AttributeName":"RC4-MD5","AttributeValue":"false"},'
            '{"AttributeName":"DES-CBC3-SHA","AttributeValue":"false"}'
        ']'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return 1

    return 0

def set_policy(load_balancer, policy_name):
    """Sets the SSL policy.

    Enables a policy for the default HTTPS listener (port 443) on the
    specified load balancer.

    Args:
        load_balancer: The name of the AWS load balancer the policy is
            associated with.
        policy_name: The name of the policy to enable.

    Returns:
        The status code that is set to 0 on success and 1 otherwise.
    """
    proc = subprocess.Popen(['aws',
        'elb',
        'set-load-balancer-policies-of-listener',
        '--load-balancer-name', load_balancer,
        '--load-balancer-port', '443',
        '--policy-names', policy_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if 0 != proc.returncode:
        return 1

    return 0

def main():
    parser = optparse.OptionParser('Usage: %prog <load_balancer> [options]')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        return 1

    load_balancer = args[0]
    policy_name = 'SSLNegotiationPolicy-' +
        load_balancer +
        '-' +
        time.strftime('%Y%m%d%H%M%S', time.gmtime())

    if create_policy(load_balancer, policy_name):
        print '[ERROR] could not create \'{0}\' for \'{1}\''.format(policy_name,
            load_balancer)
        return 1

    if set_policy(load_balancer, policy_name):
        print '[ERROR] could not set \'{0}\' for \'{1}\''.format(policy_name,
            load_balancer)
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())