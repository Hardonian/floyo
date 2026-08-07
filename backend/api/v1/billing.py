"""Billing and subscription API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from backend.database import get_db
from database.models import User, Subscription, SubscriptionPlan, BillingEvent
from backend.monetization import SubscriptionManager, BillingManager
from backend.stripe_integration import StripeIntegration
from backend.auth.utils import get_current_user
from backend.rate_limit import limiter, RATE_LIMIT_PER_MINUTE
import logging

logger = logging.getLogger(__name__)

billing_router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
router = billing_router


@billing_router.post("/subscribe")
@limiter.limit("10/hour")  # Restrictive for payment operations
async def subscribe(
    request: Request,
    plan_id: UUID,
    billing_cycle: str = "monthly",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Subscribe to a plan."""
    try:
        # Get plan
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.is_active == True
        ).first()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        # Check if user already has active subscription
        existing = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active subscription"
            )
        
        # Create Stripe checkout session
        checkout_session = StripeIntegration.create_checkout_session(
            db=db,
            user_id=current_user.id,
            plan_id=plan_id,
            billing_cycle=billing_cycle,
        )
        
        return {
            "checkout_url": checkout_session["url"],
            "session_id": checkout_session["id"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )


@billing_router.post("/cancel")
@limiter.limit("5/hour")  # Restrictive for cancellation
async def cancel_subscription(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel current subscription."""
    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )
        
        # Cancel via Stripe
        StripeIntegration.cancel_subscription(
            db=db,
            subscription_id=subscription.id,
            user_id=current_user.id,
        )
        
        return {
            "message": "Subscription cancelled successfully",
            "status": "cancelled",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel subscription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@billing_router.get("/invoices")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def get_invoices(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0,
):
    """Get invoice history."""
    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(["active", "cancelled"])
        ).first()
        
        if not subscription:
            return []
        
        invoices = db.query(BillingEvent).filter(
            BillingEvent.subscription_id == subscription.id,
            BillingEvent.event_type == "invoice.paid"
        ).order_by(BillingEvent.created_at.desc()).limit(limit).offset(offset).all()
        
        return [
            {
                "id": str(invoice.id),
                "amount": invoice.amount,
                "currency": invoice.currency,
                "status": invoice.status,
                "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
                "invoice_url": invoice.metadata.get("invoice_url") if invoice.metadata else None,
            }
            for invoice in invoices
        ]
    except Exception as e:
        logger.error(f"Get invoices error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch invoices"
        )


@billing_router.get("/payment-methods")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def get_payment_methods(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get payment methods."""
    try:
        payment_methods = StripeIntegration.get_payment_methods(
            db=db,
            user_id=current_user.id,
        )
        
        return payment_methods
    except Exception as e:
        logger.error(f"Get payment methods error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment methods"
        )


@billing_router.post("/payment-methods")
@limiter.limit("10/hour")  # Restrictive for payment method operations
async def add_payment_method(
    request: Request,
    payment_method_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a payment method."""
    try:
        result = StripeIntegration.add_payment_method(
            db=db,
            user_id=current_user.id,
            payment_method_id=payment_method_id,
        )
        
        return result
    except Exception as e:
        logger.error(f"Add payment method error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add payment method"
        )
