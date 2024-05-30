import os
import pickle
from argparse import ArgumentParser

from tqdm import tqdm
from linear_rl.true_online_sarsa import TrueOnlineSarsaLambda
from traffic_tail.environment import create_env


class SUMOTrainer(object): #훈련함수
    """
    Main training code.
    Train a DQN model for each module in the environment.
    """
    def __init__(self, env_config):#초기화함수
        self.result_dir = f"results/{env_config.name}"#에이전트 저장할 디렉토리 설정
        self.best_reward = -float('inf')#현재까지 최고 보상을 초기화
        self.env = create_env(env_config)#환경 생성
        
        print(f"Initializing RL agents. (This may take a while)")#에이전트 초기화
        self.agents = {
            ts_id: TrueOnlineSarsaLambda(
                self.env.observation_spaces(ts_id),
                self.env.action_spaces(ts_id),
                alpha=0.000000001,#학습률
                gamma=0.95,#할인인자
                epsilon=0.05,#탐험률
                lamb=0.1,
                fourier_order=7,
            )
            for ts_id in self.env.ts_ids # 각 객체별로 진행
        }
    
    def train(self, episodes=1, run=None):#훈련. 기본 에피소드횟수는 1, 기본 에이전트는 없다
        self.total_rewards = []
        pbar = tqdm(range(episodes * self.env.sim_max_time))#실행 바 표시
        for episode in range(episodes):
            total_reward = 0
            state = self.env.reset()
            done = {"__all__": False}
            
            pbar.set_description(f"Episode {episode}/{episodes}: Total Reward --")
            while not done["__all__"]:
                actions = {#행동을 선택한다.
                    ts_id: self.agents[ts_id].act(state[ts_id]) 
                    for ts_id in state.keys()
                }
                
                next_state, reward, done, _ = self.env.step(action=actions)

                for ts_id in next_state.keys():
                    self.agents[ts_id].learn(#학습한다
                        state=next_state[ts_id], 
                        action=actions[ts_id], 
                        reward=reward[ts_id], 
                        next_state=next_state[ts_id], 
                        done=done[ts_id]
                    )
                    state[ts_id] = next_state[ts_id]
                
                total_reward += sum(reward.values())
                pbar.update(self.env.delta_time)
            
            # self.save(f'{self.result_dir}/pretrained_agents_run_{episode}.pkl')
            self.total_rewards.append(total_reward)
            pbar.set_description(
                f"Episode {episode}/{episodes}: Total Reward {total_reward:.3f}"
            )
            
            if run is not None:
                save_dir = f"{self.result_dir}/best_agents_run_{run}.pkl"#디렉토리와 이름 지정
            else:
                save_dir = f"{self.result_dir}/best_agents.pkl"
            
            if total_reward > self.best_reward:#만약 최적의 에이전트라면
                self.best_reward = total_reward#최고 보상값 갱신
                self.save(save_dir)#저장
            
        self.env.close()
        return self.agents
    
    def save(self, path=None):#저장함수
        if path is None:
            path = os.path.join(
                self.result_dir, 
                'pretrained_agents.pkl'
            )
        with open(path, 'wb') as f:
            pickle.dump(self.agents, f)
            
    def load(self, path):
        with open(path, 'rb') as f:
            self.agents = pickle.load(f)
        return self


parser = ArgumentParser()
parser.add_argument('--use-gui', action='store_true', default=False)
parser.add_argument('--env', type=str, default='default')


if __name__ == "__main__":
    args = parser.parse_args()
    trainer = SUMOTrainer(env=args.env)
    trainer.train()