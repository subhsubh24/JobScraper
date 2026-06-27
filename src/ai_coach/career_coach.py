"""AI Career Coach - Chat interface for career guidance."""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from src.db.models import ChatMessage, User, JobPosting, Application
from src.llm import get_llm_client, llm_available, chat_model


class CareerCoach:
    """AI-powered career coaching through a chat interface."""

    MODEL = chat_model()
    MAX_CONTEXT_MESSAGES = 20

    SYSTEM_PROMPT = """You are an expert career coach specializing in tech careers. You help professionals:
- Navigate job searches effectively
- Prepare for interviews
- Negotiate salaries
- Make career decisions
- Build their professional brand

Your style:
- Be direct and actionable
- Give specific advice, not generic platitudes
- Ask clarifying questions when needed
- Reference their resume and job applications when relevant
- Be encouraging but honest

You have access to the user's profile and job applications for context."""

    def __init__(self, db: Session):
        self.db = db
        self.client = get_llm_client()

    @staticmethod
    def available() -> bool:
        """Whether the coach can call the LLM (key configured)."""
        return llm_available()

    def _get_user_context(self, user: User) -> str:
        """Build context string from user's profile and applications."""
        context_parts = []

        # User profile
        if user.full_name:
            context_parts.append(f"User: {user.full_name}")

        if user.resume_text:
            # Truncate resume for context
            resume_preview = user.resume_text[:1500]
            context_parts.append(f"Resume Summary:\n{resume_preview}")

        # Recent applications
        applications = self.db.query(Application).filter(
            Application.user_id == user.id
        ).order_by(Application.created_at.desc()).limit(5).all()

        if applications:
            context_parts.append("\nRecent Applications:")
            for app in applications:
                job = self.db.query(JobPosting).get(app.job_id)
                if job:
                    context_parts.append(
                        f"- {job.title} at {job.company_name} ({app.status.value})"
                    )

        return "\n".join(context_parts)

    def _get_conversation_history(
        self,
        user: User,
        session_id: str,
        limit: int = None
    ) -> List[dict]:
        """Get recent conversation history for context."""
        limit = limit or self.MAX_CONTEXT_MESSAGES

        messages = self.db.query(ChatMessage).filter(
            ChatMessage.user_id == user.id,
            ChatMessage.session_id == session_id,
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

        # Reverse to get chronological order
        messages = list(reversed(messages))

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    def chat(
        self,
        user: User,
        message: str,
        session_id: Optional[str] = None,
        job_context: Optional[JobPosting] = None
    ) -> str:
        """Send a message and get a response from the coach."""
        if self.client is None:
            raise RuntimeError("GEMINI_API_KEY not configured")

        # Create session if needed
        if not session_id:
            session_id = str(uuid.uuid4())

        # Build system prompt with context
        user_context = self._get_user_context(user)
        system_content = f"{self.SYSTEM_PROMPT}\n\n--- USER CONTEXT ---\n{user_context}"

        if job_context:
            system_content += "\n\n--- CURRENT JOB FOCUS ---\n"
            system_content += f"Title: {job_context.title}\n"
            system_content += f"Company: {job_context.company_name}\n"
            system_content += f"Description: {job_context.description[:500] if job_context.description else 'N/A'}"

        # Get conversation history
        history = self._get_conversation_history(user, session_id)

        # Build messages for API
        messages = [{"role": "system", "content": system_content}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        # Call LLM
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )

        assistant_message = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else None

        # Save messages to database
        user_msg = ChatMessage(
            user_id=user.id,
            role="user",
            content=message,
            session_id=session_id,
            job_id=job_context.id if job_context else None,
        )
        self.db.add(user_msg)

        assistant_msg = ChatMessage(
            user_id=user.id,
            role="assistant",
            content=assistant_message,
            session_id=session_id,
            job_id=job_context.id if job_context else None,
            tokens_used=tokens_used,
        )
        self.db.add(assistant_msg)
        self.db.flush()

        return assistant_message

    def get_suggested_questions(self, user: User) -> List[str]:
        """Get suggested questions based on user's situation."""
        # Check user's current state
        applications = self.db.query(Application).filter(
            Application.user_id == user.id
        ).all()

        suggestions = []

        if not applications:
            suggestions = [
                "How do I optimize my resume for ATS systems?",
                "What's the best strategy for finding remote jobs?",
                "How many jobs should I apply to per week?",
                "Should I use a cover letter for every application?",
            ]
        else:
            # Check for interviews
            interviewing = [a for a in applications if a.status.value in ["phone_screen", "interview"]]
            if interviewing:
                suggestions = [
                    "How do I prepare for a technical interview?",
                    "What questions should I ask the interviewer?",
                    "How do I handle behavioral interview questions?",
                    "What should I wear to a video interview?",
                ]
            else:
                suggestions = [
                    "How can I improve my application response rate?",
                    "Should I follow up on my applications?",
                    "How do I network effectively on LinkedIn?",
                    "What skills should I learn to be more competitive?",
                ]

        return suggestions

    def get_session_summary(self, user: User, session_id: str) -> str:
        """Get a summary of a coaching session."""
        messages = self._get_conversation_history(user, session_id, limit=50)

        if len(messages) < 2:
            return "Session too short to summarize."

        conversation_text = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in messages
        ])

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Summarize this career coaching session in 3-4 bullet "
                        "points. Focus on key advice given and action items."
                    ),
                },
                {"role": "user", "content": conversation_text}
            ],
            temperature=0.5,
            max_tokens=300,
        )

        return response.choices[0].message.content
