#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
from elastalert.alerts import Alerter, BasicMatchString
from requests.exceptions import RequestException
from elastalert.util import elastalert_logger,EAException
from elastalert.util import pretty_ts
import requests

'''
#################################################################
# 微信推送消息                                                  #
#                                                     		#
# 作者: jik.shu <337806904@qq.com>                              #
# Github: https://github.com/sz-sunset/elastalert-wechat-plugin #
#                                                               #
#################################################################
'''
class WxAlerter(Alerter):

    #必填字段
    required_options = frozenset(['appid','secret','openid','template_id','template_text'])

    def __init__(self, *args):
        super(WxAlerter, self).__init__(*args)
        self.appid = self.rule.get('appid', '')         #公众号ID
        self.secret = self.rule.get('secret', '')       #secret
        self.openid = self.rule.get('openid', '')       #应用id
        self.access_token = ''                          #微信身份令牌
        self.template_id = self.rule.get('template_id')#模版id
        self.template_text = self.rule.get('template_text')#模版内容
        self.expires_in=datetime.datetime.now() - datetime.timedelta(seconds=60)#令牌过期时间

    def alert(self, matches):
    	
        # 获取或者更新access_token
        self.get_token()

        self.send_template_data(matches)

        elastalert_logger.info("send message to %s" % (self.openid))

    def get_token(self):
	
        if self.expires_in >= datetime.datetime.now() and self.access_token:
            return self.access_token
        
        #构建获取token的url
        get_token_url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' %(self.appid,self.secret)
        
        try:
            response = requests.get(get_token_url).json()
        except RequestException as e:
            raise EAException("get access_token failed , stacktrace:%s" % e)

        #获取access_token和expires_in
        self.access_token = response.get('access_token')
        self.expires_in = datetime.datetime.now() + datetime.timedelta(seconds=response['expires_in'])

        return self.access_token
        
    def send_template_data(self, matches):
	try:
		# 微信发送消息文档      
		send_url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=%s' %(self.access_token)
		for matche in matches:
			body = {"touser": '',"template_id": self.template_id,"data": ''}
			templateData = { }
			for templateKey in self.template_text.keys():
				value = ''
				if matche.has_key(self.template_text[templateKey]["value"].decode('utf-8')):
					value = matche[self.template_text[templateKey]["value"].decode('utf-8')]
				if self.template_text[templateKey].has_key("type") and self.template_text[templateKey]["type"] == "time":
					value = pretty_ts(value)
				templateDataVal ={"value":value,"color":self.template_text[templateKey]["color"]}
				templateData[templateKey] = templateDataVal;
			body["data"] = templateData
			for openidTemp in self.openid:
				body["touser"] = openidTemp
        	
		response = requests.post(send_url,data=json.dumps(body))
        except Exception as e:
		raise EAException("send message has error: %s" % e)
        elastalert_logger.info("send msg and response: %s" % response)
        
    def get_info(self):
        return {'type': 'WxAlerter'}
