/**
 * NurseSchedule 모듈 진입점
 * SOLID 원칙에 따라 분리된 컴포넌트들을 조합
 */

// 메인 컴포넌트
export { default as NurseScheduleApp } from './NurseScheduleAppNew';

// 뷰 컴포넌트들
export { SetupView } from './views/SetupView';
export { CalendarView } from './views/CalendarView';
export { SettingsView } from './views/SettingsView';

// 훅
export { useNurseSchedule } from './hooks/useNurseSchedule';

// 타입 정의
export * from './types';