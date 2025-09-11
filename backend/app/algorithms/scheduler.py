"""
간호사 근무표 생성 알고리즘
Hybrid Metaheuristic: Simulated Annealing + Local Search
"""
import random
import math
import copy
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

class NurseScheduler:
    """간호사 근무표 최적화 스케줄러"""
    
    def __init__(self, ward_id: int, month: int, year: int):
        self.ward_id = ward_id
        self.month = month
        self.year = year
        self.days_in_month = self._get_days_in_month(year, month)
        
        # 근무 유형
        self.shift_types = ["day", "evening", "night", "off"]
        
        # 알고리즘 파라미터
        self.initial_temp = 100.0
        self.final_temp = 0.1
        self.cooling_rate = 0.95
        self.max_iterations = 1000
        
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
        """근무표 생성"""
        
        # 1. 초기 근무표 생성
        initial_schedule = self._generate_initial_schedule(employees)
        
        # 2. Simulated Annealing으로 최적화
        optimized_schedule = self._simulated_annealing(
            initial_schedule, employees, constraints, shift_requests
        )
        
        # 3. Local Search로 미세조정
        final_schedule = self._local_search(
            optimized_schedule, employees, constraints, shift_requests
        )
        
        # 4. 결과 포맷팅
        return self._format_schedule(final_schedule, employees)
    
    def _generate_initial_schedule(self, employees: List[Dict]) -> List[List[int]]:
        """초기 근무표 생성 (랜덤)"""
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
        """적합도 함수"""
        
        total_score = 0.0
        
        # 1. 커버리지 점수 (필수 근무 인원 충족)
        total_score += self._coverage_score(schedule, constraints)
        
        # 2. 근무 형평성 점수
        total_score += self._fairness_score(schedule, employees)
        
        # 3. 연속근무 제약 점수
        total_score += self._consecutive_shifts_score(schedule, employees)
        
        # 4. 희망근무 반영 점수
        total_score += self._preference_score(schedule, employees, shift_requests)
        
        # 5. 근무패턴 점수
        total_score += self._pattern_score(schedule, employees)
        
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