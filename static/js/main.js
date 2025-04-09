// 탭 전환 기능
document.addEventListener('DOMContentLoaded', function() {
    // 인증 탭
    const authTabs = document.querySelectorAll('.auth-tabs li');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (authTabs.length > 0) {
        authTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                // 모든 탭에서 active 클래스 제거
                authTabs.forEach(t => t.classList.remove('active'));
                
                // 클릭한 탭에 active 클래스 추가
                this.classList.add('active');
                
                // 모든 탭 컨텐츠 숨기기
                tabContents.forEach(content => content.classList.remove('active'));
                
                // 해당 탭 컨텐츠 보이기
                const target = this.querySelector('a').getAttribute('href').replace('#', '');
                document.getElementById(target).classList.add('active');
            });
        });
    }
    
    // 댓글 답글 토글
    const replyButtons = document.querySelectorAll('.reply-button');
    if (replyButtons.length > 0) {
        replyButtons.forEach(button => {
            button.addEventListener('click', function() {
                const replyForm = this.nextElementSibling;
                if (replyForm.style.display === 'none' || replyForm.style.display === '') {
                    replyForm.style.display = 'block';
                } else {
                    replyForm.style.display = 'none';
                }
            });
        });
    }
});