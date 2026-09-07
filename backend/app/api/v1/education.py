"""Awareness content and quizzes. REQ-20, REQ-21, REQ-22.

Articles and quizzes are readable without an account: SRS 2.3 defines a Guest
class whose whole purpose is to read this material, and a scam-awareness page
that demands a login helps nobody.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user, require_roles
from app.db.session import get_db
from app.models.education import AwarenessContent, Quiz, QuizAttempt, QuizQuestion
from app.models.enums import Role
from app.models.user import User
from app.schemas import (
    ArticleCreate,
    ArticleOut,
    ArticleUpdate,
    QuizAttemptResult,
    QuizDetail,
    QuizOut,
    QuizSubmission,
)

router = APIRouter(tags=["education"])


@router.get("/articles", response_model=list[ArticleOut])
def list_articles(
    category: str | None = None, db: Session = Depends(get_db)
) -> list[AwarenessContent]:
    """REQ-20: categorised awareness articles, open to guests."""
    query = select(AwarenessContent).where(AwarenessContent.is_published.is_(True))
    if category:
        query = query.where(AwarenessContent.category == category)
    return list(db.scalars(query.order_by(AwarenessContent.id.desc())).all())


@router.get("/articles/{article_id}", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)) -> AwarenessContent:
    article = db.get(AwarenessContent, article_id)
    if article is None or not article.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article


@router.post(
    "/articles",
    response_model=ArticleOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def create_article(
    payload: ArticleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_optional_user),
) -> AwarenessContent:
    """REQ-22: administrators create awareness content."""
    article = AwarenessContent(
        title=payload.title,
        category=payload.category,
        body=payload.body,
        author_id=user.id if user else None,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.patch(
    "/articles/{article_id}",
    response_model=ArticleOut,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def update_article(
    article_id: int, payload: ArticleUpdate, db: Session = Depends(get_db)
) -> AwarenessContent:
    """REQ-22: edit or unpublish. Unpublishing is how content is removed --
    an article cited in a case should not vanish from the record."""
    article = db.get(AwarenessContent, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)
    return article


@router.get("/quizzes", response_model=list[QuizOut])
def list_quizzes(db: Session = Depends(get_db)) -> list[Quiz]:
    return list(
        db.scalars(select(Quiz).where(Quiz.is_published.is_(True))).all()
    )


@router.get("/quizzes/{quiz_id}", response_model=QuizDetail)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)) -> QuizDetail:
    """Questions and options, without the answers -- those would make the
    quiz pointless to anyone who opened the network tab."""
    quiz = db.get(Quiz, quiz_id)
    if quiz is None or not quiz.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    questions = db.scalars(
        select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.id)
    ).all()

    return QuizDetail(
        id=quiz.id,
        title=quiz.title,
        category=quiz.category,
        questions=[
            {"id": q.id, "prompt": q.prompt, "options": q.options.split("\n")}
            for q in questions
        ],
    )


@router.post("/quizzes/{quiz_id}/attempt", response_model=QuizAttemptResult)
def submit_quiz(
    quiz_id: int,
    payload: QuizSubmission,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> QuizAttemptResult:
    """REQ-21: score the attempt and explain every answer.

    The explanation is returned whether the answer was right or wrong -- the
    point of the feature is to teach scam recognition, not to grade people.
    """
    quiz = db.get(Quiz, quiz_id)
    if quiz is None or not quiz.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    questions = list(
        db.scalars(
            select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.id)
        ).all()
    )
    answers = {a.question_id: a.selected_index for a in payload.answers}

    feedback = []
    score = 0
    for question in questions:
        selected = answers.get(question.id)
        correct = selected == question.correct_index
        score += 1 if correct else 0
        feedback.append(
            {
                "question_id": question.id,
                "prompt": question.prompt,
                "selected_index": selected,
                "correct_index": question.correct_index,
                "is_correct": correct,
                "explanation": question.explanation,
            }
        )

    db.add(
        QuizAttempt(
            quiz_id=quiz.id,
            user_id=user.id if user else None,
            score=score,
            total=len(questions),
        )
    )
    db.commit()

    return QuizAttemptResult(
        quiz_id=quiz.id, score=score, total=len(questions), feedback=feedback
    )
