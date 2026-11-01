# 工具类
# 喵喵喵
import hashlib
import requests
import os
# import ddddocr

from fox_config import read_int

def http_post(url, **kwargs):
    kwargs.setdefault('timeout', read_int('FOX_REQUEST_TIMEOUT',25,5,120))
    return requests.post(url, **kwargs)

def http_get(url, **kwargs):
    kwargs.setdefault('timeout', read_int('FOX_REQUEST_TIMEOUT',25,5,120))
    return requests.get(url, **kwargs)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
Headers = {"User-Agent":UA}

def authCookies(token):
    return {"mars_token":token}

def authHeaders(token):
    # 新版前端除 cookie 外还会带 Authorization 和来源信息，这里照做
    return {
        "User-Agent":UA,
        "Authorization":token,
        "Origin":"https://mars.mycourse.cn",
        "Referer":"https://mars.mycourse.cn/deimos/"
        }

def pwdEncrypt(text):
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    return md5.hexdigest().upper()

def searchCollegeByName(collegeName, schoolList):
    from school_select import select_school
    return select_school(collegeName, schoolList)

def getCaptcha(timestamp):
    captcha = http_get("https://mars.mycourse.cn/marsapi/api/login/v1/getCaptcha?timestamp=%s" % timestamp)
    with open("captcha.png","wb") as f:
        f.write(captcha.content)
    return True

# def ocrCaptcha():
#     ocr = ddddocr.DdddOcr(show_ad=False)
#     with open('captcha.png', 'rb') as f:
#         image = f.read()
#         res = ocr.classification(image)
#         return res

def login(tenant, username, passwordE, captcha, timestamp):
    data = {
        "tenantCode":tenant,
        "username":username,
        "encryptedPassword":passwordE,
        "captchaCode":captcha,
        "timestamp":timestamp
        }
    res = http_post("https://mars.mycourse.cn/marsapi/api/login/v1/login", data=data, headers=Headers)
    return res.text

def logout():
    res = http_post("https://mars.mycourse.cn/marsapi/api/login/v1/logout", headers=Headers)
    return res.text

def getUserIndex():
    res = http_post("https://mars.mycourse.cn/marsapi/api/user/v1/index", headers=Headers)
    return res.text

def getActivities(token):
    Cookies = authCookies(token)
    res = http_post("https://mars.mycourse.cn/marsapi/api/study/project/v1/index", cookies=Cookies, headers=authHeaders(token))
    return res.text

def recordQuestion(token, questionId, userActivityId, useTime, answerIds):
    Cookies = authCookies(token)
    data = {
        "questionId":questionId,
        "userActivityId":userActivityId,
        "useTime":useTime,
        "answerIds":answerIds
        }
    res = http_post("https://mars.mycourse.cn/marsapi/api/study/activity/exam/v1/recordQuestion", cookies=Cookies, data=data, headers=authHeaders(token))
    return res.text

def preparePaper(token, activityId):
    Cookies = authCookies(token)
    data = {
        "userActivityId":activityId
        }
    res = http_post("https://mars.mycourse.cn/marsapi/api/study/activity/exam/v1/preparePaper", data=data, cookies=Cookies, headers=authHeaders(token))
    return res.text

def startPaper(token, activityId):
    Cookies = authCookies(token)
    data = {
        "userActivityId":activityId
        }
    res = http_post("https://mars.mycourse.cn/marsapi/api/study/activity/exam/v1/startPaper", cookies=Cookies, data=data, headers=authHeaders(token))
    return res.text

def submitPaper(token, activityId):
    Cookies = authCookies(token)
    data = {
        "userActivityId":activityId,
        }
    res = http_post("https://mars.mycourse.cn/marsapi/api/study/activity/exam/v1/submitPaper", data=data, cookies=Cookies,headers=authHeaders(token))
    return res.text

def index(token):
    Cookies = authCookies(token)
    res = http_post("https://mars.mycourse.cn/marsapi/api/user/v1/index", cookies=Cookies, headers=authHeaders(token))
    return res.text
# 练习
def preparePaperPractice(token, activityId):
    Cookies = authCookies(token)
    data = {
        "userActivityId":activityId
        }
    res = http_post("https://mars.mycourse.cn/marsapi/api/study/activity/practice/v1/preparePaper", data=data, cookies=Cookies, headers=authHeaders(token))
    return res.text

def startPaperPractice(token, activityId):
    Cookies = authCookies(token)
    data = {
        "userActivityId":activityId
        }
    res = http_post("https://mars.mycourse.cn/marsapi/api/study/activity/practice/v1/startPaper", cookies=Cookies, data=data, headers=authHeaders(token))
    return res.text

def getNear(token, activityId, seq):
    Cookies = authCookies(token)
    data = {
        "userActivityId":activityId,
        "currentIndex":seq,
        "nearType":2
        }
    res = http_post("https://mars.mycourse.cn/marsapi/api/study/activity/practice/v1/getNear", data=data, cookies=Cookies, headers=authHeaders(token))
    return res.text

def submitPaperPractice(token, activityId):
    Cookies = authCookies(token)
    data = {
        "userActivityId":activityId,
        }
    res = http_post("https://mars.mycourse.cn/marsapi/api/study/activity/practice/v1/submitPaper", data=data, cookies=Cookies,headers=authHeaders(token))
    return res.text

def recordQuestionPractice(token, questionId, userActivityId, useTime,currentIndex, answerIds):
    Cookies = authCookies(token)
    data = {
        "questionId":questionId,
        "userActivityId":userActivityId,
        "useTime":useTime,
        "currentIndex":currentIndex,
        "answerIds":answerIds
        }
    res = http_post("https://mars.mycourse.cn/marsapi/api/study/activity/practice/v1/recordQuestion", cookies=Cookies, data=data, headers=authHeaders(token))
    return res.text
