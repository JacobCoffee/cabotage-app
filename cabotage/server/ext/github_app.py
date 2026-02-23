import base64
import hashlib
import hmac
import logging
import time

import requests
import jwt

from flask import request

logger = logging.getLogger(__name__)


def _load_private_key(pem_data):
    """Load an RSA private key, working around cryptography library PEM parsing bugs.

    Some versions of cryptography reject valid PEM keys with MalformedFraming.
    This falls back to parsing the key with pyasn1 and reconstructing it.
    """
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    try:
        return load_pem_private_key(pem_data, password=None)
    except ValueError:
        pass

    # Fallback: parse with pyasn1 and reconstruct
    from pyasn1.codec.der import decoder as der_decoder
    from pyasn1_modules import rfc2437
    from cryptography.hazmat.primitives.asymmetric.rsa import (
        rsa_crt_dmp1,
        rsa_crt_dmq1,
        rsa_crt_iqmp,
        RSAPrivateNumbers,
        RSAPublicNumbers,
    )

    lines = pem_data.decode().strip().split("\n")
    body = "".join(line for line in lines if not line.startswith("-----"))
    der_data = base64.b64decode(body)

    header = lines[0]
    if "RSA PRIVATE KEY" in header:
        rsa_der = der_data
    else:
        # PKCS8 wrapper - extract inner RSA key
        seq, _ = der_decoder.decode(der_data)
        rsa_der = bytes(seq[2])

    privkey, _ = der_decoder.decode(rsa_der, asn1Spec=rfc2437.RSAPrivateKey())
    p = int(privkey["prime1"])
    q = int(privkey["prime2"])
    d = int(privkey["privateExponent"])
    e = int(privkey["publicExponent"])
    n = int(privkey["modulus"])

    pub = RSAPublicNumbers(e, n)
    priv = RSAPrivateNumbers(
        p=p,
        q=q,
        d=d,
        dmp1=rsa_crt_dmp1(d, p),
        dmq1=rsa_crt_dmq1(d, q),
        iqmp=rsa_crt_iqmp(p, q),
        public_numbers=pub,
    )
    return priv.private_key()


class GitHubApp(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.webhook_secret = None
        self.app_id = None
        self.app_private_key_pem = None
        self._private_key_obj = None
        self._bearer_token = None
        self._bearer_token_exp = -1

        if app.config["GITHUB_WEBHOOK_SECRET"]:
            self.webhook_secret = app.config["GITHUB_WEBHOOK_SECRET"]

        if app.config["GITHUB_APP_ID"]:
            self.app_id = app.config["GITHUB_APP_ID"]

        # Support loading key from file (GITHUB_APP_KEY_FILE) or base64 env var
        key_file = app.config.get("GITHUB_APP_KEY_FILE")
        if key_file:
            try:
                with open(key_file, "rb") as f:
                    pem_data = f.read()
                self.app_private_key_pem = pem_data.decode()
                self._private_key_obj = _load_private_key(pem_data)
            except FileNotFoundError:
                logger.warning(
                    "GITHUB_APP_KEY_FILE=%s not found; "
                    "GitHub App integration will be unavailable.",
                    key_file,
                )
        elif app.config["GITHUB_APP_PRIVATE_KEY"]:
            try:
                pem_data = base64.b64decode(app.config["GITHUB_APP_PRIVATE_KEY"])
                self.app_private_key_pem = pem_data.decode()
                self._private_key_obj = _load_private_key(pem_data)
            except Exception as exc:
                raise ValueError(f"Unable to decode GITHUB_APP_PRIVATE_KEY: {exc}")

        app.teardown_appcontext(self.teardown)

    def validate_webhook(self):
        if self.webhook_secret is None:
            return True
        return hmac.compare_digest(
            request.headers.get("X-Hub-Signature-256").split("=")[1],
            hmac.new(
                self.webhook_secret.encode(), msg=request.data, digestmod=hashlib.sha256
            ).hexdigest(),
        )

    def _token_needs_renewed(self):
        return (self._bearer_token_exp - int(time.time())) < 60

    @property
    def bearer_token(self):
        if self._bearer_token is None or self._token_needs_renewed():
            issued = int(time.time())
            payload = {
                "iat": issued,
                "exp": issued + 599,
                "iss": self.app_id,
            }
            self._bearer_token = jwt.encode(
                payload, self._private_key_obj, algorithm="RS256"
            )
            self._bearer_token_exp = issued + 599
        return self._bearer_token

    def fetch_installation_access_token(self, installation_id):
        access_token_response = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Accept": "application/vnd.github.machine-man-preview+json",
                "Authorization": f"Bearer {self.bearer_token}",
            },
            timeout=10,
        )
        if "token" not in access_token_response.json():
            print(f"Unable to authenticate for {installation_id}")
            return None
        return access_token_response.json()["token"]

    def teardown(self, exception):
        pass
