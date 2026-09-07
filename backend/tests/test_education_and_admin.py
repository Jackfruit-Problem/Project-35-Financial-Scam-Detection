"""Awareness content, quizzes and administration. REQ-20 to REQ-25."""
from app.models.education import AwarenessContent, Quiz, QuizQuestion
from app.models.enums import Role


def _seed_article(db_session, category: str = "phishing", published: bool = True):
    article = AwarenessContent(
        title="Why no bank will ever ask for your OTP",
        category=category,
        body="An OTP proves that you approved a transaction. Nobody else needs it.",
        is_published=published,
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article


def _seed_quiz(db_session):
    quiz = Quiz(title="Can you spot a scam?", category="phishing")
    db_session.add(quiz)
    db_session.flush()
    question = QuizQuestion(
        quiz_id=quiz.id,
        prompt="A caller asks for your OTP. What do you do?",
        options="Read it out\nHang up and call the number on your card",
        correct_index=1,
        explanation="No bank employee ever needs your OTP.",
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(quiz)
    db_session.refresh(question)
    return quiz, question


def test_guest_can_read_articles(client, db_session):
    """REQ-20 and SRS 2.3: awareness content is the Guest class's whole purpose."""
    _seed_article(db_session)
    response = client.get("/api/v1/articles")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_articles_filter_by_category(client, db_session):
    _seed_article(db_session, category="phishing")
    _seed_article(db_session, category="upi_fraud")

    response = client.get("/api/v1/articles", params={"category": "upi_fraud"})
    assert [a["category"] for a in response.json()] == ["upi_fraud"]


def test_unpublished_articles_are_hidden(client, db_session):
    article = _seed_article(db_session, published=False)
    assert client.get("/api/v1/articles").json() == []
    assert client.get(f"/api/v1/articles/{article.id}").status_code == 404


def test_only_admin_creates_articles(client, make_user, auth_headers):
    """REQ-22."""
    make_user("victim@example.com")
    make_user("admin@example.com", Role.ADMIN)
    payload = {"title": "Fake loan apps", "category": "loan_app", "body": "Check the RBI register."}

    assert client.post(
        "/api/v1/articles", json=payload, headers=auth_headers("victim@example.com")
    ).status_code == 403

    created = client.post(
        "/api/v1/articles", json=payload, headers=auth_headers("admin@example.com")
    )
    assert created.status_code == 201
    assert created.json()["title"] == "Fake loan apps"


def test_admin_can_unpublish_an_article(client, make_user, auth_headers, db_session):
    article = _seed_article(db_session)
    make_user("admin@example.com", Role.ADMIN)

    response = client.patch(
        f"/api/v1/articles/{article.id}",
        json={"is_published": False},
        headers=auth_headers("admin@example.com"),
    )
    assert response.status_code == 200
    assert client.get("/api/v1/articles").json() == []


def test_quiz_never_exposes_the_answers(client, db_session):
    """Returning correct_index would make the quiz pointless."""
    quiz, _ = _seed_quiz(db_session)
    body = client.get(f"/api/v1/quizzes/{quiz.id}").json()

    assert body["questions"][0]["options"] == [
        "Read it out",
        "Hang up and call the number on your card",
    ]
    assert "correct_index" not in body["questions"][0]


def test_quiz_scores_and_explains(client, db_session):
    """REQ-21: scored, with an explanation returned either way."""
    quiz, question = _seed_quiz(db_session)

    correct = client.post(
        f"/api/v1/quizzes/{quiz.id}/attempt",
        json={"answers": [{"question_id": question.id, "selected_index": 1}]},
    ).json()
    assert correct["score"] == 1
    assert correct["total"] == 1
    assert correct["feedback"][0]["is_correct"] is True
    assert correct["feedback"][0]["explanation"]

    wrong = client.post(
        f"/api/v1/quizzes/{quiz.id}/attempt",
        json={"answers": [{"question_id": question.id, "selected_index": 0}]},
    ).json()
    assert wrong["score"] == 0
    # The teaching moment matters more than the mark.
    assert wrong["feedback"][0]["explanation"]


def test_unanswered_question_scores_zero_without_erroring(client, db_session):
    quiz, _ = _seed_quiz(db_session)
    result = client.post(f"/api/v1/quizzes/{quiz.id}/attempt", json={"answers": []}).json()
    assert result["score"] == 0
    assert result["feedback"][0]["selected_index"] is None


def test_admin_routes_are_closed_to_everyone_else(client, make_user, auth_headers):
    make_user("victim@example.com")
    make_user("inv@example.com", Role.INVESTIGATOR)

    for email in ("victim@example.com", "inv@example.com"):
        assert client.get(
            "/api/v1/admin/users", headers=auth_headers(email)
        ).status_code == 403
    assert client.get("/api/v1/admin/users").status_code == 401


def test_admin_can_change_a_role(client, make_user, auth_headers):
    """REQ-23: the only route from victim to staff."""
    make_user("admin@example.com", Role.ADMIN)
    target = make_user("newstaff@example.com")

    response = client.patch(
        f"/api/v1/admin/users/{target.id}/role",
        json={"role": Role.INVESTIGATOR},
        headers=auth_headers("admin@example.com"),
    )
    assert response.status_code == 200
    assert response.json()["role"] == Role.INVESTIGATOR


def test_admin_can_deactivate_a_user(client, make_user, auth_headers):
    make_user("admin@example.com", Role.ADMIN)
    target = make_user("spammer@example.com")

    response = client.patch(
        f"/api/v1/admin/users/{target.id}/active",
        params={"is_active": False},
        headers=auth_headers("admin@example.com"),
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_last_administrator_cannot_be_deactivated(client, make_user, auth_headers):
    """Otherwise nobody is left who can reactivate anyone, including them."""
    admin = make_user("admin@example.com", Role.ADMIN)

    response = client.patch(
        f"/api/v1/admin/users/{admin.id}/active",
        params={"is_active": False},
        headers=auth_headers("admin@example.com"),
    )
    assert response.status_code == 409


def test_second_admin_makes_deactivation_possible(client, make_user, auth_headers):
    admin = make_user("admin@example.com", Role.ADMIN)
    make_user("admin2@example.com", Role.ADMIN)

    response = client.patch(
        f"/api/v1/admin/users/{admin.id}/active",
        params={"is_active": False},
        headers=auth_headers("admin2@example.com"),
    )
    assert response.status_code == 200


def test_blacklist_entries_are_normalised(client, make_user, auth_headers):
    """REQ-25: detection does an exact match, so casing must not create a bypass."""
    make_user("admin@example.com", Role.ADMIN)
    headers = auth_headers("admin@example.com")

    created = client.post(
        "/api/v1/admin/blacklist",
        json={"entry_type": "upi_id", "value": "  Fraudster@YBL  ", "note": "reported"},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["value"] == "fraudster@ybl"


def test_duplicate_blacklist_entry_is_rejected(client, make_user, auth_headers):
    make_user("admin@example.com", Role.ADMIN)
    headers = auth_headers("admin@example.com")
    payload = {"entry_type": "upi_id", "value": "fraudster@ybl"}

    assert client.post("/api/v1/admin/blacklist", json=payload, headers=headers).status_code == 201
    assert client.post("/api/v1/admin/blacklist", json=payload, headers=headers).status_code == 409


def test_blacklisted_value_is_used_by_detection(client, make_user, auth_headers):
    """The admin screen and the detection engine share one list, not two."""
    make_user("admin@example.com", Role.ADMIN)
    make_user("victim@example.com")
    client.post(
        "/api/v1/admin/blacklist",
        json={"entry_type": "upi_id", "value": "mule@okaxis"},
        headers=auth_headers("admin@example.com"),
    )

    result = client.post(
        "/api/v1/detection/analyse",
        json={"text": "send the refund to mule@okaxis"},
        headers=auth_headers("victim@example.com"),
    ).json()
    assert result["matched_blacklist"] is True
    assert result["risk_score"] == 100


def test_blacklist_entry_can_be_removed(client, make_user, auth_headers):
    """Unlike evidence: a wrongly listed UPI ID belongs to a real person."""
    make_user("admin@example.com", Role.ADMIN)
    headers = auth_headers("admin@example.com")
    entry_id = client.post(
        "/api/v1/admin/blacklist",
        json={"entry_type": "phone", "value": "9812345678"},
        headers=headers,
    ).json()["id"]

    assert client.delete(f"/api/v1/admin/blacklist/{entry_id}", headers=headers).status_code == 204
    assert client.get("/api/v1/admin/blacklist", headers=headers).json() == []


def test_analytics_on_an_empty_system_does_not_divide_by_zero(
    client, make_user, auth_headers
):
    """REQ-24: a fresh install shows zeroes, not a 500."""
    make_user("admin@example.com", Role.ADMIN)
    body = client.get("/api/v1/admin/analytics", headers=auth_headers("admin@example.com")).json()

    assert body["total_reports"] == 0
    assert body["resolution_rate"] == 0.0
    assert body["recovery_rate"] == 0.0


def test_analytics_counts_reports_and_categories(client, make_user, auth_headers):
    """REQ-24."""
    make_user("admin@example.com", Role.ADMIN)
    make_user("victim@example.com")
    victim = auth_headers("victim@example.com")

    for category in ("upi_fraud", "upi_fraud", "phishing"):
        client.post(
            "/api/v1/reports",
            json={
                "reporter_name": "Asha Rao",
                "reporter_contact": "9876543210",
                "category": category,
                "description": "A description of the incident.",
                "amount_involved": 1000,
            },
            headers=victim,
        )

    body = client.get("/api/v1/admin/analytics", headers=auth_headers("admin@example.com")).json()
    assert body["total_reports"] == 3
    assert body["total_cases"] == 3
    assert body["trending_categories"][0] == {"category": "upi_fraud", "count": 2}
