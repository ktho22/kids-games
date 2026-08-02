# Kids Games

아이들을 위한 HTML 미니 게임 모음집입니다. 별도의 설치나 빌드 없이 브라우저에서 바로 플레이할 수 있습니다.

## 게임 목록

| 게임 | 폴더 | 설명 |
|------|------|------|
| ⚡ 피카츄 미로 탈출 | `pikachu-maze/` | 방향키로 피카츄를 움직여 집까지 탈출하는 미로 게임 (스테이지마다 미로가 커짐) |
| 🏗️ Block Builder v2 | `block-game-v2/` | 동물, 장식, 미션, 세이브 슬롯이 추가된 블록 빌더 |
| 🧱 Block Builder | `block-game/` | Marvel x Minecraft 스타일 블록 빌딩 게임 |
| 🐙 Octonaut Animal Rescue | `octonaut-game/` | 옥토넛 크루와 함께 바다 동물을 구조하는 게임 |
| ⛏️ Minecraft Block Dodge | `minecraft-dodge/` | 떨어지는 블록을 피하는 마인크래프트 마블 에디션 |
| ⭐ Star Adventure | `english-math-game/` | 우주 모험을 통해 영어와 수학을 배우는 학습 게임 |
| 🏎️ Mini Car Race | `minicar-race/` | 나만의 미니카를 만들고 레이싱하는 게임 |
| 🏥 동물 병원 놀이 | `hospital-game/` | 아픈 동물 친구들을 진찰하고 치료해주는 놀이 |
| 🃏 Flip Card Quiz | `flip-card-quiz/` | 카드를 뒤집어 50가지 동물 수수께끼를 푸는 퀴즈 |

## 실행 방법

`index.html` 파일을 브라우저에서 열면 게임 목록이 표시됩니다. 카드를 탭하면 해당 게임이 시작됩니다.

```bash
# 로컬 서버로 실행 (선택)
python3 -m http.server 8000
# 브라우저에서 http://localhost:8000 접속
```

## 기술 스택

- HTML / CSS / JavaScript (순수 바닐라)
- 각 게임은 단일 `index.html` 파일로 구성 (외부 의존성 없음)
- 모바일 터치 지원
