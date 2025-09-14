# 간호사 근무표 시스템 - 상세 구현 가이드 (개발자용)

> 백엔드/프론트엔드/테스팅 통합 개발 사양서

---

## 🎯 개발 우선순위 로드맵

### **Phase 1: 안전성 확보 (Day 1-2)**
1. 사전 인원 검증 (Feasibility Check) - 서버 우선
2. Generate 버튼 사전 차단 로직 - 클라이언트

### **Phase 2: 상세 분석 (Day 3-5)**
3. 달력 상세보기 Modal (4탭)
4. 점수 Breakdown API 및 UI

### **Phase 3: 실시간 편집 (Week 2)**
5. Drag & Drop 편집 + 실시간 재계산

### **Phase 4: 운영 지원 (Week 3-4)**
6. 긴급 오버라이드 & AI 대체 추천
7. 개인화 알림 시스템

### **Phase 5: 편의 기능 (Week 5+)**
8. PDF/카톡 공유, 근무 교환 요청

---

## 1. 🛡️ 사전 인원 검증 (Feasibility Check) - 최우선

### **목적**
스케줄 생성 전 병동/교대별 최소 인원 및 역할 요구사항 검증으로 안전 확보

### **API 설계**

#### **엔드포인트**
```http
POST /api/schedules/validate
POST /api/schedules/generate (내부 호출)
```

#### **요청 데이터**
```json
{
  "ward_id": 1,
  "period": {
    "start": "2025-10-01",
    "end": "2025-10-31"
  },
  "nurses": [
    {
      "id": "e123",
      "roles": ["senior", "icu"],
      "employment_type": "full_time",
      "availability": {
        "2025-10-01": ["day", "evening"],
        "2025-10-02": ["night"]
      },
      "is_active": true
    }
  ],
  "shift_min_requirements": {
    "day": 3,
    "evening": 2,
    "night": 3
  },
  "role_requirements": {
    "senior": 1
  }
}
```

#### **응답 데이터**
```json
// 성공
{
  "ok": true,
  "message": "모든 요구사항이 충족됩니다"
}

// 실패
{
  "ok": false,
  "reason": "insufficient_shift_staff",
  "detail": {
    "date": "2025-10-16",
    "shift": "night",
    "required": 3,
    "available": 2
  },
  "suggestions": [
    "야간 근무 가능한 간호사 1명 추가 필요",
    "파트타임 직원의 야간 근무 허용 고려",
    "최소 인원 기준 조정 검토"
  ]
}
```

### **백엔드 구현 (FastAPI/Python)**

```python
# app/services/feasibility_service.py
from datetime import date, timedelta
from typing import List, Dict, Any

def validate_staffing_requirements(
    ward_id: int,
    nurses: List[Dict],
    period_start: date,
    period_end: date,
    shift_min_requirements: Dict[str, int],
    role_requirements: Dict[str, int]
) -> Dict[str, Any]:
    """
    스케줄 생성 가능성 검증

    Args:
        nurses: 간호사 정보 리스트
        shift_min_requirements: {'day':3,'evening':2,'night':3}
        role_requirements: {'senior':1}

    Returns:
        검증 결과 딕셔너리
    """

    # 1) 날짜별 교대별 최소 인원 검증
    for d in date_range(period_start, period_end):
        for shift, min_count in shift_min_requirements.items():
            # 해당 날짜/교대 가능한 간호사 필터링
            candidates = [
                n for n in nurses
                if n.get('is_active')
                and shift in n.get('availability', {}).get(d.isoformat(), [])
                and employment_ok(n, shift)
            ]

            if len(candidates) < min_count:
                return {
                    "ok": False,
                    "reason": "insufficient_shift_staff",
                    "detail": {
                        "date": d.isoformat(),
                        "shift": shift,
                        "required": min_count,
                        "available": len(candidates)
                    },
                    "suggestions": recommend_actions_for_shortage(
                        d, shift, candidates, min_count
                    )
                }

    # 2) 역할별 전체 인원 검증
    for role, min_role_count in role_requirements.items():
        role_count = sum(
            1 for n in nurses
            if role in n.get('roles', [])
        )
        if role_count < min_role_count:
            return {
                "ok": False,
                "reason": "insufficient_role",
                "detail": {
                    "role": role,
                    "required": min_role_count,
                    "available": role_count
                }
            }

    return {"ok": True, "message": "모든 요구사항이 충족됩니다"}

def employment_ok(nurse: Dict, shift: str) -> bool:
    """고용 형태별 교대 가능성 검증"""
    if nurse.get('employment_type') == 'part_time' and shift == 'night':
        return False  # 파트타임 야간 불가
    return True

def recommend_actions_for_shortage(
    date: date,
    shift: str,
    available_candidates: List,
    required_count: int
) -> List[str]:
    """인력 부족 시 권고사항 생성"""
    shortage = required_count - len(available_candidates)
    suggestions = []

    if shortage > 0:
        suggestions.append(f"{shift} 근무 가능한 간호사 {shortage}명 추가 필요")

    if shift == 'night':
        suggestions.append("파트타임 직원의 야간 근무 허용 고려")
        suggestions.append("야간 전담 간호사 충원 검토")

    suggestions.append("최소 인원 기준 조정 검토")
    return suggestions

# app/api/schedules.py 수정
@router.post("/generate")
async def generate_schedule(request: ScheduleGenerateRequest, db: Session = Depends(get_db)):
    # 기존 generate_schedule 함수 최상단에 추가
    validation_result = validate_staffing_requirements(
        request.ward_id,
        request.nurses,
        request.period_start,
        request.period_end,
        request.shift_min_requirements,
        request.role_requirements
    )

    if not validation_result["ok"]:
        raise HTTPException(status_code=400, detail=validation_result)

    # 기존 스케줄 생성 로직 계속...

@router.post("/validate")
async def validate_schedule_feasibility(
    request: ScheduleValidateRequest,
    db: Session = Depends(get_db)
):
    """사전 검증 전용 엔드포인트"""
    result = validate_staffing_requirements(
        request.ward_id,
        request.nurses,
        request.period_start,
        request.period_end,
        request.shift_min_requirements,
        request.role_requirements
    )

    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result)

    return result
```

### **프론트엔드 구현 (React/TypeScript)**

```typescript
// src/services/scheduleService.ts
export interface ValidationResult {
  ok: boolean;
  reason?: string;
  detail?: {
    date: string;
    shift: string;
    required: number;
    available: number;
  };
  suggestions?: string[];
}

export const validateSchedule = async (
  wardId: number,
  period: { start: string; end: string },
  nurses: any[],
  shiftRequirements: Record<string, number>,
  roleRequirements: Record<string, number>
): Promise<ValidationResult> => {
  const response = await fetch('/api/schedules/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ward_id: wardId,
      period,
      nurses,
      shift_min_requirements: shiftRequirements,
      role_requirements: roleRequirements
    })
  });

  if (!response.ok) {
    const errorData = await response.json();
    return errorData.detail;
  }

  return await response.json();
};

// src/components/ValidationModal.tsx
interface ValidationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProceedAnyway: () => void;
  validationResult: ValidationResult;
}

const ValidationModal: React.FC<ValidationModalProps> = ({
  isOpen,
  onClose,
  onProceedAnyway,
  validationResult
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="validation-modal">
        <h2>⚠️ 인력 부족 감지</h2>

        {validationResult.detail && (
          <div className="shortage-details">
            <p>
              <strong>{validationResult.detail.date}</strong> {validationResult.detail.shift} 교대
            </p>
            <p>
              필요: {validationResult.detail.required}명 /
              가능: {validationResult.detail.available}명
            </p>
          </div>
        )}

        <div className="suggestions">
          <h3>권장 조치사항:</h3>
          <ul>
            {validationResult.suggestions?.map((suggestion, idx) => (
              <li key={idx}>{suggestion}</li>
            ))}
          </ul>
        </div>

        <div className="modal-actions">
          <button onClick={onClose} className="btn-cancel">
            취소
          </button>
          <button onClick={onProceedAnyway} className="btn-force">
            강제 진행 (관리자)
          </button>
        </div>
      </div>
    </div>
  );
};

// src/components/NurseScheduleApp.tsx 수정
const handleGenerateClick = async () => {
  setIsLoading(true);

  try {
    // 1단계: 사전 검증
    const validation = await validateSchedule(
      selectedWard.id,
      { start: periodStart, end: periodEnd },
      nurses,
      { day: 3, evening: 2, night: 3 },
      { senior: 1 }
    );

    if (!validation.ok) {
      setValidationResult(validation);
      setShowValidationModal(true);
      setIsLoading(false);
      return;
    }

    // 2단계: 검증 통과 시 스케줄 생성
    await generateSchedule();

  } catch (error) {
    console.error('검증 실패:', error);
    setIsLoading(false);
  }
};
```

---

## 2. 📊 상세 달력 및 점수 Breakdown

### **목표**
달력에서 날짜/교대 클릭 → 상세 Modal(4탭) → 배정자 목록 및 점수 분석

### **API 설계**

```http
GET /api/schedules/{schedule_id}/day/{date}/details
```

```json
{
  "date": "2025-10-16",
  "shifts": {
    "day": [
      {
        "employee_id": "e123",
        "name": "김간호사",
        "role": "senior",
        "mini_score": 85,
        "score_breakdown": {
          "compliance": 20,
          "preference": 15,
          "fairness": 10,
          "pattern": -5,
          "total": 40
        }
      }
    ],
    "evening": [...],
    "night": [...],
    "off": [...]
  }
}
```

### **백엔드 구현**

```python
# app/api/schedules.py
@router.get("/{schedule_id}/day/{date}/details")
async def get_day_details(
    schedule_id: int,
    date: str,
    db: Session = Depends(get_db)
):
    """특정 날짜의 교대별 상세 정보"""

    # 해당 날짜의 모든 배정 조회
    assignments = db.query(Assignment).filter(
        Assignment.schedule_id == schedule_id,
        Assignment.date == date
    ).all()

    shifts = {"day": [], "evening": [], "night": [], "off": []}

    for assignment in assignments:
        employee = assignment.employee

        # 개별 점수 계산
        score_breakdown = calculate_employee_score_for_date(
            employee, assignment, date
        )

        employee_data = {
            "employee_id": employee.id,
            "name": employee.name,
            "role": employee.role,
            "mini_score": score_breakdown["total"],
            "score_breakdown": score_breakdown
        }

        shifts[assignment.shift].append(employee_data)

    return {
        "date": date,
        "shifts": shifts
    }
```

### **프론트엔드 구현**

```typescript
// src/components/DayDetailModal.tsx
interface DayDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  date: string;
  scheduleId: number;
}

const DayDetailModal: React.FC<DayDetailModalProps> = ({
  isOpen,
  onClose,
  date,
  scheduleId
}) => {
  const [dayData, setDayData] = useState(null);
  const [activeTab, setActiveTab] = useState('day');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && date) {
      fetchDayDetails();
    }
  }, [isOpen, date]);

  const fetchDayDetails = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/schedules/${scheduleId}/day/${date}/details`
      );
      const data = await response.json();
      setDayData(data);
    } catch (error) {
      console.error('Failed to fetch day details:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="day-detail-modal">
        <div className="modal-header">
          <h2>📅 {date} 상세 현황</h2>
          <button onClick={onClose}>✕</button>
        </div>

        <div className="tab-navigation">
          {['day', 'evening', 'night', 'off'].map(shift => (
            <button
              key={shift}
              className={`tab ${activeTab === shift ? 'active' : ''}`}
              onClick={() => setActiveTab(shift)}
            >
              {shift === 'day' ? '🌅 주간' :
               shift === 'evening' ? '🌆 저녁' :
               shift === 'night' ? '🌙 야간' : '😴 휴무'}
            </button>
          ))}
        </div>

        <div className="tab-content">
          {loading ? (
            <div className="loading-skeleton">
              {[1,2,3].map(i => (
                <div key={i} className="skeleton-item" />
              ))}
            </div>
          ) : (
            <ShiftAssignmentList
              assignments={dayData?.shifts[activeTab] || []}
              shift={activeTab}
            />
          )}
        </div>
      </div>
    </div>
  );
};

// src/components/ShiftAssignmentList.tsx
const ShiftAssignmentList: React.FC<{
  assignments: any[];
  shift: string;
}> = ({ assignments, shift }) => {
  return (
    <div className="assignment-list">
      {assignments.map(assignment => (
        <div key={assignment.employee_id} className="assignment-card">
          <div className="employee-info">
            <span className="name">{assignment.name}</span>
            <span className={`role-badge ${assignment.role}`}>
              {assignment.role}
            </span>
          </div>

          <div className="score-section">
            <div className="mini-score">{assignment.mini_score}</div>
            <div className="score-tooltip">
              <h4>점수 상세:</h4>
              <div>법규 준수: {assignment.score_breakdown.compliance}</div>
              <div>선호도: {assignment.score_breakdown.preference}</div>
              <div>공평성: {assignment.score_breakdown.fairness}</div>
              <div>패턴: {assignment.score_breakdown.pattern}</div>
            </div>
          </div>

          <div className="actions">
            <button className="btn-recommend">대체자 제안</button>
            <button className="btn-edit">편집</button>
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

## 3. 🎯 Drag & Drop 편집 + 실시간 재계산

### **목표**
달력에서 드래그로 재배치 → Optimistic Update → 서버 검증 → 확정/롤백

### **API 설계**

```http
PATCH /api/schedules/{schedule_id}/assignments
```

```json
// 요청
{
  "date": "2025-10-16",
  "shift": "night",
  "from_employee_id": "e123",
  "to_employee_id": "e456",
  "override": false
}

// 응답 (성공)
{
  "ok": true,
  "new_score": 842,
  "delta": -5,
  "violations": [],
  "employee_scores": {
    "e123": 80,
    "e456": 85
  }
}

// 응답 (실패)
{
  "ok": false,
  "violations": [
    {
      "type": "minimum_staff",
      "detail": "ICU night shift minimum not met"
    }
  ],
  "message": "변경으로 인해 최소 인력 기준을 위반합니다"
}
```

### **백엔드 구현**

```python
# app/api/schedules.py
@router.patch("/{schedule_id}/assignments")
async def update_assignment(
    schedule_id: int,
    update_request: AssignmentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """근무 배정 변경"""

    # 1) 현재 상태 백업
    original_assignments = get_assignments_backup(schedule_id, db)

    try:
        # 2) 임시 변경 적용
        apply_assignment_change(update_request, db)

        # 3) 영향 범위만 제약조건 재검증 (성능 최적화)
        affected_dates = get_affected_date_range(
            update_request.date,
            days_before=2,
            days_after=2
        )

        violations = validate_constraints_for_dates(
            schedule_id,
            affected_dates,
            db
        )

        if violations and not update_request.override:
            # 4) 위반 시 롤백
            restore_assignments_backup(original_assignments, db)
            return {
                "ok": False,
                "violations": violations,
                "message": "변경으로 인해 제약조건을 위반합니다"
            }

        # 5) 성공 시 점수 재계산
        new_scores = recalculate_affected_employee_scores(
            schedule_id,
            [update_request.from_employee_id, update_request.to_employee_id],
            db
        )

        # 6) 전체 스케줄 점수 업데이트
        schedule = db.query(Schedule).filter(
            Schedule.id == schedule_id
        ).first()

        previous_score = schedule.total_score
        schedule.total_score = calculate_total_schedule_score(schedule_id, db)
        delta = schedule.total_score - previous_score

        db.commit()

        return {
            "ok": True,
            "new_score": schedule.total_score,
            "delta": delta,
            "violations": [],
            "employee_scores": new_scores
        }

    except Exception as e:
        db.rollback()
        restore_assignments_backup(original_assignments, db)
        raise HTTPException(status_code=500, detail=str(e))

def validate_constraints_for_dates(
    schedule_id: int,
    dates: List[str],
    db: Session
) -> List[Dict]:
    """지정된 날짜 범위의 제약조건만 검증"""
    violations = []

    for date in dates:
        # 최소 인력 검증
        day_assignments = get_assignments_for_date(schedule_id, date, db)
        shift_counts = count_by_shift(day_assignments)

        for shift, count in shift_counts.items():
            min_required = get_min_staff_for_shift(shift)
            if count < min_required:
                violations.append({
                    "type": "minimum_staff",
                    "detail": f"{date} {shift}: {count} < {min_required}"
                })

    return violations
```

### **프론트엔드 구현 (React Beautiful DnD)**

```typescript
// src/hooks/useDragAndDrop.ts
export const useDragAndDrop = (scheduleId: number) => {
  const [assignments, setAssignments] = useState({});
  const [isDragging, setIsDragging] = useState(false);

  const onDragEnd = async (result: DropResult) => {
    const { source, destination, draggableId } = result;

    if (!destination) return;

    setIsDragging(true);

    // 1) Optimistic Update (즉시 UI 반영)
    const previousState = { ...assignments };
    const optimisticState = applyLocalMove(
      previousState,
      source,
      destination,
      draggableId
    );
    setAssignments(optimisticState);

    try {
      // 2) 서버 검증 요청
      const response = await fetch(
        `/api/schedules/${scheduleId}/assignments`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            date: destination.date,
            shift: destination.shift,
            from_employee_id: draggableId,
            to_employee_id: destination.employeeId
          })
        }
      );

      const result = await response.json();

      if (result.ok) {
        // 3) 성공 시 점수 업데이트 및 피드백
        updateScores(result.employee_scores);
        showScoreDelta(result.delta);
        toast.success(`점수 변화: ${result.delta > 0 ? '+' : ''}${result.delta}`);
      } else {
        // 4) 실패 시 롤백
        setAssignments(previousState);
        showViolationModal(result.violations);
        toast.error(result.message);
      }

    } catch (error) {
      // 5) 네트워크 오류 시 롤백
      setAssignments(previousState);
      toast.error('서버 연결 실패: ' + error.message);
    } finally {
      setIsDragging(false);
    }
  };

  return {
    assignments,
    onDragEnd,
    isDragging
  };
};

// src/components/DraggableCalendar.tsx
const DraggableCalendar: React.FC = () => {
  const { assignments, onDragEnd, isDragging } = useDragAndDrop(scheduleId);

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className={`calendar-grid ${isDragging ? 'dragging' : ''}`}>
        {dates.map(date => (
          <CalendarDay key={date} date={date}>
            {['day', 'evening', 'night'].map(shift => (
              <Droppable
                key={`${date}-${shift}`}
                droppableId={`${date}-${shift}`}
              >
                {(provided) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className="shift-slot"
                  >
                    {assignments[date]?.[shift]?.map((employee, index) => (
                      <Draggable
                        key={employee.id}
                        draggableId={employee.id}
                        index={index}
                      >
                        {(provided) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            className="employee-card"
                          >
                            {employee.name}
                            <span className="score">{employee.score}</span>
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            ))}
          </CalendarDay>
        ))}
      </div>
    </DragDropContext>
  );
};
```

---

## 4. 🚨 긴급 오버라이드 & AI 대체 추천

### **API 설계**

```http
GET /api/schedules/{id}/recommend_replacements?date=2025-10-16&shift=night&exclude=e123
```

```json
[
  {
    "employee_id": "e456",
    "name": "박간호사",
    "score": 85,
    "reason_breakdown": {
      "week_hours": 36,
      "night_count": 3,
      "preference_match": true,
      "senior_bonus": 10
    },
    "risks": ["연속 야간 4일차"]
  }
]
```

### **백엔드 구현**

```python
def recommend_replacements(
    date: str,
    shift: str,
    exclude_ids: List[str],
    nurses: List[Employee],
    weights: Dict[str, int]
) -> List[Dict]:
    """AI 기반 대체자 추천"""

    candidates = [
        n for n in nurses
        if n.id not in exclude_ids
        and n.is_active
        and n.is_available(date, shift)
        and employment_ok(n, shift)
    ]

    scored_candidates = []

    for nurse in candidates:
        score = 0
        risks = []

        # 주간 근무시간 패널티
        week_hours = get_week_hours(nurse, date)
        if week_hours > 40:
            score -= (week_hours - 40) * weights['over_hours']
            risks.append(f"주간 {week_hours}시간 근무")

        # 야간 근무 부담 패널티
        night_count = get_night_count_in_month(nurse, date)
        score -= night_count * weights['night_load']

        # 선호도 반영
        if nurse.prefers_shift(shift):
            score += weights['preference_bonus']
        elif nurse.avoids_shift(shift):
            score -= weights['preference_penalty']
            risks.append("기피 근무")

        # 역할 보너스
        if 'senior' in nurse.roles:
            score += weights['senior_bonus']

        # 연속 야간 체크
        consecutive_nights = get_consecutive_nights(nurse, date)
        if consecutive_nights >= 3:
            risks.append(f"연속 야간 {consecutive_nights + 1}일차")
            score -= consecutive_nights * 10

        scored_candidates.append({
            "employee_id": nurse.id,
            "name": nurse.name,
            "score": score,
            "reason_breakdown": {
                "week_hours": week_hours,
                "night_count": night_count,
                "preference_match": nurse.prefers_shift(shift),
                "senior_bonus": weights['senior_bonus'] if 'senior' in nurse.roles else 0
            },
            "risks": risks
        })

    # 점수순 정렬하여 상위 5명 반환
    return sorted(scored_candidates, key=lambda x: x['score'], reverse=True)[:5]
```

### **프론트엔드 구현**

```typescript
// src/components/EmergencyOverride.tsx
const EmergencyOverride: React.FC<{
  date: string;
  shift: string;
  onAssign: (employeeId: string) => void;
}> = ({ date, shift, onAssign }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchRecommendations();
  }, [date, shift]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/schedules/${scheduleId}/recommend_replacements?date=${date}&shift=${shift}`
      );
      const data = await response.json();
      setRecommendations(data);
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOneClickAssign = async (employeeId: string) => {
    try {
      await onAssign(employeeId);
      toast.success('긴급 배정이 완료되었습니다');
    } catch (error) {
      toast.error('배정 실패: ' + error.message);
    }
  };

  return (
    <div className="emergency-override">
      <div className="header">
        <h3>🚨 긴급 대체자 추천</h3>
        <p>{date} {shift} 교대</p>
      </div>

      {loading ? (
        <div className="loading">추천자 분석 중...</div>
      ) : (
        <div className="recommendations">
          {recommendations.map((rec, index) => (
            <div key={rec.employee_id} className="recommendation-card">
              <div className="rank">#{index + 1}</div>

              <div className="employee-info">
                <h4>{rec.name}</h4>
                <div className="score">점수: {rec.score}</div>
              </div>

              <div className="details">
                <div>주간 근무: {rec.reason_breakdown.week_hours}시간</div>
                <div>월 야간: {rec.reason_breakdown.night_count}회</div>
                <div>선호도: {rec.reason_breakdown.preference_match ? '✅' : '❌'}</div>
              </div>

              {rec.risks.length > 0 && (
                <div className="risks">
                  ⚠️ {rec.risks.join(', ')}
                </div>
              )}

              <button
                className="btn-assign"
                onClick={() => handleOneClickAssign(rec.employee_id)}
              >
                1클릭 배정
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

---

## 5. 🔔 개인화 알림 시스템

### **목표**
개인별 근무 변경 시에만 해당 사용자에게 알림 전송

### **백엔드 구현 (Firebase FCM)**

```python
# app/services/notification_service.py
import firebase_admin
from firebase_admin import messaging

class NotificationService:
    def __init__(self):
        # Firebase 초기화
        self.app = firebase_admin.initialize_app()

    def send_assignment_change_notification(
        self,
        user_id: str,
        schedule_change: Dict
    ):
        """개인별 근무 변경 알림"""

        # 사용자의 FCM 토큰 조회
        user_tokens = self.get_user_fcm_tokens(user_id)

        if not user_tokens:
            return

        message = messaging.MulticastMessage(
            tokens=user_tokens,
            notification=messaging.Notification(
                title="📅 근무 일정 변경",
                body=f"{schedule_change['date']} {schedule_change['shift']} 근무가 변경되었습니다"
            ),
            data={
                "type": "assignment_changed",
                "schedule_id": str(schedule_change['schedule_id']),
                "date": schedule_change['date'],
                "shift": schedule_change['shift'],
                "click_action": f"/schedule/{schedule_change['schedule_id']}"
            }
        )

        try:
            response = messaging.send_multicast(message)
            print(f"Successfully sent message: {response.success_count}")
        except Exception as e:
            print(f"Error sending message: {e}")

    def send_emergency_request_notification(
        self,
        user_id: str,
        emergency_request: Dict
    ):
        """긴급 근무 요청 알림"""
        user_tokens = self.get_user_fcm_tokens(user_id)

        message = messaging.MulticastMessage(
            tokens=user_tokens,
            notification=messaging.Notification(
                title="🚨 긴급 근무 요청",
                body=f"{emergency_request['date']} {emergency_request['shift']} 긴급 근무 요청이 있습니다"
            ),
            data={
                "type": "emergency_request",
                "priority": "high"
            }
        )

        messaging.send_multicast(message)

# 이벤트 후크 등록
@router.patch("/{schedule_id}/assignments")
async def update_assignment(...):
    # ... 기존 로직

    if result.ok:
        # 변경된 직원들에게만 알림
        affected_employees = [
            update_request.from_employee_id,
            update_request.to_employee_id
        ]

        for emp_id in affected_employees:
            notification_service.send_assignment_change_notification(
                emp_id,
                {
                    "schedule_id": schedule_id,
                    "date": update_request.date,
                    "shift": update_request.shift
                }
            )
```

### **프론트엔드 구현 (PWA + Service Worker)**

```javascript
// public/sw.js (Service Worker)
self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.notification.body,
      icon: '/icon-192x192.png',
      badge: '/badge-72x72.png',
      tag: data.data.type,
      data: data.data,
      actions: [
        {
          action: 'view',
          title: '일정 확인',
          icon: '/action-view.png'
        },
        {
          action: 'dismiss',
          title: '닫기'
        }
      ]
    };

    event.waitUntil(
      self.registration.showNotification(data.notification.title, options)
    );
  }
});

self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'view') {
    const scheduleId = event.notification.data.schedule_id;
    event.waitUntil(
      clients.openWindow(`/schedule/${scheduleId}`)
    );
  }
});

// src/services/pushNotificationService.ts
export class PushNotificationService {
  private vapidKey = process.env.REACT_APP_VAPID_KEY;

  async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return false;
    }

    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  async subscribeToPush(): Promise<string | null> {
    if (!('serviceWorker' in navigator)) {
      return null;
    }

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: this.vapidKey
    });

    // FCM 토큰을 서버에 등록
    const token = JSON.stringify(subscription);
    await this.registerTokenOnServer(token);

    return token;
  }

  private async registerTokenOnServer(token: string): Promise<void> {
    await fetch('/api/users/fcm-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token })
    });
  }
}
```

---

## 6. 📄 PDF/카톡 공유 Export

### **백엔드 구현 (WeasyPrint)**

```python
# app/services/export_service.py
from weasyprint import HTML, CSS
from io import BytesIO
import base64

class ExportService:
    def __init__(self):
        self.templates = {
            'ward': 'templates/ward_schedule.html',
            'personal': 'templates/personal_schedule.html'
        }

    def export_schedule_pdf(
        self,
        schedule_id: int,
        export_type: str = 'ward',
        date_range: str = '2025-10'
    ) -> BytesIO:
        """스케줄을 PDF로 내보내기"""

        # 1) 스케줄 데이터 조회
        schedule_data = self.get_schedule_data(schedule_id, export_type, date_range)

        # 2) HTML 템플릿 렌더링
        html_content = self.render_template(
            self.templates[export_type],
            schedule_data
        )

        # 3) PDF 생성
        html = HTML(string=html_content)
        css = CSS(string=self.get_pdf_styles())

        pdf_buffer = BytesIO()
        html.write_pdf(pdf_buffer, stylesheets=[css])
        pdf_buffer.seek(0)

        return pdf_buffer

    def create_share_link(
        self,
        schedule_id: int,
        user_id: int,
        expires_hours: int = 24
    ) -> str:
        """공유 링크 생성"""

        # JWT 기반 임시 토큰 생성
        token_data = {
            "schedule_id": schedule_id,
            "user_id": user_id,
            "expires": datetime.utcnow() + timedelta(hours=expires_hours)
        }

        share_token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        return f"https://yourdomain.com/shared/{share_token}"

# app/api/export.py
@router.get("/{schedule_id}/export")
async def export_schedule(
    schedule_id: int,
    format: str = 'pdf',
    type: str = 'ward',
    date: str = None,
    current_user: User = Depends(get_current_user)
):
    """스케줄 내보내기"""

    export_service = ExportService()

    if format == 'pdf':
        pdf_buffer = export_service.export_schedule_pdf(
            schedule_id,
            export_type=type,
            date_range=date
        )

        return StreamingResponse(
            io.BytesIO(pdf_buffer.getvalue()),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=schedule_{schedule_id}.pdf"
            }
        )

    elif format == 'share_link':
        share_link = export_service.create_share_link(
            schedule_id,
            current_user.id
        )

        return {"share_link": share_link}

# templates/ward_schedule.html
"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ ward_name }} 근무표 - {{ month }}</title>
    <style>
        body { font-family: 'Noto Sans KR', sans-serif; }
        .schedule-table { width: 100%; border-collapse: collapse; }
        .schedule-table th, .schedule-table td {
            border: 1px solid #ccc;
            padding: 8px;
            text-align: center;
        }
        .day-shift { background-color: #e3f2fd; }
        .evening-shift { background-color: #fff3e0; }
        .night-shift { background-color: #f3e5f5; }
        .off-day { background-color: #f5f5f5; }
    </style>
</head>
<body>
    <h1>{{ ward_name }} 근무표</h1>
    <h2>{{ month }}</h2>

    <table class="schedule-table">
        <thead>
            <tr>
                <th>간호사</th>
                {% for day in days %}
                <th>{{ day }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for nurse in nurses %}
            <tr>
                <td><strong>{{ nurse.name }}</strong></td>
                {% for assignment in nurse.assignments %}
                <td class="{{ assignment.shift }}-shift">
                    {{ assignment.shift_display }}
                </td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="legend">
        <h3>범례</h3>
        <div><span class="day-shift">D</span> 주간 (08:00-16:00)</div>
        <div><span class="evening-shift">E</span> 저녁 (16:00-00:00)</div>
        <div><span class="night-shift">N</span> 야간 (00:00-08:00)</div>
        <div><span class="off-day">O</span> 휴무</div>
    </div>
</body>
</html>
"""
```

### **프론트엔드 구현 (카카오톡 공유)**

```typescript
// src/services/shareService.ts
export class ShareService {
  private kakaoApiKey = process.env.REACT_APP_KAKAO_API_KEY;

  async shareToKakao(scheduleId: number, type: 'ward' | 'personal') {
    if (!window.Kakao) {
      await this.loadKakaoSDK();
    }

    if (!window.Kakao.isInitialized()) {
      window.Kakao.init(this.kakaoApiKey);
    }

    // 1) 공유용 링크 생성
    const shareLink = await this.createShareLink(scheduleId, type);

    // 2) 카카오링크 전송
    window.Kakao.Share.sendDefault({
      objectType: 'feed',
      content: {
        title: `${type === 'ward' ? '병동' : '개인'} 근무표`,
        description: '간호사 근무 일정을 확인하세요',
        imageUrl: await this.generatePreviewImage(scheduleId, type),
        link: {
          mobileWebUrl: shareLink,
          webUrl: shareLink
        }
      },
      buttons: [
        {
          title: '근무표 보기',
          link: {
            mobileWebUrl: shareLink,
            webUrl: shareLink
          }
        }
      ]
    });
  }

  private async loadKakaoSDK(): Promise<void> {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://developers.kakao.com/sdk/js/kakao.js';
      script.onload = () => resolve();
      document.head.appendChild(script);
    });
  }

  private async createShareLink(scheduleId: number, type: string): Promise<string> {
    const response = await fetch(`/api/schedules/${scheduleId}/export?format=share_link&type=${type}`);
    const data = await response.json();
    return data.share_link;
  }

  async exportToPDF(scheduleId: number, type: 'ward' | 'personal') {
    const link = document.createElement('a');
    link.href = `/api/schedules/${scheduleId}/export?format=pdf&type=${type}`;
    link.download = `schedule_${scheduleId}.pdf`;
    link.click();
  }
}

// src/components/ExportMenu.tsx
const ExportMenu: React.FC<{ scheduleId: number }> = ({ scheduleId }) => {
  const shareService = new ShareService();

  return (
    <div className="export-menu">
      <button onClick={() => shareService.exportToPDF(scheduleId, 'ward')}>
        📄 PDF 다운로드
      </button>

      <button onClick={() => shareService.shareToKakao(scheduleId, 'ward')}>
        💬 카카오톡 공유
      </button>

      <button onClick={() => shareService.shareToKakao(scheduleId, 'personal')}>
        👤 개인 일정 공유
      </button>
    </div>
  );
};
```

---

## 7. 🔄 근무 교환 요청 워크플로우

### **API 설계**

```http
POST /api/swap-requests
PATCH /api/swap-requests/{id}/approve
GET /api/swap-requests/my
```

### **백엔드 구현**

```python
# app/models/swap_models.py
class SwapRequest(Base):
    __tablename__ = "swap_requests"

    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))

    from_employee_id = Column(Integer, ForeignKey("employees.id"))
    to_employee_id = Column(Integer, ForeignKey("employees.id"))

    date_from = Column(Date)
    shift_from = Column(String)
    date_to = Column(Date)
    shift_to = Column(String)

    reason = Column(Text)
    status = Column(String, default="pending")  # pending -> accepted -> approved -> applied

    requested_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime)
    approved_at = Column(DateTime)

    from_employee = relationship("Employee", foreign_keys=[from_employee_id])
    to_employee = relationship("Employee", foreign_keys=[to_employee_id])

# app/api/swap_requests.py
@router.post("/swap-requests")
async def create_swap_request(
    request: SwapRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """근무 교환 요청 생성"""

    # 1) 유효성 검증
    if not validate_swap_possibility(request, db):
        raise HTTPException(400, "교환이 불가능한 근무입니다")

    # 2) 요청 생성
    swap_request = SwapRequest(
        schedule_id=request.schedule_id,
        from_employee_id=current_user.id,
        to_employee_id=request.to_employee_id,
        date_from=request.date_from,
        shift_from=request.shift_from,
        date_to=request.date_to,
        shift_to=request.shift_to,
        reason=request.reason
    )

    db.add(swap_request)
    db.commit()

    # 3) 대상자에게 알림
    notification_service.send_swap_request_notification(
        request.to_employee_id,
        swap_request.id
    )

    return {"id": swap_request.id, "status": "pending"}

@router.patch("/swap-requests/{request_id}/approve")
async def approve_swap_request(
    request_id: int,
    action: str,  # approve, reject
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """교환 요청 승인/거절"""

    swap_request = db.query(SwapRequest).filter(
        SwapRequest.id == request_id
    ).first()

    if not swap_request:
        raise HTTPException(404, "요청을 찾을 수 없습니다")

    # 권한 확인
    if current_user.id == swap_request.to_employee_id:
        # 대상자 응답
        if action == "approve":
            swap_request.status = "accepted_by_target"
            # 관리자에게 최종 승인 요청 알림
            notification_service.send_admin_approval_request(swap_request.id)
        else:
            swap_request.status = "rejected_by_target"

    elif current_user.role == "admin":
        # 관리자 최종 승인
        if action == "approve" and swap_request.status == "accepted_by_target":
            # 교환 실행
            execute_swap(swap_request, db)
            swap_request.status = "approved"
            swap_request.approved_at = datetime.utcnow()
        else:
            swap_request.status = "rejected_by_admin"

    else:
        raise HTTPException(403, "권한이 없습니다")

    swap_request.responded_at = datetime.utcnow()
    db.commit()

    return {"status": swap_request.status}

def execute_swap(swap_request: SwapRequest, db: Session):
    """실제 근무 교환 실행"""

    # 1) 기존 배정 조회
    assignment_from = db.query(Assignment).filter(
        Assignment.schedule_id == swap_request.schedule_id,
        Assignment.employee_id == swap_request.from_employee_id,
        Assignment.date == swap_request.date_from,
        Assignment.shift == swap_request.shift_from
    ).first()

    assignment_to = db.query(Assignment).filter(
        Assignment.schedule_id == swap_request.schedule_id,
        Assignment.employee_id == swap_request.to_employee_id,
        Assignment.date == swap_request.date_to,
        Assignment.shift == swap_request.shift_to
    ).first()

    # 2) 교환 실행
    assignment_from.employee_id = swap_request.to_employee_id
    assignment_to.employee_id = swap_request.from_employee_id

    # 3) 관련자에게 알림
    notification_service.send_swap_completed_notification([
        swap_request.from_employee_id,
        swap_request.to_employee_id
    ])
```

### **프론트엔드 구현**

```typescript
// src/components/SwapRequestDialog.tsx
const SwapRequestDialog: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  currentAssignment: Assignment;
}> = ({ isOpen, onClose, currentAssignment }) => {
  const [targetEmployee, setTargetEmployee] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [targetShift, setTargetShift] = useState('');
  const [reason, setReason] = useState('');

  const handleSubmit = async () => {
    try {
      const response = await fetch('/api/swap-requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schedule_id: currentAssignment.schedule_id,
          to_employee_id: targetEmployee,
          date_from: currentAssignment.date,
          shift_from: currentAssignment.shift,
          date_to: targetDate,
          shift_to: targetShift,
          reason
        })
      });

      if (response.ok) {
        toast.success('교환 요청이 전송되었습니다');
        onClose();
      }

    } catch (error) {
      toast.error('요청 전송 실패');
    }
  };

  return (
    <Dialog isOpen={isOpen} onClose={onClose}>
      <h2>🔄 근무 교환 요청</h2>

      <div className="current-assignment">
        <h3>내 근무:</h3>
        <p>{currentAssignment.date} {currentAssignment.shift}</p>
      </div>

      <div className="target-assignment">
        <h3>교환 희망:</h3>
        <select
          value={targetEmployee}
          onChange={(e) => setTargetEmployee(e.target.value)}
        >
          <option value="">간호사 선택</option>
          {availableNurses.map(nurse => (
            <option key={nurse.id} value={nurse.id}>
              {nurse.name}
            </option>
          ))}
        </select>

        <input
          type="date"
          value={targetDate}
          onChange={(e) => setTargetDate(e.target.value)}
        />

        <select
          value={targetShift}
          onChange={(e) => setTargetShift(e.target.value)}
        >
          <option value="day">주간</option>
          <option value="evening">저녁</option>
          <option value="night">야간</option>
        </select>
      </div>

      <textarea
        placeholder="교환 사유를 입력하세요"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
      />

      <div className="actions">
        <button onClick={onClose}>취소</button>
        <button onClick={handleSubmit}>요청 전송</button>
      </div>
    </Dialog>
  );
};
```

---

## 8. 🧪 테스트 전략

### **Unit Tests (Jest + pytest)**

```python
# tests/test_feasibility.py
def test_validate_staffing_insufficient_total():
    """TC1: 간호사 총원 부족"""
    nurses = [
        {"id": "e1", "is_active": True, "availability": {"2025-10-01": ["day"]}},
        {"id": "e2", "is_active": True, "availability": {"2025-10-01": ["evening"]}}
    ]

    result = validate_staffing_requirements(
        ward_id=1,
        nurses=nurses,
        period_start=date(2025, 10, 1),
        period_end=date(2025, 10, 1),
        shift_min_requirements={"day": 2, "evening": 2, "night": 1},
        role_requirements={}
    )

    assert result["ok"] == False
    assert result["reason"] == "insufficient_shift_staff"
    assert result["detail"]["shift"] == "evening"
    assert result["detail"]["required"] == 2
    assert result["detail"]["available"] == 1

def test_validate_staffing_insufficient_role():
    """TC2: 시니어 역할 부족"""
    nurses = [
        {"id": "e1", "roles": ["junior"], "is_active": True},
        {"id": "e2", "roles": ["junior"], "is_active": True}
    ]

    result = validate_staffing_requirements(
        ward_id=1,
        nurses=nurses,
        period_start=date(2025, 10, 1),
        period_end=date(2025, 10, 1),
        shift_min_requirements={"day": 1},
        role_requirements={"senior": 1}
    )

    assert result["ok"] == False
    assert result["reason"] == "insufficient_role"

# tests/test_assignment_update.py
def test_assign_patch_prevents_violation():
    """TC3: 배정 변경 시 제약조건 위반 방지"""
    # 현재 배정으로 최소 인원 만족 상태
    # 특정 간호사를 다른 교대로 이동 시 최소 인원 위반
    # 서버에서 변경을 거부해야 함
    pass
```

### **Integration Tests**

```python
# tests/test_integration.py
def test_generate_schedule_precheck_blocked_on_shortage():
    """생성 전 사전검증으로 인한 차단 테스트"""
    client = TestClient(app)

    # 인력 부족 상황 설정
    response = client.post("/api/schedules/generate", json={
        "ward_id": 1,
        "nurses": [{"id": "e1", "is_active": True}],  # 인력 부족
        "shift_min_requirements": {"day": 3, "evening": 2, "night": 1}
    })

    assert response.status_code == 400
    assert "insufficient_shift_staff" in response.json()["detail"]["reason"]

def test_assign_drag_drop_happy_path():
    """드래그앤드롭 성공 케이스"""
    client = TestClient(app)

    response = client.patch("/api/schedules/1/assignments", json={
        "date": "2025-10-16",
        "shift": "night",
        "from_employee_id": "e123",
        "to_employee_id": "e456"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] == True
    assert "new_score" in data
    assert "employee_scores" in data
```

### **E2E Tests (Cypress)**

```javascript
// cypress/e2e/day-detail-modal.cy.js
describe('Day Detail Modal', () => {
  it('TC4: 날짜 클릭 시 모달 열기 및 탭 전환', () => {
    cy.visit('/schedule/1');

    // 특정 날짜 클릭
    cy.get('[data-date="2025-10-16"]').click();

    // 모달 열림 확인
    cy.get('[data-testid="day-detail-modal"]').should('be.visible');

    // Day 탭 활성화 확인
    cy.get('[data-testid="tab-day"]').should('have.class', 'active');

    // 배정자 리스트 로딩 확인
    cy.get('[data-testid="assignment-list"]').should('exist');
    cy.get('[data-testid="employee-card"]').should('have.length.greaterThan', 0);

    // Evening 탭 클릭
    cy.get('[data-testid="tab-evening"]').click();
    cy.get('[data-testid="tab-evening"]').should('have.class', 'active');

    // 점수 breakdown 표시 확인
    cy.get('[data-testid="employee-card"]').first().within(() => {
      cy.get('[data-testid="score"]').should('be.visible');
      cy.get('[data-testid="score"]').trigger('mouseover');
      cy.get('[data-testid="score-tooltip"]').should('be.visible');
    });
  });
});

// cypress/e2e/drag-and-drop.cy.js
describe('Drag and Drop', () => {
  it('TC6: 드래그앤드롭으로 근무 변경', () => {
    cy.visit('/schedule/1');

    // 드래그 시작
    cy.get('[data-employee-id="e123"]')
      .trigger('mousedown', { which: 1 });

    // 드롭 위치로 이동
    cy.get('[data-drop-zone="2025-10-17-evening"]')
      .trigger('mousemove')
      .trigger('mouseup');

    // Optimistic update 확인
    cy.get('[data-drop-zone="2025-10-17-evening"]')
      .should('contain', '김간호사');

    // 서버 응답 후 점수 변화 확인
    cy.get('[data-testid="score-delta"]').should('be.visible');

    // 성공 토스트 확인
    cy.get('[data-testid="toast"]').should('contain', '점수 변화');
  });

  it('TC6-2: 제약조건 위반 시 롤백', () => {
    cy.visit('/schedule/1');

    // 최소 인력 위반을 유발하는 드래그
    cy.get('[data-employee-id="e123"]')
      .trigger('mousedown', { which: 1 });

    cy.get('[data-drop-zone="2025-10-17-off"]')
      .trigger('mousemove')
      .trigger('mouseup');

    // 위반 모달 표시 확인
    cy.get('[data-testid="violation-modal"]').should('be.visible');
    cy.get('[data-testid="violation-modal"]').should('contain', '최소 인력');

    // 롤백 확인
    cy.get('[data-testid="violation-modal"] [data-testid="ok-button"]').click();
    cy.get('[data-employee-id="e123"]').should('not.exist').within(
      '[data-drop-zone="2025-10-17-off"]'
    );
  });
});

// cypress/e2e/emergency-override.cy.js
describe('Emergency Override', () => {
  it('TC7: 긴급 대체자 추천 및 1클릭 배정', () => {
    cy.visit('/schedule/1');

    // 긴급상황 모드 활성화
    cy.get('[data-testid="emergency-toggle"]').click();

    // 특정 교대 클릭
    cy.get('[data-shift="2025-10-16-night"]').click();

    // 추천자 리스트 로딩 확인
    cy.get('[data-testid="recommendations"]').should('be.visible');
    cy.get('[data-testid="recommendation-card"]').should('have.length', 5);

    // 첫 번째 추천자 확인
    cy.get('[data-testid="recommendation-card"]').first().within(() => {
      cy.get('[data-testid="rank"]').should('contain', '#1');
      cy.get('[data-testid="score"]').should('be.visible');
      cy.get('[data-testid="reason"]').should('be.visible');

      // 1클릭 배정
      cy.get('[data-testid="assign-button"]').click();
    });

    // 배정 완료 확인
    cy.get('[data-testid="toast"]').should('contain', '긴급 배정이 완료되었습니다');
    cy.get('[data-shift="2025-10-16-night"]').should('contain', '박간호사');
  });
});
```

---

## 9. 📈 성능 모니터링

### **성능 목표**

```yaml
api_performance:
  validate_staffing: "< 500ms"
  day_details: "< 800ms"
  assignment_patch: "< 2000ms"
  recommend_replacements: "< 1500ms"

ui_performance:
  modal_open: "< 200ms"
  drag_response: "< 100ms"
  optimistic_update: "< 50ms"

scalability:
  nurses_count: "최대 100명"
  concurrent_users: "최대 50명"
  monthly_schedules: "최대 12개"
```

### **모니터링 구현**

```python
# app/middleware/performance.py
import time
from fastapi import Request

@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # 성능 로깅
    logger.info(f"API: {request.url.path} - {process_time:.3f}s")

    # 임계값 초과 시 알림
    if process_time > 5.0:
        alert_service.send_performance_alert(
            endpoint=request.url.path,
            duration=process_time
        )

    return response
```

---

## 10. 🚀 배포 및 운영

### **배포 체크리스트**

```markdown
## Pre-deployment
- [ ] All unit tests pass (95%+ coverage)
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Performance tests meet SLA
- [ ] Security scan clean
- [ ] Database migrations ready
- [ ] Environment variables set
- [ ] Firebase/FCM configured
- [ ] PDF export libraries installed

## Deployment
- [ ] Backend API deployment
- [ ] Frontend static files deployment
- [ ] Database schema update
- [ ] Service worker registration
- [ ] Push notification setup

## Post-deployment
- [ ] Health check endpoints responding
- [ ] Authentication working
- [ ] PDF export functional
- [ ] Push notifications working
- [ ] Performance metrics baseline
- [ ] Error logging operational
```

### **운영 모니터링**

```python
# app/api/health.py
@router.get("/health")
async def health_check():
    """시스템 상태 체크"""
    checks = {
        "database": check_database_connection(),
        "redis": check_redis_connection(),
        "firebase": check_firebase_connection(),
        "pdf_service": check_pdf_service(),
        "storage": check_storage_access()
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@router.get("/metrics")
async def get_metrics():
    """운영 메트릭"""
    return {
        "active_schedules": get_active_schedule_count(),
        "total_nurses": get_total_nurse_count(),
        "avg_response_time": get_avg_response_time(),
        "error_rate": get_error_rate(),
        "cache_hit_ratio": get_cache_hit_ratio()
    }
```

---

## 🎯 즉시 실행 가능한 작업 지시서

### **복사 붙여넣기용 Task Commands**

```bash
# Phase 1: 안전성 확보
/task add — server: generate-schedule 엔드포인트 최상단에 validate_staffing_requirements() 추가. 부족 시 HTTP400 + 상세 메시지.
/task add — server: POST /schedules/validate 구현 (pre-check API).
/task add — frontend: Generate 버튼 누르면 먼저 /schedules/validate 호출; 실패시 모달로 부족세부(몇명/어떤 역할) 보여주고 생성 차단.

# Phase 2: 상세 분석
/task add — frontend: ScheduleCalendar 날짜 클릭 시 DayDetailModal 열고 상단 4개 탭(D/E/N/Off) 추가. 각 탭은 GET /schedules/{id}/day/{date}/details 호출.
/task add — server: GET /schedules/{id}/day/{date}/details API 구현. 교대별 배정자 + score_breakdown 반환.

# Phase 3: 실시간 편집
/task add — frontend/backend: Drag&Drop API 연동(PATCH /schedules/{id}/assignments), 응답에서 new_score/delta/violations 반환. UI는 optimistic update 후 응답으로 확정/롤백.
/task add — frontend: react-beautiful-dnd 설치 및 DraggableCalendar 컴포넌트 구현.

# Phase 4: 운영 지원
/task add — server: recommend_replacements(date,shift) 함수 및 GET /schedules/{id}/recommend_replacements API 구현.
/task add — frontend: Emergency Override toggle + 추천자 리스트 UI. 1-클릭으로 assign (admin 승인 흐름 포함).
/task add — server: implement per-user push notifications for "assignment_changed" events; only affected users receive push.

# Phase 5: 편의 기능
/task add — server/frontend: export endpoint GET /schedules/{id}/export?format=pdf (server-side) + client-side html2canvas fallback.
/task add — server: swap-request CRUD API 및 notification hooks.
/task add — frontend: 카카오톡 공유 기능 (Kakao SDK 연동).

# 테스팅
/task add — qa: add unit/integration tests TC1~TC7 and Cypress E2E for Drag&Drop and Emergency flows.
```

---

이 가이드를 통해 개발팀은 **단계적으로 안전하고 효율적인 간호사 근무표 시스템**을 구축할 수 있습니다. 각 Phase는 독립적으로 배포 가능하며, 운영 리스크를 최소화하면서 점진적으로 기능을 확장할 수 있도록 설계되었습니다.