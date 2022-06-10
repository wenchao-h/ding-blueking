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

from components.component import Component, SetupConfMixin
from common.forms import BaseComponentForm, ListField
from common.constants import API_TYPE_Q
from .toolkit import tools, configs
from common.log import logger

class SendMessageByUserid(Component, SetupConfMixin):
    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    class Form(BaseComponentForm):
        ding_app_key = forms.CharField(label="ding app key", required=True)
        ding_app_secret = forms.CharField(label="ding app secret", required=True)
        userid = ListField(label="dingtalk userid", required=True)
        msg_key = forms.CharField(label="message key type", required=True)
        msg_param = forms.CharField(label="message param", required=True)

    def get_dingtalk_access_token(self, params):
        result = self.invoke_other("generic.dingtalk.get_token", kwargs=params)
        logger.info("SendMessageByUserid dingtalk_token: %s"%result)
        return  result["data"]["access_token"] if result["result"] else None

    def handle(self):
        access_token = self.get_dingtalk_access_token(params=self.form_data)
        if not access_token:
            self.response.payload = {
                "result": False,
                "message": "invalid access_token, please contact the component developer to handle it."
            }
        else:
            data = {
                "robotCode": self.form_data["ding_app_key"],
                "userIds": self.form_data["userid"],
                "msgKey": "sampleText" if self.form_data.get("msg_key", "text") == "text" else "sampleMarkdown",
                "msgParam": self.form_data["msg_param"],
            }
            client = tools.DINGClient(self.outgoing.http_client)
            path = "/v1.0/robot/oToMessages/batchSend"
            headers = {
                "x-acs-dingtalk-access-token": access_token,
                "Content-Type": "application/json"
            }
            host = "https://api.dingtalk.com",
            logger.info("SendMessageByUserid data: %s"%data)
            result = client.post(path=path, data=json.dumps(data), headers=headers, host=host)
            logger.info("SendMessageByUserid: %s"%result)
            if result["result"]:
                err_msg = ""
                if ("invalidStaffIdList" in result["data"]) and result["data"]["invalidStaffIdList"]:
                    err_msg += ",".join(result["data"]["invalidStaffIdList"]) + " are invalid userids; "
                if ("flowControlledStaffIdList" in result["data"]) and result["data"]["flowControlledStaffIdList"]:
                    err_msg += ",".join(result["data"]["flowControlledStaffIdList"]) + " are under flow controlled;"
                if err_msg:
                    self.response.payload = {
                        "result": False,
                        "message": err_msg
                    }
                else:
                    self.response.payload = result
            else:
                self.response.payload = result