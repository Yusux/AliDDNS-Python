# AliDDNS

阿里云域名 DDNS 自动配置。路由器或者连接路由器的任一电脑运行此脚本均可

# 使用方法

### 1.安装python和pip
    
    sudo apt install python3 python3-pip
    
### 2.安装阿里云sdk

    pip3 install aliyun-python-sdk-alidns

### 3.申请阿里云AccessKey

从 [https://ak-console.aliyun.com/#/accesskey](https://ak-console.aliyun.com/#/accesskey) 申请即可

### 4.使用方法

修改 `config.py` 中对应参数即可：

- AccessKeyId: 申请的 AccessKeyId
- AccessKeySecret: 申请的 AccessKeySecret
- ResourceRecords: 需要修改的域名
- UseDingTalk: 是否使用钉钉通知
- DingTalkAccessToken: 钉钉机器人的 AccessToken
- DingTalkSecret: 钉钉机器人的 Secret
