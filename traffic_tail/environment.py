import traci
from sumo_rl import SumoEnvironment

'''
Speed Mode
bit0: Regard safe speed
bit1: Regard maximum acceleration
bit2: Regard maximum deceleration
bit3: Regard right of way at intersections (only applies to approaching foe vehicles outside the intersection)
bit4: Brake hard to avoid passing a red light
bit5: Disregard right of way within intersections (only applies to foe vehicles that have entered the intersection).
Setting the bit enables the check (the according value is regarded), keeping the bit==zero disables the check.

Examples:
default (all checks on) -> [0 1 1 1 1 1] -> Speed Mode = 31
most checks off (legacy) -> [0 0 0 0 0 0] -> Speed Mode = 0
all checks off -> [1 0 0 0 0 0] -> Speed Mode = 32
disable right of way check -> [1 1 0 1 1 1] -> Speed Mode = 55
run a red light [0 0 0 1 1 1] = 7 (also requires setSpeed or slowDown)
run a red light even if the intersection is occupied [1 0 0 1 1 1] = 39 (also requires setSpeed or slowDown)
'''


class TailGatingEnv(SumoEnvironment):#SumoRL 환경을 상속받은 꼬리물기 환경 클래스
    def __init__(self, tailgating=True, default_mode=31, *args, **kwargs):##클래스 초기화. 기본 speed_mode = 31로 설정됨
        super(TailGatingEnv, self).__init__(*args, **kwargs)
        self.tailgating = tailgating
        self.default_mode = default_mode

    def _set_default_mode(self):#차량 speed_mode 초기화함수
        for vehID in self.sumo.vehicle.getIDList():
            self.sumo.vehicle.setSpeedMode(vehID, self.default_mode)#환경의 자동차들 speed_mode 설정
                        
    def _apply_tailgating(self):#꼬리물기를 구현하는 함수
        for tlsID in self.sumo.trafficlight.getIDList():#모든 신호등에 대해
            controlledLanes = self.sumo.trafficlight.getControlledLanes(tlsID) #이 신호등에 영향받는 차선을 받는다
            stateString = self.sumo.trafficlight.getRedYellowGreenState(tlsID) #신호등 상태를 받는다
            
            for idx, lane in enumerate(controlledLanes):
                vehicles = self.sumo.lane.getLastStepVehicleIDs(lane)
                for vehID in vehicles:#각 차들에 대해
                    if 'y' in stateString[idx]:#노란불이 신호등 상태에 있다면
                        self.sumo.vehicle.setSpeedMode(vehID, 0) #교통법규를 어기고 과속한다.
            
    def _apply_realistic_impatience_gap(self):#운전자의 남아있는 인내심에 따라 꼬리물기를 하도록 한다
        for vehID in self.sumo.vehicle.getIDList():#각 자동차들에 대해
            impatience = self.sumo.vehicle.getImpatience(vehID)#운전자의 인내를 받는다
            minGap = 2.5 if impatience < 1 else 0.5 #인내가 1 미만이면 앞차와의 거리를 2.5, 아니면 0.5m로 설정
            self.sumo.vehicle.setMinGap(vehID, minGap)

    def _sumo_step(self):#다음 단계(Scene)로 진행하는 함수
        self._set_default_mode()
        if self.tailgating:#꼬리물기를 한다면
            self._apply_tailgating()#꼬리물기 적용
            # self._apply_realistic_impatience_gap()
        self.sumo.simulationStep()#다음단계 진행
        

def create_env(env_config): #환경 생성하는 함수
    print(f"Creating {env_config.name} environment.")
    if env_config.tailgating:#꼬리물기 시의 파일, 노란불에 교차로를 통과하려는 정도가 높게 설정되어있다
        net_file = "nets/network.net.xml"
        route_file = "nets/flow_tailgating.rou.xml"
    else:#기본 파일
        net_file = "nets/network.net.xml"
        route_file = "nets/flow_default.rou.xml"
    return TailGatingEnv(
        tailgating=env_config.tailgating,
        default_mode=env_config.default_mode,
        net_file=net_file,
        route_file=route_file,
        single_agent=False,
        use_gui=env_config.use_gui,
        num_seconds=env_config.num_seconds,
        yellow_time=3,
        min_green=5,
        max_green=60,
        delta_time=5,
        sumo_warnings=False,
    )