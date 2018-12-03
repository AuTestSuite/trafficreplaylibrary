'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
'''

import json
import random
import os
import uuid
from argparse import ArgumentParser

# made in accordance to replay_format.json


def genResps():
    pass

# TODO: do http AND https and or mixed


def genReqs(scheme):
    REQ_TEMPLATE = {
        'version': '1.1',
        'scheme': scheme,
        'method': 'GET',
        'url': '/{0}',
        'headers': {
            'fields': [
                ['Host', 'thiswebsitedoesntexist.com.org.edu.com'],
                ['User-Agent', 'Traffic-Replay client'],
                ['Accept', '*/*']
            ]
        }
    }

    url_junk = uuid.uuid4().hex

    c_req = REQ_TEMPLATE
    c_req['url'] = c_req['url'].format(url_junk)

    p_req = REQ_TEMPLATE
    p_req['url'] = p_req['url'].format(url_junk)

    return (c_req, p_req)


def genResps():
    RESP_TEMPLATE = {
        'status': 200,
        'reason': "OK",
        'content': {
            'size': None
        },
        'headers': {
            'fields': [
                ["Connection", "keep-alive"],
                ["Content-Type", "text/html; charset=utf-8"],
                ["Content-Length", "{0}"],
                ["Last-Modified", "Fri, 06 Apr 2018 14:38:27 GMT"]
            ]
        }
    }

    content_size = random.randint(1, 20)

    s_resp = RESP_TEMPLATE
    s_resp['content']['size'] = content_size
    # I'm sorry god you have to see this nasty thing below
    s_resp['headers']['fields'][2][1] = s_resp['headers']['fields'][2][1].format(
        content_size)

    p_resp = RESP_TEMPLATE
    p_resp['content']['size'] = content_size
    # I'm sorry god you have to see this nasty thing below
    p_resp['headers']['fields'][2][1] = p_resp['headers']['fields'][2][1].format(
        content_size)

    return (s_resp, p_resp)


def genTxn(scheme):
    # ignoring start-time

    txn = {}

    txn['uuid'] = uuid.uuid4().hex

    c_req, p_req = genReqs(scheme)
    txn['client-request'] = c_req
    txn['proxy-request'] = p_req

    s_resp, p_resp = genResps()
    txn['server-response'] = s_resp
    txn['proxy-response'] = p_resp

    return txn


def genSession(scheme):
    # ignoring protocol

    sesh = {'connect-time': None, 'transactions': []}

    # 1 ~ 20 transactions per session
    for i in range(random.randint(1, 20)):
        sesh['connect-time'] = random.randint(1, 1527269900)
        sesh['transactions'].append(genTxn(scheme))

    return sesh


def generate(output_dir, num_sessions, scheme):
    count = 0

    while num_sessions > 0:
        count += 1
        sessions_in_file = random.randint(1, num_sessions)

        aFile = {'meta': {'version': '1.1'}, 'sessions': []}

        for _ in range(0, sessions_in_file):
            aFile['sessions'].append(genSession(scheme))

        sessionfile = open(os.path.join(
            output_dir, 'session_{0}.json'.format(count)), 'w')
        # if this fails just let it fail straight, not bothering to catch
        json.dump(aFile, sessionfile, indent=2)

        num_sessions -= sessions_in_file


def main():
    parser = ArgumentParser()

    parser.add_argument('--number', '-n',
                        required=True,
                        type=int,
                        help='number of sessions to generate')

    parser.add_argument('--scheme', '-s',
                        type=str,
                        default='http',
                        help='scheme type to generate. Supported: http/https')

    parser.add_argument('--dir', '-d',
                        required=True,
                        type=str,
                        help='output directory')

    args = parser.parse_args()

    generate(args.dir, args.number, args.scheme)


if __name__ == '__main__':
    main()
