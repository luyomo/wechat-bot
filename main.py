from typing import Optional
from fastapi import FastAPI, Request, Response, Header
import hashlib
from wechat_sdk import WechatConf
from wechat_sdk import WechatBasic
import xml.etree.ElementTree as ET
import xmltodict
import json
from json2xml import json2xml

import yaml
from cryptonews.dogeTopPosition       import dogeTopPosition

from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from wechatpy import parse_message
from wechatpy.replies import TextReply, ImageReply, create_reply
import re


with open(r'/etc/opt/config.yml') as file: _config = yaml.load(file, Loader=yaml.FullLoader)

print(f"The db config is {_config['db']}")

__topDoge = dogeTopPosition(_config['db'], _config['dogeTopUrl'])

app = FastAPI()

conf = WechatConf(
    token            = _config['wechatpy']['token'           ] ,
    appid            = _config['wechatpy']['appid'           ] ,
    appsecret        = _config['wechatpy']['appsecret'       ] ,
    encrypt_mode     = _config['wechatpy']['encrypt_mode'    ] ,
    encoding_aes_key = _config['wechatpy']['encoding_aes_key']
)

@app.get("/")
async def getWechat(signature: str, echostr: int, timestamp: str, nonce: str):
    wechat_instance = WechatBasic(conf=conf)
    if not wechat_instance.check_signature(signature=signature, timestamp=timestamp, nonce=nonce):
        return 'Verify Failed'
    else:
        return echostr


#signature=b5b0785974ab1fedd6c75c34100b8d95fad1d85d&echostr=108915514908556663&timestamp=1619271956&nonce=526119712
@app.post("/")
async def postWechat(request: Request, user_agent: Optional[str] = Header(None)):
    __data = await request.body()
    __msg = parse_message(__data)
    print(f"What's the message <{__msg.content}>")
    print(f"{user_agent}")
    if __msg.type == 'text':
         __p = re.compile('doge')
         if __p.match(__msg.content) != None:
             __reply = TextReply(content=__topDoge.run(), message=__msg)
             print(f"The reply is {__reply}")
             __xml = __reply.render()
             #return __xml
             headers = {'CONTENT_TYPE': 'text/html'}
             return Response(content=__xml, headers=headers)

         #print(f"The matched message is {__m}")
         #articles = [
         #    {
         #        'title': 'test',
         #        'description': 'test \n second line \n description',
         #        'image': 'https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png',
         #        'url': 'https://www.yahoo.co.jp'
         #    }
         #]

         #__reply = TextReply(content="How &#13;&#10; are you", message=__msg)
         #__reply = TextReply(content=__msg.content, message=__msg)
         #__reply = create_reply(__msg.content, __msg)
         #__reply = create_reply(articles, __msg)

    __reply = TextReply(content="I don't know what are you talking about.", message=__msg)
    __xml = __reply.render()
    headers = {'CONTENT_TYPE': 'text/html'}
    return Response(content=__xml, headers=headers)
    return __xml
