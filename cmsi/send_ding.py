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
from esb.bkcore.models import ESBChannel
from esb.channel import get_channel_manager
from components.component import Component, SetupConfMixin
from common.forms import BaseComponentForm, ListField
from common.constants import API_TYPE_OP
from .toolkit import configs, tools
from common.log import logger


class SendDing(Component, SetupConfMixin):
    """
    apiLabel {{ _("发送钉钉消息") }}
    apiMethod POST

    ### {{ _("功能描述") }}

    {{ _("如果接收人是群机器人用户，消息会发送到群，如果接收人是普通用户，消息会通过内部机器人发送单聊消息到用户") }}

    ### {{ _("请求参数") }}

    {{ common_args_desc }}

    #### {{ _("接口参数") }}

    | {{ _("字段") }}               |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |--------------------|------------|--------|------------|
    | receiver__username |  string    | {{ _("是") }}     | {{ _("钉钉接收者，包含用户名，用户需在蓝鲸平台注册，多个以逗号分隔") }} |
    | msg_key            |  string    | {{ _("否") }}     | {{ _("消息格式，text文本消息/markdown markdown消息，默认text") }}  |
    | title              |  string    | {{ _("是") }}     | {{ _("消息标题") }} |
    | content            |  string    | {{ _("是") }}     | {{ _("消息内容") }} |


    ### {{ _("请求参数示例") }}

    ```python
        {
            "bk_app_code": "xxx",
            "bk_app_secret": "xxx",
            "bk_username": "xxx",
            "receiver__username": "xxx,xxx",  # 蓝鲸用户名
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

    class Form(BaseComponentForm):
        receiver__username = ListField(label="dingtalk receiver", required=True)
        msg_key = forms.CharField(label="message key type", required=False)
        title = forms.CharField(label="message title", required=True)
        content = forms.CharField(label="message content", required=True)

        def clean(self):
            data = self.cleaned_data
            return {
                "receiver__username": data["receiver__username"],
                "title": data["title"],
                "content": data["content"],
                "msg_key": data.get("msg_key", "text"),
            }

    def handle(self):
        dingbot_user = []
        dingtalk_user = []
        token_field_in_db = "qq"
        sign_field_in_db = "wx_userid"
        try:
            channel = ESBChannel.objects.get(path="/cmsi/send_dingbot/")
            conf_dict = dict(json.loads(channel.comp_conf))
            token_field_in_db = conf_dict["token_field"]
            sign_field_in_db = conf_dict["sign_field"]
            logger.info("token_field_in_db: ", token_field_in_db)
            logger.info("sign_field_in_db: ", sign_field_in_db)
        except ESBChannel.DoesNotExist:
            logger.error("send_dingbot channel does not register.")
        except Exception as e:
            logger.warning(str(e))
        token_field = token_field_in_db or getattr(configs, "token_field") or "qq"
        sign_field = sign_field_in_db or getattr(configs, "sign_field") or "wx_userid"
        dingbot_user, dingtalk_user = tools.group_by_user_type(self.form_data["receiver__username"], token_field, sign_field)
        logger.info("dingbot_user: ", dingbot_user)
        logger.info("dingtalk_user: ", dingtalk_user)
        channel_manager = get_channel_manager()
        if dingbot_user or  dingtalk_user:
            if dingbot_user:
                dingbot_data = {
                    "receiver__username": dingbot_user,
                    "msg_key": "text" if self.form_data.get("msg_key", "text") == "text" else "markdown",
                    "title": self.form_data["title"],
                    "content": self.form_data["content"]
                }
                path = "/cmsi/send_dingbot/"
                channel_conf = channel_manager.get_channel_by_path(path, "POST")
                comp_conf = channel_conf.get("comp_conf") or {} if channel_conf else {}
                comp_obj= self.prepare_other("generic.cmsi.send_dingbot", kwargs=dingbot_data)
                comp_obj.setup_conf(comp_conf)
                dingbot_result = comp_obj.invoke()
            else:
                dingbot_result = {
                    "result": True,
                    "message": "no dingbot receiver."
                }
            
            if dingtalk_user:
                dingtalk_data = {
                    "receiver__username": dingtalk_user,
                    "msg_key": "sampleText" if self.form_data.get("msg_key", "text") == "text" else "sampleMarkdown",
                    "title": self.form_data["title"],
                    "content": self.form_data["content"]
                }

                path = "/cmsi/send_dingtalk/"
                channel_conf = channel_manager.get_channel_by_path(path, "POST")
                comp_conf = channel_conf.get("comp_conf") or {} if channel_conf else {}
                comp_obj= self.prepare_other("generic.cmsi.send_dingtalk", kwargs=dingtalk_data)
                comp_obj.setup_conf(comp_conf)
                dingtalk_result = comp_obj.invoke()
            else:
                dingtalk_result = {
                    "result": True,
                    "message": "no dingtalk receiver."
                }
        
            logger.info("dingbot_result: ", dingbot_result)
            logger.info("dingtalk_result:", dingtalk_result)
            if dingbot_result["result"] and dingtalk_result["result"]:
                result = {
                    "result": True,
                    "message": "ok"
                }
            else:
                message = "[dingbot] %s; "%dingbot_result.get("message", "send success") + "[dingtalk] %s"%dingtalk_result.get("message", "send success") 
                result = {
                    "result": False,
                    "message": message
                }
                
        else:
            result = {
                "result": False,
                "message": "no valid receiver."
            }
        logger.info("send_ding result: ", result)
        self.response.payload = result

