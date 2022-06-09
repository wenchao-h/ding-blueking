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


from common.constants import API_TYPE_OP
from components.component import Component, SetupConfMixin
from .toolkit import configs, tools
from common.log import logger

class SendMessage(Component, SetupConfMixin):
    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    def handle(self):
        request_data = self.request.kwargs
        bots_info = request_data.get("bots_info")
        if not bots_info:
            self.response.payload = {
                "result": False,
                "message": u"dingbot message sending failed, there is no valid user",
            }
        else:
            msg_key = request_data.get("msg_key")
            msg_data = {
                "msgtype": "text",
            }
            if msg_key == "text":
                msg_data.update({                
                    "text": {
                        "content": request_data.get("content")
                }})
            else:
                msg_data.update({
                    "msgtype": "markdown",
                    "markdown": {
                        "title": request_data.get("title"),
                        "text": request_data.get("content")
                    }
                })
            logger.info("dingbot.SendMessage data: %s"%msg_data)
            ding_client = tools.DINGClient(self.outgoing.http_client)
            send_errors = []
            for bot in bots_info:
                timestamp, sign = tools.gen_timestamp_sign(bot["sign"])
                path = "/robot/send?access_token={}&timestamp={}&sign={}".format(bot["token"], timestamp, sign)
                result = ding_client.post(path, data=json.dumps(msg_data, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"})
                logger.info("dingbot.send_message result for %s: %s"%(bot, result))
                if not result["result"]:
                    err = "%s send failed,"%bot["username"] + result["message"]
                    send_errors.append(err) 
            if send_errors:
                data = {
                    "result": False,
                    "message": ";".join(send_errors)
                }
            else:
                data = {"result": True, "message": u"dingbot message sending succeeded"}
            self.response.payload = data

