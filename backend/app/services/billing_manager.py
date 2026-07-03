import logging
from sqlalchemy.orm import Session
from app import models
import datetime

logger = logging.getLogger(__name__)

class BillingManager:
    @staticmethod
    def create_checkout_session(user_id: int, plan: str) -> str:
        """
        Creates Stripe subscription checkout sessions.
        Returns mock payment URL for local developer environments.
        """
        logger.info(f"Billing: Creating Stripe checkout session for user {user_id} plan: {plan}")
        return f"http://localhost:3000/saas?payment_success=true&plan={plan}"

    @staticmethod
    def process_credits_transaction(
        db: Session,
        user_id: int,
        amount: int,
        transaction_type: str,
        description: str = None
    ) -> models.CreditTransaction:
        """
        Deducts or credits tokens from user accounts, updating billing balance logs.
        """
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
            
        user.credits += amount
        if user.credits < 0:
            user.credits = 0 # bound credits boundary
            
        tx = models.CreditTransaction(
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            user_id=user_id
        )
        db.add(tx)
        db.add(user)
        db.commit()
        db.refresh(tx)
        
        logger.info(f"Billing: Committed credit change of {amount} for user {user_id}")
        return tx

    @staticmethod
    def verify_subscription_role(db: Session, user_id: int, required_plan: str) -> bool:
        """
        Checks subscription access permissions for enterprise levels.
        """
        sub = db.query(models.Subscription).filter(
            models.Subscription.user_id == user_id,
            models.Subscription.status == "active"
        ).first()
        
        if not sub:
            return required_plan == "free"
            
        plan_rank = {"free": 0, "creator": 1, "enterprise": 2}
        user_rank = plan_rank.get(sub.plan_name, 0)
        req_rank = plan_rank.get(required_plan, 0)
        
        return user_rank >= req_rank
