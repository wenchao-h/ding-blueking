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


class SendDingbot(Component, SetupConfMixin):
    """
    apiLabel {{ _("发送钉钉群消息") }}
    apiMethod POST

    ### {{ _("功能描述") }}

    {{ _("发送通过自定义群机器人发送消息") }}

    ### {{ _("请求参数") }}

    {{ common_args_desc }}

    #### {{ _("接口参数") }}

    | {{ _("字段") }}               |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |--------------------|------------|--------|------------|
    | receiver__username |  string    | {{ _("是") }}     | {{ _("钉钉群助手名称，该名称需在蓝鲸平台注册，多个以逗号分隔") }} |
    | msg_key            |  string    | {{ _("否") }}     | {{ _("消息格式，text 文本消息/markdown markdown消息，默认text") }}
    | title              |  string    | {{ _("是") }}     | {{ _("消息标题") }} |
    | content            |  string    | {{ _("是") }}     | {{ _("消息内容") }}|


    ### {{ _("请求参数示例") }}

    ```python
    {
        "bk_app_code": "xxx",
        "bk_app_secret": "xxx",
        "bk_username": "xxx",
        "receiver__username": "xxx,xxx",  # 机器人在用户管理注册的用户名
        "msg_key": "xxx",  # sampleText文本消息/sampleMarkdown markdown消息
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

    class Form(BaseComponentForm):
        receiver__username = ListField(label="dingbot receiver usernames", required=True)
        title = forms.CharField(label="message title", required=True)
        content = forms.CharField(label="message content", required=True)
        msg_key = forms.CharField(label="msg key", required=True)

        def clean(self):
            data = self.cleaned_data
            return {
                "receiver__username": data["receiver__username"],
                "title": data["title"],
                "content": data["content"],
                "msg_key": data.get("msg_key", "text"),
            }


    def handle(self):
        user_data = tools.get_token_sign_with_username(
            username_list=self.form_data["receiver__username"],
            token_field=(getattr(self, "token_field", "") or getattr(configs, "token_field", "extras__ddNumber")),
            sign_field=(getattr(self, "sign_field", "") or getattr(configs, "sign_field", "wx_userid"))
        )
        data = {
            "bots_info": user_data["bots_info"],
            "title": self.form_data["title"],
            "content": self.form_data["content"],
            "msg_key": self.form_data["msg_key"],
        }
        logger.info("send_dingbot data: %s"%data)
        result = self.invoke_other("generic.dingbot.send_message", kwargs=data)

        if result["result"] and data.get("_extra_user_error_msg"):
            result = {
                "result": False,
                "message": u"Some bots failed to send dingtalk message. %s" % data["_extra_user_error_msg"],
            }
        self.response.payload = result
