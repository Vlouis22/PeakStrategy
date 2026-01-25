import yfinance as yf
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from .baze_analyzer import BaseAnalyzer


class BusinessIntelligenceAnalyzer(BaseAnalyzer):
    """Institution-grade business intelligence"""
    
    def get_business_intelligence(self) -> Dict[str, Any]:
        """Compile complete institutional-grade business intelligence"""
        return {
            'metadata': {
                'ticker': self.ticker,
                'reportDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                'dataSources': ['Yahoo Finance'],
                'dataQuality': 'Institution-grade'
            },
            'companyOverview': self._get_company_overview(),
            'leadershipGovernance': self._get_leadership_governance(),
            'businessModel': self._get_business_model(),
            'productsServices': self._get_products_services(),
            'strategicPosition': self._get_strategic_position(),
            'operationalMetrics': self._get_operational_metrics(),
            'strategicInitiatives': {'focus': 'Data not available via free APIs'}
        }
    
    def _get_company_overview(self) -> Dict[str, Any]:
        """Concise company overview"""
        summary = self.info.get('longBusinessSummary', '')
        first_sentence = summary.split('.')[0] + '.' if summary else 'N/A'
        
        return {
            'companyName': self.info.get('longName', 'N/A'),
            'ticker': self.ticker,
            'oneLineSummary': first_sentence,
            'sector': self.info.get('sector', 'N/A'),
            'industry': self.info.get('industry', 'N/A'),
            'founded': self._extract_founding_year(summary),
            'headquarters': {
                'city': self.info.get('city', 'N/A'),
                'state': self.info.get('state', 'N/A'),
                'country': self.info.get('country', 'N/A')
            }
        }
    
    def _extract_founding_year(self, summary: str) -> str:
        """Extract founding year from business summary"""
        patterns = [r'founded in (\d{4})', r'established in (\d{4})', r'incorporated in (\d{4})', r'formed in (\d{4})']
        
        for pattern in patterns:
            match = re.search(pattern, summary.lower())
            if match:
                return match.group(1)
        
        return 'N/A'
    
    def _get_leadership_governance(self) -> Dict[str, Any]:
        """Leadership team with validated CEO identification"""
        officers = self.info.get('companyOfficers', [])
        
        ceo = self._validate_ceo(officers)
        
        c_suite = []
        board_members = []
        
        for officer in officers[:15]:
            title = officer.get('title', '').lower()
            exec_data = {
                'name': officer.get('name', 'N/A'),
                'title': officer.get('title', 'N/A'),
                'age': officer.get('age'),
            }
            
            if any(x in title for x in ['chief', 'ceo', 'cfo', 'coo', 'cto']):
                c_suite.append(exec_data)
            elif 'director' in title or 'board' in title:
                board_members.append(exec_data)
        
        return {
            'ceo': ceo,
            'cSuite': c_suite[:8],
            'boardMembers': board_members[:5],
            'governance': {
                'auditRisk': self.info.get('auditRisk', 'N/A'),
                'boardRisk': self.info.get('boardRisk', 'N/A'),
                'compensationRisk': self.info.get('compensationRisk', 'N/A'),
                'overallRisk': self.info.get('overallRisk', 'N/A')
            }
        }
    def _validate_ceo(self, officers: List[Dict]) -> Optional[Dict[str, Any]]:
        """Validate and identify the actual CEO from officer list"""
        if not officers:
            return None
        
        ceo_titles = ['chief executive officer', 'ceo', 'president and ceo', 'chairman and ceo', 
                      'chairman & chief executive officer', 'president & ceo']
        
        for officer in officers:
            title = officer.get('title', '').lower()
            for ceo_title in ceo_titles:
                if ceo_title in title and 'executive vice president' not in title and 'commercial' not in title and 'division' not in title:
                    return {
                        'name': officer.get('name', 'N/A'),
                        'title': officer.get('title', 'N/A'),
                        'age': officer.get('age'),
                        'yearBorn': officer.get('yearBorn'),
                        'validated': True
                    }
        
        if officers:
            return {
                'name': officers[0].get('name', 'N/A'),
                'title': officers[0].get('title', 'N/A'),
                'age': officers[0].get('age'),
                'yearBorn': officers[0].get('yearBorn'),
                'validated': False
            }
        
        return None
    
    def _get_business_model(self) -> Dict[str, Any]:
        """How the company makes money and operates"""
        summary = self.info.get('longBusinessSummary', '')
        sentences = [s.strip() for s in summary.split('.') if s.strip()]
        model_description = '. '.join(sentences[1:4]) + '.' if len(sentences) > 1 else 'N/A'
        
        return {
            'description': model_description,
            'revenueModel': self._infer_revenue_model(),
            'customerSegments': self._infer_customer_segments(),
            'valueProposition': sentences[0] + '.' if sentences else 'N/A',
            'operationalStructure': self.info.get('quoteType', 'N/A')
        }
    
    def _infer_revenue_model(self) -> str:
        """Infer revenue model from sector and industry"""
        sector = self.info.get('sector', '').lower()
        industry = self.info.get('industry', '').lower()
        
        if 'software' in industry or 'technology' in sector:
            return 'Primarily subscription and licensing-based revenue with enterprise sales'
        elif 'retail' in industry:
            return 'Product sales and services revenue'
        elif 'financial' in sector:
            return 'Fee-based and interest income'
        elif 'healthcare' in sector:
            return 'Product sales, services, and licensing'
        return 'Diversified revenue streams'
    
    def _infer_customer_segments(self) -> str:
        """Infer customer segments from industry"""
        industry = self.info.get('industry', '').lower()
        
        if 'enterprise' in industry or 'software' in industry:
            return 'Enterprise customers, government, and SMBs'
        elif 'consumer' in industry:
            return 'End consumers and retail customers'
        return 'B2B and B2C segments'
    
    def _get_products_services(self) -> Dict[str, Any]:
        """Concise summary of core products and services"""
        summary = self.info.get('longBusinessSummary', '')
        sentences = [s.strip() for s in summary.split('.') if s.strip()]
        
        product_sentences = [s for s in sentences if any(
            keyword in s.lower() for keyword in 
            ['product', 'service', 'offer', 'solution', 'platform', 'device']
        )]
        
        product_description = '. '.join(product_sentences[:2]) + '.' if product_sentences else sentences[-1] + '.' if sentences else 'N/A'
        
        return {
            'coreFocus': product_description,
            'primaryOfferings': f"{self.info.get('sector', 'N/A')} sector solutions with focus on {self.info.get('industry', 'N/A')}",
            'sector': self.info.get('sector', 'N/A'),
            'industry': self.info.get('industry', 'N/A')
        }
    
    def _get_strategic_position(self) -> Dict[str, Any]:
        """Competitive positioning and strategic focus"""
        employees = self.info.get('fullTimeEmployees', 0)
        
        return {
            'marketPosition': self._assess_market_position(employees),
            'competitiveAdvantage': 'Market leadership through scale and innovation',
            'geographicPresence': {
                'headquarters': self.info.get('country', 'N/A'),
                'scope': 'Global operations' if employees > 50000 else 'Regional focus'
            },
            'industryContext': {
                'sector': self.info.get('sector', 'N/A'),
                'industry': self.info.get('industry', 'N/A')
            }
        }
    
    def _assess_market_position(self, employees: int) -> str:
        """Assess market position based on company size"""
        if employees >= 100000:
            return 'Large-cap global leader with dominant market position'
        elif employees >= 50000:
            return 'Major player with significant global presence'
        elif employees >= 10000:
            return 'Established mid-to-large cap company with strong market position'
        elif employees >= 5000:
            return 'Mid-cap company with growing market presence'
        return 'Focused player in specialized market segment'
    
    def _get_operational_metrics(self) -> Dict[str, Any]:
        """Operational scale and infrastructure"""
        return {
            'employees': self.info.get('fullTimeEmployees', 'N/A'),
            'locations': {
                'headquarters': f"{self.info.get('city', 'N/A')}, {self.info.get('state', 'N/A')}",
                'country': self.info.get('country', 'N/A')
            },
            'exchange': {
                'listing': self.info.get('exchange', 'N/A'),
                'symbol': self.ticker
            },
            'corporateStructure': self.info.get('quoteType', 'N/A'),
            'website': self.info.get('website', 'N/A'),
            'phone': self.info.get('phone', 'N/A')
        }
