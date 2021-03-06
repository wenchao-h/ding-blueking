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

import os
import base64
from collections import OrderedDict, defaultdict

from common.errors import CommonAPIError
from common.log import logger

default_nation_code = "86"
ICON_DIR = os.path.dirname(os.path.abspath(__file__))


def valid_email(email):
    if not isinstance(email, basestring) or email.find("@") < 0:
        return False
    return True


def valid_phone(phone):
    if not isinstance(phone, (basestring, int)) or not str(phone).isdigit():
        return False
    return True


def get_user_contact(user, contact_way):
    if contact_way == "email":
        contact_info = user["email"]
        return contact_info, valid_email(contact_info)
    elif contact_way == "phone":
        contact_info = {
            "nation_code": user.get("country_code"),
            "telephone": user["telephone"],
        }
        return contact_info, valid_phone(contact_info["telephone"])
    else:
        contact_info = user.get(contact_way)
        return contact_info, bool(contact_info)


def validate_receiver(receiver, contact_way="phone"):
    valid_receiver = []
    error_contact_user = []
    for user_contact in receiver:
        if contact_way == "email":
            is_valid = valid_email(user_contact)
        elif contact_way == "phone":
            is_valid = valid_phone(user_contact["telephone"])
        if is_valid:
            valid_receiver.append(user_contact)
        else:
            error_contact_user.append(user_contact)
    if error_contact_user:
        raise CommonAPIError(
            "User message failed to send. The following users contact format are incorrect: %s, please check"
            % ",".join(error_contact_user)
        )  # noqa
    return valid_receiver


def get_receiver_with_username(receiver__username=None, cc__username=None, contact_way="phone"):  # noqa
    username_list = []
    if receiver__username:
        username_list.extend(receiver__username)
    if cc__username:
        username_list.extend(cc__username)

    if not username_list:
        return {}

    user_data = _get_users(username_list)

    result = {}
    not_exist_user = []
    error_contact_user = []
    if receiver__username:
        result["receiver"] = []
        for username in receiver__username:
            user = user_data.get(username)
            if not user:
                not_exist_user.append(username)
                continue
            user_contact, is_valid = get_user_contact(user, contact_way)
            if is_valid:
                result["receiver"].append(user_contact)
            else:
                error_contact_user.append(username)

    if cc__username:
        result["cc"] = []
        for username in cc__username:
            user = user_data.get(username)
            if not user:
                not_exist_user.append(username)
                continue
            user_contact, is_valid = get_user_contact(user, contact_way)
            if is_valid:
                result["cc"].append(user_contact)
            else:
                error_contact_user.append(username)

    _extra_user_error_msg = []
    if not_exist_user:
        _extra_user_error_msg.append(u"The following users are not blueking users: %s" % ",".join(not_exist_user))
    if error_contact_user:
        _extra_user_error_msg.append(
            u"The following users contact format are incorrect: %s" % ",".join(error_contact_user)
        )
    result["_extra_user_error_msg"] = ";".join(_extra_user_error_msg)

    if receiver__username and not result.get("receiver"):
        raise CommonAPIError(u"All users message failed to be sent. %s" % result["_extra_user_error_msg"])

    return result


def get_user_contact_with_username(username_list=None, contact_way="phone"):
    user_data = _get_users(username_list)

    user_contact_info = OrderedDict()
    not_exist_user = []
    error_contact_user = []
    for username in username_list:
        user = user_data.get(username)
        if not user:
            not_exist_user.append(username)
            continue
        user_contact, is_valid = get_user_contact(user, contact_way)
        if is_valid:
            user_contact_info[username] = user_contact
        else:
            error_contact_user.append(username)

    _extra_user_error_msg = []
    if not_exist_user:
        _extra_user_error_msg.append(u"The following users are not blueking users: %s" % ",".join(not_exist_user))
    if error_contact_user:
        _extra_user_error_msg.append(
            u"The following users contact format are incorrect: %s" % ",".join(error_contact_user)
        )
    _extra_user_error_msg = ";".join(_extra_user_error_msg)

    if not user_contact_info:
        raise CommonAPIError(u"All users contact information failed to get, %s" % _extra_user_error_msg)

    return {"user_contact_info": user_contact_info, "_extra_user_error_msg": _extra_user_error_msg}


def get_base64_icon(path):
    with open(os.path.join(ICON_DIR, path), "rb") as f:
        return base64.b64encode(f.read())


def _get_users(usernames):
    from components.bk.apisv2.usermanage.list_users import ListUsers

    result = ListUsers().invoke(
        kwargs={
            "lookup_field": "username",
            "no_page": True,
            "best_match": 1,
            "exact_lookups": ",".join(usernames),
            "fields": "username,country_code,telephone,email,wx_userid",
        }
    )
    if not result["result"]:
        raise CommonAPIError(u"Failed to get users contact information based on username, %s" % result["message"])

    return {user["username"]: user for user in result["data"]}


def group_by_nation_code(telephones):
    groups = defaultdict(list)
    for tel in telephones:
        tel["nation_code"] = tel.get("nation_code") or default_nation_code
        if tel["nation_code"] == default_nation_code:
            groups["default"].append(tel)
        else:
            groups["other"].append(tel)

    return [groups[key] for key in sorted(groups.keys())]


def valid_bot(token, sign):
    """机器人用户必须要有token以及sign字段信息，且sign信息必须以SEC开头"""
    if token and sign.startswith("SEC"):
        return True
    else:
        return False

def get_token_sign_with_username(username_list=None, token_field="extras__ddNumber", sign_field="wx_userid"):
    """通过username获取对应的token和sign字段信息，支持token和sign为扩展字段"""
    token_field_list = token_field.split("__")
    sign_field_list = sign_field.split("__")
    from components.bk.apisv2.usermanage.list_users import ListUsers
    result = ListUsers().invoke(
        kwargs={
            "lookup_field": "username",
            "no_page": True,
            "best_match": 1,
            "exact_lookups": ",".join(username_list),
            "fields": ",".join(["username", token_field_list[0], sign_field_list[0]])
        }
    )
    logger.info("ListUsers invoke: %s"%result)
    if not result["result"]:
        raise CommonAPIError(u"Failed to get users contact information based on username, %s" % result["message"])
    user_data = {user["username"]: user for user in result["data"]}
    result = {}
    result["bots_info"] = []
    not_exist_bot = []
    error_config_bot = []
    for username in username_list:
        if username not in user_data:
            not_exist_bot.append(username)
        else:
            try:
                user = user_data.get(username)
                if len(token_field_list) > 1:
                    token_key1 = token_field_list[0]
                    token_key2 = token_field_list[1]
                    token = user[token_key1][token_key2]
                elif len(token_field_list) == 1:
                    token_key1 = token_field_list[0]
                    token = user[token_key1]
                
                if len(sign_field_list) > 1:
                    sign_key1 = sign_field_list[0]
                    sign_key2 = sign_field_list[1]
                    sign = user[sign_key1][sign_key2]
                elif len(sign_field_list) == 1:
                    sign_key1 = sign_field_list[0]
                    sign = user[sign_key1]
            except KeyError as e:
                error_config_bot.append(username)
                continue
            except Exception as e:
                raise CommonAPIError("get %s token/sign failed, maybe there is no  %s"%(username, str(e)))
            if valid_bot(token, sign):
                item = {
                    "username": user["username"],
                    "token": token,
                    "sign": sign
                }
                result["bots_info"].append(item)
            else:
                error_config_bot.append(username)
    _extra_user_error_msg = []
    if not_exist_bot:
        _extra_user_error_msg.append(u"The following users are not blueking users: %s" % ",".join(not_exist_bot))
    if error_config_bot:
        _extra_user_error_msg.append(u"The following users dingbot config format are incorrect: %s" % ",".join(error_config_bot))
    result["_extra_user_error_msg"] = ";".join(_extra_user_error_msg)

    if username_list and not result.get("bots_info"):
        raise CommonAPIError(u"All dingbots message failed to be sent. %s" % result["_extra_user_error_msg"])

    logger.info("result: %s"%result)
    return result

def group_by_user_type(receiver__username=[], token_field="extras__ddNumber", sign_field="wx_userid"):
    """区分单聊用户和机器人用户"""
    dingbot_user = []
    dingtalk_user = []
    if not receiver__username:
        return dingbot_user, dingtalk_user
    bots = []
    try:
        bots_result = get_token_sign_with_username(receiver__username, token_field, sign_field)
        bots = [bot["username"] for bot in bots_result["bots_info"]]
    except CommonAPIError as e:
        logger.warning(str(e))
    for user in receiver__username:
        if user not in bots:
            dingtalk_user.append(user)
    dingbot_user = bots
    return dingbot_user, dingtalk_user

