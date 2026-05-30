# pyFastPlot 사용자 매뉴얼

pyFastPlot은 CSV 파일이나 엑셀에서 복사한 표 형식 데이터를 빠르게
Matplotlib 그래프로 만드는 데스크톱 프로그램입니다.

## 1. 기본 사용 흐름

1. CSV 파일을 불러오거나 `Generate`를 눌러 빈 테이블을 만듭니다.
2. 스프레드시트 영역에 데이터를 붙여넣거나 직접 편집합니다.
3. X 컬럼과 Y 컬럼을 선택합니다.
4. `Plot New`로 기존 plot을 교체하거나 `Overlay Plot`으로 선을 추가합니다.
5. Plot 옵션을 조정합니다.
6. `Update Plot`을 누릅니다.
7. 그래프를 클립보드로 복사하거나 이미지 파일로 저장합니다.

## 2. Data Table 패널

왼쪽 아래 `Data Table` 패널에는 불러온 CSV 파일과 생성한 테이블이 표시됩니다.

주요 버튼:

- `Generate`: 빈 편집 테이블 생성
- `Clear`: 선택된 테이블 초기화
- `Remove All`: 모든 테이블 제거

`.csv` 파일은 앱 창으로 드래그해서 불러올 수도 있습니다.

## 3. 스프레드시트 편집

중앙 테이블은 다음 작업을 지원합니다.

- `Ctrl+V`로 표 데이터 붙여넣기
- `Ctrl+Shift+V`로 Text Import Wizard 열기
- Delete 또는 Backspace로 선택 셀 삭제
- `Ctrl+Z`로 undo
- `Ctrl+Y`로 redo
- 행 header 우클릭으로 행 삭제 또는 column label 지정
- 열 header 우클릭으로 열 이름 변경 또는 열 삭제

데이터 안에 header 행이 포함되어 있으면 `Set as Column Labels`로 해당 행을
컬럼 이름으로 승격할 수 있습니다.

## 4. Data Selection

아래쪽 오른쪽 영역에는 다음 항목이 있습니다.

- `X`: X축 데이터입니다. X 데이터가 없으면 `Index`를 사용합니다.
- `Y`: Y축 데이터입니다.
- `Label`: 그래프 선에 사용할 사용자 지정 label입니다.
- `Plot New`: 기존 plotted line을 지우고 선택 시리즈를 추가합니다.
- `Overlay Plot`: 기존 plot에 선택 시리즈를 추가합니다.

숫자로 변환 가능한 값만 plot됩니다. 텍스트 header, 비어 있는 값, 결측치는
plot 과정에서 제외됩니다.

## 5. Plot Options

그래프 오른쪽 옵션 패널에서 figure와 line 스타일을 조정합니다.

### Global 탭

`Global` 탭에서는 다음 항목을 설정합니다.

- figure width/height
- DPI
- font
- title과 title size
- X/Y label
- label size와 tick size
- legend 표시 여부, 크기, 위치
- X/Y axis limit
- X/Y log scale

Font가 `Auto`이면 표시 텍스트에 한글이 있는 경우 한글 표시가 가능한 시스템
폰트를 사용합니다.

### Lines 탭

`Lines` 탭은 plot에 올라간 선 목록입니다. 각 행에서 다음 항목을 조정할 수
있습니다.

- plot 표시 여부
- label
- color
- line style
- line width
- marker
- marker size
- marker fill style
- source table

행을 우클릭하고 `Delete Line`을 선택하면 해당 선을 제거할 수 있습니다.

## 6. Plot Export

옵션 패널 아래 버튼을 사용합니다.

- `Update Plot`: 현재 설정으로 그래프를 다시 그림
- `Copy to Clipboard`: 현재 그래프 이미지를 클립보드로 복사
- `Save Plot`: PNG 또는 SVG로 저장

## 7. 로그

앱이 시작되지 않거나 오류가 발생하면 다음 로그를 확인하세요.

```text
%USERPROFILE%\.pyfastplot\pyfastplot.log
```

## 8. 패키징

빌드와 설치 파일 생성 방법은 README와 `packaging/README.md`에 정리되어
있습니다. NSIS 설치 관리자는 설치 직후 앱을 자동 실행하지 않습니다. 이렇게
해야 관리자 권한으로 실행된 앱에서 Explorer drag-and-drop이 막히는 문제를
피할 수 있습니다.
