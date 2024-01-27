import hashlib
import hmac

def verify_signature(payload, header_signature, secret):
    sha_name, signature = header_signature.split('=')
    if sha_name != 'sha1':
        return False

    secret = secret.encode() if not isinstance(secret, bytes) else secret
    mac = hmac.new(secret, msg=payload, digestmod=hashlib.sha1)

    return hmac.compare_digest(mac.hexdigest(), signature)