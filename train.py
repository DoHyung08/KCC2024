#훈련 실행하는 파일
#line 50까지는 기본 세팅
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import seaborn as sns

from tqdm import tqdm
from traffic_tail.environment import create_env
from traffic_tail.trainer import SUMOTrainer


USE_SUMO_GUI = True#sumo gui를 띄운다
TOTAL_TIME = 900#900 = 60초 x 15 = 15분
NUM_SEEDS = 5#시드
NUM_EPISODES = 20#5회의 에피소드


class DefaultConfig: #기본환경
    name = "default"
    use_gui = USE_SUMO_GUI
    num_seconds = TOTAL_TIME
    tailgating = False
    default_mode = 31


class OverspeedConfig: #과속환경
    name = "overspeed"
    use_gui = USE_SUMO_GUI
    num_seconds = TOTAL_TIME
    tailgating = False
    default_mode = 24
    

class TailgatingConfig: #꼬리물기 환경
    name = "tailgating"
    use_gui = USE_SUMO_GUI
    num_seconds = TOTAL_TIME
    tailgating = True
    default_mode = 31
    

class TailgatingOverspeedConfig: # 꼬리물기 + 과속 환경
    name = "tailgating_overspeed"
    use_gui = USE_SUMO_GUI
    num_seconds = TOTAL_TIME
    tailgating = True
    default_mode = 24
    

def run_experiment(config):#실험 진행한다
    reward_curve = []
    for seed in range(NUM_SEEDS):
        trainer_default = SUMOTrainer(config)
        trainer_default.train(episodes=NUM_EPISODES)
        reward_curve.append(trainer_default.total_rewards)
        
    reward_curve = np.array(reward_curve)#학습이 진행되면서 각 에피소드에서 얻는 보상
    np.save(f"results/rewards_{config.name}.npy", reward_curve)#학습기록 저장


if __name__ == '__main__':#환경별로 실행한다
    
    default_config = DefaultConfig()
    overspeed_config = OverspeedConfig()
    tailgating_config = TailgatingConfig()
    tailgating_overspeed_config = TailgatingOverspeedConfig()
    
    # for config in [default_config, overspeed_config, tailgating_config, tailgating_overspeed_config]:
    #     run_experiment(config)

    run_experiment(tailgating_overspeed_config)
    #run_experiment(default_config)
    #run_experiment(overspeed_config)
    #run_experiment(tailgating_overspeed_config)