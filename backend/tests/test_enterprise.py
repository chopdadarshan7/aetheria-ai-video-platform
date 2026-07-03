import pytest
import os
import json
from app import models
from app.services.mlops_manager import MLOpsManager
from app.services.billing_manager import BillingManager
from app.services.copilot_service import CopilotService

def test_dataset_upload_validation(db):
    # Verify MLOps auto tag duplicate scanner
    report = MLOpsManager.validate_and_caption_dataset("dummy_storage_path")
    assert report["status"] == "VALIDATED"
    assert report["num_images"] >= 15
    assert "img_0.jpg" in report["auto_captions"]

def test_mlops_training_simulation():
    # Verify loss curves metrics decrease
    step_metrics = MLOpsManager.execute_training_step(epoch=5, total_epochs=10, base_lr=1e-4)
    assert step_metrics["epoch"] == 5
    assert step_metrics["loss"] < 0.45
    assert step_metrics["learning_rate"] < 1e-4

def test_credit_ledger_transactions(db):
    user = models.User(
        username="billinguser",
        email="billing@example.com",
        hashed_password="...",
        credits=100
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    tx = BillingManager.process_credits_transaction(
        db=db,
        user_id=user.id,
        amount=250,
        transaction_type="purchase",
        description="Stripe test checkout"
    )
    assert tx.id is not None
    assert tx.amount == 250
    assert tx.transaction_type == "purchase"
    assert user.credits == 350

def test_api_keys_creation(db):
    user = models.User(
        username="apikeyuser",
        email="api@example.com",
        hashed_password="..."
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    key = models.ApiKey(
        name="Test API Deploy Key",
        key_hash="ath_test_xyz123",
        user_id=user.id
    )
    db.add(key)
    db.commit()
    db.refresh(key)

    assert key.id is not None
    assert key.key_hash == "ath_test_xyz123"

def test_copilot_services():
    # Check prompt enhancer suggestions
    guidance = CopilotService.generate_prompt_guidance("A glowing red spaceship")
    assert "wan-2.1" in guidance["recommended_model"] or "cogvideox-2b" in guidance["recommended_model"]
    assert "glowing red spaceship" in guidance["enhanced_prompt"]

    # Check VRAM estimation calculator
    cost = CopilotService.estimate_rendering_cost(duration=10.0, steps=25)
    assert cost["credits_cost"] == 50
    assert cost["estimated_vram_time_seconds"] > 0.0
