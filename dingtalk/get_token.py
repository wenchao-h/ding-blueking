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
import json
from django import forms
from django.core.cache import cache

from components.component import Component, SetupConfMixin
from common.forms import BaseComponentForm
from common.constants import API_TYPE_Q
from .toolkit import tools, configs
from common.log import logger

class GetToken(Component, SetupConfMixin):
    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    class Form(BaseComponentForm):
        ding_app_key = forms.CharField(label="app key", required=True)
        ding_app_secret = forms.CharField(label="app secret", required=True)

    def handle(self):
        access_token = cache.get(self.form_data["ding_app_key"], "")
        if access_token:
            self.response.payload = {"result": True, "data": {"access_token": access_token}}
        else:
            client = tools.DINGClient(self.outgoing.http_client)
            # path="/gettoken?appkey={}&appsecret={}".format(self.form_data["appkey"], self.form_data["appsecret"])
            result = client.get(path="/gettoken", params={
                "appkey": self.form_data["ding_app_key"],
                "appsecret": self.form_data["ding_app_secret"]
            })

            logger.info("GetToken result: %s"%result)
            if result["result"]:
                token_data = result["data"]
                access_token = token_data["access_token"]
                expire_in = token_data["expires_in"]
                if expire_in > 60:
                    cache.set(self.form_data["ding_app_key"], access_token, expire_in-60)
                self.response.payload = {"result": True, "data": {"access_token": access_token}}
            else:
                self.response.payload = result
