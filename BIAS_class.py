import numpy as np
import pandas as pd
import oandapy
import os
from datetime import datetime

class BIAS(oandapy.Streamer):
    def __init__(self,*args,**kwargs):
        oandapy.Streamer.__init__(self,*args,**kwargs)
        self.ticks=0
        self.oanda=oandapy.API(kwargs["environment"],
                                 kwargs["access_token"])

    
    account_number=os.getenv("account_number")
    access_token=os.getenv("access_token")
    
    def invested(self):
        return self.oanda.get_trades(account_id=account_number)['trades']

    def Bollinger_Band(self,df,n):
        Middle=df['MidClose'].rolling(window=n).mean()
        Upper=Middle+1.96*df['MidClose'].rolling(window=n).std()
        Lower=Middle-1.96*df['MidClose'].rolling(window=n).std()
    
        df1=pd.DataFrame(data=Middle)
        df2=pd.DataFrame(data=Upper)
        df3=pd.DataFrame(data=Lower)
    
        df_Middle=df1.rename(columns={'MidClose':'Middle'})
        df_Upper=df2.rename(columns={'MidClose':'Upper'})
        df_Lower=df3.rename(columns={'MidClose':'Lower'})
        
        df=pd.concat([df_Middle,df_Upper,df_Lower],axis=1)
    
    
        return df
    
    def long(self,units,short_take,middle,ask):
        return self.oanda.create_order(account_id=account_number,
                                      instruments='EUR_USD',
                                      units=units,
                                      side='buy',
                                      takeProfit=round(short_take,5) if ask<short_take else round(middle,5),
                                      type='market')
    
    def short(self,units,long_take,middle,bid):
        return self.oanda.create_order(account_id=account_number,
                                      instruments='EUR_USD',
                                      units=units,
                                      side='sell',
                                      takeProfit=round(long_take,5) if bid>long_take else round(middle,5),
                                      type='market')
    
    def net_asset_value(self):
        return self.oanda.get_transaction_history(account_id=account_number)['transactions'][0]['accountBalance']
    
    def time_now(self):
        return (datetime.utcnow().isoformat('T')+'Z')[0:19]
    
    #Starting analysis
    
    def on_success(self,data):
        self.ticks += 1
        try:
            oanda = oandapy.API(environment="practice" , access_token=access_token)
            response = oanda.get_history(instrument="EUR_USD",
                                      granularity='S5',
                                      count = 5000)
    
            df2=pd.DataFrame(data=response['candles'],index=None)
    
    

            df_midclose=pd.DataFrame(data=(df2['closeAsk']+df2['closeBid'])/2,columns=['MidClose'])

            EMA1=df_midclose['MidClose'].ewm(span=6).mean()
            EMA2=df_midclose['MidClose'].ewm(span=12).mean()
            EMA3=df_midclose['MidClose'].ewm(span=24).mean()

            BIAS1=(df_midclose['MidClose']-EMA1)/EMA1
            BIAS2=(df_midclose['MidClose']-EMA2)/EMA2
            BIAS3=(df_midclose['MidClose']-EMA3)/EMA3

            statistics=(5*BIAS1+3*BIAS2+2*BIAS3)/10
            a=statistics/df_midclose['MidClose'].apply(np.log)
            MEAN=np.mean(a)
            STD=np.std(a)
            upper=MEAN+2.8*STD
            lower=MEAN-2.8*STD
            upper2=MEAN+4*STD
            lower2=MEAN-4*STD

            long_take=self.Bollinger_Band(df_midclose,26)['Upper'][4999]
            short_take=self.Bollinger_Band(df_midclose,26)['Lower'][4999]
            middle=self.Bollinger_Band(df_midclose,26)['Middle'][4999]

            live=oanda.get_prices(instruments='EUR_USD')
            ask=live['prices'][0]['ask']
            bid=live['prices'][0]['bid']
            
            if self.invested()==[]:
                if a[4999]<lower and a[4999]>lower2:
                    self.long(20000,short_take,middle,ask)
                    
                elif a[4999]>upper and a[4999]<upper2:
                    self.short(20000,long_take,middle,bid)
            
            
            print('Time:',self.time_now())
            print('Net_Asset_Value:',self.net_asset_value())
            print('ratio:',a[4999]*10000)
            print('upper:',upper*10000,'lower:',lower*10000)
        except Exception as e:
            print(str(e))
            
if __name__ == "__main__":
    account_number=os.getenv("account_number")
    access_token=os.getenv("access_token")
    system = BIAS(environment="practice", access_token=access_token)
    system.start(accountId=account_number, instruments="EUR_USD")
            
