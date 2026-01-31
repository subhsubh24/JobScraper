"""Authentication service with JWT tokens and password hashing."""
import os
import json
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import User, UserTier


class AuthService:
    """Handles user authentication, JWT tokens, and tier management."""

    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    JWT_EXPIRY_DAYS = 30

    def __init__(self, db: Session):
        self.db = db

    # ============ PASSWORD HASHING ============

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256 with salt."""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return base64.b64encode(salt + key).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            decoded = base64.b64decode(password_hash.encode('utf-8'))
            salt = decoded[:32]
            stored_key = decoded[32:]
            new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return hmac.compare_digest(stored_key, new_key)
        except Exception:
            return False

    # ============ JWT TOKENS (Simple implementation) ============

    def _base64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    def _base64url_decode(self, data: str) -> bytes:
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data)

    def create_token(self, user: User) -> str:
        """Create a JWT token for a user."""
        header = {"alg": "HS256", "typ": "JWT"}

        exp_time = datetime.utcnow() + timedelta(days=self.JWT_EXPIRY_DAYS)
        payload = {
            "user_id": user.id,
            "email": user.email,
            "tier": user.tier.value if isinstance(user.tier, UserTier) else user.tier,
            "exp": int(exp_time.timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
        }

        header_b64 = self._base64url_encode(json.dumps(header).encode())
        payload_b64 = self._base64url_encode(json.dumps(payload).encode())

        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.JWT_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = self._base64url_encode(signature)

        return f"{message}.{signature_b64}"

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify a JWT token and return the payload."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None

            header_b64, payload_b64, signature_b64 = parts

            # Verify signature
            message = f"{header_b64}.{payload_b64}"
            expected_sig = hmac.new(
                self.JWT_SECRET.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            actual_sig = self._base64url_decode(signature_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            # Decode payload
            payload = json.loads(self._base64url_decode(payload_b64))

            # Check expiration
            if payload.get('exp', 0) < datetime.utcnow().timestamp():
                return None

            return payload
        except Exception:
            return None

    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get a user from a JWT token."""
        payload = self.verify_token(token)
        if not payload:
            return None

        user = self.db.query(User).filter(User.id == payload["user_id"]).first()
        return user

    # ============ USER MANAGEMENT ============

    def register(self, email: str, password: str, full_name: Optional[str] = None) -> tuple[User, str]:
        """Register a new user and return (user, token)."""
        # Check if user exists
        existing = self.db.query(User).filter(User.email == email.lower()).first()
        if existing:
            raise ValueError("User with this email already exists")

        # Create user
        user = User(
            email=email.lower(),
            password_hash=self.hash_password(password),
            full_name=full_name,
            tier=UserTier.FREE,
        )
        self.db.add(user)
        self.db.flush()  # Get the ID

        token = self.create_token(user)
        return user, token

    def login(self, email: str, password: str) -> tuple[User, str]:
        """Login a user and return (user, token)."""
        user = self.db.query(User).filter(User.email == email.lower()).first()
        if not user:
            raise ValueError("Invalid email or password")

        if not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        token = self.create_token(user)
        return user, token

    # ============ TIER MANAGEMENT ============

    def upgrade_to_premium(self, user: User, receipt_data: Optional[str] = None) -> User:
        """Upgrade a user to premium tier."""
        # In production, verify the App Store / Play Store receipt here
        # For now, just upgrade
        user.tier = UserTier.PREMIUM
        self.db.flush()
        return user

    def check_usage_limits(self, user: User) -> dict:
        """Check if user has exceeded their free tier limits."""
        # Reset monthly limits if needed
        now = datetime.utcnow()
        if user.usage_reset_date and (now - user.usage_reset_date).days >= 30:
            user.jobs_added_this_month = 0
            user.prep_packs_this_month = 0
            user.usage_reset_date = now
            self.db.flush()

        # Free tier limits
        FREE_JOBS_LIMIT = 5
        FREE_PREP_PACKS_LIMIT = 1

        if user.tier == UserTier.PREMIUM:
            return {
                "can_add_job": True,
                "can_generate_prep": True,
                "jobs_remaining": "unlimited",
                "prep_packs_remaining": "unlimited",
            }

        return {
            "can_add_job": user.jobs_added_this_month < FREE_JOBS_LIMIT,
            "can_generate_prep": user.prep_packs_this_month < FREE_PREP_PACKS_LIMIT,
            "jobs_remaining": max(0, FREE_JOBS_LIMIT - user.jobs_added_this_month),
            "prep_packs_remaining": max(0, FREE_PREP_PACKS_LIMIT - user.prep_packs_this_month),
        }

    def increment_job_usage(self, user: User):
        """Increment the job usage counter."""
        user.jobs_added_this_month += 1
        self.db.flush()

    def increment_prep_usage(self, user: User):
        """Increment the prep pack usage counter."""
        user.prep_packs_this_month += 1
        self.db.flush()
