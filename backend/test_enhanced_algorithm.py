#!/usr/bin/env python3
"""
Enhanced Algorithm Test Script
고도화된 간호사 근무표 생성 알고리즘 테스트
"""
import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.algorithms.scheduler import NurseScheduler

def create_sample_employees():
    """테스트용 샘플 직원 데이터 생성"""
    return [
        {
            "id": 1,
            "user_id": 101,
            "employee_number": "N001",
            "skill_level": "senior",
            "years_experience": 5,
            "role": "staff_nurse",
            "employment_type": "full_time",
            "preferences": {},
            "user": {"full_name": "김간호사"}
        },
        {
            "id": 2,
            "user_id": 102,
            "employee_number": "N002",
            "skill_level": "junior",
            "years_experience": 1,
            "role": "new_nurse",
            "employment_type": "full_time",
            "preferences": {},
            "user": {"full_name": "이신입"}
        },
        {
            "id": 3,
            "user_id": 103,
            "employee_number": "N003",
            "skill_level": "senior",
            "years_experience": 7,
            "role": "head_nurse",
            "employment_type": "full_time",
            "preferences": {},
            "user": {"full_name": "박수간호사"}
        },
        {
            "id": 4,
            "user_id": 104,
            "employee_number": "N004",
            "skill_level": "mid",
            "years_experience": 3,
            "role": "staff_nurse",
            "employment_type": "full_time",
            "preferences": {},
            "user": {"full_name": "최간호사"}
        },
        {
            "id": 5,
            "user_id": 105,
            "employee_number": "N005",
            "skill_level": "mid",
            "years_experience": 2,
            "role": "staff_nurse",
            "employment_type": "part_time",
            "preferences": {},
            "user": {"full_name": "정시간제"}
        }
    ]

def create_sample_constraints():
    """테스트용 제약조건 생성"""
    return {
        "required_staff": {
            "day": 3,
            "evening": 2,
            "night": 1
        },
        "max_consecutive_work_days": 5,
        "max_consecutive_nights": 3,
        "min_rest_days_per_week": 1
    }

def create_sample_shift_requests():
    """테스트용 근무 요청 데이터 생성"""
    return [
        {
            "employee_id": 1,
            "request_date": datetime(2024, 12, 15),
            "shift_type": "day",
            "request_type": "request",
            "reason": "선호 근무"
        },
        {
            "employee_id": 2,
            "request_date": datetime(2024, 12, 20),
            "shift_type": "night",
            "request_type": "avoid",
            "reason": "개인 사정"
        }
    ]

def run_enhanced_algorithm_test():
    """고도화된 알고리즘 테스트 실행"""
    print("🚀 Enhanced Nurse Scheduling Algorithm Test")
    print("=" * 50)
    
    # 테스트 데이터 준비
    employees = create_sample_employees()
    constraints = create_sample_constraints()
    shift_requests = create_sample_shift_requests()
    
    print(f"📊 Test Data:")
    print(f"  - Employees: {len(employees)}")
    print(f"  - Constraints: {len(constraints)} rules")
    print(f"  - Shift Requests: {len(shift_requests)}")
    print()
    
    # 스케줄러 생성
    scheduler = NurseScheduler(ward_id=1, month=12, year=2024)
    
    print(f"🎯 Algorithm Parameters:")
    print(f"  - Initial Temperature: {scheduler.initial_temp}")
    print(f"  - Max Iterations: {scheduler.max_iterations}")
    print(f"  - Tabu List Size: {scheduler.tabu_list_size}")
    print(f"  - Neighborhood Types: {len(scheduler.neighborhood_weights)}")
    print()
    
    try:
        # 근무표 생성 실행
        print("⚡ Starting Enhanced Schedule Generation...")
        start_time = datetime.now()
        
        result = scheduler.generate_schedule(employees, constraints, shift_requests)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Schedule Generation Completed!")
        print(f"⏱️ Execution Time: {execution_time:.2f} seconds")
        print()
        
        # 결과 분석
        print("📈 Results Analysis:")
        print(f"  - Final Score: {result.get('total_score', 0):.2f}")
        print(f"  - Algorithm Phases: {', '.join(result.get('optimization_details', {}).get('algorithm_phases', []))}")
        print(f"  - Constraint Violations: {result.get('optimization_details', {}).get('constraint_violations', 0)}")
        print()
        
        # 제약조건 위반 보고서
        constraint_report = result.get('constraint_report', {})
        total_violations = constraint_report.get('total_violations', 0)
        
        print("🔍 Constraint Violation Report:")
        if total_violations == 0:
            print("  ✅ No constraint violations detected!")
        else:
            print(f"  ⚠️ Total violations: {total_violations}")
            
            legal_violations = constraint_report.get('legal_violations', [])
            if legal_violations:
                print(f"  📋 Legal violations: {len(legal_violations)}")
                for violation in legal_violations[:3]:  # Show first 3
                    print(f"    - {violation}")
            
            safety_violations = constraint_report.get('safety_violations', [])
            if safety_violations:
                print(f"  🚨 Safety violations: {len(safety_violations)}")
                for violation in safety_violations[:3]:  # Show first 3
                    print(f"    - {violation}")
        
        print()
        
        # 통계 정보
        stats = result.get('statistics', {})
        print("📊 Schedule Statistics:")
        print(f"  - Total Employees: {stats.get('total_employees', 0)}")
        print(f"  - Total Days: {stats.get('total_days', 0)}")
        
        shift_dist = stats.get('shift_distribution', {})
        print(f"  - Shift Distribution:")
        for shift_type, count in shift_dist.items():
            print(f"    {shift_type}: {count}")
        
        print()
        
        # 샘플 스케줄 출력 (첫 7일)
        schedule_data = result.get('schedule_data', {})
        print("📅 Sample Schedule (First 7 Days):")
        
        dates = sorted(schedule_data.keys())[:7]
        for date in dates:
            assignments = schedule_data[date]
            print(f"  {date}:")
            for assignment in assignments:
                emp_name = assignment['employee_name']
                shift = assignment['shift_type']
                print(f"    {emp_name}: {shift}")
            print()
        
        print("🎉 Enhanced Algorithm Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_enhanced_algorithm_test()
    sys.exit(0 if success else 1)