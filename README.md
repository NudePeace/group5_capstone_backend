# 5th-group-Capstone-Design
요구한 기능이 추가되었습니다.

smtp_utils.py 관련 사항
- sender_email과 sender_password 항목은 실제로 인증메일을 보낼 구글 계정으로 수정해야 합니다.
- sender_password는 sender_email에 입력한 구글 계정의 비밀번호를 입력하시면 됩니다.

챗봇  api 코드 중에서 pydub을 사용하고 있는데, 이 기능은 파이썬 3.12부터 지원하지 않습니다.
파이썬 환경을 3.11 이하로 구동해주세요.
