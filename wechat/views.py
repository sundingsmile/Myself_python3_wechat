from django.shortcuts import render
from django.http import HttpResponse
from hashlib import sha1
import requests,wechatpy,time
# Create your views here.

'''全局变量'''
token = 'huiduowulian'  # 微信公众号平台设置的token
#default_msg = '''查询天气的格式为“xx天气”，xx可以是市、县、也可以是区，例如“北京天气”、“鹿泉天气”、“大兴天气”，就会查询出相应地方的天气'''
access_token = ''
'''
解决access_token过期问题：
    设置这个是为了定时刷新access_token的，因为access_token默认有效期为7200秒，
    access_token_create_time是记录他创建时间，每次调用access_token时判断下,
    access_token_create_time和现在调用的时间是不相差7200秒，如果是的话重新给，
    access_token_create_time赋值，并重新获取access_token
'''
access_token_create_time = 0
reply_content = '''
您好，感谢您的关注与支持！
由于后台消息回复人数众多，您可以先咨询：
查询天气的格式为“xx天气”，xx可以是市、县、也可以是区，
例如“北京天气”、“鹿泉天气”、“大兴天气”，就会查询出相应地方的天气
回复“0” 可以和机器人进行聊天，回复“退出聊天”退出和机器人的聊天
'''
robot_flag = False  # 开启聊天机器人的标志位，False表示未开启机器人，True表示开启机器人


# 调用高德地图天气查询API查询天气
def get_weather(adr,key = '55fd4a7d8be5db9fbd220222fc5d0646'):
    url = 'https://restapi.amap.com/v3/weather/weatherInfo?city=%s&key=%s&extensions=all' %(adr,key)  # 高德天气查询地址，key为高德应用参数
    res = requests.get(url)  # 访问高德api，并将内容返回
    temp = res.json()['forecasts']
    if temp:
        '''判断天气查询结果是否为空，如果为空返回默认字符串，如果不为空返回天气信息'''
        weather_info = '''
        时间：%s
        地点：%s
        白天：
            白天气象：%s
            白天温度：%s 摄氏度
            白天风向：%s
            白天风力：%s级
        晚上：
            夜间气象：%s
            夜间温度：%s 摄氏度
            夜间风向：%s
            夜间风力：%s级
        ''' %(temp[0]['reporttime'],adr,temp[0]['casts'][0]['dayweather'],temp[0]['casts'][0]['daytemp'],temp[0]['casts'][0]['daywind'],temp[0]['casts'][0]['daypower'],temp[0]['casts'][0]['nightweather'],temp[0]['casts'][0]['nighttemp'],temp[0]['casts'][0]['nightwind'],temp[0]['casts'][0]['nightpower'])
        return weather_info
    else:
        return default_msg


'''调用思知机器人'''
def robot_wechat(content):
    url = 'https://api.ownthink.com/bot?spoken=%s' % content
    res = requests.get(url).json()['data']['info']['text']
    print(res)
    return res


'''获取微信公众号accesstoken'''
def get_access_token(appid='wx9690b57a3b5f4661',appsecret='ccb08dd6eb01698327ba7e817cf023a2'):
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' %(appid,appsecret)
    res = requests.get(url)  # 获取返回值
    print(res.json())
    return res.json()['access_token']  # 将获得的access_token返回


'''test'''
def test(access_token):
    url = 'https://api.weixin.qq.com/customservice/kfaccount/add?access_token=%s' %access_token
    print(url)
    data = {
        "kf_account": "test1@test",
        "nickname": "客服1",
        "password": "pswmd5"
    }
    res = requests.post(url,data)
    print(res.json())


# 微信公众号服务程序
def wx(request):
    global robot_flag
    '''和微信服务器进行连接'''
    if request.method == 'GET':
        print('配置服务器')
        access_token_create_time = round(time.time())  # 记录access_token的获取时间
        access_token = get_access_token()  # 获取access_token值
        test(access_token)

        '''分别取出其中重要参数'''
        wx_gw_cs = request.GET  # 微信服务器在GET中携带的参数
        wx_gw_signature = wx_gw_cs['signature']
        wx_gw_echostr = wx_gw_cs['echostr']
        wx_gw_timestamp = wx_gw_cs['timestamp']
        wx_gw_nonce = wx_gw_cs['nonce']
        hash_list = [token,wx_gw_timestamp,wx_gw_nonce]  #新建一个临时文件list

        '''
        服务器对接步骤：
            1、token,wx_gw_timestamp,wx_gw_nonce这几个参数进行排序；
            2、按照排好的顺序拼接成一个字符串然后进行sha1加密；
            3、跟微信服务器发送过来的wx_gx_signature参数进行对比，如果相同并且原样返回wx_gx_echostr字符串表示对接成功；
        '''
        hash_list.sort()  # 对三个参数进行排序
        temp_str = ''.join(hash_list)  # 将排序好的字符串连接起来
        local_signature = sha1(temp_str.encode('utf-8')).hexdigest()  # 对排序好的字符串进行sha1加密并且以16进制方式显示
        if local_signature == wx_gw_signature:  # 如果签名相同原样返回wx_gw_echostr，表示服务器链接成功
            print('配置服务器成功')
            return HttpResponse(wx_gw_echostr)
        else:
            return HttpResponse('Signature is wrong!')

    elif request.method == 'POST':  # 对接收到的信息进行处理
        msg = wechatpy.parse_message(request.body)  # 解析用户发送过来的信息
        if msg.type == 'text':
            temp_con = msg.content
            if temp_con == "0":  # 打开机器人
                robot_flag = True
                reply = wechatpy.replies.TextReply(content='您好，现在您可以开始聊天了，请发个“笑话”试试,发送“退出聊天”结束聊天！', message=msg)
            elif robot_flag:  # 判断是否开启机器人
                if temp_con == '退出聊天':  # 判断是否退出机器人，如果退出将标志位置为False
                    robot_flag = False
                    reply = wechatpy.replies.TextReply(content='期待与您的再次相遇，记得想我呦！', message=msg)
                else:
                    temp_robot = robot_wechat(temp_con)
                    while not temp_robot:  #  判断robot_wechat函数是否已经返回内容，如果没返回继续调用
                        time.sleep(0.5)
                    reply = wechatpy.replies.TextReply(content=temp_robot, message=msg)
            elif '天气' in temp_con:  # 进入天气查询
                temp = temp_con[:-2]
                if temp:
                    reply = wechatpy.replies.TextReply(content=get_weather(temp), message=msg)
                else:
                    reply = wechatpy.replies.TextReply(content=reply_content, message=msg)
            else:
                reply = wechatpy.replies.TextReply(content=reply_content, message=msg)

        elif msg.type == 'image':
            reply = wechatpy.replies.TextReply(content='图片消息', message=msg)
        elif msg.type == 'voice':
            reply = wechatpy.replies.TextReply(content='语音消息', message=msg)
        elif msg.type == 'video':
            reply = wechatpy.replies.TextReply(content='视频消息', message=msg)
        elif msg.type == 'shortvideo':
            reply = wechatpy.replies.TextReply(content='短视频消息', message=msg)
        elif msg.type == 'location':
            reply = wechatpy.replies.TextReply(content='位置消息', message=msg)
        elif msg.type == 'link':
            reply = wechatpy.replies.TextReply(content='链接消息', message=msg)
        elif msg.type == 'event':
            if msg.event == 'subscribe':
                reply = wechatpy.replies.TextReply(content=reply_content, message=msg)
            else:
                print('您慢走，欢迎再来。')
                reply = wechatpy.replies.TextReply(content='祝您一路顺风！', message=msg)
        else:
            reply = wechatpy.replies.TextReply(content='其他类型', message=msg)

        return HttpResponse(reply.render(),content_type="application/xml")  # reply.render()是将reply转换为xml格式

    else:
        print(wechatpy.parse_message(request.body))
        print('===========================')
        return HttpResponse('Thanks！')