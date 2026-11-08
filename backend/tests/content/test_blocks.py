import pytest

from app.modules.content.blocks import youtube_id


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?si=abc",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        " https://youtu.be/dQw4w9WgXcQ ",
    ],
)
def test_youtube_id_from_known_addresses(url: str) -> None:
    assert youtube_id(url) == "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        "https://vimeo.com/123456",
        "https://www.youtube.com/watch?v=short",
        "https://www.youtube.com/channel/UC123",
        "https://youtube.com.evil.pl/watch?v=dQw4w9WgXcQ",
        "javascript:alert(1)",
        "dQw4w9WgXcQ",
    ],
)
def test_youtube_id_rejects_other_addresses(url: str) -> None:
    assert youtube_id(url) is None
