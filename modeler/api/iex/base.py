import requests, json
import pandas as pd
from sseclient import SSEClient  
                     
class IEXClient:

    URLS = {
        'base': 'https://cloud.iexapis.com/v1/stock/market/batch/',
        'market' : 'https://cloud.iexapis.com/v1/data-points/market/{}',
        'stream': 'https://cloud-sse.iexapis.com/stable/{}?token={}&symbols={}'}
    
    FIELDS = {
        'company': ['exchange','industry','sector','tags'],
        'advanced_stats': ['revenuePerShare','revenuePerEmployee','debtToEquity','profitMargin','enterpriseValue','enterpriseValueToRevenue','priceToSales','priceToBook','forwardPERatio','pegRatio','peRatio','peHigh','peLow'],
        'quote': ['change','changePercent','iexAskPrice','iexAskSize','iexBidPrice','iexBidSize','iexRealtimeSize','latestPrice','latestTime','latestUpdate','volume'],
        'balance_sheet': ['accountsPayable', 'capitalSurplus', 'commonStock', 'currentAssets', 'currentCash', 'currentLongTermDebt', 'goodwill', 'intangibleAssets', 'inventory', 'longTermDebt', 'longTermInvestments', 'minorityInterest', 'netTangibleAssets', 'otherAssets', 'otherCurrentAssets', 'otherCurrentLiabilities', 'otherLiabilities', 'propertyPlantEquipment', 'receivables', 'reportDate', 'retainedEarnings', 'shareholderEquity', 'shortTermInvestments', 'totalAssets', 'totalCurrentLiabilities', 'totalLiabilities', 'treasuryStock'],
        'income_statement': ['costOfRevenue', 'ebit', 'grossProfit', 'incomeTax', 'interestIncome', 'netIncome', 'netIncomeBasic', 'operatingExpense', 'operatingIncome', 'otherIncomeExpenseNet', 'pretaxIncome', 'reportDate', 'researchAndDevelopment', 'sellingGeneralAndAdmin', 'totalRevenue'],
        'cash_flow': ['capitalExpenditures', 'cashChange', 'cashFlow', 'cashFlowFinancing', 'changesInInventories', 'changesInReceivables', 'depreciation', 'dividendsPaid', 'exchangeRateEffect', 'investingActivityOther', 'investments', 'netBorrowings', 'otherFinancingCashFlows', 'reportDate', 'totalInvestingCashFlows'],
        'financials': ['currentDebt', 'operatingRevenue', 'reportDate', 'shortTermDebt', 'totalCash', 'totalDebt'],
        'news': ['datetime','hasPaywall','headline','related','source','summary','url'],
        'key_stats': ['marketcap', 'employees', 'float', 'ttmEPS', 'ttmDividendRate', 'companyName', 'sharesOutstanding', 'nextDividendDate', 'dividendYield', 'nextEarningsDate', 'exDividendDate', 'beta'],
        'analyst': ['updateDate','buy', 'hold', 'sell', 'ratingScaleMark', 'priceTargetAverage', 'priceTargetHigh', 'priceTargetLow', 'numberOfAnalysts', 'consensusEPS', 'numberOfEstimates', 'reportDate', 'fiscalPeriod', 'fiscalEndDate'],
        'valuation': ['peRatio','priceToBook','priceToSales','pegRatio','forwardPERatio','revenuePerEmployee','enterpriseValueToRevenue'],
        'minute': ['date','minute','open','high','low','close','volume'],
        'daily': ['date','open','high','low','close','change','changePercent','volume']}
    
    ENDPOINTS = {
        'base': ['key_stats','advanced_stats','balance_sheet','cash_flow','earnings','financials','income_statement','company','dividends','estimates','fund_ownership','insider_roster','insider_summary','insider_transactions','institutional_ownership'],
        'commodities': ['oil','natural_gas','heating_oil','jet_fuel','diesel','gas','propane'],
        'economic_data': ['daily_treasury_rates','cpi','cc_interest_rates','fed_fund_rate','real_gdp','imf','initial_claims','industrial_production_interest','mortgage_rates','total_housing_starts','total_payrolls','total_vehicle_sales','retail_money_funds','unemployment_rate','recession_probability']
    }
    
    def __init__(self, symbol=None, token=None):
        self.symbol = symbol.upper() if symbol else None
        self.session = requests.session()
        self.token = 'pk_a06a25225ada4526b58688e6a1bf95c4' if not token else token

    def params(self, endpoint, optional_params = {}):
        return {**{'symbols': self.symbol,'types': endpoint, 'token': self.token}, **{k: str(v).lower() if v is True or v is False else str(v) for k, v in optional_params.items()}}

    def fetch(self, endpoint, params={}, stream=False):
        response = self.session.get(url=self.URLS['base'], params=self.params(endpoint,params)) if not stream else SSEClient(self.URLS['stream'].format(endpoint,self.token,self.symbol))
        return response.json()[self.symbol][endpoint] if not stream else response
    
    def fetch_market(self, endpoint):
        response = self.session.get(url = self.URLS['market'].format(endpoint), params={'token':self.token})
        return response.json()

    ### base api calls ###
    def get_base(self):
        return {ep: getattr(self,'get_%s' % ep)() for ep in self.ENDPOINTS['base']}

    def get_key_stats(self, **kwargs):
        return {k: round(v*100,2) if 'Percent' in k else v for k, v in self.fetch('stats', params=kwargs).items() if k in self.FIELDS['key_stats']} 
		
    def get_advanced_stats(self, **kwargs):
        return {k: round(v*100,2) if k == 'profitMargin' else (round(v,2) if type(v) == float else v) for k, v in self.fetch('advanced-stats', params=kwargs).items() if k in self.FIELDS['advanced_stats']}

    def get_balance_sheet(self, **kwargs):
        return pd.DataFrame(list(map(lambda x: {k:v for k, v in x.items() if k in self.FIELDS['balance_sheet']}, self.fetch('balance-sheet', params=kwargs)['balancesheet'])))
	
    def get_cash_flow(self, **kwargs):
        return pd.DataFrame(list(map(lambda x: {k:v for k, v in x.items() if k in self.FIELDS['cash_flow']}, self.fetch('cash-flow', params=kwargs)['cashflow'])))

    def get_earnings(self, **kwargs):
        return pd.DataFrame(list(map(lambda x: {k if k != 'fiscalEndDate' else 'reportDate': v for k, v in x.items()}, self.fetch('earnings', params=kwargs)['earnings'])))

    def get_financials(self, **kwargs):
        return pd.DataFrame(list(map(lambda x: {k:v for k, v in x.items() if k in self.FIELDS['financials']}, self.fetch('financials', params=kwargs)['financials'])))
    
    def get_income_statement(self, **kwargs):
        return pd.DataFrame(list(map(lambda x: {k:v for k, v in x.items() if k in self.FIELDS['income_statement']}, self.fetch('income', params=kwargs)['income'])))

    def get_company(self, **kwargs):
        return {k:v for k, v in self.fetch('company', params=kwargs).items() if k in self.FIELDS['company']}

    def get_dividends(self, **kwargs):
        return pd.DataFrame(self.fetch('dividends', params=kwargs))

    def get_estimates(self):
        return self.fetch('estimates')['estimates'][0]

    def get_fund_ownership(self):
        df = pd.DataFrame(self.fetch('fund-ownership'))
        df['reportDate'] = df['report_date']
        return df[['entityProperName','adjHolding','adjMv','reportDate']]

    def get_insider_roster(self):
        return pd.DataFrame(self.fetch('insider-roster'))

    def get_insider_summary(self):
        return pd.DataFrame(self.fetch('insider-summary'))

    def get_insider_transactions(self):
        return pd.DataFrame(self.fetch('insider-transactions'))

    def get_institutional_ownership(self):
        return pd.DataFrame(self.fetch('institutional-ownership'))[['entityProperName','adjHolding','adjMv','reportDate']]

    def get_historical_prices(self, **kwargs):
        return pd.DataFrame(self.fetch('chart', params=kwargs))

    def get_recommendation_trends(self):
        r = self.fetch('recommendation-trends')[0]
        r['buy'], r['sell'], r['hold'] =  r['ratingBuy'] + r['ratingOverweight'], r['ratingSell'] + r['ratingUnderweight'], r['ratingHold']
        return r
        
    def get_news(self, **kwargs):
        return pd.DataFrame(self.fetch('news', params=kwargs))[self.FIELDS['news']]

    def get_previous_day_prices(self):
        return pd.Series({k:v for k, v in self.fetch('previous').items() if k != 'symbol'})[self.FIELDS['daily']]

    def get_book(self):
        return self.fetch('book')
        
    def get_price(self):
        return self.fetch('price')

    def get_price_target(self):
        return self.fetch('price-target')
    
    def get_peers(self):
        return {'peers': self.fetch('peers')}

    def get_quote(self, **kwargs):
        return self.fetch('quote', params=kwargs)

    def get_volume_by_venue(self):
        return pd.DataFrame(self.fetch('volume-by-venue'))

    ### stream api calls ###
    def get_quote_stream(self):
        return self.fetch('stocksUSNoUTP',stream=True)
    
    def get_news_stream(self):
        return self.fetch('news-stream',stream=True)

    ### market api calls ###
    ### commodoties
    def get_commodities(self):
        return pd.DataFrame([(commodity, getattr(self, 'get_{}_prices'.format(commodity))()) for commodity in self.ENDPOINTS['commodities']])

    def get_oil_prices(self, brent=False):
        return self.fetch_market('DCOILWTICO' if not brent else 'DCOILBRENTEU')
    
    def get_natural_gas_prices(self):
        return self.fetch_market('DHHNGSP')
    
    def get_heating_oil_prices(self):
        return self.fetch_market('DHOILNYH')

    def get_jet_fuel_prices(self):
        return self.fetch_market('DJFUELUSGULF')
    
    def get_diesel_prices(self):
        return self.fetch_market('GASDESW')
    
    def get_gas_prices(self):
        return self.fetch_market('GASREGCOVW')
    
    def get_propane_prices(self):
        return self.fetch_market('DPROPANEMBTX')

    ### economic Deta ###
    def get_economic_data(self):
        return pd.DataFrame([(data_point, getattr(self, 'get_{}'.format(data_point))()) for data_point in self.ENDPOINTS['economic_data']])
    
    def get_daily_treasury_rates(self, rate=30):
        return self.fetch_market('DGS' + str(rate))

    def get_cpi(self):
        return self.fetch_market('CPIAUCSL')

    def get_cc_interest_rates(self):
        return self.fetch_market('TERMCBCCALLNS')
    
    def get_fed_fund_rate(self):
        return self.fetch_market('FEDFUNDS')
    
    def get_real_gdp(self):
        return self.fetch_market('A191RL1Q225SBEA')
    
    def get_imf(self):
        return self.fetch_market('WIMFSL')
    
    def get_initial_claims(self):
        return self.fetch_market('IC4WSA')
    
    def get_industrial_production_interest(self):
        return self.fetch_market('INDPRO')
    
    def get_mortgage_rates(self, length=30):
        return self.fetch_market('MORTGAGE30US' if length == 30 else ('MORTGAGE15US' if length == 15 else 'MORTGAGE5US'))
    
    def get_total_housing_starts(self):
        return self.fetch_market('HOUST')
    
    def get_total_payrolls(self):
        return self.fetch_market('PAYEMS')
    
    def get_total_vehicle_sales(self):
        return self.fetch_market('TOTALSA')
    
    def get_retail_money_funds(self):
        return self.fetch_market('WRMFSL')
    
    def get_unemployment_rate(self):
        return self.fetch_market('UNRATE')
    
    def get_recession_probability(self):
        return self.fetch_market('RECPROUSM156N')
