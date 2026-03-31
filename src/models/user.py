"""User profile collected on the KYC landing page."""
from dataclasses import dataclass


@dataclass
class UserProfile:
    name: str
    email: str
    department: str
    position: str

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        return cls(
            name=data["name"],
            email=data["email"],
            department=data["department"],
            position=data["position"],
        )
