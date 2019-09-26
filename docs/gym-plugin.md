The `gym_ex` example demonstrates to Reinforcement Learning developers the AEA framework's flexibility.

There is no immediate use case for this example as you can train an RL agent without the AEA proxy layer just fine (and faster). 

However, the example decouples the RL agent from the `gym.Env` allowing them to run in separate environments, potentially owned by different entities.


## Quick start

### Dependencies

``` bash
pip install numpy gym
```

### Files

You will have already downloaded the `examples` directory during the AEA <a href="../quickstart" target=_blank>quick start demo</a>.

``` bash
cd examples/gym_ex
```

### Run the example

``` bash
python train.py
```

Notice the usual RL setup, i.e. the fit method of the RL agent has the typical signature and a familiar implementation. 

Note how `train.py` demonstrates how easy it is to use an AEA agent as a proxy layer between an OpenAI `gym.Env` and a standard RL agent.

It is just one line of code!

``` python
from gyms.env import BanditNArmedRandom
from proxy.env import ProxyEnv
from rl.agent import RLAgent


if __name__ == "__main__":
    NB_GOODS = 10
    NB_PRICES_PER_GOOD = 100
    NB_STEPS = 4000

    # Use any gym.Env compatible environment:
    gym_env = BanditNArmedRandom(nb_bandits=NB_GOODS, nb_prices_per_bandit=NB_PRICES_PER_GOOD)

    # Pass the gym environment to a proxy environment:
    proxy_env = ProxyEnv(gym_env)

    # Use any RL agent compatible with the gym environment and call the fit method:
    rl_agent = RLAgent(nb_goods=NB_GOODS)
    rl_agent.fit(env=proxy_env, nb_steps=NB_STEPS)
```

<br />