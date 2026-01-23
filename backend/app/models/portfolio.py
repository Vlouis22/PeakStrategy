# app/models/portfolio.py
from datetime import datetime
from typing import List, Dict, Any

class Portfolio:
    """Portfolio model for Firestore operations"""
    
    @staticmethod
    def create(uid: str, name: str, holdings: List[Dict[str, Any]], portfolio_id: str = None):
        """
        Create a new portfolio document structure
        
        Args:
            uid: User ID
            name: Portfolio name
            holdings: List of holding dictionaries
            portfolio_id: Optional custom ID (generated if not provided)
            
        Returns:
            Dictionary with portfolio data
        """
        from datetime import datetime
        import uuid
        
        portfolio_id = portfolio_id or str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        # Calculate total cost basis
        total_cost_basis = sum(float(h.get('shares', 0)) * float(h.get('averageCost', 0)) for h in holdings)
        
        return {
            'id': portfolio_id,
            'uid': uid,
            'name': name.strip(),
            'holdings': holdings,
            'createdAt': current_time,
            'updatedAt': current_time,
            'totalCostBasis': total_cost_basis
        }
    
    @staticmethod
    def validate_holding(holding: Dict[str, Any]) -> tuple:
        """
        Validate a holding object
        
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['symbol', 'shares', 'averageCost']
        
        for field in required_fields:
            if field not in holding:
                return False, f"Missing required field: {field}"
        
        try:
            shares = float(holding['shares'])
            avg_cost = float(holding['averageCost'])
            
            if shares <= 0:
                return False, "Shares must be greater than 0"
            if avg_cost <= 0:
                return False, "Average cost must be greater than 0"
                
        except (ValueError, TypeError):
            return False, "Invalid number format for shares or average cost"
        
        return True, None
    
    @staticmethod
    def calculate_cost_basis(holdings: List[Dict[str, Any]]) -> float:
        """Calculate total cost basis for all holdings"""
        try:
            return sum(float(h.get('shares', 0)) * float(h.get('averageCost', 0)) for h in holdings)
        except (ValueError, TypeError):
            return 0.0