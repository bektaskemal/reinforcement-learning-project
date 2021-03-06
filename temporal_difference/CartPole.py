
# coding: utf-8

# # CARTPOLE PROBLEMİNİN ZAMANSAL FARK ÖĞRENMESİ YÖNTEMLERİYLE ÇÖZÜMÜ

# In[1]:


import gym
import itertools
import numpy as np
import pandas as pd


# In[2]:


env = gym.make('CartPole-v0')


# ## Gerekli fonksiyonların tanımlanması

# In[3]:


def discretization(observation):
    
    discrete=np.zeros((1,2))
    theta_bins=np.linspace(-0.42, 0.42, 20)
    thetadot_bins=np.linspace(-1,1, 10)
    discrete[0][0]=np.digitize(observation[2],theta_bins)
    discrete[0][1]=np.digitize(observation[3],thetadot_bins)
    
    return discrete.astype(np.int64)


# In[4]:


def make_epsilon_greedy_policy(Q, epsilon, nA):
    """
    Creates an epsilon-greedy policy based on a given Q-function and epsilon.
    
    Args:
        Q: A dictionary that maps from state -> action-values.
            Each value is a numpy array of length nA (see below)
        epsilon: The probability to select a random action . float between 0 and 1.
        nA: Number of actions in the environment.
    
    Returns:
        A function that takes the observation as an argument and returns
        the probabilities for each action in the form of a numpy array of length nA.
    
    """
    def policy_fn(observation):
        A_probs= np.ones(nA, dtype=float) * epsilon / nA
        best_action = np.argmax(Q[observation[0][0]][observation[0][1]])
        A_probs[best_action] += (1.0 - epsilon)
        return A_probs#.reshape(1,-1)
    
    return policy_fn


# In[5]:


def render_games(Q,num_episodes) :
    scores=[]
    observations=[]
    for episode in range(num_episodes):
        score=0
        observation=env.reset()
        for t in range(200):
            policy = make_epsilon_greedy_policy(Q, 0, env.action_space.n)
            env.render()
            state=discretization(observation)
            action_probs = policy(state)
            action = np.random.choice(np.arange(len(action_probs)), p=action_probs)
            observation, reward, done, info = env.step(action)
            observations.append(observation)
            score += reward
            if done:
                break
        scores.append(score)
    print('Average Score:',sum(scores)/len(scores))


# ## Modellerin Tanımlanması 

# ### SARSA : POLİTİKALI ZAMANSAL FARK ÖĞRENMESİ YÖNTEMİ

# Bu yöntemde güncelleme için kullanılan bir sonraki eylem politika tarafından seçilir.

# SARSA Tahmin güncelleme kuralı:
#     $$Q(S_t,A_t) \leftarrow Q(S_t,A_t) + \alpha\big[R_{t+1} + \gamma Q(S_{t+1},A_{t+1}) - Q(S_t,A_t)\big]$$

# In[6]:


def Sarsa(env, num_episodes, discount_factor=0.9, alpha=0.5, epsilon=0.1):
    
    # Q table initialization
    Q_sarsa = np.zeros((21,11, env.action_space.n))

    policy = make_epsilon_greedy_policy(Q_sarsa, epsilon, env.action_space.n)
    
    for i_episode in range(num_episodes):

        observation = env.reset()
        state=discretization(observation)
        
        for t in itertools.count():
            
            # Take a step
            action_probs = policy(state)
            action = np.random.choice(np.arange(len(action_probs)), p=action_probs)
            next_observation, reward, done, _ = env.step(action)
            next_state=discretization(next_observation)
            
            # Sarsa Update
            next_action_probs = policy(next_state)
            next_action = np.random.choice(np.arange(len(next_action_probs)), p=next_action_probs)
            td_target = reward + discount_factor * Q_sarsa[next_state[0][0]][next_state[0][1]][next_action]
            td_delta = td_target - Q_sarsa[state[0][0]][state[0][1]][action]
            Q_sarsa[state[0][0]][state[0][1]][action] += alpha * td_delta
                
            if done:
                break
                
            state = next_state
            
    return Q_sarsa


# ### Q ÖĞRENMESİ : POLİTİKASIZ ZAMANSAL FARK ÖĞRENMESİ YÖNTEMİ 

# Bu yöntemde güncelleme için kullanılan bir sonraki eylemin değeri olarak, olası eylem değerlerinin en büyüğü kullanılır.

# Q Öğrenmesi Tahmin güncelleme kuralı:
# $$Q(S_t,A_t) \leftarrow Q(S_t,A_t) + \alpha\big[R_{t+1} + \gamma max_a Q(S_{t+1},a) - Q(S_t,A_t)\big]$$

# In[7]:


def Q_learning(env, num_episodes, discount_factor=0.9, alpha=0.5, epsilon=0.1):
    
    
    # Q table initialization
    Q = np.zeros((21,11, env.action_space.n))
    
    # The policy we're following
    policy = make_epsilon_greedy_policy(Q, epsilon, env.action_space.n)
    
    for i_episode in range(num_episodes):
        
        # Reset the environment and pick the first action
        observation = env.reset()
        state=discretization(observation)
        
        for t in itertools.count():
            
            # Take a step
            action_probs = policy(state)
            action = np.random.choice(np.arange(len(action_probs)), p=action_probs)
            next_observation, reward, done, _ = env.step(action)
            next_state=discretization(next_observation)
            
            # Q Learning Update
            best_next_action = np.argmax(Q[next_state[0][0]][next_state[0][1]])
            td_target = reward + discount_factor * Q[next_state[0][0]][next_state[0][1]][best_next_action]
            td_delta = td_target - Q[state[0][0]][state[0][1]][action]
            Q[state[0][0]][state[0][1]][action] += alpha * td_delta
                
            if done:
                break
                
            state = next_state
            
    return Q


# ### BEKLENTİLİ SARSA YÖNTEMİ

# Bu yöntemde güncelleme için kullanılan bir sonraki eylemin değeri olarak, olası eylemlerin beklenen değeri kullanılır.

# Beklentili Sarsa Tahmin güncelleme kuralı:
# $$Q(S_t,A_t) \leftarrow Q(S_t,A_t) + \alpha\big[R_{t+1} + \gamma \sum\limits_a{\pi(a\mid S_{t+1})Q(S_{t+1},a)} - Q(S_t,A_t)\big]$$

# In[8]:


def Expected_Sarsa(env, num_episodes, discount_factor=1, alpha=0.5, epsilon=0.1):
    
    # Q Table Initialization
    Q_expsarsa = np.zeros((21,11, env.action_space.n))
    
    policy = make_epsilon_greedy_policy(Q_expsarsa, epsilon, env.action_space.n)
    
    for i_episode in range(num_episodes):
        observation = env.reset()
        state=discretization(observation)

        for t in itertools.count():
            
            # Take a step
            action_probs = policy(state)
            action = np.random.choice(np.arange(len(action_probs)), p=action_probs)
            next_observation, reward, done, _ = env.step(action)
            next_state=discretization(next_observation)
            
            # Expected Sarsa Update
            next_action_prob=policy(next_state)
            expected_value = np.sum(np.multiply(Q_expsarsa[next_state[0][0]][next_state[0][1]][:],next_action_prob))
            td_target = reward + discount_factor * expected_value
            td_delta = td_target - Q_expsarsa[state[0][0]][state[0][1]][action]
            Q_expsarsa[state[0][0]][state[0][1]][action] += alpha * td_delta
                
            if done:
                break
                
            state = next_state
            
    return Q_expsarsa


# ## Modellerin Eğitimi

# In[9]:


Q_s = Sarsa(env, 1200)


# In[10]:


Q_q= Q_learning(env, 600)


# In[11]:


Q_es = Expected_Sarsa(env, 400)


# ## Sonuçların Test Edilmesi ve Görüntülenmesi

# In[12]:


render_games(Q_s,5)


# In[13]:


render_games(Q_q,5)


# In[14]:


render_games(Q_es,5)

