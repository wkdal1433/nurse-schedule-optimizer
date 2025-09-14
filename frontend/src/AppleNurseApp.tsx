import React, { useState } from 'react';
import { AppleDesign } from './styles/AppleDesignSystem';
import AppleButton from './components/ui/AppleButton';
import AppleCard from './components/ui/AppleCard';
import AppleInput from './components/ui/AppleInput';

interface Nurse {
  id: number;
  name: string;
  role: 'head_nurse' | 'staff_nurse' | 'new_nurse';
  employment_type: 'full_time' | 'part_time';
  experience_level: number;
}

interface Ward {
  id: number;
  name: string;
  min_nurses_per_shift: number;
  shift_types: string[];
  icon: string;
  color: string;
}

interface ScheduleData {
  date: string;
  nurses: {
    [nurseId: number]: {
      shift: 'DAY' | 'EVENING' | 'NIGHT' | 'OFF';
      nurse: Nurse;
    };
  };
}

const AppleNurseApp: React.FC = () => {
  const [currentView, setCurrentView] = useState<'setup' | 'calendar' | 'settings'>('setup');
  const [nurses, setNurses] = useState<Nurse[]>([]);
  const [selectedWard, setSelectedWard] = useState<Ward | null>(null);
  const [scheduleData, setScheduleData] = useState<ScheduleData[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [isLoading, setIsLoading] = useState(false);

  const wards: Ward[] = [
    {
      id: 1,
      name: '내과 병동',
      min_nurses_per_shift: 3,
      shift_types: ['DAY', 'EVENING', 'NIGHT'],
      icon: '🏥',
      color: AppleDesign.colors.systemBlue
    },
    {
      id: 2,
      name: '외과 병동',
      min_nurses_per_shift: 4,
      shift_types: ['DAY', 'EVENING', 'NIGHT'],
      icon: '⚕️',
      color: AppleDesign.colors.systemGreen
    },
    {
      id: 3,
      name: '중환자실',
      min_nurses_per_shift: 2,
      shift_types: ['DAY', 'NIGHT'],
      icon: '🚨',
      color: AppleDesign.colors.systemRed
    },
    {
      id: 4,
      name: '응급실',
      min_nurses_per_shift: 5,
      shift_types: ['DAY', 'EVENING', 'NIGHT'],
      icon: '🚑',
      color: AppleDesign.colors.systemOrange
    }
  ];

  const addNurse = (name: string, role: Nurse['role'], employment_type: Nurse['employment_type'], experience: number) => {
    const newNurse: Nurse = {
      id: Date.now(),
      name,
      role,
      employment_type,
      experience_level: experience
    };
    setNurses([...nurses, newNurse]);
  };

  const generateSchedule = async () => {
    if (!selectedWard || nurses.length === 0) {
      alert('병동과 간호사를 먼저 설정해주세요.');
      return;
    }

    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 2000)); // 로딩 시뮬레이션

      const schedule: ScheduleData[] = [];
      const startDate = new Date(selectedDate);

      for (let i = 0; i < 30; i++) {
        const currentDate = new Date(startDate);
        currentDate.setDate(startDate.getDate() + i);

        const daySchedule: ScheduleData = {
          date: currentDate.toISOString().split('T')[0],
          nurses: {}
        };

        nurses.forEach((nurse, index) => {
          const shifts = ['DAY', 'EVENING', 'NIGHT', 'OFF'] as const;
          const shift = shifts[(index + i) % 4];
          daySchedule.nurses[nurse.id] = { shift, nurse };
        });

        schedule.push(daySchedule);
      }

      setScheduleData(schedule);
      setCurrentView('calendar');
    } catch (error) {
      console.error('근무표 생성 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={appStyles}>
      <div style={containerStyles}>
        {currentView === 'setup' && <SetupView />}
        {currentView === 'calendar' && <CalendarView />}
        {currentView === 'settings' && <SettingsView />}
      </div>
    </div>
  );

  function SetupView() {
    return (
      <div style={screenStyles}>
        {/* 헤더 */}
        <div style={headerStyles}>
          <div style={titleContainerStyles}>
            <h1 style={mainTitleStyles}>🏥 간호사 근무표</h1>
            <p style={subtitleStyles}>스마트한 근무 스케줄링</p>
          </div>
        </div>

        {/* 병동 선택 */}
        <AppleCard padding="large" elevated>
          <h2 style={sectionTitleStyles}>병동 선택</h2>
          <div style={wardGridStyles}>
            {wards.map(ward => (
              <WardCard
                key={ward.id}
                ward={ward}
                selected={selectedWard?.id === ward.id}
                onSelect={() => setSelectedWard(ward)}
              />
            ))}
          </div>
        </AppleCard>

        {/* 간호사 등록 */}
        <AppleCard padding="large" elevated>
          <div style={nurseHeaderStyles}>
            <h2 style={sectionTitleStyles}>간호사 등록</h2>
            <div style={nurseBadgeStyles}>
              {nurses.length}명
            </div>
          </div>

          <NurseRegistrationForm onAdd={addNurse} />

          {nurses.length > 0 && (
            <div style={nurseListStyles}>
              {nurses.map(nurse => (
                <NurseItem
                  key={nurse.id}
                  nurse={nurse}
                  onDelete={() => setNurses(nurses.filter(n => n.id !== nurse.id))}
                />
              ))}
            </div>
          )}
        </AppleCard>

        {/* 생성 버튼 */}
        <div style={buttonContainerStyles}>
          <AppleButton
            onClick={generateSchedule}
            disabled={!selectedWard || nurses.length === 0}
            loading={isLoading}
            size="large"
            fullWidth
            icon={<span>📅</span>}
          >
            {isLoading ? '근무표 생성 중...' : '근무표 생성'}
          </AppleButton>
        </div>
      </div>
    );
  }

  function WardCard({ ward, selected, onSelect }: { ward: Ward; selected: boolean; onSelect: () => void }) {
    return (
      <AppleCard
        interactive
        selected={selected}
        onClick={onSelect}
        padding="medium"
      >
        <div style={wardCardContentStyles}>
          <div style={{...wardIconStyles, backgroundColor: `${ward.color}15`}}>
            <span style={{fontSize: '24px'}}>{ward.icon}</span>
          </div>
          <div style={wardInfoStyles}>
            <h3 style={wardNameStyles}>{ward.name}</h3>
            <p style={wardDetailsStyles}>
              최소 {ward.min_nurses_per_shift}명/교대
            </p>
          </div>
        </div>
      </AppleCard>
    );
  }

  function NurseRegistrationForm({ onAdd }: { onAdd: (name: string, role: Nurse['role'], employment: Nurse['employment_type'], experience: number) => void }) {
    const [showForm, setShowForm] = useState(false);
    const [name, setName] = useState('');
    const [role, setRole] = useState<Nurse['role']>('staff_nurse');
    const [employment, setEmployment] = useState<Nurse['employment_type']>('full_time');
    const [experience, setExperience] = useState(1);

    const handleSubmit = () => {
      if (!name.trim()) return;
      onAdd(name, role, employment, experience);
      setName('');
      setRole('staff_nurse');
      setEmployment('full_time');
      setExperience(1);
      setShowForm(false);
    };

    if (!showForm) {
      return (
        <AppleButton
          variant="secondary"
          onClick={() => setShowForm(true)}
          icon={<span>+</span>}
        >
          간호사 추가
        </AppleButton>
      );
    }

    return (
      <div style={formContainerStyles}>
        <AppleInput
          label="간호사 이름"
          placeholder="예: 김간호사"
          value={name}
          onChange={setName}
          icon={<span>👤</span>}
        />

        <div style={formRowStyles}>
          <div style={{flex: 1}}>
            <label style={labelStyles}>역할</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as Nurse['role'])}
              style={selectStyles}
            >
              <option value="head_nurse">수간호사</option>
              <option value="staff_nurse">간호사</option>
              <option value="new_nurse">신입간호사</option>
            </select>
          </div>

          <div style={{flex: 1}}>
            <label style={labelStyles}>고용형태</label>
            <select
              value={employment}
              onChange={(e) => setEmployment(e.target.value as Nurse['employment_type'])}
              style={selectStyles}
            >
              <option value="full_time">정규직</option>
              <option value="part_time">시간제</option>
            </select>
          </div>
        </div>

        <div>
          <label style={labelStyles}>
            경력: {experience}년차
          </label>
          <input
            type="range"
            min="0"
            max="30"
            value={experience}
            onChange={(e) => setExperience(parseInt(e.target.value))}
            style={sliderStyles}
          />
        </div>

        <div style={formActionsStyles}>
          <AppleButton onClick={handleSubmit} size="medium">
            추가
          </AppleButton>
          <AppleButton variant="secondary" onClick={() => setShowForm(false)} size="medium">
            취소
          </AppleButton>
        </div>
      </div>
    );
  }

  function NurseItem({ nurse, onDelete }: { nurse: Nurse; onDelete: () => void }) {
    const getRoleText = (role: string) => {
      const roleMap = {
        head_nurse: '수간호사',
        staff_nurse: '간호사',
        new_nurse: '신입간호사'
      };
      return roleMap[role as keyof typeof roleMap] || role;
    };

    const getEmploymentText = (type: string) => {
      return type === 'full_time' ? '정규직' : '시간제';
    };

    return (
      <div style={nurseItemStyles}>
        <div style={nurseAvatarStyles}>
          <span style={nurseInitialStyles}>{nurse.name.charAt(0)}</span>
        </div>
        <div style={nurseContentStyles}>
          <h4 style={nurseNameStyles}>{nurse.name}</h4>
          <p style={nurseDetailsTextStyles}>
            {getRoleText(nurse.role)} • {getEmploymentText(nurse.employment_type)} • {nurse.experience_level}년차
          </p>
        </div>
        <button style={deleteButtonStyles} onClick={onDelete}>
          ✕
        </button>
      </div>
    );
  }

  function CalendarView() {
    const days = getDaysInMonth(selectedDate);
    const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];

    return (
      <div style={screenStyles}>
        {/* 헤더 */}
        <div style={calendarHeaderStyles}>
          <AppleButton
            variant="secondary"
            size="small"
            onClick={() => setCurrentView('setup')}
            icon={<span>←</span>}
          >
            설정
          </AppleButton>
          <h1 style={calendarTitleStyles}>
            {selectedDate.getFullYear()}년 {monthNames[selectedDate.getMonth()]}
          </h1>
          <AppleButton
            variant="secondary"
            size="small"
            onClick={() => setCurrentView('settings')}
            icon={<span>⚙️</span>}
          >
            설정
          </AppleButton>
        </div>

        {/* 달력 */}
        <AppleCard padding="large" elevated>
          <div style={calendarNavStyles}>
            <button
              style={monthNavButtonStyles}
              onClick={() => {
                const prev = new Date(selectedDate);
                prev.setMonth(prev.getMonth() - 1);
                setSelectedDate(prev);
              }}
            >
              ‹
            </button>
            <button
              style={monthNavButtonStyles}
              onClick={() => {
                const next = new Date(selectedDate);
                next.setMonth(next.getMonth() + 1);
                setSelectedDate(next);
              }}
            >
              ›
            </button>
          </div>

          <div style={calendarGridStyles}>
            <div style={weekdaysStyles}>
              {dayNames.map(day => (
                <div key={day} style={weekdayStyles}>{day}</div>
              ))}
            </div>

            <div style={daysGridStyles}>
              {days.map((date, index) => (
                <CalendarDay
                  key={index}
                  date={date}
                  schedule={date ? getScheduleForDate(date) : undefined}
                  isToday={date ? date.toDateString() === new Date().toDateString() : false}
                />
              ))}
            </div>
          </div>
        </AppleCard>

        {/* 범례 */}
        <AppleCard padding="medium">
          <div style={legendStyles}>
            <div style={legendItemStyles}>
              <span style={{...legendColorStyles, backgroundColor: AppleDesign.colors.systemGreen}}></span>
              주간 (D)
            </div>
            <div style={legendItemStyles}>
              <span style={{...legendColorStyles, backgroundColor: AppleDesign.colors.systemOrange}}></span>
              저녁 (E)
            </div>
            <div style={legendItemStyles}>
              <span style={{...legendColorStyles, backgroundColor: AppleDesign.colors.systemPurple}}></span>
              야간 (N)
            </div>
            <div style={legendItemStyles}>
              <span style={{...legendColorStyles, backgroundColor: AppleDesign.colors.systemGray}}></span>
              휴무 (-)
            </div>
          </div>
        </AppleCard>
      </div>
    );
  }

  function CalendarDay({ date, schedule, isToday }: { date: Date | null; schedule?: ScheduleData; isToday: boolean }) {
    if (!date) {
      return <div style={emptyDayStyles}></div>;
    }

    const dayStyles = {
      ...calendarDayStyles,
      ...(isToday ? todayStyles : {}),
    };

    return (
      <div style={dayStyles}>
        <div style={dayNumberStyles}>{date.getDate()}</div>
        {schedule && (
          <div style={dayScheduleStyles}>
            {Object.values(schedule.nurses).map((assignment, i) => (
              <div
                key={i}
                style={{
                  ...scheduleItemStyles,
                  backgroundColor: getShiftColor(assignment.shift),
                }}
              >
                <div style={nurseInitialSmallStyles}>
                  {assignment.nurse.name.charAt(0)}
                </div>
                <div style={shiftTypeStyles}>
                  {assignment.shift === 'DAY' ? 'D' :
                   assignment.shift === 'EVENING' ? 'E' :
                   assignment.shift === 'NIGHT' ? 'N' : '-'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  function SettingsView() {
    return (
      <div style={screenStyles}>
        <div style={settingsHeaderStyles}>
          <AppleButton
            variant="secondary"
            size="small"
            onClick={() => setCurrentView('calendar')}
            icon={<span>←</span>}
          >
            달력
          </AppleButton>
          <h1 style={settingsTitleStyles}>설정</h1>
        </div>

        <AppleCard padding="large" elevated>
          <h2 style={sectionTitleStyles}>현재 설정</h2>
          {selectedWard ? (
            <div style={currentSettingsStyles}>
              <div style={settingItemStyles}>
                <span style={settingIconStyles}>{selectedWard.icon}</span>
                <div>
                  <h3 style={settingNameStyles}>{selectedWard.name}</h3>
                  <p style={settingDetailStyles}>
                    최소 {selectedWard.min_nurses_per_shift}명/교대 • {selectedWard.shift_types.join(', ')}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <p style={noSettingsStyles}>병동이 선택되지 않았습니다.</p>
          )}

          <div style={settingsSectionStyles}>
            <h3 style={settingsSubtitleStyles}>등록된 간호사 ({nurses.length}명)</h3>
            <div style={nursesSummaryStyles}>
              {nurses.map(nurse => (
                <div key={nurse.id} style={nurseSummaryItemStyles}>
                  {nurse.name}
                </div>
              ))}
            </div>
          </div>
        </AppleCard>

        <div style={settingsActionsStyles}>
          <AppleButton
            onClick={() => setCurrentView('setup')}
            fullWidth
            size="large"
            icon={<span>✏️</span>}
          >
            설정 수정
          </AppleButton>
          <AppleButton
            variant="secondary"
            onClick={generateSchedule}
            disabled={isLoading}
            fullWidth
            size="large"
            icon={<span>🔄</span>}
          >
            근무표 재생성
          </AppleButton>
        </div>
      </div>
    );
  }

  // 유틸리티 함수들
  function getDaysInMonth(date: Date): (Date | null)[] {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startDayOfWeek = firstDay.getDay();

    const days: (Date | null)[] = [];

    for (let i = 0; i < startDayOfWeek; i++) {
      days.push(null);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }

    return days;
  }

  function getScheduleForDate(date: Date): ScheduleData | undefined {
    const dateStr = date.toISOString().split('T')[0];
    return scheduleData.find(s => s.date === dateStr);
  }

  function getShiftColor(shift: string) {
    const colorMap = {
      DAY: AppleDesign.colors.systemGreen,
      EVENING: AppleDesign.colors.systemOrange,
      NIGHT: AppleDesign.colors.systemPurple,
      OFF: AppleDesign.colors.systemGray,
    };
    return colorMap[shift as keyof typeof colorMap] || AppleDesign.colors.systemGray;
  }
};

// 스타일 정의
const appStyles: React.CSSProperties = {
  minHeight: '100vh',
  background: `linear-gradient(135deg, ${AppleDesign.colors.systemBlue}08 0%, ${AppleDesign.colors.systemPurple}08 100%)`,
  fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif',
  color: AppleDesign.colors.label,
  paddingTop: 'env(safe-area-inset-top)',
  paddingBottom: 'env(safe-area-inset-bottom)',
};

const containerStyles: React.CSSProperties = {
  maxWidth: '428px',
  margin: '0 auto',
  minHeight: '100vh',
  background: 'transparent',
};

const screenStyles: React.CSSProperties = {
  padding: AppleDesign.spacing.lg,
  display: 'flex',
  flexDirection: 'column',
  gap: AppleDesign.spacing.lg,
};

const headerStyles: React.CSSProperties = {
  textAlign: 'center',
  marginBottom: AppleDesign.spacing.md,
};

const titleContainerStyles: React.CSSProperties = {
  background: AppleDesign.colors.systemBackground,
  borderRadius: AppleDesign.borderRadius.xlarge,
  padding: AppleDesign.spacing.xl,
  boxShadow: AppleDesign.shadows.large,
  backdropFilter: 'blur(20px)',
};

const mainTitleStyles: React.CSSProperties = {
  ...AppleDesign.typography.largeTitle,
  fontWeight: '700',
  margin: '0 0 8px 0',
  background: `linear-gradient(135deg, ${AppleDesign.colors.systemBlue}, ${AppleDesign.colors.systemPurple})`,
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
};

const subtitleStyles: React.CSSProperties = {
  ...AppleDesign.typography.title3,
  color: AppleDesign.colors.secondaryLabel,
  margin: 0,
  fontWeight: '400',
};

const sectionTitleStyles: React.CSSProperties = {
  ...AppleDesign.typography.title2,
  fontWeight: '600',
  margin: `0 0 ${AppleDesign.spacing.md} 0`,
  color: AppleDesign.colors.label,
};

const wardGridStyles: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr',
  gap: AppleDesign.spacing.md,
};

const wardCardContentStyles: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: AppleDesign.spacing.md,
};

const wardIconStyles: React.CSSProperties = {
  width: '56px',
  height: '56px',
  borderRadius: AppleDesign.borderRadius.medium,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const wardInfoStyles: React.CSSProperties = {
  flex: 1,
};

const wardNameStyles: React.CSSProperties = {
  ...AppleDesign.typography.headline,
  margin: '0 0 4px 0',
  color: AppleDesign.colors.label,
};

const wardDetailsStyles: React.CSSProperties = {
  ...AppleDesign.typography.subheadline,
  color: AppleDesign.colors.secondaryLabel,
  margin: 0,
};

const nurseHeaderStyles: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  marginBottom: AppleDesign.spacing.md,
};

const nurseBadgeStyles: React.CSSProperties = {
  background: AppleDesign.colors.systemBlue,
  color: 'white',
  padding: '6px 12px',
  borderRadius: AppleDesign.borderRadius.large,
  ...AppleDesign.typography.caption1,
  fontWeight: '600',
};

const buttonContainerStyles: React.CSSProperties = {
  padding: `0 ${AppleDesign.spacing.md}`,
};

const formContainerStyles: React.CSSProperties = {
  background: AppleDesign.colors.tertiarySystemBackground,
  borderRadius: AppleDesign.borderRadius.large,
  padding: AppleDesign.spacing.lg,
  margin: `${AppleDesign.spacing.md} 0`,
  display: 'flex',
  flexDirection: 'column',
  gap: AppleDesign.spacing.md,
};

const formRowStyles: React.CSSProperties = {
  display: 'flex',
  gap: AppleDesign.spacing.md,
};

const labelStyles: React.CSSProperties = {
  ...AppleDesign.typography.subheadline,
  color: AppleDesign.colors.secondaryLabel,
  fontWeight: '500',
  display: 'block',
  marginBottom: AppleDesign.spacing.sm,
};

const selectStyles: React.CSSProperties = {
  width: '100%',
  padding: AppleDesign.spacing.md,
  border: `1px solid ${AppleDesign.colors.systemGray4}`,
  borderRadius: AppleDesign.borderRadius.medium,
  background: AppleDesign.colors.systemBackground,
  color: AppleDesign.colors.label,
  fontFamily: 'inherit',
  ...AppleDesign.typography.body,
  minHeight: '44px',
};

const sliderStyles: React.CSSProperties = {
  width: '100%',
  marginTop: AppleDesign.spacing.sm,
  WebkitAppearance: 'none',
  appearance: 'none',
  height: '6px',
  borderRadius: '3px',
  background: AppleDesign.colors.systemGray5,
  outline: 'none',
};

const formActionsStyles: React.CSSProperties = {
  display: 'flex',
  gap: AppleDesign.spacing.md,
  marginTop: AppleDesign.spacing.md,
};

const nurseListStyles: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: AppleDesign.spacing.sm,
  marginTop: AppleDesign.spacing.md,
};

const nurseItemStyles: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: AppleDesign.spacing.md,
  padding: AppleDesign.spacing.md,
  background: AppleDesign.colors.systemBackground,
  borderRadius: AppleDesign.borderRadius.medium,
  border: `1px solid ${AppleDesign.colors.systemGray5}`,
};

const nurseAvatarStyles: React.CSSProperties = {
  width: '44px',
  height: '44px',
  borderRadius: '50%',
  background: AppleDesign.colors.systemBlue,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const nurseInitialStyles: React.CSSProperties = {
  color: 'white',
  fontWeight: '600',
  fontSize: '18px',
};

const nurseContentStyles: React.CSSProperties = {
  flex: 1,
};

const nurseNameStyles: React.CSSProperties = {
  ...AppleDesign.typography.headline,
  margin: '0 0 2px 0',
  color: AppleDesign.colors.label,
};

const nurseDetailsTextStyles: React.CSSProperties = {
  ...AppleDesign.typography.footnote,
  color: AppleDesign.colors.secondaryLabel,
  margin: 0,
};

const deleteButtonStyles: React.CSSProperties = {
  background: AppleDesign.colors.systemRed,
  color: 'white',
  border: 'none',
  borderRadius: '50%',
  width: '32px',
  height: '32px',
  cursor: 'pointer',
  fontSize: '14px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

// Calendar styles
const calendarHeaderStyles: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  background: AppleDesign.colors.systemBackground,
  padding: AppleDesign.spacing.lg,
  borderRadius: AppleDesign.borderRadius.xlarge,
  boxShadow: AppleDesign.shadows.medium,
};

const calendarTitleStyles: React.CSSProperties = {
  ...AppleDesign.typography.title1,
  fontWeight: '600',
  margin: 0,
  textAlign: 'center',
  flex: 1,
};

const calendarNavStyles: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  marginBottom: AppleDesign.spacing.lg,
};

const monthNavButtonStyles: React.CSSProperties = {
  background: AppleDesign.colors.systemGray6,
  border: 'none',
  borderRadius: '50%',
  width: '44px',
  height: '44px',
  fontSize: '20px',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: AppleDesign.colors.systemBlue,
  transition: 'all 0.2s ease',
};

const calendarGridStyles: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: AppleDesign.spacing.sm,
};

const weekdaysStyles: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(7, 1fr)',
  gap: '4px',
  marginBottom: AppleDesign.spacing.md,
};

const weekdayStyles: React.CSSProperties = {
  textAlign: 'center',
  ...AppleDesign.typography.caption1,
  fontWeight: '600',
  color: AppleDesign.colors.secondaryLabel,
  padding: AppleDesign.spacing.sm,
};

const daysGridStyles: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(7, 1fr)',
  gap: '4px',
};

const calendarDayStyles: React.CSSProperties = {
  minHeight: '80px',
  borderRadius: AppleDesign.borderRadius.medium,
  padding: AppleDesign.spacing.sm,
  border: `1px solid ${AppleDesign.colors.systemGray5}`,
  background: AppleDesign.colors.systemBackground,
  display: 'flex',
  flexDirection: 'column',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
};

const todayStyles: React.CSSProperties = {
  background: `${AppleDesign.colors.systemBlue}15`,
  borderColor: AppleDesign.colors.systemBlue,
  borderWidth: '2px',
};

const emptyDayStyles: React.CSSProperties = {
  minHeight: '80px',
};

const dayNumberStyles: React.CSSProperties = {
  ...AppleDesign.typography.subheadline,
  fontWeight: '600',
  color: AppleDesign.colors.label,
  marginBottom: '4px',
};

const dayScheduleStyles: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '2px',
  flex: 1,
};

const scheduleItemStyles: React.CSSProperties = {
  width: '20px',
  height: '20px',
  borderRadius: '6px',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  color: 'white',
  fontSize: '8px',
  fontWeight: '600',
};

const nurseInitialSmallStyles: React.CSSProperties = {
  fontSize: '6px',
  lineHeight: '1',
};

const shiftTypeStyles: React.CSSProperties = {
  fontSize: '6px',
  lineHeight: '1',
  marginTop: '1px',
};

const legendStyles: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-around',
  flexWrap: 'wrap',
  gap: AppleDesign.spacing.md,
};

const legendItemStyles: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: AppleDesign.spacing.sm,
  ...AppleDesign.typography.footnote,
  fontWeight: '500',
};

const legendColorStyles: React.CSSProperties = {
  width: '12px',
  height: '12px',
  borderRadius: '3px',
};

// Settings styles
const settingsHeaderStyles: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: AppleDesign.spacing.md,
  background: AppleDesign.colors.systemBackground,
  padding: AppleDesign.spacing.lg,
  borderRadius: AppleDesign.borderRadius.xlarge,
  boxShadow: AppleDesign.shadows.medium,
};

const settingsTitleStyles: React.CSSProperties = {
  ...AppleDesign.typography.title1,
  fontWeight: '600',
  margin: 0,
  flex: 1,
};

const currentSettingsStyles: React.CSSProperties = {
  marginBottom: AppleDesign.spacing.lg,
};

const settingItemStyles: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: AppleDesign.spacing.md,
  padding: AppleDesign.spacing.md,
  background: AppleDesign.colors.tertiarySystemBackground,
  borderRadius: AppleDesign.borderRadius.medium,
};

const settingIconStyles: React.CSSProperties = {
  fontSize: '32px',
};

const settingNameStyles: React.CSSProperties = {
  ...AppleDesign.typography.headline,
  margin: '0 0 4px 0',
  color: AppleDesign.colors.systemBlue,
};

const settingDetailStyles: React.CSSProperties = {
  ...AppleDesign.typography.subheadline,
  color: AppleDesign.colors.secondaryLabel,
  margin: 0,
};

const noSettingsStyles: React.CSSProperties = {
  ...AppleDesign.typography.body,
  color: AppleDesign.colors.tertiaryLabel,
  textAlign: 'center',
  padding: AppleDesign.spacing.xl,
};

const settingsSectionStyles: React.CSSProperties = {
  marginTop: AppleDesign.spacing.lg,
  paddingTop: AppleDesign.spacing.lg,
  borderTop: `1px solid ${AppleDesign.colors.systemGray5}`,
};

const settingsSubtitleStyles: React.CSSProperties = {
  ...AppleDesign.typography.headline,
  margin: `0 0 ${AppleDesign.spacing.md} 0`,
  color: AppleDesign.colors.label,
};

const nursesSummaryStyles: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: AppleDesign.spacing.sm,
};

const nurseSummaryItemStyles: React.CSSProperties = {
  background: AppleDesign.colors.systemBlue,
  color: 'white',
  padding: '6px 12px',
  borderRadius: AppleDesign.borderRadius.medium,
  ...AppleDesign.typography.caption1,
  fontWeight: '500',
};

const settingsActionsStyles: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: AppleDesign.spacing.md,
};

export default AppleNurseApp;