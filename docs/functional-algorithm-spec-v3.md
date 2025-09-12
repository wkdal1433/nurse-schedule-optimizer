# Nurse Shift Scheduling Application – Functional & Algorithm Specification (v3)

## Overview

The Nurse Shift Scheduling Application provides automated generation, validation, and management of hospital shift schedules. It integrates optimization algorithms with manual adjustment features, ensuring compliance with labor regulations, hospital policies, individual nurse preferences, and staff roles.

This document reflects enhanced requirements based on clinical feedback, including role-based assignment, employment type constraints, pattern prevention, and emergency handling.

## Functional Requirements

### 1. Shift Rules & Legal Compliance

- Maximum consecutive night shifts: Limit 2–3 days.
- Maximum consecutive working days: Limit 5 days.
- Weekly rest guarantee: At least 1 off-day per week.
- Legal working hours: Weekly cap of 40 hours, with balanced weekly distribution.
- Configurable constraints: Admin can toggle/adjust these rules per hospital policy.

### 2. Personal Preferences & Requests

Nurses can submit:
- Vacation/leave requests (specific dates).
- Shift avoidance preferences (e.g., fewer nights).
- Preferred shift patterns.

Admin dashboard must include a pre-scheduling request form.
Optimization algorithm integrates preferences while maintaining fairness and compliance.

### 3. Role-Based & Employment-Type Assignment

**Roles**: Head nurse, Staff nurse, New nurse, Education coordinator, etc.

Role-specific constraints:
- Example: New nurses always paired with a senior nurse on the same shift.

**Employment type**: Full-time vs. Part-time
- Part-time nurses assigned only to allowable shifts.

### 4. Shift Pattern Validation

Prevent unreasonable sequences:
- Avoid patterns like Day → next-day Night or excessive sequential Night shifts.
- Rule-based scoring reduces fatigue risk and improves staff satisfaction.

### 5. Manual Editing & Emergency Override

- Drag-and-drop editing for schedule adjustments.
- Real-time recalculation of optimization score.
- Emergency mode: Admin can immediately reassign shifts due to illness or unexpected absence.
- Optional AI recommendation: Suggest optimal replacement based on availability, legal hours, past workload.

### 6. Notifications & Sharing

Shift schedule distribution:
- PDF / Image export.
- KakaoTalk / Email sharing.
- Push notifications for schedule updates.
- Personalized view: Each nurse sees only their assigned shifts.

### 7. Staffing Safety Verification

- Enforce minimum staff thresholds per ward and shift (e.g., ICU Night ≥3).
- Automatic validation with warning messages if thresholds are not met.

### 8. Statistics & Reporting

Monthly summaries:
- Individual counts of Day / Evening / Night / Off.
- Night shift distribution fairness.
- Leave usage and request fulfillment.
- Exportable for management reporting.

## Algorithm Design

### Inputs

- **Nurses**: name, role, employment type, experience level.
- **Constraints**: hospital rules, shift patterns, legal hours, minimum staffing.
- **Preferences**: individual requests and restrictions.
- **Period**: scheduling month (start–end dates).

### Process

#### Constraint Encoding
- **Hard constraints**: legal rules, staffing minimums, shift sequence rules.
- **Soft constraints**: personal preferences, fairness, workload balance.

#### Initial Schedule Generation
- Use constraint satisfaction problem (CSP) solver or Hybrid Metaheuristic to generate a valid base schedule.

#### Optimization Loop
**Scoring function**:
- Hard constraint satisfaction = mandatory
- Preference satisfaction = weighted
- Role & employment-type compliance = weighted
- Shift sequence penalties for fatigue reduction

**Iterative improvement**: Swap, Block Move, Shift Reassign

#### Validation & Safety Checks
- Enforce minimum staffing.
- Detect unfair workloads or illegal shift sequences.

#### Manual Adjustment & Emergency Handling
- Admin can drag-and-drop shifts; score recalculated.
- Emergency override: rapid reassignment with AI-based suggestions.

#### Finalization & Distribution
- Lock schedule; export PDF/Image.
- Personalized views for each nurse; notifications pushed.

## Optimization Scoring Breakdown

### Compliance (Hard constraints):
- +100 per rule satisfied
- −1000 per violation (legal/role/staffing breach)

### Preferences (Soft constraints):
- +20 per satisfied request
- −10 per ignored request

### Fairness:
- Balance night shift distribution (variance penalty).

### Role & Employment-Type Compliance:
- −50 per violation (e.g., part-time assigned to invalid shift, new nurse without mentor)

### Shift Pattern Penalty:
- −30 per unreasonable sequence (Day → Night, consecutive nights > 3)

### Safety:
- −500 if minimum staff per shift not met.

## Conclusion

This version of the Nurse Shift Scheduling Application incorporates real-world operational requirements:

- Legal and hospital-specific shift constraints
- Personal requests and preferences
- Role-based and employment-type-aware scheduling
- Manual adjustments and emergency overrides
- Personalized views and reporting

By integrating these, the application becomes clinically viable, allowing hospital administrators to generate, evaluate, and distribute fair and safe shift schedules with minimal friction.