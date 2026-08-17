# Kids Games

아이들을 위한 HTML 미니 게임 모음집입니다. 별도의 설치나 빌드 없이 브라우저에서 바로 플레이할 수 있습니다.

## 게임 목록

| 게임 | 폴더 | 설명 |
|------|------|------|
| 🔴 Pocket Mini Adventure | `pocket-mini-adventure/` | 포켓몬을 잡고 진화시켜 동굴 5개를 깨고 메가뮤츠X를 잡는 미니 게임 |
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
npm run serve
# 브라우저에서 http://localhost:8000 접속
```

## 호스팅

같은 파일들을 두 곳에서 서비스합니다. 어느 쪽 주소로 들어가도 게임은 동일합니다.

| 위치 | 주소 | 업데이트 방법 |
|------|------|--------------|
| GitHub Pages | https://ktho22.github.io/kids-games/ | `git push` 하면 자동 반영 |
| Netlify | 배포 후 발급되는 `*.netlify.app` 주소 | `npm run deploy` |

### Netlify에 올리기

처음 한 번만 로그인이 필요합니다. 아래 명령을 실행하면 브라우저가 열리고, 거기서 Netlify 계정으로 승인하면 됩니다.

```bash
npm run login
```

이후에는 배포 명령 한 줄이면 새 게임이나 수정 사항이 반영됩니다.

```bash
npm run deploy
```

라이브 주소를 건드리지 않고 먼저 확인만 하고 싶다면 미리보기 배포를 씁니다. 비공개 임시 URL이 발급됩니다.

```bash
npm run preview
```

CLI 없이 올리고 싶다면 [app.netlify.com/drop](https://app.netlify.com/drop) 에 이 폴더를 그대로 끌어다 놓아도 됩니다.

> **게임 저장 데이터는 주소별로 따로 보관됩니다.** 브라우저가 사이트마다 저장 공간을 분리하기 때문에, GitHub Pages에서 하던 진행 상황이 Netlify 주소로 자동으로 넘어가지는 않습니다. Pocket Mini Adventure는 저장 슬롯의 📤 버튼으로 공유 코드를 복사해서, 새 주소에서 📥 로 붙여넣으면 그대로 이어서 할 수 있습니다.

## 기술 스택

- HTML / CSS / JavaScript (순수 바닐라)
- 각 게임은 단일 `index.html` 파일로 구성 (외부 의존성 없음)
- 모바일 터치 지원
