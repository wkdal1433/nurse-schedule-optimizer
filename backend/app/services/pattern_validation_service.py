from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import Employee, ShiftAssignment
import logging

logger = logging.getLogger(__name__)

class PatternValidationService:
    """근무 패턴 검증 서비스 - 피로도 누적 방지 및 안전한 근무 패턴 보장"""
    
    def __init__(self):
        # 위험한 패턴 정의
        self.dangerous_patterns = {
            'day_to_night': {'penalty': -30, 'description': 'Day 다음날 Night 근무'},
            'excessive_nights': {'penalty': -30, 'description': '연속 3일 이상 Night 근무'},
            'no_rest_after_nights': {'penalty': -25, 'description': 'Night 근무 후 충분한 휴식 없음'},
            'weekend_overload': {'penalty': -20, 'description': '주말 연속 근무 과부하'},
            'split_shifts': {'penalty': -15, 'description': '분할 근무 패턴'},
        }
    
    def validate_employee_pattern(
        self, 
        db: Session, 
        employee_id: int, 
        assignments: List[Dict],
        period_start: datetime,
        period_end: datetime
    ) -> Dict:
        """직원별 근무 패턴 검증"""
        try:
            violations = []
            total_penalty = 0
            
            # 시간순으로 정렬된 배정 리스트
            sorted_assignments = sorted(assignments, key=lambda x: x['shift_date'])
            
            # 1. Day → Next Day Night 패턴 검사
            day_night_violations = self._check_day_to_night_pattern(sorted_assignments)
            violations.extend(day_night_violations)
            
            # 2. 연속 야간 근무 검사
            consecutive_night_violations = self._check_consecutive_nights(sorted_assignments)
            violations.extend(consecutive_night_violations)
            
            # 3. 야간 근무 후 휴식 검사
            night_rest_violations = self._check_night_rest_pattern(sorted_assignments)
            violations.extend(night_rest_violations)
            
            # 4. 주말 과부하 검사
            weekend_violations = self._check_weekend_overload(sorted_assignments)
            violations.extend(weekend_violations)
            
            # 5. 분할 근무 패턴 검사
            split_shift_violations = self._check_split_shifts(sorted_assignments)
            violations.extend(split_shift_violations)
            
            # 총 패널티 계산
            for violation in violations:
                total_penalty += violation['penalty']
            
            return {
                'employee_id': employee_id,
                'is_valid': len(violations) == 0,
                'total_penalty': total_penalty,
                'violations': violations,
                'pattern_score': max(0, 100 + total_penalty),  # 100점 만점에서 패널티 차감
                'recommendations': self._generate_recommendations(violations)
            }
            
        except Exception as e:
            logger.error(f"패턴 검증 중 오류 발생 - employee_id: {employee_id}, error: {str(e)}")
            return {
                'employee_id': employee_id,
                'is_valid': False,
                'total_penalty': -100,
                'violations': [{'type': 'system_error', 'description': '패턴 검증 시스템 오류'}],
                'pattern_score': 0,
                'recommendations': ['시스템 관리자에게 문의하세요']
            }
    
    def _check_day_to_night_pattern(self, assignments: List[Dict]) -> List[Dict]:
        """Day 근무 다음날 Night 근무 패턴 검사"""
        violations = []
        
        for i in range(len(assignments) - 1):
            current = assignments[i]
            next_shift = assignments[i + 1]
            
            current_date = datetime.strptime(current['shift_date'], '%Y-%m-%d').date()
            next_date = datetime.strptime(next_shift['shift_date'], '%Y-%m-%d').date()
            
            # 연속된 날짜인지 확인
            if (next_date - current_date).days == 1:
                if current['shift_type'] == 'day' and next_shift['shift_type'] == 'night':
                    violations.append({
                        'type': 'day_to_night',
                        'penalty': self.dangerous_patterns['day_to_night']['penalty'],
                        'description': f"{current_date} Day → {next_date} Night 근무",
                        'date_range': f"{current_date} ~ {next_date}",
                        'severity': 'high'
                    })
        
        return violations
    
    def _check_consecutive_nights(self, assignments: List[Dict]) -> List[Dict]:
        """연속 야간 근무 검사"""
        violations = []
        consecutive_nights = 0
        start_date = None
        
        for assignment in assignments:
            if assignment['shift_type'] == 'night':
                if consecutive_nights == 0:
                    start_date = assignment['shift_date']
                consecutive_nights += 1
            else:
                if consecutive_nights > 3:  # 3일 초과 시 위반
                    violations.append({
                        'type': 'excessive_nights',
                        'penalty': self.dangerous_patterns['excessive_nights']['penalty'],
                        'description': f"연속 {consecutive_nights}일 Night 근무",
                        'date_range': f"{start_date} ~ {assignments[assignments.index(assignment)-1]['shift_date']}",
                        'severity': 'high' if consecutive_nights > 4 else 'medium'
                    })
                consecutive_nights = 0
                start_date = None
        
        # 마지막까지 연속 야간이었다면
        if consecutive_nights > 3:
            violations.append({
                'type': 'excessive_nights',
                'penalty': self.dangerous_patterns['excessive_nights']['penalty'],
                'description': f"연속 {consecutive_nights}일 Night 근무",
                'date_range': f"{start_date} ~ {assignments[-1]['shift_date']}",
                'severity': 'high' if consecutive_nights > 4 else 'medium'
            })
        
        return violations
    
    def _check_night_rest_pattern(self, assignments: List[Dict]) -> List[Dict]:
        """야간 근무 후 충분한 휴식 시간 검사"""
        violations = []
        
        for i in range(len(assignments) - 1):
            current = assignments[i]
            next_shift = assignments[i + 1]
            
            if current['shift_type'] == 'night':
                current_date = datetime.strptime(current['shift_date'], '%Y-%m-%d').date()
                next_date = datetime.strptime(next_shift['shift_date'], '%Y-%m-%d').date()
                
                # 야간 근무 후 다음 근무까지의 간격
                days_gap = (next_date - current_date).days
                
                if days_gap == 1:  # 야간 근무 다음날 바로 근무
                    violations.append({
                        'type': 'no_rest_after_nights',
                        'penalty': self.dangerous_patterns['no_rest_after_nights']['penalty'],
                        'description': f"Night 근무 후 충분한 휴식 없음 ({current_date} Night → {next_date} {next_shift['shift_type']})",
                        'date_range': f"{current_date} ~ {next_date}",
                        'severity': 'medium'
                    })
        
        return violations
    
    def _check_weekend_overload(self, assignments: List[Dict]) -> List[Dict]:
        """주말 과부하 패턴 검사"""
        violations = []
        weekend_counts = {}
        
        for assignment in assignments:
            date = datetime.strptime(assignment['shift_date'], '%Y-%m-%d').date()
            week_num = date.isocalendar()[1]  # 주차
            
            if date.weekday() >= 5:  # 토요일(5), 일요일(6)
                if week_num not in weekend_counts:
                    weekend_counts[week_num] = 0
                weekend_counts[week_num] += 1
        
        for week_num, count in weekend_counts.items():
            if count >= 2:  # 주말 이틀 모두 근무
                violations.append({
                    'type': 'weekend_overload',
                    'penalty': self.dangerous_patterns['weekend_overload']['penalty'],
                    'description': f"{week_num}주차 주말 연속 근무 ({count}일)",
                    'date_range': f"Week {week_num}",
                    'severity': 'low'
                })
        
        return violations
    
    def _check_split_shifts(self, assignments: List[Dict]) -> List[Dict]:
        """분할 근무 패턴 검사 (하루 안에 여러 근무)"""
        violations = []
        date_shifts = {}
        
        for assignment in assignments:
            date = assignment['shift_date']
            if date not in date_shifts:
                date_shifts[date] = []
            date_shifts[date].append(assignment['shift_type'])
        
        for date, shifts in date_shifts.items():
            if len(shifts) > 1:  # 하루에 여러 근무
                violations.append({
                    'type': 'split_shifts',
                    'penalty': self.dangerous_patterns['split_shifts']['penalty'],
                    'description': f"분할 근무: {date}에 {', '.join(shifts)} 근무",
                    'date_range': date,
                    'severity': 'low'
                })
        
        return violations
    
    def _generate_recommendations(self, violations: List[Dict]) -> List[str]:
        """위반사항에 대한 개선 권장사항 생성"""
        recommendations = []
        
        violation_types = [v['type'] for v in violations]
        
        if 'day_to_night' in violation_types:
            recommendations.append("Day 근무와 Night 근무 사이에 최소 1일의 휴게일을 배치하세요")
        
        if 'excessive_nights' in violation_types:
            recommendations.append("연속 야간 근무는 최대 3일로 제한하고, 이후 충분한 휴게일을 제공하세요")
        
        if 'no_rest_after_nights' in violation_types:
            recommendations.append("Night 근무 후에는 최소 1일의 휴게일 또는 Day 근무로 배치하세요")
        
        if 'weekend_overload' in violation_types:
            recommendations.append("주말 근무 배정을 공평하게 분배하고 연속 주말 근무를 피하세요")
        
        if 'split_shifts' in violation_types:
            recommendations.append("하루에 여러 근무를 배정하지 말고 연속된 근무 시간으로 조정하세요")
        
        if not recommendations:
            recommendations.append("현재 근무 패턴에 특별한 문제가 없습니다")
        
        return recommendations
    
    def validate_schedule_patterns(
        self, 
        db: Session, 
        schedule_id: int
    ) -> Dict:
        """전체 스케줄의 패턴 검증"""
        try:
            # 스케줄의 모든 배정 조회
            assignments = db.query(ShiftAssignment).filter(
                ShiftAssignment.schedule_id == schedule_id
            ).all()
            
            if not assignments:
                return {
                    'schedule_id': schedule_id,
                    'is_valid': True,
                    'total_violations': 0,
                    'employee_results': [],
                    'overall_score': 100,
                    'summary': '배정된 근무가 없습니다'
                }
            
            # 직원별로 그룹화
            employee_assignments = {}
            for assignment in assignments:
                if assignment.employee_id not in employee_assignments:
                    employee_assignments[assignment.employee_id] = []
                
                employee_assignments[assignment.employee_id].append({
                    'shift_date': assignment.shift_date.strftime('%Y-%m-%d'),
                    'shift_type': assignment.shift_type,
                    'assignment_id': assignment.id
                })
            
            employee_results = []
            total_violations = 0
            total_penalty = 0
            
            # 각 직원별 패턴 검증
            for employee_id, emp_assignments in employee_assignments.items():
                period_start = min([datetime.strptime(a['shift_date'], '%Y-%m-%d') for a in emp_assignments])
                period_end = max([datetime.strptime(a['shift_date'], '%Y-%m-%d') for a in emp_assignments])
                
                result = self.validate_employee_pattern(
                    db, employee_id, emp_assignments, period_start, period_end
                )
                employee_results.append(result)
                total_violations += len(result['violations'])
                total_penalty += result['total_penalty']
            
            overall_score = max(0, 100 + (total_penalty / len(employee_assignments)))  # 평균 점수
            
            return {
                'schedule_id': schedule_id,
                'is_valid': total_violations == 0,
                'total_violations': total_violations,
                'employee_results': employee_results,
                'overall_score': round(overall_score, 1),
                'summary': self._generate_schedule_summary(employee_results)
            }
            
        except Exception as e:
            logger.error(f"스케줄 패턴 검증 중 오류 발생 - schedule_id: {schedule_id}, error: {str(e)}")
            return {
                'schedule_id': schedule_id,
                'is_valid': False,
                'total_violations': -1,
                'employee_results': [],
                'overall_score': 0,
                'summary': '패턴 검증 시스템 오류'
            }
    
    def _generate_schedule_summary(self, employee_results: List[Dict]) -> str:
        """스케줄 전체 패턴 검증 요약 생성"""
        total_employees = len(employee_results)
        valid_employees = len([r for r in employee_results if r['is_valid']])
        
        if valid_employees == total_employees:
            return f"모든 직원({total_employees}명)의 근무 패턴이 안전합니다"
        else:
            problem_count = total_employees - valid_employees
            return f"{total_employees}명 중 {problem_count}명의 근무 패턴에 개선이 필요합니다"
    
    def get_pattern_statistics(self, db: Session, ward_id: int, period_start: datetime, period_end: datetime) -> Dict:
        """병동별 패턴 통계 생성"""
        try:
            # 해당 병동의 직원들 조회
            employees = db.query(Employee).filter(Employee.ward_id == ward_id).all()
            
            pattern_stats = {
                'ward_id': ward_id,
                'period': f"{period_start.strftime('%Y-%m-%d')} ~ {period_end.strftime('%Y-%m-%d')}",
                'total_employees': len(employees),
                'pattern_violations': {
                    'day_to_night': 0,
                    'excessive_nights': 0,
                    'no_rest_after_nights': 0,
                    'weekend_overload': 0,
                    'split_shifts': 0
                },
                'average_pattern_score': 0,
                'high_risk_employees': []
            }
            
            # 각 직원별 패턴 분석 (실제 구현에서는 최근 스케줄 데이터 사용)
            # 여기서는 기본 구조만 제공
            
            return pattern_stats
            
        except Exception as e:
            logger.error(f"패턴 통계 생성 중 오류 발생 - ward_id: {ward_id}, error: {str(e)}")
            return {
                'ward_id': ward_id,
                'error': '패턴 통계 생성 실패'
            }