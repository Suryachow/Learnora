"""The shipped catalogue has to be complete and gradeable.

Every lesson must carry a video (the quiz gate depends on it) and one quiz whose
questions can actually be marked. These checks run without a database, so a
typo in a lesson module fails the suite rather than the product.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.catalogue import CATALOGUE  # noqa: E402
from scripts.catalogue.helpers import EMBED  # noqa: E402


def test_catalogue_teaches_exactly_c_and_python():
    assert [course["category"] for course in CATALOGUE] == ["C", "Python"]
    assert [course["title"] for course in CATALOGUE] == ["C Programming", "Python Programming"]


def test_each_course_is_a_full_syllabus():
    for course in CATALOGUE:
        assert course["description"].strip()
        assert len(course["topics"]) >= 15, course["title"]
        titles = [topic["title"] for topic in course["topics"]]
        assert len(set(titles)) == len(titles), f"duplicate lesson title in {course['title']}"


def test_each_course_has_its_price():
    prices = {course["category"]: course["price_paise"] for course in CATALOGUE}
    assert prices == {"C": 34900, "Python": 34900}


def test_every_lesson_has_a_video_and_notes():
    for course in CATALOGUE:
        for topic in course["topics"]:
            assert topic["video_url"].startswith(f"{EMBED}/"), topic["title"]
            assert len(topic["content"]) > 200, f"{topic['title']} needs real notes"


def test_every_lesson_has_one_markable_quiz():
    for course in CATALOGUE:
        for topic in course["topics"]:
            assert len(topic["tasks"]) == 1, topic["title"]
            task = topic["tasks"][0]
            assert 0 <= task["pass_percent"] <= 100
            assert 0 <= task["reward"] <= 20000, "reward must stay inside the platform cap"

            questions = task["questions"]
            assert len(questions) >= 4, f"{topic['title']} needs at least four questions"
            prompts = [question["prompt"] for question in questions]
            assert len(set(prompts)) == len(prompts), f"duplicate prompt in {topic['title']}"

            for question in questions:
                options = question["options"]
                assert len(options) == 4, question["prompt"]
                assert len(set(options)) == 4, f"options repeat in: {question['prompt']}"
                assert all(option.strip() for option in options), question["prompt"]
                assert 0 <= question["correct_index"] < 4, question["prompt"]
