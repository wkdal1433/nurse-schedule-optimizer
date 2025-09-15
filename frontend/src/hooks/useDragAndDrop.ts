import { useState } from 'react';
import { DragEndEvent } from '@dnd-kit/core';

interface AssignmentUpdateRequest {
  date: string;
  shift: string;
  from_employee_id: number;
  to_employee_id?: number;
  override?: boolean;
}

interface AssignmentUpdateResponse {
  ok: boolean;
  new_score?: number;
  delta?: number;
  violations?: Array<{
    type: string;
    detail: string;
    shift?: string;
    required?: number;
    actual?: number;
  }>;
  message?: string;
  employee_scores?: Record<string, number>;
}

export const useDragAndDrop = (scheduleId: number) => {
  const [assignments, setAssignments] = useState<Record<string, Record<string, number[]>>>({});
  const [isDragging, setIsDragging] = useState(false);
  const [dragError, setDragError] = useState<string | null>(null);

  const applyLocalMove = (
    prevState: Record<string, Record<string, number[]>>,
    draggedId: string,
    sourceDroppableId: string,
    destinationDroppableId: string
  ) => {
    const newState = { ...prevState };
    const employeeId = parseInt(draggedId);

    // Parse droppable IDs: "date-shift" format
    const [sourceDate, sourceShift] = sourceDroppableId.split('-');
    const [destDate, destShift] = destinationDroppableId.split('-');

    // Remove from source
    if (newState[sourceDate] && newState[sourceDate][sourceShift]) {
      newState[sourceDate][sourceShift] = newState[sourceDate][sourceShift].filter(
        id => id !== employeeId
      );
    }

    // Add to destination (if not 'off' shift)
    if (destShift !== 'off') {
      if (!newState[destDate]) newState[destDate] = {};
      if (!newState[destDate][destShift]) newState[destDate][destShift] = [];
      newState[destDate][destShift].push(employeeId);
    }

    return newState;
  };

  const onDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setIsDragging(true);
    setDragError(null);

    if (!over || active.id === over.id) {
      setIsDragging(false);
      return;
    }

    const draggedId = active.id.toString();
    const sourceDroppableId = active.data.current?.droppableId;
    const destinationDroppableId = over.id.toString();

    if (!sourceDroppableId) {
      setIsDragging(false);
      return;
    }

    // 1) Optimistic Update (즉시 UI 반영)
    const previousState = { ...assignments };
    const optimisticState = applyLocalMove(
      previousState,
      draggedId,
      sourceDroppableId,
      destinationDroppableId
    );
    setAssignments(optimisticState);

    try {
      // 2) 서버 검증 요청
      const [destDate, destShift] = destinationDroppableId.split('-');
      const [, sourceShift] = sourceDroppableId.split('-');

      const updateRequest: AssignmentUpdateRequest = {
        date: destDate,
        shift: sourceShift, // 원래 교대에서 제거
        from_employee_id: parseInt(draggedId),
        to_employee_id: destShift !== 'off' ? parseInt(draggedId) : undefined
      };

      const response = await fetch(
        `/api/schedules/${scheduleId}/assignments`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateRequest)
        }
      );

      const result: AssignmentUpdateResponse = await response.json();

      if (result.ok) {
        // 3) 성공 시 점수 업데이트
        if (result.delta !== undefined) {
          console.log(`Score change: ${result.delta > 0 ? '+' : ''}${result.delta}`);
          const message = `점수 변화: ${result.delta > 0 ? '+' : ''}${result.delta}`;
          console.log(message);
        }
      } else {
        // 4) 실패 시 롤백
        setAssignments(previousState);
        setDragError(result.message || '배정 변경이 실패했습니다');

        if (result.violations && result.violations.length > 0) {
          const violationMsg = result.violations
            .map(v => `${v.detail}`)
            .join(', ');
          setDragError(`제약조건 위반: ${violationMsg}`);
        }
      }

    } catch (error) {
      // 5) 네트워크 오류 시 롤백
      setAssignments(previousState);
      setDragError('서버 연결 실패: ' + (error as Error).message);
    } finally {
      setIsDragging(false);
    }
  };

  const clearError = () => setDragError(null);

  return {
    assignments,
    setAssignments,
    onDragEnd,
    isDragging,
    dragError,
    clearError
  };
};