---
name: lead-campaign-analysis
description: Use when reviewing weekly or monthly Google Ads and Naver Search Ads CSV/XLSX exports for quote-request or brochure-download lead campaigns, identifying search-term and budget actions, or preparing a marketer-ready action queue.
---

# 리드 광고 캠페인 분석

Google Ads와 네이버 검색광고 데이터를 읽어 전환수 확대 기회를 찾고, 사람이 검토할 실행 후보를 우선순위로 정리한다.

## 사용 시점

- 주간 성과 점검과 즉시 최적화 후보가 필요할 때
- 월간 성과 회고와 다음 달 우선순위를 정할 때
- 캠페인·광고그룹·검색어 단위의 전환 기여와 낭비 비용을 확인할 때

## 필요한 입력

- 현재 기간의 Google Ads 또는 네이버 검색광고 CSV/XLSX 파일
- 가능하면 동일 기간 길이의 이전 기간 파일
- 분석 주기: `weekly` 또는 `monthly`
- 선택: 총예산 또는 캠페인별 예산 정보

기간 시작일·종료일이 있는 내보내기와 캠페인 수준의 실제 예산/소진 정보가 가장 좋다. 검색어 행마다 반복된 예산값은 합산하거나 소진 판단에 사용하지 않는다.

필수 열과 플랫폼별 별칭은 `references/platform-schemas.md`를 확인한다. 입력 파일은 읽기 전용으로 취급한다.

## 실행 단계

1. 파일의 플랫폼·기간·열 누락·중복·최근 전환 지연 가능성을 확인한다. 날짜가 없으면 동등 기간 비교와 전환 지연 판단이 제한된다고 표시한다.
2. CSV는 아래 스크립트로 요약한다. XLSX는 스프레드시트 도구로 필요한 열을 CSV로 내보내거나 같은 열 구성을 확인한 뒤 진행한다.

   ```bash
   python3 scripts/analyze_campaigns.py --period weekly --input current-google.csv current-naver.csv --previous previous-google.csv previous-naver.csv
   ```

3. Google Ads와 네이버는 각각 내부 기준선으로 분석한다. 입찰가, CPC, 절대 CPA는 플랫폼 간 비교 대상이 아니다.
4. 검색어 제외·확장, 플랫폼 내부 예산 재배분, 구조 점검 순서로 액션을 만든다.
5. 예산 증액은 총예산 유지, 내부 재배분, 검색어 정리, 구조 개선을 모두 검토한 뒤에도 근거가 충분할 때만 `마지막 대안`으로 표기한다.
6. `assets/report-template.md` 형식으로 마케터가 검토할 결과를 작성한다.

## 결과물 형식

- 주간: 핵심 요약, 이상 탐지, 원인 분해, 최대 5개의 추천 액션, 제약 검증
- 월간: 월간 추세, 전환 기여도 변화, 검색어 품질, 예산 배분, 다음 달 우선순위
- 각 액션: 우선순위, 대상, 권장 조치, 근거, 기대 효과, 주의점, 다음 확인 KPI

## 금지사항

- 광고 계정 변경, 자동 입찰 변경, 예산 변경 실행, 업로드용 변경 파일 생성
- 원본 파일 수정·삭제
- 플랫폼 간 입찰가·CPC·절대 CPA의 직접 비교 또는 순위화
- 데이터가 부족하거나 전환 지연이 의심되는 항목에 대한 단정적 추천

## 사람 검토 지점

- 제외·확장할 검색어가 실제 사업 의도와 맞는지
- 예산 재배분이 브랜드, 영업, 재고, 시즌성 제약과 충돌하지 않는지
- 전환 정의가 두 플랫폼에서 모두 견적 문의 또는 브로셔 다운로드 제출인지
- 예산 증액 추천은 다른 최적화 수단을 모두 검토했는지

## 리소스

- `references/platform-schemas.md`: 입력 열, 지표, 비교 규칙
- `scripts/analyze_campaigns.py`: 익명 CSV의 읽기 전용 요약 도구
- `mock-data/`: 개인정보가 없는 예시 입력 파일
- `assets/report-template.md`: 결과 보고서 양식
