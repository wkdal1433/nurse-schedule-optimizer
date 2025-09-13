"""
권한 관리 서비스 - Manual editing & emergency override 권한 제어
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.models import User, Employee
import logging

logger = logging.getLogger(__name__)

class PermissionService:
    """Manual editing 및 Emergency override 권한 관리"""
    
    def __init__(self):
        # 권한 레벨 정의
        self.permission_levels = {
            'admin': 5,           # 시스템 관리자 - 모든 권한
            'head_nurse': 4,      # 수간호사 - 병동 내 모든 권한
            'senior_nurse': 3,    # 선임 간호사 - 제한적 편집 권한
            'staff_nurse': 2,     # 일반 간호사 - 기본 편집 권한
            'new_nurse': 1        # 신입 간호사 - 읽기 전용
        }
        
        # 기능별 최소 권한 레벨
        self.required_permissions = {
            'view_schedule': 1,           # 스케줄 조회
            'edit_own_requests': 1,       # 본인 근무 희망 편집
            'basic_schedule_edit': 2,     # 기본 스케줄 편집
            'shift_swap': 2,             # 근무 교환
            'emergency_request': 2,       # 응급 상황 요청
            'approve_swap': 3,           # 근무 교환 승인
            'manual_override': 3,        # 수동 오버라이드 (제한적)
            'emergency_override': 4,     # 응급 오버라이드
            'schedule_publish': 4,       # 스케줄 발행
            'bulk_edit': 4,              # 대량 편집
            'system_override': 5         # 시스템 레벨 오버라이드
        }
    
    def check_permission(
        self, 
        db: Session, 
        user_id: int, 
        action: str, 
        ward_id: Optional[int] = None,
        target_employee_id: Optional[int] = None
    ) -> Dict:
        """권한 검사 수행"""
        try:
            # 사용자 정보 조회
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    'allowed': False,
                    'reason': '사용자 정보를 찾을 수 없습니다',
                    'level': 0
                }
            
            employee = db.query(Employee).filter(Employee.user_id == user_id).first()
            if not employee:
                return {
                    'allowed': False,
                    'reason': '직원 정보를 찾을 수 없습니다',
                    'level': 0
                }
            
            # 사용자 권한 레벨 확인
            user_level = self.permission_levels.get(employee.role, 0)
            required_level = self.required_permissions.get(action, 999)
            
            if user_level < required_level:
                return {
                    'allowed': False,
                    'reason': f'권한 부족 - 필요 레벨: {required_level}, 현재 레벨: {user_level}',
                    'level': user_level
                }
            
            # 병동별 권한 검사
            ward_permission = self._check_ward_permission(employee, ward_id)
            if not ward_permission['allowed']:
                return ward_permission
            
            # 대상 직원에 대한 권한 검사 (있는 경우)
            if target_employee_id:
                target_permission = self._check_target_employee_permission(
                    db, employee, target_employee_id
                )
                if not target_permission['allowed']:
                    return target_permission
            
            return {
                'allowed': True,
                'reason': 'Permission granted',
                'level': user_level,
                'role': employee.role
            }
            
        except Exception as e:
            logger.error(f"권한 검사 중 오류: {str(e)}")
            return {
                'allowed': False,
                'reason': '권한 검사 중 오류 발생',
                'level': 0
            }
    
    def _check_ward_permission(self, employee: Employee, ward_id: Optional[int]) -> Dict:
        """병동 권한 검사"""
        if not ward_id:
            return {'allowed': True, 'reason': 'No ward restriction'}
        
        # 관리자는 모든 병동 접근 가능
        if employee.role == 'admin':
            return {'allowed': True, 'reason': 'Admin access'}
        
        # 수간호사는 자신의 병동만 관리 가능
        if employee.role == 'head_nurse':
            if employee.ward_id == ward_id:
                return {'allowed': True, 'reason': 'Head nurse ward access'}
            else:
                return {
                    'allowed': False, 
                    'reason': '다른 병동에 대한 권한이 없습니다'
                }
        
        # 일반 간호사들은 자신의 병동만 편집 가능
        if employee.ward_id != ward_id:
            return {
                'allowed': False,
                'reason': '자신의 병동에 대해서만 편집 권한이 있습니다'
            }
        
        return {'allowed': True, 'reason': 'Same ward access'}
    
    def _check_target_employee_permission(
        self, 
        db: Session, 
        requester: Employee, 
        target_employee_id: int
    ) -> Dict:
        """대상 직원에 대한 권한 검사"""
        target_employee = db.query(Employee).filter(Employee.id == target_employee_id).first()
        if not target_employee:
            return {
                'allowed': False,
                'reason': '대상 직원 정보를 찾을 수 없습니다'
            }
        
        # 관리자는 모든 직원 편집 가능
        if requester.role == 'admin':
            return {'allowed': True, 'reason': 'Admin privilege'}
        
        # 수간호사는 자신의 병동 직원들 편집 가능
        if requester.role == 'head_nurse':
            if requester.ward_id == target_employee.ward_id:
                return {'allowed': True, 'reason': 'Head nurse ward authority'}
            else:
                return {
                    'allowed': False,
                    'reason': '다른 병동 직원은 편집할 수 없습니다'
                }
        
        # 선임 간호사는 동일 레벨 이하 직원만 편집 가능
        if requester.role == 'senior_nurse':
            requester_level = self.permission_levels.get(requester.role, 0)
            target_level = self.permission_levels.get(target_employee.role, 0)
            
            if requester_level >= target_level and requester.ward_id == target_employee.ward_id:
                return {'allowed': True, 'reason': 'Senior nurse authority'}
            else:
                return {
                    'allowed': False,
                    'reason': '동일 레벨 이하 직원만 편집 가능합니다'
                }
        
        # 일반 간호사는 본인만 편집 가능
        if requester.id == target_employee_id:
            return {'allowed': True, 'reason': 'Self edit'}
        else:
            return {
                'allowed': False,
                'reason': '다른 직원의 스케줄은 편집할 수 없습니다'
            }
    
    def get_available_actions(self, db: Session, user_id: int, ward_id: Optional[int] = None) -> List[str]:
        """사용자에게 허용된 액션 목록 반환"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            
            employee = db.query(Employee).filter(Employee.user_id == user_id).first()
            if not employee:
                return []
            
            user_level = self.permission_levels.get(employee.role, 0)
            available_actions = []
            
            for action, required_level in self.required_permissions.items():
                if user_level >= required_level:
                    # 병동 권한도 체크
                    if ward_id:
                        ward_check = self._check_ward_permission(employee, ward_id)
                        if ward_check['allowed']:
                            available_actions.append(action)
                    else:
                        available_actions.append(action)
            
            return available_actions
            
        except Exception as e:
            logger.error(f"사용자 액션 목록 조회 중 오류: {str(e)}")
            return []
    
    def create_permission_summary(self, db: Session, user_id: int) -> Dict:
        """사용자 권한 요약 생성"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'error': '사용자 정보 없음'}
            
            employee = db.query(Employee).filter(Employee.user_id == user_id).first()
            if not employee:
                return {'error': '직원 정보 없음'}
            
            user_level = self.permission_levels.get(employee.role, 0)
            
            return {
                'user_id': user_id,
                'role': employee.role,
                'permission_level': user_level,
                'ward_id': employee.ward_id,
                'available_actions': self.get_available_actions(db, user_id, employee.ward_id),
                'permissions': {
                    'can_edit_schedules': user_level >= 2,
                    'can_approve_changes': user_level >= 3,
                    'can_emergency_override': user_level >= 4,
                    'can_system_override': user_level >= 5,
                    'can_manage_ward': user_level >= 4,
                    'can_access_all_wards': user_level >= 5
                }
            }
            
        except Exception as e:
            logger.error(f"권한 요약 생성 중 오류: {str(e)}")
            return {'error': '권한 요약 생성 실패'}

def check_manual_editing_permission(action: str):
    """Manual editing API를 위한 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # FastAPI의 Depends를 통해 전달된 user_id와 db 추출
            db = kwargs.get('db')
            user_id = kwargs.get('current_user_id')  # 실제 auth에서 가져온 user_id
            ward_id = kwargs.get('ward_id')
            
            if not user_id or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            permission_service = PermissionService()
            permission_result = permission_service.check_permission(
                db, user_id, action, ward_id
            )
            
            if not permission_result['allowed']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"권한 부족: {permission_result['reason']}"
                )
            
            # 권한 정보를 kwargs에 추가하여 함수에 전달
            kwargs['permission_info'] = permission_result
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator