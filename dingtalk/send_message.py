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

from common.constants import API_TYPE_OP
from components.component import Component, SetupConfMixin
from common.forms import BaseComponentForm, ListField
from .toolkit import configs
from common.log import logger


class SendMessage(Component, SetupConfMixin):
    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    class Form(BaseComponentForm):
        ding_app_key = forms.CharField(label="app key", required=True)
        ding_app_secret = forms.CharField(label="app secret", required=True)
        receiver_type = forms.CharField(label="receiver type", required=True)
        receiver = ListField(label="receiver", required=True)
        msg_key = forms.CharField(label="msg key", required=True)
        title = forms.CharField(label="message title", required=False)
        content = forms.CharField(label="content", required=True)

    def get_dingtalk_access_token(self, params):
        result = self.invoke_other("generic.dingtalk.get_token", kwargs=params)
        logger.info("SendMessage dingtalk_token: %s"%result)
        return  result["data"]["access_token"] if result["result"] else None

    def handle(self):
        access_token = self.get_dingtalk_access_token(params=self.form_data)
        if not access_token:
            self.response.payload = {
                "result": False,
                "message": "invalid access_token, please contact the component developer to handle it."
            }
        else:
            msg_param = ""
            if self.form_data["msg_key"] == "text":
                msg_param = json.dumps({
                    "content": self.form_data["content"]
                })
            else:
                msg_param = json.dumps({
                    "title": self.form_data["title"],
                    "text": self.form_data["content"]
                })
            data = {
                "ding_app_key": self.form_data["ding_app_key"],
                "ding_app_secret": self.form_data["ding_app_secret"],
                "userid": self.form_data["receiver"],
                "msg_key": self.form_data["msg_key"],
                "msg_param": msg_param,
            }
            userid = []
            result={}
            
            if self.form_data["receiver_type"] == "mobile":
                mobile_data = {
                    "ding_app_key": self.form_data["ding_app_key"],
                    "ding_app_secret": self.form_data["ding_app_secret"],
                    "mobile": self.form_data["receiver"],
                }
                logger.info("dingtalk.sendmessage mobile_data: %s"%mobile_data)
                userid_result = self.invoke_other("generic.dingtalk.get_userid", kwargs=mobile_data)
                if userid_result["result"]:
                    userid = userid_result["data"]["userid"]
                    data.update({"userid": userid})
                    logger.info("dingtalk.send_message_by_userid data: %s"%data)
                    result = self.invoke_other("generic.dingtalk.send_message_by_userid", kwargs=data)
                    if result["result"] and userid_result.get("_extra_user_error_msg"):
                        result = {
                            "result": False,
                            "message": userid_result.get("_extra_user_error_msg")
                        }
                else:
                    result = userid_result
            else:
                logger.info("dingtalk.send_message_by_userid data: %s"%data)
                result = self.invoke_other("generic.dingtalk.send_message_by_userid", kwargs=data)
            self.response.payload = result



