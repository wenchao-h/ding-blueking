# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS
Community Edition) available.
Copyright (C) 2017-2018 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""


SYSTEM_DOC_CATEGORY = [
    # {
    #     'label': 'Test-Catg',
    #     'priority': 100,
    #     'systems': ['TEST']    # system_name
    # },
]


SYSTEMS = [
    # {
    #     'name': 'TEST',
    #     'label': 'My Test',
    #     'remark': 'My Test',
    #     'interface_admin': 'admin',
    #     'execute_timeout': 30,
    #     'query_timeout': 30,
    # },
]


CHANNELS = [
    # TEST
    # ('/test/healthz/', {'comp_codename': 'generic.test.healthz'}),
    (
        '/cmsi/send_dingtalk/',
        {
            "comp_codename": "generic.cmsi.send_dingtalk",
            "comp_conf_to_db": [
                ("ding_app_key", ""),
                ("ding_app_secret", ""),
            ],
        }
    ),
    (
        '/cmsi/send_dingbot/',
        {
            "comp_codename": "generic.cmsi.send_dingbot",
            "comp_conf_to_db": [
                ("token_field", "qq"),
                ("sign_field", "wx_userid")
            ]
        }
    ),
    (
        '/cmsi/send_ding/',
        {
            "comp_codename": "generic.cmsi.send_ding",
        }
    )
]


# Self-service components
BUFFET_COMPONENTS = [
    # {
    #     # Register config
    #     'name': 'get template list',
    #     'system_name': 'TEST',
    #     'registed_http_method': 'GET',
    #     'registed_path': '/test/heartbeat/',
    #     'type': 2,  # 2 is query, 1 is operate
    #     # Before request
    #     'extra_headers': {
    #         'Token': '1234567890',
    #     },
    #     # Request target
    #     'dest_url': 'http://domain.test.com/test/heartbeat/',
    #     'dest_http_method': 'POST',
    #     'favor_post_ctype': 'json',   # json / form
    #     'timeout_time': 10,
    # },
]
