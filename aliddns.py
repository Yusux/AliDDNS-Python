#!/usr/bin/env python
# coding=utf-8
from aliyunsdkcore.client import AcsClient
from aliyunsdkalidns.request.v20150109.AddDomainRecordRequest import AddDomainRecordRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
from  aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
import urllib.request
import json
import ipaddress
import logging
import config
from config import ResourceRecord
from dingtalk_utils import dingtalk

def getIPv4():
    """
    Get IPv4 address via ZJU speedtest
    - return: IPv4 address
    """
    url = "http://speedtest.zju.edu.cn/getIP.php"
    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')
    ip = html.strip()
    # Check if ip is valid
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        logging.error("Invalid IPv4 address: " + ip)
        raise
    return ip

def getIPv6():
    """
    Get IPv6 address via ZJU speedtest
    - return: IPv6 address
    """
    url = "http://speedtest.zju6.edu.cn/getIP.php"
    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')
    ip = html.strip()
    # Check if ip is valid
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        logging.error("Invalid IPv6 address: " + ip)
        raise
    return ip

def getRecords(client, rr, domain):
    """
    Get all records of a domain
    - client: Aliyun client
    - rr: resource record
    - domain: domain
    - return: records
    """
    request = DescribeDomainRecordsRequest()
    request.set_accept_format('json')
    request.set_DomainName(domain)
    request.set_RRKeyWord(rr)
    response = client.do_action_with_exception(request)
    logging.info(f"Get records of domain: {domain}")
    jsonData = json.loads(response)
    return jsonData['DomainRecords']['Record']

def post_dingtalk(rrs: list[ResourceRecord]):
    """
    Post message to DingTalk in text format
    - rrs: resource records
    """
    ipv4_text = ""
    ipv6_text = ""
    for rr in rrs:
        if rr.success:
            if rr.result is None:
                continue
            text = f"Update Result: Success\n  - Domain: {rr.rr}.{rr.domain}\n  - New IP: {rr.result}\n"
            if rr.type == "A":
                # If ipv4_text has some content, add a new divider
                if ipv4_text != "":
                    ipv4_text += "------------------\n"
                ipv4_text += text
            elif rr.type == "AAAA":
                # If ipv6_text has some content, add a new divider
                if ipv6_text != "":
                    ipv6_text += "------------------\n"
                ipv6_text += text
        else:
            text = f"Update Result: Failed\n  - Domain: {rr.rr}.{rr.domain}\n  - Error: {rr.result}\n"
            if rr.type == "A":
                # If ipv4_text has some content, add a new divider
                if ipv4_text != "":
                    ipv4_text += "------------------\n"
                ipv4_text += text
            elif rr.type == "AAAA":
                # If ipv6_text has some content, add a new divider
                if ipv6_text != "":
                    ipv6_text += "------------------\n"
                ipv6_text += text
    # If both ipv4_text and ipv6_text are empty, no need to send message to DingTalk
    if ipv4_text == "" and ipv6_text == "":
        logging.info("No record updated, no need to send message to DingTalk")
        return
    # Send message to DingTalk
    body_text = f"#### Aliyun DDNS Update\n"
    if ipv4_text != "":
        body_text += f"##### ====== IPv4 ======\n{ipv4_text}\n"
    if ipv6_text != "":
        body_text += f"##### ====== IPv6 ======\n{ipv6_text}\n"
    body_text += "##### === AliyunDDNS ===\n"
    if config.UseDingTalk:
        ding = dingtalk()
        send_body = {
            "msgtype": "markdown",
            "markdown": {
                "title": "Aliyun DDNS Update",
                "text": body_text
            }
        }
        ding.post(send_body)

def addDomainRecord(client, rr, domain, type, ip):
    """
    Add a record to a domain
    - client: Aliyun client
    - rr: resource record
    - domain: domain
    - type: record type
    - ip: IP address
    """
    request = AddDomainRecordRequest()
    request.set_action_name("AddDomainRecord")
    request.set_accept_format('json')
    request.set_RR(rr)
    request.set_DomainName(domain)
    request.set_Type(type)
    request.set_Value(ip)
    request.set_TTL(600)
    _ = client.do_action_with_exception(request)
    logging.info(f"Add record: {rr}.{domain} -> {ip}")

def updateDomainRecord(client, rr, domain, record_id, type, ip):
    """
    Update a record of a domain
    - client: Aliyun client
    - rr: resource record
    - domain: domain
    - record_id: record id
    - type: record type
    - ip: IP address
    """
    request = UpdateDomainRecordRequest()
    request.set_action_name("UpdateDomainRecord")
    request.set_accept_format('json')
    request.set_RR(rr)
    request.set_RecordId(record_id)
    request.set_Type(type)
    request.set_Value(ip)
    request.set_TTL(600)
    _ = client.do_action_with_exception(request)
    logging.info(f"Update record: {rr}.{domain} -> {ip}")

def maintainDomainRecord(client, record: ResourceRecord, ip):
    """
    Maintain a record of a domain
    - client: Aliyun client
    - record: resource record
    - ip: IP address
    """
    rr     = record.rr
    domain = record.domain
    type   = record.type
    records = getRecords(client, rr, domain)
    record_id=None
    for record in records:
        if (
            record['RR']         == rr     and
            record['DomainName'] == domain and
            record['Type']       == type
        ):
            record_id    = record['RecordId']
            avail_ip     = record['Value']
            break
    if record_id is None:
        logging.info(f"Record not found, adding record: {rr}.{domain} -> {ip}")
        addDomainRecord(client, rr, domain, ip, type)
        record.success = True
        record.result = ip
    else:
        logging.info(f"Record found: {rr}.{domain} -> {avail_ip}")
        if avail_ip == ip:
            logging.info(f"IP not changed, no need to update record: {avail_ip}")
            record.success = True
        else:
            logging.info(f"IP changed, updating record: {avail_ip} -> {ip}")
            updateDomainRecord(client,rr,domain,record_id,type,ip)
            record.success = True
            record.result = ip

        
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Create Aliyun client
    client = AcsClient(config.AccessKeyId, config.AccessKeySecret, 'cn-hangzhou')

    # Maintain all records
    for record in config.ResourceRecords:
        # Get IP address
        try: 
            if record.type == "A":
                ip = getIPv4()
            elif record.type == "AAAA":
                ip = getIPv6()
            else:
                # Invalid type
                raise ValueError(f"Invalid record type: {record.type}")

            # Maintain record
            maintainDomainRecord(client, record, ip)
        
        except Exception as e:
            logging.error(f"Failed for {str(record)}: {str(e)}")
            record.success = False
            record.result = str(e)
            continue
    
    # Post message to DingTalk
    post_dingtalk(config.ResourceRecords)
