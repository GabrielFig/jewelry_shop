"""
Concrete Payment Strategy implementations.

To integrate a real payment gateway, subclass AbstractPaymentStrategy and
implement the process() method. Register the new strategy in the service layer.

Example — adding PayPal:

    class PayPalStrategy(AbstractPaymentStrategy):
        def __init__(self, client_id: str, secret: str):
            self.client_id = client_id
            self.secret = secret

        def process(self, order: Order) -> bool:
            # call PayPal SDK here
            return True
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.models import AbstractPaymentStrategy

if TYPE_CHECKING:
    from app.domain.models import Order


class MockPaymentStrategy(AbstractPaymentStrategy):
    """
    Always succeeds. Use during development and automated testing.
    """

    def process(self, order: "Order") -> bool:
        return True


class CreditCardPaymentStrategy(AbstractPaymentStrategy):
    """
    Placeholder for a real credit-card gateway (Stripe, Braintree, etc.).
    Replace the process() body with the actual SDK call.
    """

    def __init__(self, token: str):
        self.token = token

    def process(self, order: "Order") -> bool:
        # Example: stripe.PaymentIntent.create(amount=..., currency=..., payment_method=self.token)
        return True


PAYMENT_STRATEGIES = {
    "mock": MockPaymentStrategy,
    "credit_card": CreditCardPaymentStrategy,
}


def get_payment_strategy(method: str, **kwargs) -> AbstractPaymentStrategy:
    """
    Factory helper — returns an instantiated payment strategy.

    Usage:
        strategy = get_payment_strategy("mock")
        strategy = get_payment_strategy("credit_card", token="tok_visa")
    """
    cls = PAYMENT_STRATEGIES.get(method)
    if cls is None:
        raise ValueError(
            f"Unknown payment method '{method}'. "
            f"Available: {list(PAYMENT_STRATEGIES.keys())}"
        )
    return cls(**kwargs)
