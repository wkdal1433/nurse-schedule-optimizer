"""
간호사 근무표 생성 알고리즘
Enhanced Hybrid Metaheuristic: Advanced Simulated Annealing + Multi-neighborhood Local Search + Tabu Search
"""
import random
import math
import copy
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
from enum import Enum

class ShiftType(Enum):
    DAY = 0
    EVENING = 1
    NIGHT = 2
    OFF = 3

class ConstraintType(Enum):
    HARD = "hard"
    SOFT = "soft"

class NeighborhoodType(Enum):
    SINGLE_SWAP = "single_swap"
    SHIFT_ROTATION = "shift_rotation" 
    BLOCK_MOVE = "block_move"
    EMPLOYEE_SWAP = "employee_swap"

class NurseScheduler:
    """Enhanced 간호사 근무표 최적화 스케줄러 with Advanced Metaheuristics"""
    
    def __init__(self, ward_id: int, month: int, year: int):
        self.ward_id = ward_id
        self.month = month
        self.year = year
        self.days_in_month = self._get_days_in_month(year, month)
        
        # 근무 유형
        self.shift_types = ["day", "evening", "night", "off"]
        
        # Enhanced 알고리즘 파라미터
        self.initial_temp = 1000.0
        self.final_temp = 0.01
        self.cooling_rate = 0.985  # 더 느린 냉각
        self.max_iterations = 5000  # 더 많은 반복
        self.reheat_threshold = 100  # 재가열 임계값
        self.reheat_factor = 2.0    # 재가열 배수
        
        # Tabu Search 파라미터
        self.tabu_list_size = 50
        self.tabu_tenure = 7
        self.aspiration_threshold = 0.95
        
        # Multi-neighborhood 가중치
        self.neighborhood_weights = {
            NeighborhoodType.SINGLE_SWAP: 0.4,
            NeighborhoodType.SHIFT_ROTATION: 0.25,
            NeighborhoodType.BLOCK_MOVE: 0.2,
            NeighborhoodType.EMPLOYEE_SWAP: 0.15
        }
        
        # 제약조건 가중치 (사양서 기준)
        self.constraint_weights = {
            "legal_compliance": 1000,      # Hard constraint penalty
            "staffing_safety": 500,        # Safety penalty
            "role_compliance": 50,         # Role violation penalty
            "pattern_penalty": 30,         # Pattern penalty
            "preference_bonus": 20,        # Preference satisfaction bonus
            "preference_penalty": 10,      # Preference ignore penalty
            "compliance_bonus": 100        # Compliance satisfaction bonus
        }
        
        # Tabu list for moves
        self.tabu_list = deque(maxlen=self.tabu_list_size)
        self.best_global_score = float('-inf')
        self.stagnation_count = 0
        
    def _get_days_in_month(self, year: int, month: int) -> int:
        """월의 일수 계산"""
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        
        current_month = datetime(year, month, 1)
        return (next_month - current_month).days
    
    def generate_schedule(self, employees: List[Dict], 
                         constraints: Dict[str, Any],
                         shift_requests: List[Dict]) -> Dict[str, Any]:
        """Enhanced 근무표 생성 with Advanced Metaheuristics"""
        
        print(f"🚀 Starting Enhanced Schedule Generation for {len(employees)} employees")
        
        # 1. 제약조건 전처리 및 분석
        processed_constraints = self._preprocess_constraints(constraints, employees)
        
        # 2. CSP 기반 초기 해 생성 (더 스마트한 초기화)
        initial_schedule = self._generate_csp_based_initial_schedule(
            employees, processed_constraints, shift_requests
        )
        print(f"✅ Initial schedule generated with score: {self._calculate_fitness(initial_schedule, employees, processed_constraints, shift_requests):.2f}")
        
        # 3. Hybrid Metaheuristic 최적화
        # Phase 1: Enhanced Simulated Annealing with Reheating
        sa_schedule = self._enhanced_simulated_annealing(
            initial_schedule, employees, processed_constraints, shift_requests
        )
        print(f"✅ Simulated Annealing completed with score: {self._calculate_fitness(sa_schedule, employees, processed_constraints, shift_requests):.2f}")
        
        # Phase 2: Tabu Search for intensive local optimization
        tabu_schedule = self._tabu_search(
            sa_schedule, employees, processed_constraints, shift_requests
        )
        print(f"✅ Tabu Search completed with score: {self._calculate_fitness(tabu_schedule, employees, processed_constraints, shift_requests):.2f}")
        
        # Phase 3: Multi-neighborhood Variable Local Search
        final_schedule = self._multi_neighborhood_local_search(
            tabu_schedule, employees, processed_constraints, shift_requests
        )
        
        final_score = self._calculate_fitness(final_schedule, employees, processed_constraints, shift_requests)
        print(f"✅ Final optimization completed with score: {final_score:.2f}")
        
        # 4. 제약조건 검증 및 보고서 생성
        constraint_report = self._generate_constraint_report(
            final_schedule, employees, processed_constraints, shift_requests
        )
        
        # 5. 결과 포맷팅
        result = self._format_schedule(final_schedule, employees)
        result['constraint_report'] = constraint_report
        result['optimization_details'] = {
            'algorithm_phases': ['CSP_Initial', 'Enhanced_SA', 'Tabu_Search', 'Multi_Neighborhood_LS'],
            'final_score': final_score,
            'constraint_violations': constraint_report.get('total_violations', 0)
        }
        
        return result
    
    def _preprocess_constraints(self, constraints: Dict[str, Any], employees: List[Dict]) -> Dict[str, Any]:
        """제약조건 전처리 및 분석"""
        processed = copy.deepcopy(constraints)
        
        # 직원별 역할 및 고용형태 분석
        processed['employee_roles'] = {}
        processed['employment_types'] = {}
        processed['experience_levels'] = {}
        
        for emp in employees:
            emp_id = emp['id']
            processed['employee_roles'][emp_id] = emp.get('role', 'staff_nurse')
            processed['employment_types'][emp_id] = emp.get('employment_type', 'full_time')
            processed['experience_levels'][emp_id] = emp.get('years_experience', 1)
        
        # 신입간호사-선임간호사 페어링 요구사항
        processed['new_nurse_pairs'] = self._identify_new_nurse_pairs(employees)
        
        # 최소 인력 요구사항 강화
        if 'required_staff' not in processed:
            processed['required_staff'] = {"day": 3, "evening": 2, "night": 1}
        
        return processed
    
    def _identify_new_nurse_pairs(self, employees: List[Dict]) -> Dict[int, List[int]]:
        """신입간호사와 매칭할 선임간호사 식별"""
        new_nurses = []
        senior_nurses = []
        
        for emp in employees:
            if emp.get('years_experience', 1) <= 1 or emp.get('role') == 'new_nurse':
                new_nurses.append(emp['id'])
            elif emp.get('years_experience', 1) >= 3:
                senior_nurses.append(emp['id'])
        
        # 신입간호사별로 가능한 선임간호사 리스트 생성
        pairs = {}
        for new_nurse_id in new_nurses:
            pairs[new_nurse_id] = senior_nurses.copy()
        
        return pairs
    
    def _generate_csp_based_initial_schedule(self, employees: List[Dict], 
                                           constraints: Dict[str, Any],
                                           shift_requests: List[Dict]) -> List[List[int]]:
        """CSP 기반 스마트 초기 스케줄 생성"""
        schedule = []
        
        # 각 날짜별로 제약조건을 만족하는 스케줄 생성
        for day in range(self.days_in_month):
            daily_schedule = self._generate_daily_schedule_csp(
                day, employees, constraints, shift_requests, schedule
            )
            schedule.append(daily_schedule)
        
        return schedule
    
    def _generate_daily_schedule_csp(self, day: int, employees: List[Dict], 
                                   constraints: Dict[str, Any],
                                   shift_requests: List[Dict],
                                   previous_days: List[List[int]]) -> List[int]:
        """하루 스케줄을 CSP로 생성"""
        required_staff = constraints.get('required_staff', {"day": 3, "evening": 2, "night": 1})
        daily_assignments = [3] * len(employees)  # 기본은 OFF
        
        # 1. 휴가/연차 요청 먼저 처리
        for req in shift_requests:
            if self._is_request_for_day(req, day):
                emp_idx = self._get_employee_index(req['employee_id'], employees)
                if emp_idx is not None and req['request_type'] == 'leave':
                    daily_assignments[emp_idx] = 3  # OFF
        
        # 2. 필수 인력 배치
        available_employees = [i for i, assignment in enumerate(daily_assignments) if assignment == 3]
        
        # 각 시프트별로 필요한 인력 배치
        for shift_type, required_count in required_staff.items():
            if shift_type == "off":
                continue
            
            shift_idx = self.shift_types.index(shift_type)
            assigned_count = 0
            
            # 선호도와 제약조건을 고려한 배치
            for emp_idx in available_employees[:]:
                if assigned_count >= required_count:
                    break
                
                if self._can_assign_shift(emp_idx, shift_idx, day, employees, constraints, previous_days):
                    daily_assignments[emp_idx] = shift_idx
                    available_employees.remove(emp_idx)
                    assigned_count += 1
        
        return daily_assignments
    
    def _can_assign_shift(self, emp_idx: int, shift_idx: int, day: int,
                         employees: List[Dict], constraints: Dict[str, Any],
                         previous_days: List[List[int]]) -> bool:
        """특정 직원에게 특정 시프트 배정이 가능한지 확인"""
        emp = employees[emp_idx]
        
        # 1. 고용형태 확인
        if emp.get('employment_type') == 'part_time' and shift_idx == 2:  # 시간제는 야간근무 불가
            return False
        
        # 2. 연속근무 제한 확인
        if len(previous_days) >= 4:  # 최근 4일 확인
            consecutive_work = 0
            for prev_day in reversed(previous_days[-4:]):
                if prev_day[emp_idx] != 3:  # OFF가 아니면
                    consecutive_work += 1
                else:
                    break
            
            if consecutive_work >= 4 and shift_idx != 3:  # 5일째 근무 시도
                return False
        
        # 3. 야간근무 후 패턴 확인
        if len(previous_days) > 0:
            last_shift = previous_days[-1][emp_idx]
            if last_shift == 2 and shift_idx == 0:  # 야간 → 주간 금지
                return False
        
        return True
    
    def _enhanced_simulated_annealing(self, schedule: List[List[int]], 
                                    employees: List[Dict],
                                    constraints: Dict[str, Any],
                                    shift_requests: List[Dict]) -> List[List[int]]:
        """Enhanced Simulated Annealing with Adaptive Reheating"""
        
        current_schedule = copy.deepcopy(schedule)
        best_schedule = copy.deepcopy(schedule)
        
        current_score = self._calculate_fitness(current_schedule, employees, constraints, shift_requests)
        best_score = current_score
        self.best_global_score = best_score
        
        temperature = self.initial_temp
        no_improvement_count = 0
        
        for iteration in range(self.max_iterations):
            # Multi-neighborhood 이웃해 생성
            neighbor_schedule = self._generate_multi_neighborhood_neighbor(
                current_schedule, employees, constraints
            )
            neighbor_score = self._calculate_fitness(neighbor_schedule, employees, constraints, shift_requests)
            
            # 해 수용 결정
            delta = neighbor_score - current_score
            
            if delta > 0 or (temperature > 0 and random.random() < math.exp(delta / temperature)):
                current_schedule = neighbor_schedule
                current_score = neighbor_score
                
                if current_score > best_score:
                    best_schedule = copy.deepcopy(current_schedule)
                    best_score = current_score
                    self.best_global_score = best_score
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
            else:
                no_improvement_count += 1
            
            # Adaptive Reheating
            if no_improvement_count >= self.reheat_threshold:
                temperature *= self.reheat_factor
                no_improvement_count = 0
                print(f"🔥 Reheating at iteration {iteration}, new temp: {temperature:.2f}")
            
            # 온도 감소
            temperature *= self.cooling_rate
            
            # 종료 조건
            if temperature < self.final_temp:
                break
            
            # 진행상황 출력
            if iteration % 500 == 0:
                print(f"🔄 SA Iteration {iteration}: Score={current_score:.2f}, Best={best_score:.2f}, Temp={temperature:.4f}")
        
        print(f"✅ Enhanced SA completed after {iteration+1} iterations")
        return best_schedule
    
    def _tabu_search(self, schedule: List[List[int]], 
                    employees: List[Dict],
                    constraints: Dict[str, Any],
                    shift_requests: List[Dict]) -> List[List[int]]:
        """Tabu Search for intensive local optimization"""
        
        current_schedule = copy.deepcopy(schedule)
        best_schedule = copy.deepcopy(schedule)
        
        current_score = self._calculate_fitness(current_schedule, employees, constraints, shift_requests)
        best_score = current_score
        
        tabu_iterations = min(1000, self.max_iterations // 2)
        no_improvement = 0
        
        for iteration in range(tabu_iterations):
            best_neighbor = None
            best_neighbor_score = float('-inf')
            best_move = None
            
            # 이웃해 탐색
            neighbors = self._generate_tabu_neighbors(current_schedule, employees, constraints)
            
            for neighbor, move in neighbors:
                neighbor_score = self._calculate_fitness(neighbor, employees, constraints, shift_requests)
                
                # Tabu가 아니거나 Aspiration 조건 만족
                if (not self._is_tabu_move(move) or 
                    neighbor_score > best_score * self.aspiration_threshold):
                    
                    if neighbor_score > best_neighbor_score:
                        best_neighbor = neighbor
                        best_neighbor_score = neighbor_score
                        best_move = move
            
            if best_neighbor is not None:
                current_schedule = best_neighbor
                current_score = best_neighbor_score
                
                # Tabu list 업데이트
                self.tabu_list.append(best_move)
                
                if current_score > best_score:
                    best_schedule = copy.deepcopy(current_schedule)
                    best_score = current_score
                    no_improvement = 0
                else:
                    no_improvement += 1
            else:
                no_improvement += 1
            
            # 조기 종료
            if no_improvement >= 100:
                break
            
            if iteration % 200 == 0:
                print(f"🔄 Tabu Search {iteration}: Score={current_score:.2f}, Best={best_score:.2f}")
        
        print(f"✅ Tabu Search completed after {iteration+1} iterations")
        return best_schedule
    
    def _multi_neighborhood_local_search(self, schedule: List[List[int]], 
                                       employees: List[Dict],
                                       constraints: Dict[str, Any],
                                       shift_requests: List[Dict]) -> List[List[int]]:
        """Multi-neighborhood Variable Local Search"""
        
        current_schedule = copy.deepcopy(schedule)
        improved = True
        iteration = 0
        
        while improved and iteration < 500:
            improved = False
            iteration += 1
            
            current_score = self._calculate_fitness(current_schedule, employees, constraints, shift_requests)
            
            # 각 neighborhood 타입별로 시도
            for neighborhood_type in NeighborhoodType:
                if random.random() < self.neighborhood_weights[neighborhood_type]:
                    neighbor = self._generate_neighborhood_move(
                        current_schedule, neighborhood_type, employees, constraints
                    )
                    
                    if neighbor is not None:
                        neighbor_score = self._calculate_fitness(neighbor, employees, constraints, shift_requests)
                        
                        if neighbor_score > current_score:
                            current_schedule = neighbor
                            improved = True
                            break
        
        print(f"✅ Multi-neighborhood LS completed after {iteration} iterations")
        return current_schedule
    
    def _generate_initial_schedule(self, employees: List[Dict]) -> List[List[int]]:
        """초기 근무표 생성 (랜덤) - Legacy method"""
        schedule = []
        
        for day in range(self.days_in_month):
            daily_shifts = []
            
            for emp in employees:
                # 랜덤하게 근무 배정 (가중치 적용)
                weights = [3, 3, 2, 2]  # day, evening, night, off
                shift = random.choices(range(4), weights=weights)[0]
                daily_shifts.append(shift)
            
            schedule.append(daily_shifts)
        
        return schedule
    
    def _generate_multi_neighborhood_neighbor(self, schedule: List[List[int]], 
                                            employees: List[Dict],
                                            constraints: Dict[str, Any]) -> List[List[int]]:
        """Multi-neighborhood 기반 이웃해 생성"""
        
        # 가중치에 따라 neighborhood 선택
        neighborhood_type = random.choices(
            list(NeighborhoodType), 
            weights=list(self.neighborhood_weights.values())
        )[0]
        
        return self._generate_neighborhood_move(schedule, neighborhood_type, employees, constraints)
    
    def _generate_neighborhood_move(self, schedule: List[List[int]], 
                                  neighborhood_type: NeighborhoodType,
                                  employees: List[Dict],
                                  constraints: Dict[str, Any]) -> Optional[List[List[int]]]:
        """특정 neighborhood 타입으로 이웃해 생성"""
        
        neighbor = copy.deepcopy(schedule)
        
        if neighborhood_type == NeighborhoodType.SINGLE_SWAP:
            return self._single_swap_move(neighbor, employees)
        elif neighborhood_type == NeighborhoodType.SHIFT_ROTATION:
            return self._shift_rotation_move(neighbor, employees)
        elif neighborhood_type == NeighborhoodType.BLOCK_MOVE:
            return self._block_move(neighbor, employees)
        elif neighborhood_type == NeighborhoodType.EMPLOYEE_SWAP:
            return self._employee_swap_move(neighbor, employees)
        
        return neighbor
    
    def _single_swap_move(self, schedule: List[List[int]], employees: List[Dict]) -> List[List[int]]:
        """단일 시프트 변경"""
        day = random.randint(0, self.days_in_month - 1)
        emp_idx = random.randint(0, len(employees) - 1)
        new_shift = random.randint(0, 3)
        
        schedule[day][emp_idx] = new_shift
        return schedule
    
    def _shift_rotation_move(self, schedule: List[List[int]], employees: List[Dict]) -> List[List[int]]:
        """시프트 순환 변경"""
        day = random.randint(0, self.days_in_month - 1)
        num_employees = min(3, len(employees))
        selected_employees = random.sample(range(len(employees)), num_employees)
        
        # 순환 시프트
        temp_shift = schedule[day][selected_employees[0]]
        for i in range(len(selected_employees) - 1):
            schedule[day][selected_employees[i]] = schedule[day][selected_employees[i + 1]]
        schedule[day][selected_employees[-1]] = temp_shift
        
        return schedule
    
    def _block_move(self, schedule: List[List[int]], employees: List[Dict]) -> List[List[int]]:
        """블록 단위 이동"""
        emp_idx = random.randint(0, len(employees) - 1)
        block_size = min(random.randint(2, 5), self.days_in_month // 2)
        start_day = random.randint(0, self.days_in_month - block_size)
        
        # 블록 내 모든 시프트를 동일하게 변경
        new_shift = random.randint(0, 3)
        for day in range(start_day, start_day + block_size):
            schedule[day][emp_idx] = new_shift
        
        return schedule
    
    def _employee_swap_move(self, schedule: List[List[int]], employees: List[Dict]) -> List[List[int]]:
        """두 직원의 전체 스케줄 교환"""
        emp1_idx = random.randint(0, len(employees) - 1)
        emp2_idx = random.randint(0, len(employees) - 1)
        
        if emp1_idx != emp2_idx:
            # 특정 기간 동안 두 직원의 시프트 교환
            swap_days = random.randint(3, min(7, self.days_in_month))
            start_day = random.randint(0, self.days_in_month - swap_days)
            
            for day in range(start_day, start_day + swap_days):
                schedule[day][emp1_idx], schedule[day][emp2_idx] = schedule[day][emp2_idx], schedule[day][emp1_idx]
        
        return schedule
    
    def _simulated_annealing(self, schedule: List[List[int]], 
                           employees: List[Dict],
                           constraints: Dict[str, Any],
                           shift_requests: List[Dict]) -> List[List[int]]:
        """Simulated Annealing 최적화"""
        
        current_schedule = copy.deepcopy(schedule)
        best_schedule = copy.deepcopy(schedule)
        
        current_score = self._calculate_fitness(current_schedule, employees, constraints, shift_requests)
        best_score = current_score
        
        temperature = self.initial_temp
        
        for iteration in range(self.max_iterations):
            # 이웃 해 생성
            neighbor_schedule = self._generate_neighbor(current_schedule, employees)
            neighbor_score = self._calculate_fitness(neighbor_schedule, employees, constraints, shift_requests)
            
            # 해 수용 결정
            delta = neighbor_score - current_score
            
            if delta > 0 or random.random() < math.exp(delta / temperature):
                current_schedule = neighbor_schedule
                current_score = neighbor_score
                
                if current_score > best_score:
                    best_schedule = copy.deepcopy(current_schedule)
                    best_score = current_score
            
            # 온도 감소
            temperature *= self.cooling_rate
            
            # 종료 조건
            if temperature < self.final_temp:
                break
        
        return best_schedule
    
    def _local_search(self, schedule: List[List[int]], 
                     employees: List[Dict],
                     constraints: Dict[str, Any],
                     shift_requests: List[Dict]) -> List[List[int]]:
        """Local Search 미세조정"""
        
        current_schedule = copy.deepcopy(schedule)
        improved = True
        
        while improved:
            improved = False
            current_score = self._calculate_fitness(current_schedule, employees, constraints, shift_requests)
            
            # 모든 가능한 단일 변경 시도
            for day in range(self.days_in_month):
                for emp_idx in range(len(employees)):
                    for new_shift in range(4):
                        if current_schedule[day][emp_idx] != new_shift:
                            # 변경 시도
                            old_shift = current_schedule[day][emp_idx]
                            current_schedule[day][emp_idx] = new_shift
                            
                            new_score = self._calculate_fitness(current_schedule, employees, constraints, shift_requests)
                            
                            if new_score > current_score:
                                current_score = new_score
                                improved = True
                            else:
                                # 원복
                                current_schedule[day][emp_idx] = old_shift
        
        return current_schedule
    
    def _generate_neighbor(self, schedule: List[List[int]], employees: List[Dict]) -> List[List[int]]:
        """이웃 해 생성"""
        neighbor = copy.deepcopy(schedule)
        
        # 랜덤하게 몇 개의 변경을 수행
        num_changes = random.randint(1, 3)
        
        for _ in range(num_changes):
            day = random.randint(0, self.days_in_month - 1)
            emp_idx = random.randint(0, len(employees) - 1)
            new_shift = random.randint(0, 3)
            
            neighbor[day][emp_idx] = new_shift
        
        return neighbor
    
    def _calculate_fitness(self, schedule: List[List[int]], 
                          employees: List[Dict],
                          constraints: Dict[str, Any],
                          shift_requests: List[Dict]) -> float:
        """Enhanced 적합도 함수 with weighted constraints"""
        
        total_score = 0.0
        weights = self.constraint_weights
        
        # 1. Hard Constraints (법적 준수)
        legal_score = self._legal_compliance_score(schedule, employees, constraints)
        total_score += legal_score * weights["legal_compliance"]
        
        # 2. Safety Constraints (인력 안전)
        safety_score = self._staffing_safety_score(schedule, constraints)
        total_score += safety_score * weights["staffing_safety"]
        
        # 3. Role Compliance (역할 기반)
        role_score = self._role_compliance_score(schedule, employees, constraints)
        total_score += role_score * weights["role_compliance"]
        
        # 4. Shift Pattern Quality (피로도 관리)
        pattern_score = self._enhanced_pattern_score(schedule, employees)
        total_score += pattern_score * weights["pattern_penalty"]
        
        # 5. Preference Satisfaction (선호도)
        preference_score = self._enhanced_preference_score(schedule, employees, shift_requests)
        total_score += preference_score
        
        # 6. Fairness (공평성)
        fairness_score = self._enhanced_fairness_score(schedule, employees)
        total_score += fairness_score
        
        # 7. Coverage Quality (커버리지)
        coverage_score = self._enhanced_coverage_score(schedule, constraints)
        total_score += coverage_score * weights["compliance_bonus"]
        
        return total_score
    
    def _coverage_score(self, schedule: List[List[int]], constraints: Dict[str, Any]) -> float:
        """커버리지 점수 - 각 근무시간대별 필요 인원 충족도"""
        score = 0.0
        
        required_staff = constraints.get("required_staff", {
            "day": 3, "evening": 2, "night": 1
        })
        
        for day_schedule in schedule:
            for shift_type in range(3):  # day, evening, night만 체크 (off 제외)
                actual_count = day_schedule.count(shift_type)
                required_count = required_staff.get(self.shift_types[shift_type], 1)
                
                if actual_count >= required_count:
                    score += 10.0
                else:
                    # 부족한 인원수에 따른 페널티
                    shortage = required_count - actual_count
                    score -= shortage * 20.0
        
        return score
    
    def _fairness_score(self, schedule: List[List[int]], employees: List[Dict]) -> float:
        """근무 형평성 점수"""
        score = 0.0
        
        # 각 직원별 근무 유형별 카운트
        employee_shift_counts = []
        for emp_idx in range(len(employees)):
            shift_counts = [0, 0, 0, 0]  # day, evening, night, off
            for day_schedule in schedule:
                shift_counts[day_schedule[emp_idx]] += 1
            employee_shift_counts.append(shift_counts)
        
        # 각 근무 유형별 형평성 계산
        for shift_type in range(3):  # off 제외
            shift_counts = [counts[shift_type] for counts in employee_shift_counts]
            if len(shift_counts) > 1:
                avg_count = sum(shift_counts) / len(shift_counts)
                variance = sum([(count - avg_count) ** 2 for count in shift_counts]) / len(shift_counts)
                score -= variance * 2.0  # 분산이 클수록 페널티
        
        return score
    
    def _consecutive_shifts_score(self, schedule: List[List[int]], employees: List[Dict]) -> float:
        """연속근무 제약 점수"""
        score = 0.0
        
        for emp_idx in range(len(employees)):
            consecutive_work_days = 0
            
            for day in range(self.days_in_month):
                if schedule[day][emp_idx] != 3:  # 3은 off
                    consecutive_work_days += 1
                    
                    # 5일 이상 연속근무 시 페널티
                    if consecutive_work_days >= 5:
                        score -= (consecutive_work_days - 4) * 10.0
                else:
                    consecutive_work_days = 0
        
        return score
    
    def _preference_score(self, schedule: List[List[int]], 
                         employees: List[Dict],
                         shift_requests: List[Dict]) -> float:
        """희망근무 반영 점수"""
        score = 0.0
        
        for request in shift_requests:
            emp_id = request.get("employee_id")
            request_date = request.get("request_date")
            shift_type = request.get("shift_type")
            request_type = request.get("request_type")
            
            # 직원 인덱스 찾기
            emp_idx = None
            for idx, emp in enumerate(employees):
                if emp["id"] == emp_id:
                    emp_idx = idx
                    break
            
            if emp_idx is not None:
                # 요청 날짜에 해당하는 스케줄 확인
                try:
                    request_day = request_date.day - 1  # 0-based index
                    if 0 <= request_day < self.days_in_month:
                        assigned_shift = schedule[request_day][emp_idx]
                        requested_shift = self.shift_types.index(shift_type)
                        
                        if request_type == "request":
                            if assigned_shift == requested_shift:
                                score += 15.0  # 희망근무 반영 보너스
                            else:
                                score -= 5.0   # 희망근무 미반영 페널티
                        elif request_type == "avoid":
                            if assigned_shift != requested_shift:
                                score += 10.0  # 기피근무 회피 보너스
                            else:
                                score -= 15.0  # 기피근무 배정 페널티
                except (AttributeError, ValueError, IndexError):
                    continue
        
        return score
    
    def _pattern_score(self, schedule: List[List[int]], employees: List[Dict]) -> float:
        """근무패턴 점수"""
        score = 0.0
        
        for emp_idx in range(len(employees)):
            for day in range(self.days_in_month - 1):
                current_shift = schedule[day][emp_idx]
                next_shift = schedule[day + 1][emp_idx]
                
                # 야근 후 바로 주간근무 금지
                if current_shift == 2 and next_shift == 0:  # night -> day
                    score -= 25.0
                
                # 야근 후 저녁근무도 부담
                if current_shift == 2 and next_shift == 1:  # night -> evening
                    score -= 10.0
        
        return score
    
    def _format_schedule(self, schedule: List[List[int]], employees: List[Dict]) -> Dict[str, Any]:
        """스케줄 결과를 JSON 형태로 포맷팅"""
        
        formatted_schedule = {}
        
        # 날짜별 스케줄
        for day in range(self.days_in_month):
            date_key = f"{self.year}-{self.month:02d}-{day+1:02d}"
            daily_assignments = []
            
            for emp_idx, shift_type_idx in enumerate(schedule[day]):
                daily_assignments.append({
                    "employee_id": employees[emp_idx]["id"],
                    "employee_name": employees[emp_idx].get("user", {}).get("full_name", f"Employee {emp_idx+1}"),
                    "shift_type": self.shift_types[shift_type_idx]
                })
            
            formatted_schedule[date_key] = daily_assignments
        
        # 통계 정보
        stats = self._calculate_schedule_stats(schedule, employees)
        
        return {
            "schedule_data": formatted_schedule,
            "statistics": stats,
            "generated_at": datetime.utcnow().isoformat(),
            "total_score": self._calculate_fitness(schedule, employees, {}, [])
        }
    
    def _calculate_schedule_stats(self, schedule: List[List[int]], employees: List[Dict]) -> Dict[str, Any]:
        """스케줄 통계 계산"""
        
        stats = {
            "total_employees": len(employees),
            "total_days": self.days_in_month,
            "shift_distribution": {},
            "employee_workload": {}
        }
        
        # 근무 유형별 분포
        shift_counts = {shift_type: 0 for shift_type in self.shift_types}
        
        for day_schedule in schedule:
            for shift_idx in day_schedule:
                shift_counts[self.shift_types[shift_idx]] += 1
        
        stats["shift_distribution"] = shift_counts
        
        # 직원별 근무량
        for emp_idx, emp in enumerate(employees):
            emp_shifts = {shift_type: 0 for shift_type in self.shift_types}
            
            for day_schedule in schedule:
                shift_type = self.shift_types[day_schedule[emp_idx]]
                emp_shifts[shift_type] += 1
            
            stats["employee_workload"][emp["id"]] = {
                "name": emp.get("user", {}).get("full_name", f"Employee {emp_idx+1}"),
                "shifts": emp_shifts,
                "total_work_days": sum([count for shift, count in emp_shifts.items() if shift != "off"])
            }
        
        return stats

    # ============ Enhanced Scoring Functions ============
    
    def _legal_compliance_score(self, schedule: List[List[int]], 
                              employees: List[Dict],
                              constraints: Dict[str, Any]) -> float:
        """법적 준수 점수 (Hard Constraint)"""
        score = 0.0
        
        for emp_idx, emp in enumerate(employees):
            # 연속 근무일 제한 (최대 5일)
            max_consecutive_work = 0
            current_consecutive = 0
            
            for day in range(self.days_in_month):
                if schedule[day][emp_idx] != 3:  # OFF가 아니면
                    current_consecutive += 1
                    max_consecutive_work = max(max_consecutive_work, current_consecutive)
                else:
                    current_consecutive = 0
            
            if max_consecutive_work > 5:
                score -= (max_consecutive_work - 5) * 100  # 심각한 위반
            
            # 연속 야간근무 제한 (최대 3일)
            consecutive_nights = 0
            max_consecutive_nights = 0
            
            for day in range(self.days_in_month):
                if schedule[day][emp_idx] == 2:  # Night shift
                    consecutive_nights += 1
                    max_consecutive_nights = max(max_consecutive_nights, consecutive_nights)
                else:
                    consecutive_nights = 0
            
            if max_consecutive_nights > 3:
                score -= (max_consecutive_nights - 3) * 150
            
            # 주간 휴식 보장 (최소 주 1회 OFF)
            weeks = self.days_in_month // 7 + (1 if self.days_in_month % 7 > 0 else 0)
            for week in range(weeks):
                week_start = week * 7
                week_end = min((week + 1) * 7, self.days_in_month)
                
                week_off_count = 0
                for day in range(week_start, week_end):
                    if schedule[day][emp_idx] == 3:
                        week_off_count += 1
                
                if week_off_count == 0:
                    score -= 200  # 주간 휴식 없음
        
        return score
    
    def _staffing_safety_score(self, schedule: List[List[int]], 
                             constraints: Dict[str, Any]) -> float:
        """인력 안전 점수"""
        score = 0.0
        required_staff = constraints.get('required_staff', {"day": 3, "evening": 2, "night": 1})
        
        for day_schedule in schedule:
            for shift_type in range(3):  # day, evening, night
                actual_count = day_schedule.count(shift_type)
                required_count = required_staff.get(self.shift_types[shift_type], 1)
                
                if actual_count < required_count:
                    shortage = required_count - actual_count
                    score -= shortage * 100  # 인력 부족 심각한 페널티
                elif actual_count >= required_count:
                    score += 10  # 적정 인력 보너스
        
        return score
    
    def _role_compliance_score(self, schedule: List[List[int]], 
                             employees: List[Dict],
                             constraints: Dict[str, Any]) -> float:
        """역할 기반 준수 점수"""
        score = 0.0
        new_nurse_pairs = constraints.get('new_nurse_pairs', {})
        
        # 신입간호사-선임간호사 페어링 확인
        for day_idx, day_schedule in enumerate(schedule):
            for shift_type in range(3):  # day, evening, night만 확인
                # 해당 시프트에 근무하는 직원들
                shift_workers = [emp_idx for emp_idx, shift in enumerate(day_schedule) if shift == shift_type]
                
                # 신입간호사가 있는지 확인
                new_nurses_working = []
                senior_nurses_working = []
                
                for emp_idx in shift_workers:
                    emp = employees[emp_idx]
                    if emp['id'] in new_nurse_pairs:
                        new_nurses_working.append(emp_idx)
                    elif emp.get('years_experience', 1) >= 3:
                        senior_nurses_working.append(emp_idx)
                
                # 신입간호사가 있으면 선임간호사도 있어야 함
                for new_nurse_idx in new_nurses_working:
                    if not senior_nurses_working:
                        score -= 50  # 신입간호사 혼자 근무
                    else:
                        score += 10  # 올바른 페어링
        
        # 고용형태별 제약 확인
        for emp_idx, emp in enumerate(employees):
            if emp.get('employment_type') == 'part_time':
                night_shifts = sum(1 for day_schedule in schedule if day_schedule[emp_idx] == 2)
                if night_shifts > 0:
                    score -= night_shifts * 25  # 시간제 야간근무 위반
        
        return score
    
    def _enhanced_pattern_score(self, schedule: List[List[int]], employees: List[Dict]) -> float:
        """향상된 근무패턴 점수"""
        score = 0.0
        
        for emp_idx in range(len(employees)):
            for day in range(self.days_in_month - 1):
                current_shift = schedule[day][emp_idx]
                next_shift = schedule[day + 1][emp_idx]
                
                # 야근 후 바로 주간근무 강력한 금지
                if current_shift == 2 and next_shift == 0:  # night -> day
                    score -= 50
                
                # 야근 후 저녁근무도 부담
                if current_shift == 2 and next_shift == 1:  # night -> evening
                    score -= 20
                
                # 좋은 패턴에 보너스
                if current_shift == 2 and next_shift == 3:  # night -> off
                    score += 10
                
                # 연속된 같은 시프트 (OFF 제외)
                if current_shift != 3 and current_shift == next_shift:
                    score += 5  # 연속성 보너스
        
        return score
    
    def _enhanced_preference_score(self, schedule: List[List[int]], 
                                 employees: List[Dict],
                                 shift_requests: List[Dict]) -> float:
        """향상된 선호도 점수"""
        score = 0.0
        weights = self.constraint_weights
        
        for request in shift_requests:
            emp_id = request.get("employee_id")
            request_date = request.get("request_date")
            shift_type = request.get("shift_type")
            request_type = request.get("request_type")
            
            emp_idx = self._get_employee_index(emp_id, employees)
            if emp_idx is None:
                continue
            
            try:
                if hasattr(request_date, 'day'):
                    request_day = request_date.day - 1
                elif isinstance(request_date, str):
                    # Parse string date
                    date_obj = datetime.strptime(request_date, '%Y-%m-%d')
                    request_day = date_obj.day - 1
                else:
                    continue
                    
                if 0 <= request_day < self.days_in_month:
                    assigned_shift = schedule[request_day][emp_idx]
                    requested_shift = self.shift_types.index(shift_type)
                    
                    if request_type == "request":
                        if assigned_shift == requested_shift:
                            score += weights["preference_bonus"]
                        else:
                            score -= weights["preference_penalty"]
                    elif request_type == "avoid":
                        if assigned_shift != requested_shift:
                            score += weights["preference_bonus"] * 0.8
                        else:
                            score -= weights["preference_penalty"] * 1.5
            except (AttributeError, ValueError, IndexError):
                continue
        
        return score
    
    def _enhanced_fairness_score(self, schedule: List[List[int]], employees: List[Dict]) -> float:
        """향상된 공평성 점수"""
        score = 0.0
        
        # 각 직원별 근무 유형별 카운트
        employee_shift_counts = []
        for emp_idx in range(len(employees)):
            shift_counts = [0, 0, 0, 0]  # day, evening, night, off
            for day_schedule in schedule:
                shift_counts[day_schedule[emp_idx]] += 1
            employee_shift_counts.append(shift_counts)
        
        # 야간근무 공평성 (가장 중요)
        night_counts = [counts[2] for counts in employee_shift_counts]
        if len(night_counts) > 1 and max(night_counts) > 0:
            night_variance = np.var(night_counts)
            score -= night_variance * 10  # 야간근무 불균형 페널티
        
        # 전체 근무일 공평성
        total_work_days = [sum(counts[:3]) for counts in employee_shift_counts]  # OFF 제외
        if len(total_work_days) > 1 and max(total_work_days) > 0:
            work_variance = np.var(total_work_days)
            score -= work_variance * 5
        
        # 휴일 공평성
        off_counts = [counts[3] for counts in employee_shift_counts]
        if len(off_counts) > 1:
            off_variance = np.var(off_counts)
            score -= off_variance * 3
        
        return score
    
    def _enhanced_coverage_score(self, schedule: List[List[int]], constraints: Dict[str, Any]) -> float:
        """향상된 커버리지 점수"""
        score = 0.0
        required_staff = constraints.get("required_staff", {"day": 3, "evening": 2, "night": 1})
        
        for day_schedule in schedule:
            for shift_type in range(3):  # day, evening, night
                actual_count = day_schedule.count(shift_type)
                required_count = required_staff.get(self.shift_types[shift_type], 1)
                
                if actual_count >= required_count:
                    score += 10
                    # 초과 인력에 대한 작은 보너스
                    if actual_count > required_count:
                        score += (actual_count - required_count) * 2
        
        return score
    
    # ============ Utility Functions ============
    
    def _generate_tabu_neighbors(self, schedule: List[List[int]], 
                               employees: List[Dict],
                               constraints: Dict[str, Any]) -> List[Tuple[List[List[int]], str]]:
        """Tabu Search를 위한 이웃해 생성"""
        neighbors = []
        max_neighbors = 20
        
        for _ in range(max_neighbors):
            neighborhood_type = random.choice(list(NeighborhoodType))
            neighbor = self._generate_neighborhood_move(schedule, neighborhood_type, employees, constraints)
            
            if neighbor is not None:
                move_description = f"{neighborhood_type.value}_{random.randint(1000, 9999)}"
                neighbors.append((neighbor, move_description))
        
        return neighbors
    
    def _is_tabu_move(self, move: str) -> bool:
        """Tabu move 여부 확인"""
        return move in self.tabu_list
    
    def _is_request_for_day(self, request: Dict, day: int) -> bool:
        """특정 날짜에 대한 요청인지 확인"""
        try:
            request_date = request.get("request_date")
            if hasattr(request_date, 'day'):
                return request_date.day - 1 == day
            elif isinstance(request_date, str):
                date_obj = datetime.strptime(request_date, '%Y-%m-%d')
                return date_obj.day - 1 == day
        except (AttributeError, ValueError):
            pass
        return False
    
    def _get_employee_index(self, employee_id: int, employees: List[Dict]) -> Optional[int]:
        """직원 ID로 인덱스 찾기"""
        for idx, emp in enumerate(employees):
            if emp['id'] == employee_id:
                return idx
        return None
    
    def _generate_constraint_report(self, schedule: List[List[int]], 
                                  employees: List[Dict],
                                  constraints: Dict[str, Any],
                                  shift_requests: List[Dict]) -> Dict[str, Any]:
        """제약조건 위반 보고서 생성"""
        report = {
            'legal_violations': [],
            'safety_violations': [],
            'role_violations': [],
            'pattern_violations': [],
            'total_violations': 0
        }
        
        # 법적 위반 검사
        for emp_idx, emp in enumerate(employees):
            violations = self._check_legal_violations(schedule, emp_idx, emp)
            report['legal_violations'].extend(violations)
        
        # 안전 위반 검사
        safety_violations = self._check_safety_violations(schedule, constraints)
        report['safety_violations'].extend(safety_violations)
        
        # 역할 위반 검사
        role_violations = self._check_role_violations(schedule, employees, constraints)
        report['role_violations'].extend(role_violations)
        
        report['total_violations'] = (len(report['legal_violations']) + 
                                    len(report['safety_violations']) + 
                                    len(report['role_violations']))
        
        return report
    
    def _check_legal_violations(self, schedule: List[List[int]], emp_idx: int, emp: Dict) -> List[str]:
        """법적 위반 검사"""
        violations = []
        
        # 연속 근무일 확인
        max_consecutive = 0
        current_consecutive = 0
        for day in range(self.days_in_month):
            if schedule[day][emp_idx] != 3:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        if max_consecutive > 5:
            violations.append(f"Employee {emp['id']}: {max_consecutive} consecutive work days (max: 5)")
        
        return violations
    
    def _check_safety_violations(self, schedule: List[List[int]], constraints: Dict[str, Any]) -> List[str]:
        """안전 위반 검사"""
        violations = []
        required_staff = constraints.get('required_staff', {"day": 3, "evening": 2, "night": 1})
        
        for day_idx, day_schedule in enumerate(schedule):
            for shift_type in range(3):
                actual_count = day_schedule.count(shift_type)
                required_count = required_staff.get(self.shift_types[shift_type], 1)
                
                if actual_count < required_count:
                    violations.append(
                        f"Day {day_idx+1}, {self.shift_types[shift_type]} shift: "
                        f"{actual_count} staff (required: {required_count})"
                    )
        
        return violations
    
    def _check_role_violations(self, schedule: List[List[int]], 
                             employees: List[Dict], 
                             constraints: Dict[str, Any]) -> List[str]:
        """역할 위반 검사"""
        violations = []
        
        # 시간제 야간근무 위반 검사
        for emp_idx, emp in enumerate(employees):
            if emp.get('employment_type') == 'part_time':
                night_shifts = sum(1 for day_schedule in schedule if day_schedule[emp_idx] == 2)
                if night_shifts > 0:
                    violations.append(f"Part-time employee {emp['id']} assigned {night_shifts} night shifts")
        
        return violations