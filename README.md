# Quoridor Pathfinding Comparison — Web Edition

브라우저에서 바로 실행하는 BFS, DFS, Dijkstra, A* 경로 탐색 비교 대시보드입니다.

## 실행

`index.html` 파일을 더블클릭하거나 GitHub Pages로 배포한 주소에 접속합니다. 별도의 설치가 필요 없습니다.

## GitHub Pages 배포

1. GitHub 저장소에 `index.html` 파일을 업로드합니다.
2. 저장소의 **Settings → Pages**에서 **Build and deployment → Deploy from a branch**를 선택합니다.
3. Branch를 `main`, 폴더를 `/(root)`로 지정하고 **Save**를 누릅니다.
4. Pages에 표시된 주소를 카카오톡 단체방에 공유합니다.

## 기능

- 19×19 격자 장애물 편집, 출발점/목적지 이동, 랜덤/예시 맵
- BFS, DFS, Dijkstra, A* 동일 조건 비교
- 네 알고리즘의 4분할 동시 탐색 애니메이션
- 경로 길이(칸), 방문 노드 수, 탐색 계산 시간(ms) 그래프
- 결과 CSV 저장

주의: 애니메이션 재생 속도는 실제 탐색 계산 시간과 다릅니다. 이동 비용이 동일하므로 BFS, Dijkstra, A*는 최단 경로 길이가 같습니다.
