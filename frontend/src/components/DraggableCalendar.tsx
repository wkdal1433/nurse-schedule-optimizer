import React, { useState, useEffect } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  sortableKeyboardCoordinates,
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import {
  CSS,
} from '@dnd-kit/utilities';

import { useDragAndDrop } from '../hooks/useDragAndDrop';
import EmergencyOverride from './EmergencyOverride';

interface Nurse {
  id: number;
  name: string;
  role: string;
  employment_type: string;
  experience_level: number;
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

interface DraggableCalendarProps {
  scheduleId: number;
  scheduleData: ScheduleData[];
  nurses: Nurse[];
  selectedDate: Date;
  onDateChange: (date: Date) => void;
}

// 드래그 가능한 간호사 카드 컴포넌트
const DraggableNurseCard: React.FC<{
  nurse: Nurse;
  shift: string;
  date: string;
}> = ({ nurse, shift, date }) => {
  const droppableId = `${date}-${shift}`;
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: nurse.id.toString(),
    data: { droppableId, nurse }
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`draggable-nurse-card ${shift.toLowerCase()}`}
    >
      <div className="nurse-initial">
        {nurse.name.charAt(0)}
      </div>
      <div className="nurse-info">
        <div className="nurse-name">{nurse.name}</div>
        <div className="shift-indicator">
          {shift === 'DAY' ? 'D' :
           shift === 'EVENING' ? 'E' :
           shift === 'NIGHT' ? 'N' : '-'}
        </div>
      </div>
    </div>
  );
};

// 드롭 영역 컴포넌트
const DropZone: React.FC<{
  shift: string;
  date: string;
  assignments: number[];
  nurses: Nurse[];
  onEmergencyOverride: (date: string, shift: string) => void;
}> = ({ shift, date, assignments, nurses, onEmergencyOverride }) => {
  const droppableId = `${date}-${shift}`;

  return (
    <div
      className={`drop-zone ${shift.toLowerCase()}`}
      data-droppable-id={droppableId}
    >
      <div className="shift-label">
        {shift === 'DAY' ? '🌅' :
         shift === 'EVENING' ? '🌆' :
         shift === 'NIGHT' ? '🌙' : '😴'}
      </div>

      <SortableContext
        items={assignments.map(id => id.toString())}
        strategy={verticalListSortingStrategy}
      >
        <div className="nurses-container">
          {assignments.map(nurseId => {
            const nurse = nurses.find(n => n.id === nurseId);
            return nurse ? (
              <DraggableNurseCard
                key={nurseId}
                nurse={nurse}
                shift={shift}
                date={date}
              />
            ) : null;
          })}
        </div>
      </SortableContext>

      {assignments.length === 0 && (
        <div className="empty-shift">
          드래그하여 배치
        </div>
      )}

      {/* 긴급 오버라이드 버튼 */}
      <button
        className="emergency-override-btn"
        onClick={() => onEmergencyOverride(date, shift)}
        title="긴급상황 오버라이드"
      >
        🚨
      </button>
    </div>
  );
};

const DraggableCalendar: React.FC<DraggableCalendarProps> = ({
  scheduleId,
  scheduleData,
  nurses,
  selectedDate,
  onDateChange
}) => {
  const {
    assignments,
    setAssignments,
    onDragEnd,
    isDragging,
    dragError,
    clearError
  } = useDragAndDrop(scheduleId);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const [draggedNurse, setDraggedNurse] = useState<Nurse | null>(null);
  const [showEmergencyOverride, setShowEmergencyOverride] = useState(false);
  const [emergencyOverrideDate, setEmergencyOverrideDate] = useState('');
  const [emergencyOverrideShift, setEmergencyOverrideShift] = useState('');

  useEffect(() => {
    // scheduleData를 assignments 형태로 변환
    const assignmentsByDate: Record<string, Record<string, number[]>> = {};

    scheduleData.forEach(dayData => {
      const dateKey = dayData.date;
      assignmentsByDate[dateKey] = {
        DAY: [],
        EVENING: [],
        NIGHT: [],
        OFF: []
      };

      Object.values(dayData.nurses).forEach(assignment => {
        const shift = assignment.shift;
        const nurseId = assignment.nurse.id;
        assignmentsByDate[dateKey][shift].push(nurseId);
      });
    });

    setAssignments(assignmentsByDate);
  }, [scheduleData, setAssignments]);

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();

    const days: Date[] = [];
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }
    return days;
  };

  const days = getDaysInMonth(selectedDate);

  const handleDragStart = (event: any) => {
    const nurseId = parseInt(event.active.id);
    const nurse = nurses.find(n => n.id === nurseId);
    setDraggedNurse(nurse || null);
  };

  const handleDragEnd = (event: any) => {
    setDraggedNurse(null);
    onDragEnd(event);
  };

  const handleEmergencyOverride = (date: string, shift: string) => {
    setEmergencyOverrideDate(date);
    setEmergencyOverrideShift(shift);
    setShowEmergencyOverride(true);
  };

  const handleEmergencyOverrideSuccess = (result: any) => {
    console.log('Emergency override successful:', result);
    // 필요시 assignments 상태 업데이트
    // setAssignments 등을 통해 UI 즉시 반영
  };

  return (
    <div className="draggable-calendar">
      {dragError && (
        <div className="drag-error-banner">
          <span>{dragError}</span>
          <button onClick={clearError}>✕</button>
        </div>
      )}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className={`calendar-grid ${isDragging ? 'dragging' : ''}`}>
          {days.slice(0, 7).map((date, index) => {
            const dateKey = date.toISOString().split('T')[0];
            const dayAssignments = assignments[dateKey] || {
              DAY: [], EVENING: [], NIGHT: [], OFF: []
            };

            return (
              <div key={dateKey} className="calendar-day">
                <div className="day-header">
                  <div className="day-number">{date.getDate()}</div>
                  <div className="day-name">
                    {['일', '월', '화', '수', '목', '금', '토'][date.getDay()]}
                  </div>
                </div>

                <div className="shifts-container">
                  {(['DAY', 'EVENING', 'NIGHT'] as const).map(shift => (
                    <DropZone
                      key={`${dateKey}-${shift}`}
                      shift={shift}
                      date={dateKey}
                      assignments={dayAssignments[shift]}
                      nurses={nurses}
                      onEmergencyOverride={handleEmergencyOverride}
                    />
                  ))}
                </div>

                {/* OFF 상태 (휴무) */}
                <DropZone
                  shift="OFF"
                  date={dateKey}
                  assignments={dayAssignments.OFF}
                  nurses={nurses}
                  onEmergencyOverride={handleEmergencyOverride}
                />
              </div>
            );
          })}
        </div>

        <DragOverlay>
          {draggedNurse ? (
            <div className="drag-overlay">
              <div className="nurse-preview">
                {draggedNurse.name}
              </div>
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Emergency Override Modal */}
      {showEmergencyOverride && (
        <EmergencyOverride
          scheduleId={scheduleId}
          selectedDate={emergencyOverrideDate}
          selectedShift={emergencyOverrideShift}
          nurses={nurses}
          onClose={() => setShowEmergencyOverride(false)}
          onSuccess={handleEmergencyOverrideSuccess}
        />
      )}

      <style jsx>{`
        .draggable-calendar {
          padding: 20px;
          background: #f8f9fa;
          border-radius: 16px;
        }

        .drag-error-banner {
          background: #fee2e2;
          border: 1px solid #fecaca;
          color: #dc2626;
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .drag-error-banner button {
          background: none;
          border: none;
          color: #dc2626;
          cursor: pointer;
          font-size: 16px;
          font-weight: bold;
        }

        .calendar-grid {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 16px;
          margin-bottom: 20px;
        }

        .calendar-grid.dragging {
          user-select: none;
        }

        .calendar-day {
          background: white;
          border-radius: 12px;
          padding: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          transition: all 0.2s ease;
        }

        .calendar-day:hover {
          box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }

        .day-header {
          text-align: center;
          margin-bottom: 12px;
        }

        .day-number {
          font-size: 18px;
          font-weight: 600;
          color: #1f2937;
        }

        .day-name {
          font-size: 12px;
          color: #6b7280;
          margin-top: 2px;
        }

        .shifts-container {
          margin-bottom: 8px;
        }

        .drop-zone {
          min-height: 60px;
          border-radius: 8px;
          padding: 8px;
          margin-bottom: 6px;
          border: 2px dashed transparent;
          transition: all 0.2s ease;
        }

        .drop-zone.day {
          background: linear-gradient(135deg, #e3f2fd, #f8f9ff);
        }

        .drop-zone.evening {
          background: linear-gradient(135deg, #fff3e0, #fffaf7);
        }

        .drop-zone.night {
          background: linear-gradient(135deg, #f3e5f5, #faf7ff);
        }

        .drop-zone.off {
          background: linear-gradient(135deg, #f5f5f5, #ffffff);
        }

        .drop-zone:hover {
          border-color: #6366f1;
        }

        .shift-label {
          text-align: center;
          font-size: 12px;
          margin-bottom: 4px;
          opacity: 0.7;
        }

        .nurses-container {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
        }

        .draggable-nurse-card {
          background: white;
          border-radius: 6px;
          padding: 6px;
          cursor: grab;
          box-shadow: 0 1px 4px rgba(0,0,0,0.1);
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 4px;
          min-width: 60px;
        }

        .draggable-nurse-card:hover {
          box-shadow: 0 2px 8px rgba(0,0,0,0.2);
          transform: translateY(-1px);
        }

        .draggable-nurse-card:active {
          cursor: grabbing;
        }

        .nurse-initial {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #6366f1;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: 600;
        }

        .nurse-info {
          flex: 1;
          min-width: 0;
        }

        .nurse-name {
          font-size: 10px;
          font-weight: 500;
          color: #1f2937;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .shift-indicator {
          font-size: 8px;
          color: #6b7280;
        }

        .empty-shift {
          text-align: center;
          color: #9ca3af;
          font-size: 11px;
          padding: 8px;
        }

        .drag-overlay {
          background: white;
          border-radius: 8px;
          padding: 8px 12px;
          box-shadow: 0 4px 16px rgba(0,0,0,0.2);
          border: 2px solid #6366f1;
        }

        .nurse-preview {
          font-weight: 600;
          color: #6366f1;
        }

        .emergency-override-btn {
          position: absolute;
          top: 4px;
          right: 4px;
          width: 20px;
          height: 20px;
          border: none;
          background: #dc2626;
          color: white;
          border-radius: 50%;
          font-size: 10px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0.7;
          transition: all 0.2s ease;
          z-index: 10;
        }

        .emergency-override-btn:hover {
          opacity: 1;
          transform: scale(1.1);
          box-shadow: 0 2px 8px rgba(220, 38, 38, 0.4);
        }

        .drop-zone {
          position: relative;
        }

        @media (max-width: 768px) {
          .calendar-grid {
            grid-template-columns: 1fr;
            gap: 12px;
          }

          .draggable-nurse-card {
            min-width: 80px;
          }

          .nurse-name {
            font-size: 11px;
          }
        }
      `}</style>
    </div>
  );
};

export default DraggableCalendar;