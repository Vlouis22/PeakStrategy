from app.services.stock_research_service import StockResearchService
from pprint import pprint
import yfinance as yf
import finqual as fq

ticker = "AAPL"

# able to get revenue, net income, and cash_flow from finqual # current data format is pd.DataFrame
# income_statement = fq.Finqual(ticker).income_stmt_period(0, 2025) # want "Total Revenue" and "Net Income"
# cash_flow = fq.Finqual(ticker).cash_flow_period(0, 2025) # want free cash flow by "Operating Cash Flow" + "Investing Cash Flow"


# income_dict = {
#     row[0]: {income_statement.columns[i]: row[i] for i in range(1, len(row))}
#     for row in income_statement.to_numpy()
# }

# cash_flow_dict = {
#     row[0]: {cash_flow.columns[i]: row[i] for i in range(1, len(row))}
#     for row in cash_flow.to_numpy()
# }

# operating_cash_flow_values = list(cash_flow_dict["Operating Cash Flow"].values())
# investing_cash_flow_values = list(cash_flow_dict["Investing Cash Flow"].values())
# cash_flow__years = list(cash_flow_dict["Operating Cash Flow"].keys())


# cash_flow__years = []
# cash_flows = []

# for operating, investing, year in zip(operating_cash_flow_values, investing_cash_flow_values, cash_flow__years):
#     cash_flow__years.append(year)
#     cash_flows.append(operating + investing)
    
# total_revenue_values = list(income_dict["Total Revenue"].values())
# total_revenue_years = list(income_dict["Total Revenue"].keys())

# net_income_values = list(income_dict["Net Income"].values())
# net_income_years = list(income_dict["Net Income"].keys())






#print("Total Revenue values: ", total_revenue_values)



#print(type(income_statement))
#print(income_statement)


#print(cash_flow)



research_service = StockResearchService(ticker)
research_data = research_service._get_financial_foundation()

print(research_data["core_trends"]["free_cash_flow"])
