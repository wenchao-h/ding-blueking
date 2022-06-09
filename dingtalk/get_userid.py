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
from common.forms import BaseComponentForm, ListField
from common.constants import API_TYPE_Q
from .toolkit import tools, configs
from common.log import logger

class GetUserid(Component, SetupConfMixin):
    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    class Form(BaseComponentForm):
        ding_app_key = forms.CharField(label="ding app key", required=True)
        ding_app_secret = forms.CharField(label="ding app secret", required=True)
        mobile = ListField(label="dingtalk mobile", required=False)


    def get_dingtalk_access_token(self, params):
        result = self.invoke_other("generic.dingtalk.get_token", kwargs=params)
        logger.info("GetUserid dingtalk_token: %s"%result)
        return  result["data"]["access_token"] if result["result"] else None

    def handle(self):
        access_token = self.get_dingtalk_access_token(params=self.form_data)
        if not access_token:
            self.response.payload = {
                "result": False,
                "message": "invalid access_token, please contact the component developer to handle it."
            }
        else:
            client = tools.DINGClient(self.outgoing.http_client)
            path = "/topapi/v2/user/getbymobile?access_token={}".format(access_token)
            # invalid_mobile = []
            invalid_mobile_msg = []
            valid_userid = []
            for m in self.form_data["mobile"]:
                logger.info("DING mobile number: %s"%m)
                mobile_result = client.post(
                    path=path, 
                    data=json.dumps({
                        "mobile": m
                    })
                )
                logger.info("GetUserid mobile_result: %s"%mobile_result)
                if mobile_result["result"]:
                    userid = mobile_result["data"]["result"]["userid"]
                    valid_userid.append(userid)
                else:
                    invalid_mobile_msg.append("invalid mobile %s, %s"%(m, mobile_result["message"]))
            result = {}
            if invalid_mobile_msg:
                result["_extra_user_error_msg"] = ";".join(invalid_mobile_msg)
                if valid_userid:
                    result.update({
                        "result": True,
                        "data":{
                            "userid": valid_userid
                        }
                    })
                    self.response.payload = result
                else:
                    result.update({
                        "result": False,
                        "message": "no valid userid",
                    })
                    self.response.payload = result
            else:
                self.response.payload = {
                    "result": True,
                    "data": {
                        "userid": valid_userid
                    }
                }