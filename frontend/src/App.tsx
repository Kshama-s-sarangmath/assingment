import { FormEvent, startTransition, useDeferredValue, useEffect, useState } from "react";

type LearningResponse = {
  type: "search" | "enroll" | "enrolled" | "enrollment_list" | "unenroll" | "unenrolled" | "answer";
  title: string;
  learning_ids: string[];
  message: string;
  next_step_questions: string[];
};

type StreamEvent =
  | { type: "chunk"; text: string }
  | { type: "tool"; name: string }
  | { type: "result"; response: LearningResponse };

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  response?: LearningResponse;
  status?: string;
};

const starterPrompts = [
  "I want to learn machine learning",
  "Only beginner ones under 5 hours",
  "What's trending?",
  "What am I enrolled in?"
];

function getSessionId() {
  const existing = localStorage.getItem("minilearn-session-id");
  if (existing) {
    return existing;
  }
  const created = crypto.randomUUID();
  localStorage.setItem("minilearn-session-id", created);
  return created;
}

export default function App() {
  const [sessionId, setSessionId] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: crypto.randomUUID(),
      role: "assistant",
      text: "Ask about skills, filters, enrollments, or trending courses.",
      response: {
        type: "answer",
        title: "MiniLearn is ready",
        learning_ids: [],
        message: "Try a topic like machine learning, React, cloud, or analytics.",
        next_step_questions: starterPrompts.slice(0, 3)
      }
    }
  ]);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    setSessionId(getSessionId());
  }, []);

  const deferredMessages = useDeferredValue(messages);

  async function sendMessage(message: string) {
    if (!message.trim() || !sessionId || isSending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: message.trim()
    };
    const assistantId = crypto.randomUUID();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      text: "",
      status: "Thinking"
    };

    startTransition(() => {
      setMessages((current) => [...current, userMessage, assistantMessage]);
      setInput("");
    });

    setIsSending(true);
    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId, message })
      });

      if (!response.ok || !response.body) {
        throw new Error("Streaming request failed.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.trim()) {
            continue;
          }

          const event = JSON.parse(line) as StreamEvent;
          if (event.type === "chunk") {
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? { ...item, text: `${item.text}${event.text}`, status: "Streaming" }
                  : item
              )
            );
          }

          if (event.type === "tool") {
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId ? { ...item, status: `Using ${event.name}` } : item
              )
            );
          }

          if (event.type === "result") {
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? {
                      ...item,
                      text: event.response.message,
                      response: event.response,
                      status: event.response.type
                    }
                  : item
              )
            );
          }
        }
      }
    } catch (error) {
      const messageText = error instanceof Error ? error.message : "Unknown error";
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantId
            ? {
                ...item,
                text: "MiniLearn could not complete that request.",
                status: messageText
              }
            : item
        )
      );
    } finally {
      setIsSending(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendMessage(input);
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Learning Discovery Agent</p>
          <h1>MiniLearn pairs a Strands agent with a streaming React workspace.</h1>
          <p className="subtitle">
            Search the catalog, refine filters, enroll, unenroll, and keep the conversation alive across turns.
          </p>
        </div>
        <div className="hero-card">
          <span>Session</span>
          <strong>{sessionId || "Preparing..."}</strong>
          <p>Ask for courses, say “the second one”, or switch to trending recommendations.</p>
        </div>
      </header>

      <main className="workspace">
        <section className="prompt-rail">
          <h2>Try a live flow</h2>
          {starterPrompts.map((prompt) => (
            <button key={prompt} className="chip" onClick={() => void sendMessage(prompt)} disabled={isSending}>
              {prompt}
            </button>
          ))}
        </section>

        <section className="chat-panel">
          <div className="messages">
            {deferredMessages.map((message) => (
              <article key={message.id} className={`bubble bubble-${message.role}`}>
                <div className="bubble-meta">
                  <span>{message.role === "user" ? "Learner" : "MiniLearn"}</span>
                  {message.status ? <em>{message.status}</em> : null}
                </div>
                {message.response ? <h3>{message.response.title}</h3> : null}
                <p>{message.text}</p>
                {message.response?.learning_ids.length ? (
                  <div className="id-row">
                    {message.response.learning_ids.map((learningId) => (
                      <span key={learningId} className="id-pill">
                        {learningId}
                      </span>
                    ))}
                  </div>
                ) : null}
                {message.response?.next_step_questions.length ? (
                  <div className="followups">
                    {message.response.next_step_questions.map((question) => (
                      <button
                        key={question}
                        className="followup"
                        onClick={() => void sendMessage(question)}
                        disabled={isSending}
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Find me beginner machine learning courses under 5 hours"
              rows={3}
            />
            <button type="submit" disabled={isSending || !input.trim()}>
              {isSending ? "Streaming..." : "Send"}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
