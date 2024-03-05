import gym

from gym import spaces
import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
import glob
import random

BINANCE_OB_FILE="/home/string-1/Documents/python bn/binance_ob_btcusdt*.csv"

LVLS_IN_OBS=10
nrows=1000000
fee=.001




class TradingEnv(gym.Env):
    
    def __init__(self, ob_file,lvls_obs=LVLS_IN_OBS):
        self.column_names = ['price', 'quantity', 'side']
        filenames=glob.glob(ob_file)
        self.obs = [ pd.read_csv(file, names=self.column_names,nrows=nrows) for file in filenames]
        self.ob = random.choice(self.obs)
        self.norm_fac_price=50000.   
        self.norm_fac_quant=10.
        self.balance=10000. 
        self.quantity=0.
        self.total_worth=self.balance      
        self.t=0  
        #self.plot_price()
        print("length ob: ",len(self.ob)/100)
        #self.action_space = spaces.Box(low=-self.balance/self.norm_fac_price,high=self.balance/self.norm_fac_price,dtype=np.float32)
        self.action_space=spaces.Discrete(3)
        self.get_ob_snap(0,lvls_obs)

        obs_low=np.array([.6 for _ in range(2*LVLS_IN_OBS)]+[0. for _ in range(2*LVLS_IN_OBS)],dtype=np.float32)
        obs_high=np.array([1.2 for _ in range(2*LVLS_IN_OBS)]+[10. for _ in range(2*LVLS_IN_OBS)],dtype=np.float32)

        self.observation_space = spaces.Box(low=obs_low, high=obs_high)
        
        self.episode_count=0
        self.reset()
    def plot_price(self):
        prices = self.ob.iloc[49::100, 0]
        plt.plot([i for i in range(len(prices))], prices.values)
        
        return plt
    
    def get_ob_snap(self,i,lvls_obs):
        price_lvls_a=self.ob.iloc[i*100+50-lvls_obs:i*100+50, 0].to_numpy()
        price_lvls_b=self.ob.iloc[i*100+50:i*100+50+lvls_obs, 0].to_numpy()
        quantities_a=self.ob.iloc[i*100+50-lvls_obs:i*100+50, 1].to_numpy()
        quantities_b=self.ob.iloc[i*100+50:i*100+50+lvls_obs, 1].to_numpy()
        return price_lvls_a,price_lvls_b,quantities_a,quantities_b
        # print(price_lvls_a)
        # print(quantities_a)
        # print(price_lvls_b)
        # print(quantities_b) 


#the decision to buy, sell or hold is made after every snapshop of the orderbook, perhaps shouldnt be so frequent
    def step(self, action):
        if action==1: #BUY
            action=.01 #this should be a variable of the buy amount
        if action==2: #SELL
            action=-.01   
        
        price_lvls_a,price_lvls_b,quantities_a,quantities_b=self.get_ob_snap(self.t,LVLS_IN_OBS)
        buy_price=price_lvls_a[-1]
        sell_price=price_lvls_b[1]
        buy=action>0
        
        if buy:
            self.balance-=buy_price*action
            self.quantity+=(1.-fee)*action
            
        else:
            self.balance-=(1.-fee)*sell_price*action
            self.quantity+=action
            
        
        

        obs = np.concatenate((price_lvls_a/self.norm_fac_price,price_lvls_b/self.norm_fac_price,quantities_a/self.norm_fac_quant,quantities_b/self.norm_fac_quant),dtype=np.float32)
        reward=-self.total_worth+self.balance+self.quantity*sell_price
        self.total_worth=self.balance+self.quantity*sell_price
        info = { 'action' :action, "balance":self.balance,"eqt":self.quantity,'full cash' : self.total_worth,"price":(sell_price+buy_price)/2 }
        self.t+=1
        done = self.t*100>=len(self.ob)-1 or self.balance+self.quantity*sell_price<0 
        
        if(done): 
            print(self.total_worth)
        return obs, reward, done, self.balance+self.quantity*sell_price<0,info     
    def _get_obs(self):
        price_lvls_a,price_lvls_b,quantities_a,quantities_b=self.get_ob_snap(self.t,LVLS_IN_OBS)

        return np.concatenate((price_lvls_a/self.norm_fac_price,price_lvls_b/self.norm_fac_price,quantities_a/self.norm_fac_quant,quantities_b/self.norm_fac_quant),dtype=np.float32)
    

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.ob = random.choice(self.obs)
        self.balance=10000. 
        self.total_worth=self.balance 
        self.quantity=0.      
        self.t=0  
        self.episode_count += 1
        obs=self._get_obs()
        self.t=1
    
       

        return obs,{}   

# env=TradingEnv(BINANCE_OB_FILE)
# done =False
# action=-1
# while(not done):
#     obs, reward, done, info=env.step(action)
#     action=0
#     print(info)
    # try:
        
    #     obs, reward, done, info=env.step(action)
    #     print(info)
    # except ValueError:
    #     print('Enter a valid float')

