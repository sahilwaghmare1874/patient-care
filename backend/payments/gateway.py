"""
PatientCare Healthcare Platform — Payment Gateway Adapter Layer
Integrates sovereign YouPI-PG (https://github.com/youpi-pg/YouPI-PG)
and provides an auditable, cryptographic Sandbox engine for testing.
"""

import abc
import hashlib
import hmac
import json
import logging
import urllib.parse
from decimal import Decimal
try:
    import requests
except ImportError:
    requests = None
from django.conf import settings

logger = logging.getLogger(__name__)


class GatewayError(Exception):
    """Base exception for payment gateway operations."""
    pass


class SignatureVerificationError(GatewayError):
    """Raised when webhook signature verification fails."""
    pass


class PaymentGatewayAdapter(abc.ABC):
    """Abstract interface defining the payment gateway contract."""

    @abc.abstractmethod
    def create_payment_session(self, order, return_url=None):
        """Creates an upstream payment session and returns (payment_id, checkout_url)."""
        pass

    @abc.abstractmethod
    def verify_webhook_signature(self, raw_body_bytes, signature_header):
        """Verifies the HMAC-SHA256 signature of the raw webhook body."""
        pass

    @abc.abstractmethod
    def parse_webhook_payload(self, raw_body_bytes):
        """Parses and validates the raw webhook JSON payload."""
        pass


class YoupiPaymentGateway(PaymentGatewayAdapter):
    """
    Client for sovereign YouPI-PG payment gateway.
    Interacts with YouPI PG Payment Core API on port 6100 (or configured URL)
    and validates HMAC-SHA256 signed webhooks.
    """

    def __init__(self, api_url=None, merchant_id=None, webhook_secret=None):
        self.api_url = (api_url or getattr(settings, 'YOUPI_PG_API_URL', 'http://127.0.0.1:6100')).rstrip('/')
        self.merchant_id = merchant_id or getattr(settings, 'YOUPI_PG_MERCHANT_ID', 'mer_patientcare_default')
        self.webhook_secret = webhook_secret or getattr(settings, 'YOUPI_PG_WEBHOOK_SECRET', 'whsec_patientcare_super_secure_secret_2026')

    def create_payment_session(self, order, return_url=None):
        endpoint = f"{self.api_url}/api/v1/payments"
        headers = {
            'Content-Type': 'application/json',
            'X-Merchant-Id': self.merchant_id,
        }

        resolved_return_url = return_url or order.return_url or f"/frontend/pages/patient-dashboard.html?order_id={order.order_id}"

        payload = {
            'orderId': order.order_id,
            'amount': f"{order.amount:.2f}",
            'currency': order.currency or 'INR',
            'returnUrl': resolved_return_url,
            'metadata': {
                'patient_id': order.patient.patient_id,
                'patient_name': order.patient.full_name,
                'provider_category': order.provider_category,
                'provider_id': order.provider_id,
                'service_description': order.service_description,
                'contribution_rate': str(order.contribution_rate),
                'amount_paise': order.amount_paise,
            }
        }

        if requests is None:
            raise GatewayError("The 'requests' package is required for live gateway communication. Please install requests.")
        try:
            logger.info("Initiating YouPI PG payment session for order %s at %s", order.order_id, endpoint)
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if resp.status_code not in (200, 201):
                logger.warning("YouPI PG API returned HTTP %s: %s", resp.status_code, resp.text)
                raise GatewayError(f"Gateway rejected order creation with HTTP {resp.status_code}: {resp.text}")

            data = resp.json()
            payment_id = data.get('paymentId', '')
            checkout_url = data.get('checkoutUrl', '')
            return {
                'payment_id': payment_id,
                'checkout_url': checkout_url,
                'raw_response': data,
            }
        except requests.RequestException as exc:
            logger.error("Failed to connect to YouPI PG API: %s", str(exc))
            raise GatewayError(f"Could not reach payment gateway server: {str(exc)}") from exc

    def verify_webhook_signature(self, raw_body_bytes, signature_header):
        if not signature_header:
            logger.warning("Webhook received without signature header.")
            raise SignatureVerificationError("Missing X-Gateway-Signature header.")

        # Signature format can be 'sha256=<hex>' or raw hex
        provided_sig = signature_header.strip()
        if provided_sig.startswith('sha256='):
            provided_sig = provided_sig[7:]

        expected_sig = hmac.new(
            self.webhook_secret.encode('utf-8'),
            raw_body_bytes,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(provided_sig.lower(), expected_sig.lower()):
            logger.error("HMAC signature mismatch. Provided: %s..., Expected: %s...", provided_sig[:8], expected_sig[:8])
            raise SignatureVerificationError("Cryptographic signature mismatch.")

        return True

    def parse_webhook_payload(self, raw_body_bytes):
        try:
            data = json.loads(raw_body_bytes.decode('utf-8'))
            return data
        except Exception as exc:
            raise GatewayError(f"Invalid JSON payload: {str(exc)}") from exc


class SandboxPaymentGateway(PaymentGatewayAdapter):
    """
    Deterministic Sandbox / Simulation Gateway.
    Simulates YouPI PG hosted checkout and emits verifiable HMAC-SHA256 signatures.
    Ensures CI/CD tests, development environments, and deployments succeed without
    requiring an active Android cellular phone or external SMS scraper.
    """

    def __init__(self, webhook_secret=None):
        self.webhook_secret = webhook_secret or getattr(settings, 'YOUPI_PG_WEBHOOK_SECRET', 'whsec_patientcare_super_secure_secret_2026')

    def create_payment_session(self, order, return_url=None):
        payment_id = f"PAY-SIM-{order.order_id}"
        resolved_return_url = return_url or order.return_url or f"/frontend/pages/patient-dashboard.html?order_id={order.order_id}"

        # Generate hosted sandbox checkout URL pointing to PatientCare checkout modal/page
        checkout_url = f"/frontend/pages/patient-dashboard.html?pay_order={order.order_id}"

        return {
            'payment_id': payment_id,
            'checkout_url': checkout_url,
            'raw_response': {
                'paymentId': payment_id,
                'orderId': order.order_id,
                'amount': f"{order.amount:.2f}",
                'status': 'ACTIVE',
                'checkoutUrl': checkout_url,
                'mode': 'SANDBOX_SIMULATION',
            }
        }

    def verify_webhook_signature(self, raw_body_bytes, signature_header):
        if not signature_header:
            raise SignatureVerificationError("Missing X-Gateway-Signature header.")

        provided_sig = signature_header.strip()
        if provided_sig.startswith('sha256='):
            provided_sig = provided_sig[7:]

        expected_sig = hmac.new(
            self.webhook_secret.encode('utf-8'),
            raw_body_bytes,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(provided_sig.lower(), expected_sig.lower()):
            raise SignatureVerificationError("Cryptographic signature mismatch.")

        return True

    def parse_webhook_payload(self, raw_body_bytes):
        try:
            return json.loads(raw_body_bytes.decode('utf-8'))
        except Exception as exc:
            raise GatewayError(f"Invalid JSON in webhook payload: {str(exc)}") from exc

    def create_signed_webhook_payload(self, order, event='SUCCESS', utr=None):
        """
        Helper for testing and sandbox simulations:
        Generates a valid webhook payload and its matching HMAC-SHA256 header.
        """
        simulated_utr = utr or f"UTR{order.created_at.strftime('%Y%m%d%H%M%S')}{order.id:04d}"
        payload = {
            'event': event,
            'orderId': order.order_id,
            'paymentId': order.gateway_payment_id or f"PAY-SIM-{order.order_id}",
            'amount': f"{order.amount:.2f}",
            'currency': order.currency or 'INR',
            'utr': simulated_utr,
            'metadata': {
                'patient_id': order.patient.patient_id,
                'provider_category': order.provider_category,
                'provider_id': order.provider_id,
                'amount_paise': order.amount_paise,
            }
        }
        raw_body_bytes = json.dumps(payload).encode('utf-8')
        sig = hmac.new(self.webhook_secret.encode('utf-8'), raw_body_bytes, hashlib.sha256).hexdigest()
        return raw_body_bytes, f"sha256={sig}"


def get_payment_gateway():
    """
    Gateway Factory:
    Returns YoupiPaymentGateway if configured in 'live' mode, else SandboxPaymentGateway.
    """
    mode = getattr(settings, 'PAYMENT_GATEWAY_MODE', 'sandbox').lower()
    if mode == 'live':
        return YoupiPaymentGateway()
    return SandboxPaymentGateway()
