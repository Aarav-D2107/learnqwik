"""Shared fixtures. No network, no live AI, no real Supabase."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def questions():
    """A mixed-difficulty question set: weights 1.0 + 1.5 + 2.0 = 4.5."""
    return [
        {"id": "q1", "difficulty": "Easy", "correct_index": 1,
         "question": "Easy one", "options": ["a", "b", "c", "d"]},
        {"id": "q2", "difficulty": "Medium", "correct_index": 0,
         "question": "Medium one", "options": ["a", "b", "c", "d"]},
        {"id": "q3", "difficulty": "Hard", "correct_index": 2,
         "question": "Hard one", "options": ["a", "b", "c", "d"]},
    ]


@pytest.fixture
def subject():
    return {"id": "java", "name": "Java", "tagline": "OOP on the JVM", "position": 0}


@pytest.fixture
def topics():
    names = [
        ("java-fundamentals", "Java Fundamentals"),
        ("java-oop", "Object-Oriented Programming"),
        ("java-inheritance", "Inheritance and Polymorphism"),
        ("java-exceptions", "Exception Handling"),
        ("java-collections", "Collections Framework"),
        ("java-threads", "Multithreading"),
    ]
    out = []
    for i, (tid, name) in enumerate(names):
        out.append({
            "id": tid, "subject_id": "java", "name": name, "position": i,
            "estimated_minutes": 30,
            "prerequisite_topic_ids": [names[i - 1][0]] if i else [],
        })
    return out


@pytest.fixture
def resources():
    return [
        {"id": "r1", "topic_id": "java-exceptions", "title": "Java Exceptions, Explained Simply",
         "type": "Article", "difficulty": "Easy", "duration_minutes": 8, "rating": 4.6},
        {"id": "r2", "topic_id": "java-exceptions", "title": "Try/Catch Deep Dive",
         "type": "Video", "difficulty": "Medium", "duration_minutes": 14, "rating": 4.4},
        {"id": "r4", "topic_id": "java-exceptions", "title": "10 Exception Handling Drills",
         "type": "Practice", "difficulty": "Hard", "duration_minutes": 20, "rating": 4.5},
        {"id": "r5", "topic_id": "java-collections", "title": "Java Collections Field Guide",
         "type": "Documentation", "difficulty": "Medium", "duration_minutes": 12, "rating": 4.5},
    ]


@pytest.fixture
def mastery_rows():
    """The exact scenario from the product brief."""
    data = {
        "java-fundamentals": 88, "java-oop": 81, "java-inheritance": 76,
        "java-exceptions": 32, "java-collections": 55, "java-threads": 70,
    }
    return [
        {"topic_id": tid, "subject_id": "java", "mastery_pct": pct, "attempts_count": 1}
        for tid, pct in data.items()
    ]


class MockAIProvider:
    """Stands in for a real provider. Tests never need live credentials."""

    def __init__(self, text_response=None, structured_response=None, image_response=None,
                 fail_with=None):
        self.text_response = text_response or "A mocked explanation."
        self.structured_response = structured_response or {}
        self.image_response = image_response or "A mocked vision analysis."
        self.fail_with = fail_with
        self.calls = []

    async def generate_text(self, prompt, system=None, max_tokens=None, temperature=0.3):
        self.calls.append(("generate_text", prompt))
        if self.fail_with:
            raise self.fail_with
        return self.text_response

    async def generate_structured_output(self, prompt, system=None, max_tokens=None):
        self.calls.append(("generate_structured_output", prompt))
        if self.fail_with:
            raise self.fail_with
        return self.structured_response

    async def analyze_image(self, image_bytes, prompt, media_type="image/png", system=None):
        self.calls.append(("analyze_image", len(image_bytes)))
        if self.fail_with:
            raise self.fail_with
        return self.image_response

    async def create_embedding(self, text):
        self.calls.append(("create_embedding", text))
        return [0.1] * 8


@pytest.fixture
def mock_provider():
    return MockAIProvider
