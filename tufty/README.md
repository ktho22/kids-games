# Pocket Mini Adventure — Tufty 2350 버전

웹 게임 [Pocket Mini Adventure](../pocket-mini-adventure/)를 Pimoroni **Tufty 2350**(Badgeware) 배지에서 돌아가게 옮긴 버전입니다. 포켓몬 200종, 기술, 지역별 레벨, 동굴 5개, 챔피언과 메가뮤츠X까지 규칙과 숫자가 웹 버전과 같습니다.

## 조작

| 버튼 | 하는 일 |
|------|---------|
| 위 / 아래 | 고르기 |
| B (가운데) | 확인 · 다음 메시지 |
| A (왼쪽) | 뒤로 |
| 위 + 아래 길게 | 저장하고 런처로 |

마을 메뉴의 **Save & Quit**으로도 나갈 수 있습니다. 게임은 배틀이 끝날 때마다, 그리고 회복·팀 정리 때 자동으로 저장됩니다(배지 안의 `/state`, 슬롯 1개).

## 설치

1. 배지를 USB로 연결하고 디스크 모드로 엽니다(리셋 버튼 두 번). Mac에 `TUFTY` 드라이브가 보입니다.
2. `pocket_mini_adventure` 폴더를 통째로 `TUFTY/apps/` 안에 복사합니다.
3. 복사 후 Mac이 만든 `._` 파일을 지우고 꺼내기(eject) 합니다.

```bash
rm -f /Volumes/TUFTY/apps/pocket_mini_adventure/._* /Volumes/TUFTY/apps/pocket_mini_adventure/sprites/._*
```

4. 배지를 리셋하면 런처에 포켓볼 아이콘의 **Pocket Mini Adventure**가 생깁니다.

그림 225장을 처음 복사할 때는 몇 분 걸립니다. 그 뒤로는 바뀐 `__init__.py`나 `pkdata.py`만 덮어쓰면 됩니다.

## 웹 버전과 다른 점

- 화면이 160×120이라 이모지 대신 도트 그림과 색깔 표시를 씁니다.
- 세이브 슬롯은 1개이고, 클라우드 동기화·친구 배틀·교환은 없습니다.
- 배틀 메시지는 잠깐 떠 있다가 넘어가고, B를 누르면 바로 넘어갑니다.

## 다시 만들기 / 테스트 (`tools/`)

웹 게임의 밸런스나 포켓몬을 바꿨다면 데이터와 그림을 다시 뽑아야 합니다. node와 Pillow가 필요합니다.

```bash
python3 tools/build.py
```

배지 없이 Mac에서 게임 로직을 검사하는 봇도 있습니다. 가짜 배지 API 위에서 실제 코드를 돌립니다.

```bash
python3 tools/bots.py monkey 20
```

```bash
python3 tools/bots.py smart 1
```

`monkey`는 무작위 버튼으로 오류를 찾고, `smart`는 처음부터 메가뮤츠X를 잡을 때까지 실제로 플레이합니다.
