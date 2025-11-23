import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, FEEDBACK_CATEGORIES

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

class FeedbackGenerator:
    def __init__(self, role, conversation_history, candidate_info=None):
        self.role = role
        
        # Handle both old format (list) and new format (dict with metadata)
        if isinstance(conversation_history, dict):
            self.conversation_history = conversation_history.get("messages", [])
            self.behavior_metadata = conversation_history.get("behavior_metadata", {})
        else:
            self.conversation_history = conversation_history
            self.behavior_metadata = {}
        
        self.candidate_info = candidate_info
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def generate_feedback(self):
        """Generate concise interview feedback with ratings and brief tips"""
        
        # Create conversation transcript
        transcript = self._format_transcript()
        
        # Build resume context if available
        resume_context = ""
        if self.candidate_info:
            resume_context = f"""

CANDIDATE BACKGROUND:
- Name: {self.candidate_info.get('name', 'Candidate')}
- Experience: {self.candidate_info.get('years_of_experience', 'Not specified')}
- Recent Role: {self.candidate_info.get('recent_job_title', 'Not specified')}
- Key Skills: {', '.join(self.candidate_info.get('skills', ['Not specified'])[:5])}
"""

        # Build behavior insights
        behavior_insights = ""
        user_persona = "Standard User"
        persona_notes = []
        
        if self.behavior_metadata:
            off_topic = self.behavior_metadata.get('off_topic_count', 0)
            confusion = self.behavior_metadata.get('confusion_indicators', 0)
            early_exit = self.behavior_metadata.get('user_requested_exit', False)
            duration_used = self.behavior_metadata.get('interview_duration_used', 0)
            
            # IDENTIFY USER PERSONA
            if off_topic >= 3:
                user_persona = "CHATTY USER"
                persona_notes.append("You frequently went off-topic or provided lengthy, unfocused answers")
                persona_notes.append("This indicates a tendency to provide excessive context or tangential information")
            elif off_topic >= 1:
                user_persona = "Moderately Talkative User"
                persona_notes.append("You occasionally went off-topic but generally stayed focused")
            
            if confusion >= 3:
                if user_persona != "CHATTY USER":
                    user_persona = "CONFUSED USER"
                else:
                    user_persona = "CHATTY & CONFUSED USER"
                persona_notes.append("You showed repeated confusion with interview questions")
                persona_notes.append("This suggests you may need more preparation or context about the role")
            elif confusion >= 1:
                if "Confused" not in user_persona:
                    persona_notes.append("You showed some uncertainty but recovered well")
            
            if early_exit:
                user_persona = "EARLY EXIT USER"
                persona_notes.append("You requested to end the interview before time was up")
                persona_notes.append("This may indicate nervousness, time constraints, or lack of preparation")
            
            if off_topic == 0 and confusion == 0 and not early_exit and len(self.conversation_history) >= 6:
                user_persona = "EFFICIENT USER"
                persona_notes.append("You provided focused, well-structured answers throughout")
                persona_notes.append("Your responses were clear and stayed on topic")
            
            # Build persona notes list
            persona_notes_text = '\n'.join([f'• {note}' for note in persona_notes])
            if not persona_notes_text:
                persona_notes_text = '• Standard interview behavior observed'
            
            behavior_insights = f"""

========================================
🎭 USER PERSONA DETECTED: {user_persona}
========================================

BEHAVIORAL ANALYSIS:
- Off-topic responses: {off_topic} times
- Confusion indicators: {confusion} times  
- Interview status: {'Early exit requested' if early_exit else 'Completed normally'}
- Time used: {duration_used:.1f} minutes

PERSONA CHARACTERISTICS:
{persona_notes_text}

CRITICAL INSTRUCTIONS FOR FEEDBACK:
1. START with a clear section identifying this user as a "{user_persona}"
2. Explain what this persona means and what behaviors you observed
3. Provide SPECIFIC advice tailored to this persona type
4. Reference exact moments from the interview that demonstrate this behavior

PERSONA-SPECIFIC ADVICE REQUIRED:

FOR CHATTY USER (off-topic ≥ 3):
- Emphasize the need for concise, focused answers
- Recommend the STAR method with strict time limits
- Practice 90-second answer technique
- Specific tip: "Your answer about [X] went off-topic when you mentioned [Y]"

FOR CONFUSED USER (confusion ≥ 3):
- Emphasize it's okay to ask clarifying questions
- Recommend researching common interview terminology
- Practice understanding technical concepts
- Specific tip: "When asked about [X], you seemed unsure - here's what it means..."

FOR EARLY EXIT USER:
- Be encouraging and supportive
- Focus on building confidence and stamina
- Recommend starting with shorter practice sessions
- Specific tip: "You completed {duration_used:.1f} minutes - aim for full sessions next time"

FOR EFFICIENT USER:
- Acknowledge excellent interview skills
- Provide advanced tips for even better performance
- Suggest areas for minor refinement
- Specific tip: "Your structured answers were excellent, especially when discussing [X]"
"""
        
        # Build key observations for prompt
        key_observations_text = '\n'.join([f'- {note}' for note in persona_notes]) if persona_notes else '- Standard interview behavior observed'

        feedback_prompt = f"""You are an expert interview coach analyzing a {self.role} interview.

{resume_context}
{behavior_insights}

INTERVIEW TRANSCRIPT:
{transcript}

MANDATORY: Your feedback MUST start with this exact structure:

## 🎭 User Persona Identified: {user_persona}

**What This Means:** [2-3 sentences explaining what this persona type is and specific behaviors you observed in THIS interview]

**Key Observations:**
{key_observations_text}

---

Then provide CONCISE, focused feedback in the following format:

## 🎯 Interview Performance Summary

**Overall Rating:** ⭐⭐⭐⭐☆ (X/5)

**Quick Summary:** [1-2 sentences about overall performance]

---

## 📊 Performance Ratings

### Communication Clarity
**Rating:** ⭐⭐⭐⭐☆ (X/5)
**Strength:** [1 specific strength in 1 line]
**Improve:** [1 actionable tip in 1 line]

### Technical/Domain Knowledge
**Rating:** ⭐⭐⭐⭐☆ (X/5)
**Strength:** [1 specific strength in 1 line]
**Improve:** [1 actionable tip in 1 line]

### Answer Structure (STAR Method)
**Rating:** ⭐⭐⭐⭐☆ (X/5)
**Strength:** [1 specific strength in 1 line]
**Improve:** [1 actionable tip in 1 line]

### Confidence & Professionalism
**Rating:** ⭐⭐⭐⭐☆ (X/5)
**Strength:** [1 specific strength in 1 line]
**Improve:** [1 actionable tip in 1 line]

### Use of Examples
**Rating:** ⭐⭐⭐⭐☆ (X/5)
**Strength:** [1 specific strength in 1 line]
**Improve:** [1 actionable tip in 1 line]

---

## 💪 Top 3 Strengths

1. **[Strength Name]** - [Brief 1-line explanation with example]
2. **[Strength Name]** - [Brief 1-line explanation with example]
3. **[Strength Name]** - [Brief 1-line explanation with example]

---

## 🎯 Top 3 Areas to Improve

1. **[Improvement Area]** - [1 specific actionable tip]
2. **[Improvement Area]** - [1 specific actionable tip]
3. **[Improvement Area]** - [1 specific actionable tip]

---

## 💬 Persona-Specific Advice

**Based on your {user_persona} behavior pattern, here's targeted advice:**

[Provide 3-4 bullet points of SPECIFIC advice for this persona type, referencing actual moments from the interview]

Example for Chatty User:
- Your answer about [specific project] went off-topic when you mentioned [unrelated detail] - focus on the core question
- Practice the 90-second rule: Situation (15s), Task (15s), Action (45s), Result (15s)
- Before answering, mentally ask: "Does this directly answer the question?"

Example for Confused User:
- When asked about [specific technical topic], you seemed unsure - it's perfectly fine to ask "Could you clarify what you mean by [term]?"
- Research common {self.role} terminology before interviews
- If stuck, ask: "Can you give me an example of what you're looking for?"

Example for Early Exit User:
- You completed {duration_used:.1f} minutes before requesting to end - build stamina with 5-minute practice sessions, then 10, then 15
- Practice interviews with friends to build confidence
- Remember: it's okay to take a breath between questions

Example for Efficient User:
- Your structured approach was excellent - consider adding more quantifiable metrics to strengthen impact
- You stayed focused throughout - in longer interviews, this consistency will set you apart

---

## 🚀 Action Plan

**Before Your Next Interview:**
1. [Specific action item]
2. [Specific action item]
3. [Specific action item]

**Practice Questions:**
1. [1 challenging question for their role]
2. [1 scenario-based question]

---

## ✨ Final Verdict

**Interview Readiness:** [Beginner/Intermediate/Advanced/Interview-Ready]

**One Key Takeaway:** [Most important thing to remember - 1 sentence]

**Encouragement:** [Brief encouraging message - 1-2 sentences]

---

CRITICAL INSTRUCTIONS:
- Keep it CONCISE - no long explanations
- Be SPECIFIC - reference actual interview moments briefly
- Use ⭐ emojis for all ratings (1-5 stars)
- Each "Strength" and "Improve" should be ONE line only
- Focus on actionable advice
- Make it encouraging but honest
- Total length should be much shorter than typical feedback"""

        try:
            # Generate feedback
            response = self.model.generate_content(feedback_prompt)
            return response.text
        except Exception as e:
            return f"""⚠️ Error generating feedback: {str(e)}

## Basic Feedback

**Overall Rating:** ⭐⭐⭐⭐☆ (4/5)

Thank you for completing the interview!

**Top Strengths:**
1. Good communication throughout
2. Relevant examples provided
3. Professional demeanor

**Areas to Improve:**
1. Use STAR method more consistently
2. Provide more specific metrics in examples
3. Practice technical/domain questions more

**Next Steps:**
1. Review STAR method (Situation, Task, Action, Result)
2. Prepare 3-5 strong stories with metrics
3. Research the company before interviews

Keep practicing - you're making progress! 💪"""
    
    def _format_transcript(self):
        """Format conversation history as readable transcript"""
        transcript = []
        for i, msg in enumerate(self.conversation_history):
            role = "🎤 Interviewer" if msg["role"] == "assistant" else "👤 Candidate"
            transcript.append(f"{role}: {msg['content']}")
        return "\n\n".join(transcript)