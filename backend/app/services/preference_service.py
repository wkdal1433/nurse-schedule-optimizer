"""
개인 선호도 및 요청 관리 서비스
"""
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import (
    PreferenceTemplate, ShiftRequestV2, PreferenceScore, 
    Employee, Schedule, User
)
import json
from collections import defaultdict

class PreferenceService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_preference_template(self, employee_id: int, preferences: Dict) -> PreferenceTemplate:
        """간호사의 선호도 템플릿 생성"""
        # 기존 템플릿이 있다면 비활성화
        existing = self.db.query(PreferenceTemplate).filter(
            PreferenceTemplate.employee_id == employee_id,
            PreferenceTemplate.is_active == True
        ).first()
        
        if existing:
            existing.is_active = False
        
        # 새 템플릿 생성
        new_template = PreferenceTemplate(
            employee_id=employee_id,
            preferred_shifts=preferences.get("preferred_shifts", []),
            avoided_shifts=preferences.get("avoided_shifts", []),
            max_night_shifts_per_month=preferences.get("max_night_shifts_per_month", 10),
            max_weekend_shifts_per_month=preferences.get("max_weekend_shifts_per_month", 8),
            preferred_patterns=preferences.get("preferred_patterns", []),
            avoided_patterns=preferences.get("avoided_patterns", []),
            max_consecutive_days=preferences.get("max_consecutive_days", 3),
            min_days_off_after_nights=preferences.get("min_days_off_after_nights", 1),
            cannot_work_alone=preferences.get("cannot_work_alone", False),
            needs_senior_support=preferences.get("needs_senior_support", False)
        )
        
        self.db.add(new_template)
        self.db.commit()
        self.db.refresh(new_template)
        return new_template
    
    def submit_shift_request(self, employee_id: int, request_data: Dict) -> ShiftRequestV2:
        """근무 요청 제출"""
        request = ShiftRequestV2(
            employee_id=employee_id,
            start_date=datetime.fromisoformat(request_data["start_date"]),
            end_date=datetime.fromisoformat(request_data["end_date"]),
            request_type=request_data["request_type"],
            priority=request_data.get("priority", "normal"),
            shift_type=request_data.get("shift_type"),
            reason=request_data.get("reason", ""),
            medical_reason=request_data.get("medical_reason", False),
            is_recurring=request_data.get("is_recurring", False),
            recurrence_pattern=request_data.get("recurrence_pattern"),
            flexibility_level=request_data.get("flexibility_level", 1),
            alternative_acceptable=request_data.get("alternative_acceptable", True)
        )
        
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request
    
    def review_request(self, request_id: int, reviewer_id: int, 
                      status: str, admin_notes: str = "") -> ShiftRequestV2:
        """요청 검토 및 승인/거부"""
        request = self.db.query(ShiftRequestV2).filter(
            ShiftRequestV2.id == request_id
        ).first()
        
        if not request:
            raise ValueError("요청을 찾을 수 없습니다")
        
        request.status = status
        request.admin_notes = admin_notes
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(request)
        return request
    
    def get_employee_preferences(self, employee_id: int) -> Optional[PreferenceTemplate]:
        """간호사 선호도 조회"""
        return self.db.query(PreferenceTemplate).filter(
            PreferenceTemplate.employee_id == employee_id,
            PreferenceTemplate.is_active == True
        ).first()
    
    def get_pending_requests(self, ward_id: Optional[int] = None) -> List[ShiftRequestV2]:
        """대기 중인 요청 조회"""
        query = self.db.query(ShiftRequestV2).join(Employee).filter(
            ShiftRequestV2.status == "pending"
        )
        
        if ward_id:
            query = query.filter(Employee.ward_id == ward_id)
        
        return query.order_by(ShiftRequestV2.created_at.desc()).all()
    
    def calculate_preference_score(self, employee_id: int, 
                                  schedule_data: Dict, schedule_id: int) -> PreferenceScore:
        """개별 간호사의 선호도 점수 계산"""
        preferences = self.get_employee_preferences(employee_id)
        if not preferences:
            return self._create_default_score(employee_id, schedule_id)
        
        employee_shifts = schedule_data.get(str(employee_id), [])
        if not employee_shifts:
            return self._create_default_score(employee_id, schedule_id)
        
        # 각 점수 계산
        shift_score = self._calculate_shift_preference_score(employee_shifts, preferences)
        pattern_score = self._calculate_pattern_preference_score(employee_shifts, preferences)
        workload_score = self._calculate_workload_fairness_score(employee_shifts, preferences)
        
        # 요청 충족률 계산
        vacation_rate = self._calculate_vacation_fulfillment_rate(employee_id, schedule_data)
        request_rate = self._calculate_request_fulfillment_rate(employee_id, schedule_data)
        
        # 월별 통계
        stats = self._calculate_monthly_stats(employee_shifts)
        
        # 전체 점수 계산
        total_score = (shift_score * 0.3 + pattern_score * 0.2 + 
                      workload_score * 0.2 + vacation_rate * 0.15 + 
                      request_rate * 0.15)
        
        # PreferenceScore 객체 생성
        score_obj = PreferenceScore(
            employee_id=employee_id,
            schedule_id=schedule_id,
            total_preference_score=total_score,
            shift_preference_score=shift_score,
            pattern_preference_score=pattern_score,
            workload_fairness_score=workload_score,
            vacation_fulfillment_rate=vacation_rate,
            shift_request_fulfillment_rate=request_rate,
            night_shifts_assigned=stats["night_shifts"],
            weekend_shifts_assigned=stats["weekend_shifts"],
            total_hours_assigned=stats["total_hours"]
        )
        
        self.db.add(score_obj)
        self.db.commit()
        self.db.refresh(score_obj)
        return score_obj
    
    def _calculate_shift_preference_score(self, shifts: List[str], 
                                        preferences: PreferenceTemplate) -> float:
        """근무 유형 선호도 점수 계산"""
        if not shifts:
            return 0.0
        
        preferred = preferences.preferred_shifts or []
        avoided = preferences.avoided_shifts or []
        
        score = 0.0
        total_shifts = len([s for s in shifts if s != "off"])
        
        if total_shifts == 0:
            return 100.0
        
        for shift in shifts:
            if shift == "off":
                continue
            if shift in preferred:
                score += 2.0
            elif shift in avoided:
                score -= 1.0
            else:
                score += 1.0
        
        # 0-100 범위로 정규화
        max_possible = total_shifts * 2.0
        min_possible = total_shifts * -1.0
        normalized = ((score - min_possible) / (max_possible - min_possible)) * 100
        
        return max(0.0, min(100.0, normalized))
    
    def _calculate_pattern_preference_score(self, shifts: List[str], 
                                          preferences: PreferenceTemplate) -> float:
        """근무 패턴 선호도 점수 계산"""
        if len(shifts) < 2:
            return 100.0
        
        preferred_patterns = preferences.preferred_patterns or []
        avoided_patterns = preferences.avoided_patterns or []
        
        score = 0.0
        pattern_count = 0
        
        for i in range(len(shifts) - 1):
            current = shifts[i]
            next_shift = shifts[i + 1]
            pattern = f"{current}->{next_shift}"
            
            pattern_count += 1
            
            if pattern in preferred_patterns:
                score += 2.0
            elif pattern in avoided_patterns:
                score -= 2.0
            else:
                score += 1.0
        
        if pattern_count == 0:
            return 100.0
        
        # 0-100 범위로 정규화
        max_possible = pattern_count * 2.0
        min_possible = pattern_count * -2.0
        normalized = ((score - min_possible) / (max_possible - min_possible)) * 100
        
        return max(0.0, min(100.0, normalized))
    
    def _calculate_workload_fairness_score(self, shifts: List[str], 
                                         preferences: PreferenceTemplate) -> float:
        """근무량 공정성 점수 계산"""
        night_count = shifts.count("night")
        weekend_count = self._count_weekend_shifts(shifts)
        
        # 선호 최대치와 비교
        max_nights = preferences.max_night_shifts_per_month
        max_weekends = preferences.max_weekend_shifts_per_month
        
        night_score = 100.0 if night_count <= max_nights else max(0, 100 - (night_count - max_nights) * 10)
        weekend_score = 100.0 if weekend_count <= max_weekends else max(0, 100 - (weekend_count - max_weekends) * 10)
        
        return (night_score + weekend_score) / 2
    
    def _count_weekend_shifts(self, shifts: List[str]) -> int:
        """주말 근무 횟수 계산 (토요일=5, 일요일=6)"""
        weekend_count = 0
        for i, shift in enumerate(shifts):
            if shift != "off":
                day_of_week = i % 7
                if day_of_week in [5, 6]:  # 토, 일
                    weekend_count += 1
        return weekend_count
    
    def _calculate_vacation_fulfillment_rate(self, employee_id: int, 
                                           schedule_data: Dict) -> float:
        """휴가 요청 충족률 계산"""
        # 해당 기간의 휴가 요청 조회
        vacation_requests = self.db.query(ShiftRequestV2).filter(
            ShiftRequestV2.employee_id == employee_id,
            ShiftRequestV2.request_type == "vacation",
            ShiftRequestV2.status.in_(["approved", "partially_approved"])
        ).all()
        
        if not vacation_requests:
            return 100.0
        
        fulfilled_days = 0
        total_requested_days = 0
        
        for request in vacation_requests:
            days_diff = (request.end_date - request.start_date).days + 1
            total_requested_days += days_diff
            
            # 스케줄에서 실제 휴가가 반영된 날짜 수 계산
            employee_shifts = schedule_data.get(str(employee_id), [])
            for day_idx in range(len(employee_shifts)):
                schedule_date = request.start_date + timedelta(days=day_idx)
                if (schedule_date >= request.start_date and 
                    schedule_date <= request.end_date and 
                    day_idx < len(employee_shifts) and
                    employee_shifts[day_idx] == "off"):
                    fulfilled_days += 1
        
        if total_requested_days == 0:
            return 100.0
        
        return (fulfilled_days / total_requested_days) * 100
    
    def _calculate_request_fulfillment_rate(self, employee_id: int, 
                                          schedule_data: Dict) -> float:
        """일반 근무 요청 충족률 계산"""
        shift_requests = self.db.query(ShiftRequestV2).filter(
            ShiftRequestV2.employee_id == employee_id,
            ShiftRequestV2.request_type == "shift_preference",
            ShiftRequestV2.status.in_(["approved", "partially_approved"])
        ).all()
        
        if not shift_requests:
            return 100.0
        
        # 간단한 충족률 계산 (실제로는 더 복잡한 로직 필요)
        approved_requests = len([r for r in shift_requests if r.status == "approved"])
        total_requests = len(shift_requests)
        
        return (approved_requests / total_requests) * 100 if total_requests > 0 else 100.0
    
    def _calculate_monthly_stats(self, shifts: List[str]) -> Dict[str, int]:
        """월별 근무 통계 계산"""
        return {
            "night_shifts": shifts.count("night"),
            "weekend_shifts": self._count_weekend_shifts(shifts),
            "total_hours": len([s for s in shifts if s != "off"]) * 8  # 8시간 근무 가정
        }
    
    def _create_default_score(self, employee_id: int, schedule_id: int) -> PreferenceScore:
        """기본 점수 객체 생성"""
        return PreferenceScore(
            employee_id=employee_id,
            schedule_id=schedule_id,
            total_preference_score=50.0,
            shift_preference_score=50.0,
            pattern_preference_score=50.0,
            workload_fairness_score=50.0,
            vacation_fulfillment_rate=50.0,
            shift_request_fulfillment_rate=50.0
        )
    
    def get_fairness_analysis(self, schedule: Schedule) -> Dict[str, Any]:
        """공정성 분석 리포트 생성"""
        schedule_data = schedule.schedule_data
        employees = self.db.query(Employee).filter(
            Employee.ward_id == schedule.ward_id,
            Employee.is_active == True
        ).all()
        
        analysis = {
            "total_employees": len(employees),
            "fairness_scores": [],
            "night_shift_distribution": {},
            "weekend_distribution": {},
            "preference_satisfaction": {},
            "overall_fairness_score": 0.0
        }
        
        total_fairness = 0.0
        
        for employee in employees:
            emp_shifts = schedule_data.get(str(employee.id), [])
            night_count = emp_shifts.count("night")
            weekend_count = self._count_weekend_shifts(emp_shifts)
            
            # 선호도 점수 계산
            preference_score = self.calculate_preference_score(
                employee.id, schedule_data, schedule.id
            )
            
            analysis["fairness_scores"].append({
                "employee_id": employee.id,
                "employee_name": employee.user.full_name,
                "total_score": preference_score.total_preference_score,
                "night_shifts": night_count,
                "weekend_shifts": weekend_count
            })
            
            analysis["night_shift_distribution"][employee.id] = night_count
            analysis["weekend_distribution"][employee.id] = weekend_count
            analysis["preference_satisfaction"][employee.id] = preference_score.total_preference_score
            
            total_fairness += preference_score.total_preference_score
        
        analysis["overall_fairness_score"] = total_fairness / len(employees) if employees else 0.0
        
        return analysis
    
    def get_request_statistics(self, ward_id: Optional[int] = None, 
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """요청 통계 조회"""
        query = self.db.query(ShiftRequestV2).join(Employee)
        
        if ward_id:
            query = query.filter(Employee.ward_id == ward_id)
        if start_date:
            query = query.filter(ShiftRequestV2.created_at >= start_date)
        if end_date:
            query = query.filter(ShiftRequestV2.created_at <= end_date)
        
        requests = query.all()
        
        stats = {
            "total_requests": len(requests),
            "by_type": defaultdict(int),
            "by_status": defaultdict(int),
            "by_priority": defaultdict(int),
            "approval_rate": 0.0,
            "average_processing_time": 0.0
        }
        
        processed_requests = []
        
        for request in requests:
            stats["by_type"][request.request_type] += 1
            stats["by_status"][request.status] += 1
            stats["by_priority"][request.priority] += 1
            
            if request.reviewed_at:
                processing_time = (request.reviewed_at - request.created_at).total_seconds() / 3600  # 시간 단위
                processed_requests.append(processing_time)
        
        approved = stats["by_status"]["approved"] + stats["by_status"]["partially_approved"]
        stats["approval_rate"] = (approved / len(requests)) * 100 if requests else 0.0
        stats["average_processing_time"] = sum(processed_requests) / len(processed_requests) if processed_requests else 0.0
        
        return stats