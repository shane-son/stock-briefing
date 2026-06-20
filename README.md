# Stock Briefing Email Automation

PC를 켜두지 않아도 GitHub Actions에서 평일 주식 뉴스 브리핑을 생성해 Gmail로 전송하는 자동화입니다.

## 실행 일정

- 월-금 08:05 KST
- 월-금 22:05 KST
- GitHub Actions의 `workflow_dispatch`로 수동 실행 가능

## 필요한 GitHub Secrets

Repository Settings > Secrets and variables > Actions > New repository secret 에 아래 값을 등록하세요.

- `OPENAI_API_KEY`: OpenAI API 키
- `SMTP_USER`: 발송 Gmail 주소, 예: `qpwlem98@gmail.com`
- `SMTP_APP_PASSWORD`: Gmail 앱 비밀번호
- `MAIL_TO`: 수신 이메일 주소, 예: `qpwlem98@gmail.com`

## 참고

이 저장소가 public이어도 Secrets 값은 코드에 저장되지 않습니다. 다만 앱 비밀번호나 API 키는 채팅/README/코드에 직접 적지 마세요.
