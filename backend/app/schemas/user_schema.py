from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from datetime import datetime

class UpdateProfileRequest(Schema):
    """Schema for updating user profile."""
    display_name = fields.String(
        validate=validate.Length(min=2, max=50),
        required=False
    )
    preferences = fields.Dict(required=False)
    
    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        """Ensure at least one field is provided."""
        if not data:
            raise ValidationError("At least one field must be provided for update")

class PublicProfileSchema(Schema):
    """Schema for public user profile."""
    uid = fields.String(required=True)
    display_name = fields.String(required=True)
    created_at = fields.DateTime(required=False)
    
    class Meta:
        strict = True

class UserSearchSchema(Schema):
    """Schema for user search parameters."""
    email = fields.Email(required=False)
    display_name = fields.String(required=False)
    limit = fields.Integer(
        validate=validate.Range(min=1, max=100),
        missing=10
    )
    offset = fields.Integer(
        validate=validate.Range(min=0),
        missing=0
    )
    
    @validates_schema
    def validate_search_criteria(self, data, **kwargs):
        """Ensure at least one search criteria is provided."""
        if not data.get('email') and not data.get('display_name'):
            raise ValidationError("Either email or display_name must be provided")