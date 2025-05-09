from django.core.management.base import BaseCommand
from blog.models import Post


class Command(BaseCommand):
    help = "기존 게시글의 slug에 'pn_' 접두사를 추가합니다."

    def handle(self, *args, **options):
        posts = Post.objects.all()
        updated_count = 0

        for post in posts:
            # 이미 'pn_'으로 시작하는 slug는 건너뜁니다
            if not post.slug.startswith("pn_"):
                # 중복 방지를 위해 임시로 다른 값으로 설정
                old_slug = post.slug
                post.slug = f"temp_{old_slug}"
                post.save(update_fields=["slug"])

                # 'pn_' 접두사 추가
                post.slug = f"pn_{old_slug}"
                post.save(update_fields=["slug"])
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"성공적으로 {updated_count}개의 게시글 slug가 업데이트되었습니다."
            )
        )
