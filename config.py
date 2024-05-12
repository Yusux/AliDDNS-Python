class ResourceRecord:
    def __init__(self, rr, domain, type):
        self.rr     = rr
        self.domain = domain
        self.type   = type

    def __str__(self):
        return f"[{self.rr}.{self.domain}. \t{self.type}]"

AccessKeyId     = "your-access-key-id"
AccessKeySecret = "your-access-key-secret"
ResourceRecords = [
    ResourceRecord("subdomain", "your-domain.com", "A"),
    ResourceRecord("subdomain", "your-domain.com", "A"),
]

UseDingTalk = True
DingTalkAccessToken = "your-dingtalk-access-token"
DingTalkSecret = "your-dingtalk-secret"