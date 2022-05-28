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

from django import forms

from components.component import Component, SetupConfMixin
from common.forms import BaseComponentForm, ListField
from common.constants import API_TYPE_OP
from .toolkit import configs, tools
from common.log import logger


class SendDingtalk(Component, SetupConfMixin):
    """
    apiLabel {{ _("发送钉钉单聊消息") }}
    apiMethod POST

    ### {{ _("功能描述") }}

    {{ _("通过企业内部机器人向用户发送单聊消息") }}

    ### {{ _("请求参数") }}

    {{ common_args_desc }}

    #### {{ _("接口参数") }}

    | {{ _("字段") }}               |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |--------------------|------------|--------|------------|
    | userid             |  string    | {{ _("否") }}     | {{ _("钉钉接收者，钉钉用户的userid，多个以逗号分隔, 优先级比mobile、receiver_username高") }} |
    | mobile             |  string    | {{ _("否") }}     | {{ _("钉钉接收者手机号，多个以逗号分隔，优先级比receiver_username高") }} |
    | receiver__username |  string    | {{ _("否") }}     | {{ _("钉钉接收者，包含用户名，用户需在蓝鲸平台注册，多个以逗号分隔，优先级最低") }} |
    | msg_key            |  string    | {{ _("否") }}     | {{ _("消息格式，sampleText文本消息/sampleMarkdown markdown消息，默认sampleText") }}
    | title              |  string    | {{ _("是") }}     | {{ _("消息标题") }} |
    | content            |  string    | {{ _("是") }}     | {{ _("消息内容") }} |
    | ding_app_key       |  string    | {{ _("否") }}     | {{ _("钉钉内部机器人app key") }} |
    | ding_app_secret    |  string    | {{ _("否") }}     | {{ _("钉钉内部机器人app secret") }} |

    ### {{ _("请求参数示例") }}

    ```python
        {
            "bk_app_code": "xxx",
            "bk_app_secret": "xxx",
            "bk_username": "xxx",
            "userid":"xxx,xxx", # 优先级最高
            "mobile": "xxx,xxx" # 优先级次高
            "receiver__username": "xxx,xxx",  # 蓝鲸用户名，优先级最低
            "msg_key": "xxx",  # text 文本消息/markdown markdown消息
            "title": "xx" # 标题
            "content": "xx" # 内容
        }
    ```

    ### {{ _("返回结果示例") }}

    ```python
        {
            "result": true,
            "code": "00",
            "message": "OK",
        }
    ```
    """  # noqa

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP
    contact_way = "phone"

    class Form(BaseComponentForm):
        userid = ListField(label="dingtalk userid", required=False)
        mobile = ListField(label="dingtalk mobile", required=False)
        receiver__username = ListField(label="dingtalk receiver", required=False)
        msg_key = forms.CharField(label="message key type", required=True)
        title = forms.CharField(label="message title", required=True)
        content = forms.CharField(label="message content", required=True)
        ding_app_key = forms.CharField(label="app key", required=False)
        ding_app_secret = forms.CharField(label="app secret", required=False) 

        def clean(self):
            data = self.cleaned_data

            if not (data["userid"] or data["mobile"] or data["receiver__username"]):
                raise forms.ValidationError(
                    "dingtalk receiver [userid, mobile, receiver__username] shall not be empty at the same time"
                )
            receiver_type = "userid"
            receiver = None
            if data["userid"]:
                receiver = data["userid"]
            else:
                if data["mobile"]:
                    receiver_type = "mobile"
                    receiver = data["mobile"]
                else:
                    if data["receiver__username"]:
                        receiver_type = "mobile"
                        # 根据蓝鲸平台用户数据，将用户名转换为手机号码
                        user_data = tools.get_receiver_with_username(
                            receiver__username=data["receiver__username"],
                            contact_way=SendDingtalk.contact_way,
                        )
                        receiver = [user["telephone"] for user in user_data["receiver"]]
                        logger.info("SendDingtalk receiver: ", receiver)
                        if user_data.get("_extra_user_error_msg"):
                            return {
                                "receiver_type": receiver_type,
                                "receiver": receiver,
                                "msg_key": data.get("msg_key", "sampleText"),
                                "title": data["title"],
                                "content": data["content"],
                                "_extra_user_error_msg": user_data.get("_extra_user_error_msg")
                            }

            return {
                "receiver_type": receiver_type,
                "receiver": receiver,
                "msg_key": data["msg_key"],
                "title": data["title"],
                "content": data["content"],
            }


    def handle(self):
        logger.info("dingtalk.appkey_in_db: ", getattr(self, "ding_app_key"))
        ding_app_key = (
            self.request.kwargs.get("ding_app_key")
            or getattr(self, "ding_app_key")
            or getattr(configs, "ding_app_key", "")
        )
        ding_app_secret = (
            self.request.kwargs.get("ding_app_secret")
            or getattr(self, "ding_app_secret")
            or getattr(configs, "ding_app_secret", "")
        )

        data = self.form_data
        data.update(
            {
                "ding_app_key": ding_app_key,
                "ding_app_secret": ding_app_secret,
                "receiver_type": data["receiver_type"],
                "receiver": data["receiver"],
                "msg_key": data["msg_key"],
                "title": data["title"],
                "content": data["content"],
            }
        )
        result = self.invoke_other("generic.dingtalk.send_message", kwargs=data)
     
        if result["result"] and data.get("_extra_user_error_msg"):
            result = {
                "result": False,
                "message": u"Some users failed to send wechat message. %s" % data["_extra_user_error_msg"],
            }
        logger.info("send_dingtalk result: ", result)
        self.response.payload = result
