from marshmallow import Schema, fields, validate, ValidationError
import re

class SignupRequest(Schema):
    """Signup request validation schema."""
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=8, max=128),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
                error="Password must contain uppercase, lowercase, and numbers"
            )
        ]
    )
    display_name = fields.String(
        validate=validate.Length(min=2, max=50)
    )
    
    class Meta:
        strict = True

class LoginRequest(Schema):
    """Login request validation schema."""
    email = fields.Email(required=True)
    password = fields.String(required=True)