"""SQLAlchemy database models for Floyo."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import json

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Float, 
    TIMESTAMP, ForeignKey, ARRAY, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY as PGARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True, index=True)
    email_verification_expires = Column(TIMESTAMP(timezone=True), nullable=True)
    password_reset_token = Column(String(255), nullable=True, index=True)
    password_reset_expires = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    patterns = relationship("Pattern", back_populates="user", cascade="all, delete-orphan")
    relationships = relationship("FileRelationship", back_populates="user", cascade="all, delete-orphan")
    temporal_patterns_rel = relationship("TemporalPattern", back_populates="user", cascade="all, delete-orphan")
    suggestions = relationship("Suggestion", back_populates="user", cascade="all, delete-orphan")
    config = relationship("UserConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    organization_memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    integrations = relationship("UserIntegration", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    """User session/token model."""
    __tablename__ = "user_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    device_info = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_used_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")


class Event(Base):
    """Event model for tracking user actions."""
    __tablename__ = "events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    file_path = Column(Text, nullable=True)
    tool = Column(String(100), nullable=True)
    operation = Column(String(50), nullable=True)
    details = Column(JSONB, nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="events")

    __table_args__ = (
        Index('idx_events_user_timestamp', 'user_id', 'timestamp'),
    )


class Pattern(Base):
    """Pattern model for file type usage patterns."""
    __tablename__ = "patterns"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_extension = Column(String(20), nullable=True)
    count = Column(Integer, default=0)
    last_used = Column(TIMESTAMP(timezone=True), nullable=True)
    tools = Column(PGARRAY(String), nullable=True)
    pattern_metadata = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="patterns")

    __table_args__ = (
        Index('idx_patterns_user_extension', 'user_id', 'file_extension', unique=True),
        Index('idx_patterns_user_updated', 'user_id', 'updated_at'),
    )


class FileRelationship(Base):
    """File relationship model."""
    __tablename__ = "relationships"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_file = Column(Text, nullable=False)
    target_file = Column(Text, nullable=False)
    relation_type = Column(String(50), nullable=False)
    weight = Column(Integer, default=1)
    first_seen = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_seen = Column(TIMESTAMP(timezone=True), server_default=func.now())
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="relationships")


class TemporalPattern(Base):
    """Temporal pattern model."""
    __tablename__ = "temporal_patterns"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence = Column(Text, nullable=False)
    count = Column(Integer, default=1)
    avg_time_gap = Column(Float, nullable=True)
    files = Column(JSONB, nullable=True)
    temporal_metadata = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="temporal_patterns_rel")


class Suggestion(Base):
    """Integration suggestion model."""
    __tablename__ = "suggestions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger = Column(Text, nullable=False)
    tools_involved = Column(PGARRAY(String), nullable=True)
    suggested_integration = Column(Text, nullable=False)
    sample_code = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    actual_files = Column(PGARRAY(Text), nullable=True)
    confidence = Column(Float, default=0.5)
    is_dismissed = Column(Boolean, default=False)
    is_applied = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    viewed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="suggestions")

    __table_args__ = (
        Index('idx_suggestions_user_confidence', 'user_id', 'confidence'),
        Index('idx_suggestions_user_dismissed', 'user_id', 'is_dismissed'),
    )


class UserConfig(Base):
    """User configuration model."""
    __tablename__ = "user_configs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    monitored_directories = Column(PGARRAY(Text), nullable=True)
    exclude_patterns = Column(PGARRAY(Text), nullable=True)
    tracking_config = Column(JSONB, nullable=True)
    suggestions_config = Column(JSONB, nullable=True)
    privacy_config = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="config")


class Organization(Base):
    """Organization/Workspace model for multi-tenant support."""
    __tablename__ = "organizations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    subscription_tier = Column(String(50), default="free")  # free, pro, enterprise
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, nullable=True)  # Organization-specific settings
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    workflows_org = relationship("Workflow", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    """Organization membership with roles."""
    __tablename__ = "organization_members"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="member")  # owner, admin, member, viewer
    joined_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")

    __table_args__ = (
        Index('idx_org_member_unique', 'organization_id', 'user_id', unique=True),
    )


class Role(Base):
    """RBAC role definitions."""
    __tablename__ = "roles"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSONB, nullable=False)  # List of permission strings
    is_system = Column(Boolean, default=False)  # System roles can't be deleted
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    """Audit trail for all operations."""
    __tablename__ = "audit_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, login, etc.
    resource_type = Column(String(100), nullable=False)  # event, pattern, workflow, etc.
    resource_id = Column(PGUUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=True)  # Additional context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

    organization = relationship("Organization", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_org_created', 'organization_id', 'created_at'),
        Index('idx_audit_user_created', 'user_id', 'created_at'),
    )


class WorkflowVersion(Base):
    """Workflow versioning for rollback capability."""
    __tablename__ = "workflow_versions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(PGUUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    steps = Column(JSONB, nullable=False)
    change_summary = Column(Text, nullable=True)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

    workflow = relationship("Workflow", back_populates="versions")


class WorkflowExecution(Base):
    """Workflow execution history."""
    __tablename__ = "workflow_executions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(PGUUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    triggered_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    execution_log = Column(JSONB, nullable=True)  # Step-by-step execution details
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

    workflow = relationship("Workflow", back_populates="executions")

    __table_args__ = (
        Index('idx_workflow_exec_status', 'workflow_id', 'status', 'created_at'),
    )


class IntegrationConnector(Base):
    """Pre-built integration connectors."""
    __tablename__ = "integration_connectors"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    service_type = Column(String(100), nullable=False, index=True)  # github, slack, googledrive, etc.
    description = Column(Text, nullable=True)
    config_schema = Column(JSONB, nullable=False)  # JSON schema for configuration
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System connectors can't be deleted
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class UserIntegration(Base):
    """User-configured integrations."""
    __tablename__ = "user_integrations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    connector_id = Column(PGUUID(as_uuid=True), ForeignKey("integration_connectors.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    config = Column(JSONB, nullable=False)  # Encrypted connection credentials
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_user_integration_user_active', 'user_id', 'is_active'),
    )
    last_sync_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="integrations")
    organization = relationship("Organization")
    connector = relationship("IntegrationConnector")


class Workflow(Base):
    """Workflow model for user-defined workflows."""
    __tablename__ = "workflows"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    steps = Column(JSONB, nullable=False)
    schedule_config = Column(JSONB, nullable=True)  # Cron schedule, triggers, etc.
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="workflows")
    organization = relationship("Organization", back_populates="workflows_org")
    versions = relationship("WorkflowVersion", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    shares = relationship("WorkflowShare", back_populates="workflow", cascade="all, delete-orphan")


class Referral(Base):
    """Referral code model for viral growth."""
    __tablename__ = "referrals"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    referrer_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    usage_count = Column(Integer, default=0)
    reward_count = Column(Integer, default=0)
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    referrer = relationship("User", foreign_keys=[referrer_id])
    rewards = relationship("ReferralReward", back_populates="referral", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_referrals_code', 'code', unique=True),
    )


class ReferralReward(Base):
    """Referral reward tracking."""
    __tablename__ = "referral_rewards"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    referral_id = Column(PGUUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True)
    referrer_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    referred_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reward_type = Column(String(50), nullable=False)  # signup, signup_bonus, activation, etc.
    reward_value = Column(Integer, default=1)
    status = Column(String(50), default="pending")  # pending, granted, expired
    granted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    referral = relationship("Referral", back_populates="rewards")
    referrer = relationship("User", foreign_keys=[referrer_id])
    referred_user = relationship("User", foreign_keys=[referred_user_id])
    
    __table_args__ = (
        Index('idx_referral_rewards_status', 'referral_id', 'status'),
    )


class RetentionCampaign(Base):
    """Retention campaign tracking."""
    __tablename__ = "retention_campaigns"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_type = Column(String(50), nullable=False)  # weekly_digest, activation, re_engagement, etc.
    content = Column(JSONB, nullable=False)
    status = Column(String(50), default="pending")  # pending, sent, opened, clicked
    scheduled_at = Column(TIMESTAMP(timezone=True), nullable=False)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    opened_at = Column(TIMESTAMP(timezone=True), nullable=True)
    clicked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_retention_campaigns_user_status', 'user_id', 'status', 'scheduled_at'),
    )


class WorkflowShare(Base):
    """Workflow sharing for marketplace/ecosystem."""
    __tablename__ = "workflow_shares"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(PGUUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    share_code = Column(String(100), unique=True, nullable=False, index=True)
    share_type = Column(String(50), default="public")  # public, unlisted, private
    created_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    view_count = Column(Integer, default=0)
    fork_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    workflow = relationship("Workflow", back_populates="shares")
    creator = relationship("User", foreign_keys=[created_by_id])
    
    __table_args__ = (
        Index('idx_workflow_shares_code', 'share_code', unique=True),
    )


class SubscriptionPlan(Base):
    """Subscription plan definitions."""
    __tablename__ = "subscription_plans"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    tier = Column(String(50), nullable=False, index=True)  # free, pro, enterprise
    description = Column(Text, nullable=True)
    price_monthly = Column(Float, nullable=False)
    price_yearly = Column(Float, nullable=False)
    features = Column(JSONB, nullable=False)  # Feature flags
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    """User/organization subscription."""
    __tablename__ = "subscriptions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    plan_id = Column(PGUUID(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    billing_cycle = Column(String(20), nullable=False)  # monthly, yearly
    status = Column(String(50), nullable=False, default="active")  # active, canceled, past_due, expired
    price = Column(Float, nullable=False)
    current_period_start = Column(TIMESTAMP(timezone=True), nullable=False)
    current_period_end = Column(TIMESTAMP(timezone=True), nullable=False)
    canceled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True, index=True)  # External billing system
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    billing_events = relationship("BillingEvent", back_populates="subscription", cascade="all, delete-orphan")
    usage_metrics = relationship("UsageMetric", back_populates="subscription", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_subscriptions_status', 'status', 'current_period_end'),
    )


class UsageMetric(Base):
    """Usage metrics for billing and limits."""
    __tablename__ = "usage_metrics"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    metric_type = Column(String(50), nullable=False)  # events, workflows, api_calls, storage, etc.
    amount = Column(Integer, default=0)
    period_start = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    period_end = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    subscription = relationship("Subscription", back_populates="usage_metrics")
    
    __table_args__ = (
        Index('idx_usage_metrics_period', 'user_id', 'metric_type', 'period_start'),
        Index('idx_usage_metrics_org_period', 'organization_id', 'metric_type', 'period_start'),
    )


class BillingEvent(Base):
    """Billing events (invoices, payments, refunds)."""
    __tablename__ = "billing_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # invoice, payment, refund, charge_failed, etc.
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="pending")  # pending, completed, failed, refunded
    billing_metadata = Column(JSONB, nullable=True)  # Additional event data
    external_id = Column(String(255), nullable=True, index=True)  # Stripe invoice ID, etc.
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    subscription = relationship("Subscription", back_populates="billing_events")
    
    __table_args__ = (
        Index('idx_billing_events_subscription', 'subscription_id', 'created_at'),
    )


class SSOProvider(Base):
    """SSO provider configuration (SAML, OIDC)."""
    __tablename__ = "sso_providers"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    provider_type = Column(String(50), nullable=False)  # saml, oidc
    config = Column(JSONB, nullable=False)  # Provider-specific configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    connections = relationship("SSOConnection", back_populates="provider")


class SSOConnection(Base):
    """SSO connection for organizations."""
    __tablename__ = "sso_connections"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    provider_id = Column(PGUUID(as_uuid=True), ForeignKey("sso_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    config = Column(JSONB, nullable=False)  # Connection-specific config
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    organization = relationship("Organization")
    provider = relationship("SSOProvider", back_populates="connections")
    
    __table_args__ = (
        Index('idx_sso_connections_org', 'organization_id', unique=True),
    )


class ComplianceReport(Base):
    """Compliance reports (GDPR, SOC2, etc.)."""
    __tablename__ = "compliance_reports"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)  # gdpr, soc2, hipaa, etc.
    report_data = Column(JSONB, nullable=False)
    status = Column(String(50), default="pending")  # pending, completed, failed
    generated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    organization = relationship("Organization")
    
    __table_args__ = (
        Index('idx_compliance_reports_org_type', 'organization_id', 'report_type', 'generated_at'),
    )


class EnterpriseSettings(Base):
    """Enterprise organization settings."""
    __tablename__ = "enterprise_settings"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    settings = Column(JSONB, nullable=False)  # Enterprise-specific settings
    compliance_config = Column(JSONB, nullable=True)  # Compliance requirements
    security_config = Column(JSONB, nullable=True)  # Security settings
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    organization = relationship("Organization")
    
    __table_args__ = (
        Index('idx_enterprise_settings_org', 'organization_id', unique=True),
    )


class TwoFactorAuth(Base):
    """Two-factor authentication for users."""
    __tablename__ = "two_factor_auth"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    secret = Column(String(255), nullable=True)  # TOTP secret (encrypted)
    is_enabled = Column(Boolean, default=False)
    backup_codes = Column(PGARRAY(String), nullable=True)  # Backup codes
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_two_factor_auth_user', 'user_id', unique=True),
    )


class SecurityAudit(Base):
    """Security audit log for security events."""
    __tablename__ = "security_audits"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # failed_login, password_change, 2fa_enabled, etc.
    severity = Column(String(50), nullable=False, index=True)  # low, medium, high, critical
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_security_audit_user_created', 'user_id', 'created_at'),
        Index('idx_security_audit_severity', 'severity', 'created_at'),
    )


class GuardianEvent(Base):
    """Guardian privacy monitoring events."""
    __tablename__ = "guardian_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    scope = Column(String(50), nullable=False)  # user, app, api, external
    data_class = Column(String(50), nullable=False)  # telemetry, location, audio, etc.

    # Description
    description = Column(Text, nullable=True)
    data_touched = Column(JSONB, nullable=True)
    purpose = Column(Text, nullable=True)

    # Risk assessment
    risk_level = Column(String(50), nullable=False, index=True)  # low, medium, high, critical
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_factors = Column(PGARRAY(String), nullable=True)

    # Guardian action
    guardian_action = Column(String(50), nullable=False)  # allow, mask, redact, block, alert
    action_reason = Column(Text, nullable=True)

    # User context
    user_decision = Column(String(50), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    mfa_required = Column(Boolean, default=False)

    # Metadata
    source = Column(String(255), nullable=True)
    guardian_metadata = Column(JSONB, nullable=True)

    # Timestamps
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_guardian_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_guardian_risk_level', 'risk_level', 'timestamp'),
        Index('idx_guardian_event_type', 'event_type', 'timestamp'),
    )


class TrustLedgerRoot(Base):
    """Daily hash roots for trust ledger verification."""
    __tablename__ = "trust_ledger_roots"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(TIMESTAMP(timezone=True), nullable=False, index=True)  # Date (time set to 00:00:00)
    hash_root = Column(String(255), nullable=False, index=True)  # SHA256 hash of day's entries
    entry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_trust_ledger_user_date', 'user_id', 'date', unique=True),
    )


class TrustFabricModel(Base):
    """User's Trust Fabric AI model for adaptive learning."""
    __tablename__ = "trust_fabric_models"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Learning parameters
    privacy_mode_toggles = Column(Integer, default=0)  # How often user toggles privacy modes
    disabled_signals = Column(PGARRAY(String), nullable=True)  # Which signals user disabled
    trust_responses = Column(JSONB, nullable=True)  # History of allow/deny decisions
    
    # Adaptive risk weights
    risk_weights = Column(JSONB, nullable=True)  # Personalized risk weights
    comfort_zones = Column(JSONB, nullable=True)  # User's comfort zones per data class
    
    # Statistics
    total_events_assessed = Column(Integer, default=0)
    avg_risk_score = Column(Float, default=0.0)
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_trust_fabric_user', 'user_id', unique=True),
    )


class GuardianSettings(Base):
    """User's Guardian privacy settings."""
    __tablename__ = "guardian_settings"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Mode toggles
    private_mode_enabled = Column(Boolean, default=False)
    lockdown_enabled = Column(Boolean, default=False)
    
    # Sensitive context detection
    sensitive_context_detection = Column(Boolean, default=True)
    camera_active = Column(Boolean, default=False)
    microphone_active = Column(Boolean, default=False)
    
    # MFA bubble settings
    mfa_bubble_enabled = Column(Boolean, default=True)
    elevated_session_expiry_minutes = Column(Integer, default=15)
    
    # Trust level
    trust_level = Column(String(50), default="balanced")  # strict, balanced, permissive
    
    # Metadata
    settings = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_guardian_settings_user', 'user_id', unique=True),
    )


class MLModel(Base):
    """ML model metadata for tracking trained models."""
    __tablename__ = "ml_models"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    model_type = Column(String(50), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    training_data_hash = Column(String(64), nullable=True)
    accuracy_metrics = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    model_path = Column(String(500), nullable=True)
    training_config = Column(JSONB, nullable=True)
    
    __table_args__ = (
        Index('idx_ml_models_type_active', 'model_type', 'is_active'),
    )


class Prediction(Base):
    """Track ML predictions for evaluation."""
    __tablename__ = "predictions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    model_id = Column(PGUUID(as_uuid=True), ForeignKey("ml_models.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    prediction_type = Column(String(50), nullable=False)
    input_features = Column(JSONB, nullable=True)
    prediction_result = Column(JSONB, nullable=False)
    confidence = Column(Float, nullable=True)
    actual_outcome = Column(JSONB, nullable=True)  # For evaluation
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_predictions_user_created', 'user_id', 'created_at'),
        Index('idx_predictions_model_type', 'model_id', 'prediction_type'),
    )


class Notification(Base):
    """Notification model for in-app and email notifications."""
    __tablename__ = "notifications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)  # info, success, warning, error
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSONB, nullable=True)
    read = Column(Boolean, default=False, index=True)
    action_url = Column(String(500), nullable=True)
    action_label = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    read_at = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index('idx_notifications_user_read', 'user_id', 'read', 'created_at'),
    )


class UTMTrack(Base):
    """UTM tracking for attribution and growth metrics."""
    __tablename__ = "utm_tracks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    source = Column(String(100), nullable=True, index=True)  # google, facebook, twitter, newsletter, etc.
    medium = Column(String(100), nullable=True, index=True)  # cpc, organic, email, referral, etc.
    campaign = Column(String(255), nullable=True, index=True)
    term = Column(String(255), nullable=True)
    content = Column(String(255), nullable=True)
    referrer = Column(Text, nullable=True)
    landing_page = Column(String(500), nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index('idx_utm_tracks_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_utm_tracks_source_medium', 'source', 'medium'),
    )


class PrivacyPrefs(Base):
    """User privacy preferences."""
    __tablename__ = "privacy_prefs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    monitoring_enabled = Column(Boolean, default=False)
    data_retention_days = Column(Integer, default=14)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index('idx_privacy_prefs_user', 'user_id', unique=True),
    )
