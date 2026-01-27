import json
import re
from typing import Optional
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
from openai import OpenAI

class CompanySummaryGenerator:
    """
    Generates a company summary page in strict JSON format using multiple AI APIs.
    Tries Gemini models first (with fallback), then DeepSeek as final fallback.
    Extracts company data from comprehensive research JSON and produces investor-focused analysis.
    """

    def __init__(self, api_key: str, deepseek_api_key: str):
        """
        Initialize the generator with API keys for both Gemini and DeepSeek.

        Args:
            api_key (str): Google Gemini API key
            deepseek_api_key (str): DeepSeek API key
        """
        self.api_key = api_key
        self.deepseek_api_key = deepseek_api_key
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-3-flash-preview"
        self.model_id_2 = "gemini-2.5-flash"
        self.openai_client = OpenAI(
            api_key=deepseek_api_key, 
            base_url="https://api.deepseek.com"
        )

    def generate_summary(self, research_data: dict) -> dict:
        """
        Generate a company summary in strict JSON format from research data.
        Tries multiple models with fallback logic: 
        gemini-3-flash-preview → gemini-2.5-flash → deepseek

        Args:
            research_data (dict): Comprehensive company research JSON containing:
                - company_name: Company name
                - ticker: Stock ticker
                - business_understanding: Business model and overview
                - analyst_consensus: Growth and analyst data
                - balance_sheet: Financial health metrics
                - profitability_and_efficiency: Margin and efficiency data
                - shareholder_returns: Dividend and buyback info
                - valuation: Current valuation context

        Returns:
            dict: Parsed JSON with company summary following the required schema
            
        Raises:
            ValueError: If all three models fail to generate valid output
        """
        # Extract relevant data from research JSON
        extracted_data = self._extract_company_data(research_data)
        
        # Build the prompt with company context
        prompt = self._build_prompt(extracted_data)

        # Try models in sequence with fallback logic
        models_to_try = [
            ("gemini", self.model_id, "gemini-3-flash-preview"),
            ("gemini", self.model_id_2, "gemini-2.5-flash"),
            ("deepseek", None, "deepseek"),
        ]
        
        last_error = None
        
        for api_type, model_id, model_name in models_to_try:
            try:
                print(f"Attempting to generate summary with {model_name}...")
                
                if api_type == "gemini":
                    json_output = self._call_gemini_api(prompt, model_id)
                else:  # deepseek
                    json_output = self._call_deepseek_api(prompt)
                
                print(f"✓ Successfully generated summary with {model_name}")
                return json_output
                
            except Exception as e:
                last_error = e
                print(f"✗ Failed with {model_name}: {str(e)}")
                continue
        
        # If all models failed, raise an error
        raise ValueError(
            f"All models failed to generate a valid summary. Last error: {str(last_error)}"
        )

    def _call_gemini_api(self, prompt: str, model_id: str) -> dict:
        """
        Call Gemini API and extract JSON response.

        Args:
            prompt (str): The prompt to send to Gemini
            model_id (str): The Gemini model ID to use

        Returns:
            dict: Parsed JSON response

        Raises:
            Exception: If API call fails or JSON extraction fails
        """
        response = self.client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        # Extract and parse JSON
        json_output = self._extract_json(response.text)
        
        # Validate the output
        is_valid, errors = self.validate_output(json_output)
        if not is_valid:
            raise ValueError(f"Generated JSON failed validation: {errors}")
        
        return json_output

    def _call_deepseek_api(self, prompt: str) -> dict:
        """
        Call DeepSeek API via OpenAI client and extract JSON response.

        Args:
            prompt (str): The prompt to send to DeepSeek

        Returns:
            dict: Parsed JSON response

        Raises:
            Exception: If API call fails or JSON extraction fails
        """
        response = self.openai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        # Extract the response text
        response_text = response.choices[0].message.content
        
        # Extract and parse JSON
        json_output = self._extract_json(response_text)
        
        # Validate the output
        is_valid, errors = self.validate_output(json_output)
        if not is_valid:
            raise ValueError(f"Generated JSON failed validation: {errors}")
        
        return json_output

    def _extract_company_data(self, research_data: dict) -> dict:
        """
        Extract relevant company information from comprehensive research JSON.

        Args:
            research_data (dict): Full research data

        Returns:
            dict: Extracted company data
        """
        # Basic company info
        company_name = research_data.get("company_name", "")
        ticker = research_data.get("ticker", "")
        
        # Business understanding
        business_understanding = research_data.get("business_understanding", {})
        company_overview = business_understanding.get("companyOverview", {})
        business_model = business_understanding.get("businessModel", {})
        
        industry = company_overview.get("industry", "")
        sector = company_overview.get("sector", "")
        business_description = business_model.get("description", "")
        value_proposition = business_model.get("valueProposition", "")
        
        # Extract key products from business description
        key_products = self._extract_products(business_description)
        
        # Geographic presence
        operational_metrics = business_understanding.get("operationalMetrics", {})
        locations = operational_metrics.get("locations", {})
        headquarters = locations.get("headquarters", "United States")
        
        # Leadership
        leadership = business_understanding.get("leadershipGovernance", {})
        ceo = leadership.get("ceo", {})
        ceo_name = ceo.get("name", "")
        
        # Financial context for macro analysis (not for inclusion in output)
        analyst_data = research_data.get("analyst_consensus", {})
        profitability = research_data.get("profitability_and_efficiency", {})
        balance_sheet = research_data.get("balance_sheet", {})
        valuation = research_data.get("valuation", {})
        
        growth_profile = analyst_data.get("growth_profile", {})
        revenue_growth = growth_profile.get("revenue_growth", {}).get("yoy_current", 0)
        earnings_growth = growth_profile.get("earnings_growth", {}).get("yoy_current", 0)
        
        extracted = {
            "company_name": company_name,
            "ticker": ticker,
            "sector": sector,
            "industry": industry,
            "business_description": business_description,
            "value_proposition": value_proposition,
            "key_products": key_products,
            "headquarters": headquarters,
            "ceo_name": ceo_name,
            # Context for analysis (not for output inclusion)
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "margins": profitability.get("metrics", {}),
            "debt_to_equity": balance_sheet.get("debt_to_equity", 0),
            "current_ratio": balance_sheet.get("current_ratio", 1.0),
            "valuation_verdict": valuation.get("scorecard", {}).get("verdict", ""),
        }
        
        return extracted

    def _extract_products(self, description: str) -> list:
        """
        Extract key products/services from business description using intelligent pattern matching.
        Works for any company, not hardcoded for specific companies.

        Args:
            description (str): Business description text

        Returns:
            list: List of key products (up to 8)
        """
        if not description:
            return []
        
        products = []
        description_lower = description.lower()
        
        # Common product/service indicators and patterns
        product_patterns = [
            # Look for capitalized words/phrases (likely product names)
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
        ]
        
        # Extract potential products from capitalized phrases
        import re
        for pattern in product_patterns:
            matches = re.findall(pattern, description)
            products.extend(matches)
        
        # Filter out common non-product words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'company',
            'companies', 'business', 'services', 'products', 'provides', 'offers',
            'develops', 'manufactures', 'produces', 'delivers', 'enables', 'platform',
            'platforms', 'solutions', 'solution', 'global', 'international', 'world',
            'leading', 'major', 'including', 'such', 'operates', 'operates'
        }
        
        # Filter products
        filtered_products = []
        seen = set()
        
        for product in products:
            product_lower = product.lower()
            # Skip if it's a stop word, too short, or already added
            if (product_lower not in stop_words and 
                len(product) > 2 and 
                product_lower not in seen and
                not product[0].isdigit()):
                filtered_products.append(product)
                seen.add(product_lower)
        
        # Also extract products mentioned with keywords like "including", "such as", "offers"
        product_intro_patterns = [
            r'(?:including|such as|offers?|provides?|develops?|manufactures?)\s+([^,.]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:platform|product|service|solution)',
        ]
        
        for pattern in product_intro_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                # Split comma-separated values
                items = [item.strip() for item in match.split(',')]
                for item in items:
                    item_lower = item.lower()
                    if (item_lower not in stop_words and 
                        len(item) > 2 and 
                        item_lower not in seen and
                        not item[0].isdigit()):
                        filtered_products.append(item)
                        seen.add(item_lower)
        
        # Remove duplicates while preserving order
        unique_products = list(dict.fromkeys(filtered_products))
        
        # Return top 8 products
        return unique_products[:8]

    def _build_prompt(self, company_data: dict) -> str:
        """
        Build the prompt for AI models with company context.

        Args:
            company_data (dict): Extracted company information

        Returns:
            str: Formatted prompt
        """
        company_name = company_data.get("company_name", "")
        ticker = company_data.get("ticker", "")
        industry = company_data.get("industry", "")
        sector = company_data.get("sector", "")
        business_description = company_data.get("business_description", "")
        value_proposition = company_data.get("value_proposition", "")
        key_products = company_data.get("key_products", [])
        headquarters = company_data.get("headquarters", "")
        
        products_str = ", ".join(key_products) if key_products else "Software and cloud services"

        prompt = f"""You are an expert investment analyst. Generate a company summary page in strict JSON format for the following company:

Company: {company_name} ({ticker})
Sector: {sector}
Industry: {industry}
Headquarters: {headquarters}
Business: {business_description}
Value Proposition: {value_proposition}
Key Products/Services: {products_str}

CRITICAL INSTRUCTIONS:
1. Do NOT include company name or ticker in the JSON output.
2. Use ONLY neutral, investor-focused language.
3. IGNORE all financial data (earnings, price targets, dividends, buybacks, market cap, valuations).
4. Use external context ONLY for macro sensitivity and latest high-impact headline.
5. Focus on business fundamentals, competitive position, and strategic opportunities/risks.

JSON Schema (follow EXACTLY):
{{
  "company_summary": {{
    "description": {{
      "line_1": "string",
      "line_2": "string",
      "line_3": "string"
    }},
    "bull_case": [
      {{"title": "string (3-6 words)", "explanation": "string (≤20 words)"}},
      {{"title": "string (3-6 words)", "explanation": "string (≤20 words)"}},
      {{"title": "string (3-6 words)", "explanation": "string (≤20 words)"}},
      {{"title": "string (3-6 words)", "explanation": "string (≤20 words)"}},
      {{"title": "string (3-6 words)", "explanation": "string (≤20 words)"}}
    ],
    "bear_case": [
      {{"title": "string (3-6 words)", "explanation": "string (≤20 words)"}},
      {{"title": "string (3-6 words)", "explanation": "string (≤20 words)"}},
      {{"title": "string (3-6 words)", "explanation": "string (≤20 words)"}},
      {{"title": "string (3-6 words)", "explanation": "string (≤20 words)"}},
      {{"title": "string (3-6 words)", "explanation": "string (≤20 words)"}}
    ],
    "macro_sensitivity": {{
      "interest_rates": {{
        "impact": "High | Medium | Low",
        "explanation": "string (1 sentence)"
      }},
      "economic_cycles": {{
        "impact": "High | Medium | Low",
        "explanation": "string (1 sentence)"
      }},
      "regulation_policy": {{
        "impact": "High | Medium | Low",
        "explanation": "string (1 sentence)"
      }},
      "currency_exposure": {{
        "impact": "High | Medium | Low",
        "explanation": "string (1 sentence)"
      }}
    }},
    "latest_high_impact_headline": {{
      "headline": "string",
      "why_it_matters": "string"
    }},
    "investor_takeaway": "string"
  }}
}}

CONSTRAINTS:
1. Description: exactly 3 lines, each brief and distinct.
2. Bull/Bear Cases: exactly 5 items each.
   - title: 3–6 words only
   - explanation: ≤ 20 words maximum
3. Macro Sensitivity: impact must be "High", "Medium", or "Low". One sentence per factor.
4. Latest High-Impact Headline: at most 1 material event.
   - If no material recent event, use "No material recent developments" with brief explanation.
5. NO numbers, valuation data, or financial metrics anywhere.
6. Avoid repetition; maintain neutral, investor-focused tone.
7. All text must be concise and suitable for a summary page.
8. Output ONLY valid JSON, no additional commentary.

Generate the JSON now:"""

        return prompt

    def _extract_json(self, response_text: str) -> dict:
        """
        Extract and parse JSON from the API response.

        Args:
            response_text (str): Raw response text from API

        Returns:
            dict: Parsed JSON object

        Raises:
            ValueError: If valid JSON cannot be extracted
        """
        # Try to find JSON block in the response
        json_match = re.search(r"\{[\s\S]*\}", response_text)

        if not json_match:
            raise ValueError("No valid JSON found in API response")

        json_str = json_match.group(0)

        try:
            parsed_json = json.loads(json_str)
            return parsed_json
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from response: {e}")

    def validate_output(self, json_output: dict) -> tuple[bool, list[str]]:
        """
        Validate the generated JSON against the schema and constraints.

        Args:
            json_output (dict): The generated JSON output

        Returns:
            tuple: (is_valid: bool, errors: list of error messages)
        """
        errors = []

        try:
            summary = json_output.get("company_summary", {})

            # Validate description
            description = summary.get("description", {})
            if len(description) != 3:
                errors.append("Description must have exactly 3 lines")
            for key in ["line_1", "line_2", "line_3"]:
                if key not in description:
                    errors.append(f"Missing description.{key}")

            # Validate bull_case
            bull_case = summary.get("bull_case", [])
            if len(bull_case) != 5:
                errors.append("Bull case must have exactly 5 items")
            for i, item in enumerate(bull_case):
                if "title" not in item or "explanation" not in item:
                    errors.append(f"Bull case item {i} missing title or explanation")
                elif len(item["title"].split()) > 6:
                    errors.append(f"Bull case {i} title exceeds 6 words")
                elif len(item["explanation"].split()) > 20:
                    errors.append(f"Bull case {i} explanation exceeds 20 words")

            # Validate bear_case
            bear_case = summary.get("bear_case", [])
            if len(bear_case) != 5:
                errors.append("Bear case must have exactly 5 items")
            for i, item in enumerate(bear_case):
                if "title" not in item or "explanation" not in item:
                    errors.append(f"Bear case item {i} missing title or explanation")
                elif len(item["title"].split()) > 6:
                    errors.append(f"Bear case {i} title exceeds 6 words")
                elif len(item["explanation"].split()) > 20:
                    errors.append(f"Bear case {i} explanation exceeds 20 words")

            # Validate macro_sensitivity
            macro = summary.get("macro_sensitivity", {})
            required_factors = [
                "interest_rates",
                "economic_cycles",
                "regulation_policy",
                "currency_exposure",
            ]
            for factor in required_factors:
                if factor not in macro:
                    errors.append(f"Missing macro_sensitivity.{factor}")
                else:
                    factor_data = macro[factor]
                    if factor_data.get("impact") not in ["High", "Medium", "Low"]:
                        errors.append(f"Invalid impact value for {factor}")
                    if "explanation" not in factor_data:
                        errors.append(f"Missing explanation for {factor}")

            # Validate latest_high_impact_headline
            headline_section = summary.get("latest_high_impact_headline", {})
            if "headline" not in headline_section or "why_it_matters" not in headline_section:
                errors.append(
                    "Missing headline or why_it_matters in latest_high_impact_headline"
                )

            # Validate investor_takeaway
            if "investor_takeaway" not in summary:
                errors.append("Missing investor_takeaway")

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return len(errors) == 0, errors


# Example usage
if __name__ == "__main__":
    import os

    def load_research_json(file_path: Path) -> dict:
        """Load company research JSON from file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Get API keys from environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    if not deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable not set")

    # Initialize generator with both API keys
    generator = CompanySummaryGenerator(api_key=api_key, deepseek_api_key=deepseek_api_key)

    try:
        data_file = Path(__file__).parent.parent.parent / "data" / "microsoft_research.json"
        print(data_file)
        company_research = load_research_json(data_file)
        
        # Generate summary (will auto-retry with fallback models)
        print("Generating company summary from research data...")
        summary = generator.generate_summary(company_research)

        # Validate output
        is_valid, errors = generator.validate_output(summary)

        # Display results
        print("\n" + "=" * 80)
        print("GENERATED SUMMARY")
        print("=" * 80)
        print(json.dumps(summary, indent=2))

        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        if is_valid:
            print("✓ Output is valid and meets all schema constraints!")
        else:
            print("✗ Validation errors found:")
            for error in errors:
                print(f"  - {error}")
                
    except FileNotFoundError:
        print(f"Research data file not found. Please provide a valid path.")
        print("\nUsage example:")
        print("  generator = CompanySummaryGenerator(api_key='your-key', deepseek_api_key='your-key')")
        print("  with open('microsoft_research.json') as f:")
        print("      research_data = json.load(f)")
        print("  summary = generator.generate_summary(research_data)")