import { useEffect, useState } from "react";

import { api, type Article } from "../api";
import { Alert, Empty, humanise } from "../ui";

interface QuizSummary {
  id: number;
  title: string;
  category: string;
}

interface QuizQuestion {
  id: number;
  prompt: string;
  options: string[];
}

interface QuizDetail {
  id: number;
  title: string;
  questions: QuizQuestion[];
}

interface Feedback {
  question_id: number;
  selected_index: number | null;
  correct_index: number;
  is_correct: boolean;
  explanation: string | null;
}

interface AttemptResult {
  score: number;
  total: number;
  feedback: Feedback[];
}

export default function Awareness() {
  const [articles, setArticles] = useState<Article[] | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Article[]>("/articles")
      .then(setArticles)
      .catch((err) => setError((err as Error).message));
  }, []);

  return (
    <>
      <div className="page-head">
        <h1>Learn to spot a scam</h1>
        <p>
          The three patterns below catch most people. No account needed — read
          them, then test yourself.
        </p>
      </div>

      <Alert kind="error">{error}</Alert>

      <div className="split">
        <div>
          {articles === null ? (
            <div className="card">
              <p className="muted">Loading…</p>
            </div>
          ) : articles.length === 0 ? (
            <div className="card">
              <Empty>No awareness articles have been published yet.</Empty>
            </div>
          ) : (
            articles.map((article) => (
              <div className="card" key={article.id}>
                <span className="badge neutral">{humanise(article.category)}</span>
                <h3 style={{ margin: "10px 0 8px", fontSize: 17 }}>{article.title}</h3>
                <p style={{ margin: 0 }}>
                  {open === article.id
                    ? article.body
                    : `${article.body.slice(0, 130)}${article.body.length > 130 ? "…" : ""}`}
                </p>
                {article.body.length > 130 && (
                  <button
                    className="secondary small"
                    style={{ marginTop: 10 }}
                    onClick={() => setOpen(open === article.id ? null : article.id)}
                  >
                    {open === article.id ? "Show less" : "Read more"}
                  </button>
                )}
              </div>
            ))
          )}
        </div>

        <QuizPanel />
      </div>
    </>
  );
}

function QuizPanel() {
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<QuizSummary[]>("/quizzes")
      .then((list) => (list.length ? api.get<QuizDetail>(`/quizzes/${list[0].id}`) : null))
      .then((detail) => detail && setQuiz(detail))
      .catch((err) => setError((err as Error).message));
  }, []);

  async function submit() {
    if (!quiz) return;
    try {
      setResult(
        await api.post<AttemptResult>(`/quizzes/${quiz.id}/attempt`, {
          answers: Object.entries(answers).map(([question_id, selected_index]) => ({
            question_id: Number(question_id),
            selected_index,
          })),
        }),
      );
    } catch (err) {
      setError((err as Error).message);
    }
  }

  if (error) return <div className="card"><Alert kind="error">{error}</Alert></div>;
  if (!quiz) return <div className="card"><p className="muted">Loading quiz…</p></div>;

  const feedbackFor = (questionId: number) =>
    result?.feedback.find((f) => f.question_id === questionId);

  return (
    <div className="card">
      <h2>{quiz.title}</h2>

      {result && (
        <Alert kind={result.score === result.total ? "success" : "info"}>
          You scored {result.score} out of {result.total}.
        </Alert>
      )}

      {quiz.questions.map((question, index) => {
        const feedback = feedbackFor(question.id);
        return (
          <div key={question.id} style={{ marginBottom: 20 }}>
            <p style={{ fontWeight: 600, marginBottom: 10 }}>
              {index + 1}. {question.prompt}
            </p>
            {question.options.map((option, optionIndex) => {
              // After submitting, mark the right answer and the wrong pick --
              // the explanation matters more than the score.
              const tone = !feedback
                ? ""
                : optionIndex === feedback.correct_index
                  ? "correct"
                  : optionIndex === feedback.selected_index
                    ? "wrong"
                    : "";
              return (
                <label key={optionIndex} className={`quiz-option ${tone}`}>
                  <input
                    type="radio"
                    name={`q${question.id}`}
                    checked={answers[question.id] === optionIndex}
                    disabled={!!result}
                    onChange={() => setAnswers({ ...answers, [question.id]: optionIndex })}
                  />
                  <span>{option}</span>
                </label>
              );
            })}
            {feedback?.explanation && <p className="hint">{feedback.explanation}</p>}
          </div>
        );
      })}

      {result ? (
        <button
          className="secondary"
          onClick={() => {
            setResult(null);
            setAnswers({});
          }}
        >
          Try again
        </button>
      ) : (
        <button
          disabled={Object.keys(answers).length !== quiz.questions.length}
          onClick={submit}
        >
          Check my answers
        </button>
      )}
    </div>
  );
}
