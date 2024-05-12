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

def post_dingtalk(text):
    """
    Post message to DingTalk in text format
    - title: title of the message
    - text: text of the message
    """
    if config.UseDingTalk:
        ding = dingtalk()
        send_body = {
            "msgtype": "text",
            "text": {
                "content": text
            }
        }
        ding.post(send_body)

def addDomainRecord(client,rr,domain,type,ip):
    """
    Add a record to a domain
    - client: Aliyun client
    - rr: resource record
    - domain: domain
    - type: record type
    - ip: IP address
    - return: record id
    """
    request = AddDomainRecordRequest()
    request.set_action_name("AddDomainRecord")
    request.set_accept_format('json')
    request.set_RR(rr)
    request.set_DomainName(domain)
    request.set_Type(type)
    request.set_Value(ip)
    request.set_TTL(600)
    response = client.do_action_with_exception(request)
    logging.info(f"Add record: {rr}.{domain} -> {ip}")
    return json.loads(response)['RecordId']

def updateDomainRecord(client, rr, domain, record_id, type, ip):
    """
    Update a record of a domain
    - client: Aliyun client
    - rr: resource record
    - domain: domain
    - record_id: record id
    - type: record type
    - ip: IP address
    - return: record id
    """
    request = UpdateDomainRecordRequest()
    request.set_action_name("UpdateDomainRecord")
    request.set_accept_format('json')
    request.set_RR(rr)
    request.set_RecordId(record_id)
    request.set_Type(type)
    request.set_Value(ip)
    request.set_TTL(600)
    response = client.do_action_with_exception(request)
    logging.info(f"Update record: {rr}.{domain} -> {ip}")
    return json.loads(response)['RecordId']

def maintainDomainRecord(client, rr, domain, type, ip):
    """
    Maintain a record of a domain
    - client: Aliyun client
    - rr: resource record
    - domain: domain
    - type: record type
    - ip: IP address
    - return: record id
    """
    records = getRecords(client,rr,domain)
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
        record_id = addDomainRecord(client,rr,domain,ip,type)
        post_dingtalk(
            f"Record not found, adding record: {rr}.{domain} -> {ip}"
        )
    else:
        logging.info(f"Record found: {rr}.{domain} -> {avail_ip}")
        if avail_ip == ip:
            logging.info(f"IP not changed, no need to update record: {avail_ip}")
        else:
            logging.info(f"IP changed, updating record: {avail_ip} -> {ip}")
            record_id = updateDomainRecord(client,rr,domain,record_id,type,ip)
            post_dingtalk(
                f"IP changed, updating record of {rr}.{domain} from {avail_ip} to {ip}"
            )
    return record_id

        
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Create Aliyun client
    client = AcsClient(config.AccessKeyId, config.AccessKeySecret, 'cn-hangzhou')

    # Maintain all records
    for record in config.ResourceRecords:
        rr     = record.rr
        domain = record.domain
        type   = record.type

        # Get IP address
        if type == "A":
            try:
                ip = getIPv4()
            except Exception as e:
                logging.error(f"Failed to get IPv4 address for {str(record)}: {str(e)}")
                continue
        elif type == "AAAA":
            try:
                ip = getIPv6()
            except Exception as e:
                logging.error(f"Failed to get IPv6 address for {str(record)}: {str(e)}")
                continue
        else:
            logging.error(f"Invalid record type: {type} in {str(record)}")
            continue

        # Maintain record
        try:
            maintainDomainRecord(client, rr, domain, type, ip)
        except Exception as e:
            logging.error(f"Failed to maintain record {str(record)}: {str(e)}")
            continue
