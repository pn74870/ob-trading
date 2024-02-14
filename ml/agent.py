import math
import time

from trading import TradingEnv

import torch
import torch.nn as nn

from stable_baselines3 import PPO, SAC
import matplotlib.pyplot as plt

BINANCE_OB_FILE="/Users/justinas/Documents/python/trading/binance_ob_btcusdt.csv"

LVLS_IN_OBS=10

total_steps = 1e6

# NEED TO REWRITE WITH LEARNING RATE SCHEDULER!!!!!
learning_rate = 1e-3

save_path = "weights/ppo"
train=False
device = 'cuda' if torch.cuda.is_available() else "cpu"
print(device)

policy_kwargs = dict(activation_fn = nn.ReLU, net_arch = dict(pi=[512,512,512], qf=[512,512,512]))

env = TradingEnv(BINANCE_OB_FILE,LVLS_IN_OBS)

model = PPO(
    'MlpPolicy',
    env,
    learning_rate=learning_rate,
    policy_kwargs=policy_kwargs,
    verbose=0, 
    device=device, 
)

print("Start!!!")


if train:
    start_time = time.time()
    model.learn(total_timesteps=total_steps)


    model.save(save_path)

    end_time = time.time()
    print('It took ', end_time - start_time, ' seconds!!!')
    print('That is roughly ', math.floor(100 * (end_time - start_time)/60)/100, ' minutes, or ',
            math.floor(100 * (end_time - start_time)/3600)/100, 'hours!!!')
else:
    model.load(save_path)
print("test")

obs,_=env.reset()
done =False
action=-1
plt=env.plot_price()
buys=[]
tbuys=[]
sells=[]
tsell=[]
t=0
while(not done):
    t+=1
    action,_=model.predict(obs)
    obs, reward, done,_,info=env.step(action)
    
    price=info["price"]
    if(action>0):
        buys.append(price)
        tbuys.append(t)
    else:
        sells.append(price)
        tsell.append(t)   


plt.scatter(tbuys, buys, color='green', label='Buy', marker='^')
plt.scatter(tsell, sells, color='red', label='Sell', marker='v')

plt.show()
   