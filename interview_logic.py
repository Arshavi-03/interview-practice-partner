import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, INTERVIEW_ROLES
from datetime import datetime, timedelta

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

class InterviewAgent:
    def __init__(self, role, duration_minutes, candidate_info=None, resume_text=None):
        self.role = role
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.chat = None
        self.conversation_history = []
        self.candidate_info = candidate_info or {}
        self.resume_text = resume_text
        self.candidate_name = candidate_info.get('name', 'Candidate') if candidate_info else 'Candidate'
        
        # Time management
        self.duration_minutes = duration_minutes
        self.start_time = None
        self.end_time = None
        self.is_final_question = False
        self.interview_ended = False
        
        # User behavior tracking
        self.off_topic_count = 0
        self.confusion_indicators = 0
        self.silence_count = 0
        self.user_requested_exit = False
        
        # Initialize chat session
        self._initialize_chat()
        
    def _initialize_chat(self):
        """Initialize Gemini chat session with time-aware system prompt"""
        role_info = INTERVIEW_ROLES.get(self.role, {})
        focus_areas = ", ".join(role_info.get("focus_areas", []))
        
        # Build resume context if available
        resume_context = ""
        if self.candidate_info:
            resume_context = f"""

CANDIDATE BACKGROUND:
- Name: {self.candidate_info.get('name', 'Not provided')}
- Skills: {', '.join(self.candidate_info.get('skills', ['Not provided'])[:10])}
- Experience: {self.candidate_info.get('years_of_experience', 'Not provided')}
- Recent Role: {self.candidate_info.get('recent_job_title', 'Not provided')} at {self.candidate_info.get('recent_company', 'Not provided')}
- Education: {self.candidate_info.get('education', 'Not provided')}
- Key Projects: {', '.join(self.candidate_info.get('key_projects', ['Not provided'])[:2])}

QUESTIONING STRATEGY:
- Start with 1-2 resume-based questions as warm-up
- Then move to general role-based questions
- Balance: 40% resume-specific, 60% role-based questions
- Ask scenarios, technical knowledge, problem-solving approaches
- Don't over-focus on their specific projects"""

        system_prompt = f"""You are Alex, a professional interviewer conducting a {self.role} interview.

INTERVIEW DURATION: {self.duration_minutes} minutes
ROLE FOCUS AREAS: {focus_areas}

{resume_context}

CRITICAL: QUESTION BALANCE AND VARIETY
You MUST ask a mix of different question types based on the role:

For SOFTWARE ENGINEER / DATA ANALYST roles:
- Resume questions (20%): "Tell me about X project"
- Coding/Technical questions (40%): "Write code to solve...", "How would you optimize...", "Explain algorithm..."
- System design (20%): "Design a system for...", "How would you scale..."
- Behavioral (20%): "Tell me about a time when..."

For SALES / MARKETING / BUSINESS roles:
- Resume questions (20%): Past experience
- Situational questions (40%): "What would you do if a client...", "How would you handle..."
- Role-play scenarios (20%): "Pitch this product to me", "Handle this objection..."
- Strategy questions (20%): "How would you approach...", "What's your strategy for..."

QUESTION EXAMPLES BY ROLE:

SOFTWARE ENGINEER:
- "Write a function to reverse a linked list"
- "How would you design a URL shortening service?"
- "Explain the difference between SQL and NoSQL databases"
- "Debug this code snippet..."
- "What's the time complexity of..."

DATA ANALYST:
- "Write a SQL query to find..."
- "How would you handle missing data in a dataset?"
- "Explain A/B testing methodology"
- "Given this data, what insights would you derive?"

SALES:
- "A client says your product is too expensive. How do you respond?"
- "Walk me through your sales process"
- "How do you handle rejection?"
- "Sell me this pen"

CUSTOMER SUPPORT:
- "A customer is angry about a delayed order. How do you handle it?"
- "How do you de-escalate a tense situation?"
- "What would you do if you don't know the answer?"

INTERVIEWING STYLE:
1. Ask ONE question at a time
2. Start with 1-2 warm-up questions about background
3. Then dive into technical/situational questions
4. Ask follow-ups based on their answers
5. Probe deeper if answers are vague
6. Keep questions realistic and practical
7. NO markdown formatting in responses
8. Be professional but conversational

Begin with a greeting using their name ({self.candidate_name}), brief introduction, and your first question."""

        # Start chat with system prompt
        self.chat = self.model.start_chat(history=[])
        
        # Send system prompt and get first question
        response = self.chat.send_message(system_prompt)
        first_question = response.text
        
        # Store in conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": first_question
        })
        
        return first_question
    
    def start_interview(self):
        """Start the interview timer"""
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=self.duration_minutes)
    
    def get_time_remaining(self):
        """Get remaining time in seconds"""
        if not self.start_time:
            return None
        remaining = (self.end_time - datetime.now()).total_seconds()
        return max(0, remaining)
    
    def should_ask_final_question(self):
        """Check if it's time for the final question (1 minute remaining)"""
        if not self.start_time or self.is_final_question:
            return False
        
        remaining = self.get_time_remaining()
        # Ask final question when 1 minute or less remains
        return remaining <= 60
    
    def _detect_user_exit_request(self, user_response):
        """Detect if user wants to end interview early"""
        exit_keywords = [
            'end interview', 'stop interview', 'finish interview', 'quit', 
            'want to stop', 'want to end', 'need to leave', 'have to go', 'end this',
            "that's all", 'no more questions', "i'm done", 'terminate', 'stop this'
        ]
        response_lower = user_response.lower().strip()
        
        for keyword in exit_keywords:
            if keyword in response_lower:
                return True
        return False
    
    def _detect_off_topic(self, user_response):
        """Detect if user is going off-topic or being chatty"""
        off_topic_indicators = [
            'by the way', 'speaking of', 'reminds me of', 'fun fact',
            'also wanted to mention', 'changing the subject', 'random thought',
            'off topic but', 'not related but'
        ]
        
        response_lower = user_response.lower()
        for indicator in off_topic_indicators:
            if indicator in response_lower:
                return True
        
        # Check for excessive length (chatty user)
        if len(user_response.split()) > 200:  # More than 200 words
            return True
        
        return False
    
    def _detect_confusion(self, user_response):
        """Detect if user is confused or unsure"""
        confusion_indicators = [
            "i don't understand", "i'm confused", "not sure what you mean",
            "can you clarify", "what do you mean by", "i'm not following",
            "could you explain", "i don't know", "i'm unsure", "um", "uh",
            "i guess", "maybe", "i think maybe", "not sure", "confused about"
        ]
        
        response_lower = user_response.lower()
        for indicator in confusion_indicators:
            if indicator in response_lower:
                return True
        
        # Check for very short, vague answers
        word_count = len(user_response.split())
        if word_count < 10 and any(word in response_lower for word in ['maybe', 'guess', 'think', 'not sure']):
            return True
        
        return False
    
    def _handle_silence(self):
        """Generate helpful response when user is silent for too long"""
        self.silence_count += 1
        
        if self.silence_count == 1:
            return f"Take your time, {self.candidate_name}. Would you like me to rephrase the question, or would you prefer a moment to think?"
        elif self.silence_count == 2:
            return "No rush! Would you like a hint, or shall we move to a different question?"
        else:
            return "That's okay! Let's move to the next question. I'll ask you something different."
    
    def is_time_up(self):
        """Check if interview time is completely up"""
        if not self.start_time:
            return False
        return self.get_time_remaining() <= 0
    
    def get_next_question(self, user_response):
        """Generate next question with behavior detection and adaptive responses"""
        
        # Handle empty/silence
        if not user_response or user_response.strip() == "":
            return self._handle_silence()
        
        # Reset silence count if user responds
        self.silence_count = 0
        
        # CRITICAL: CHECK FOR EARLY EXIT REQUEST FIRST (before time check)
        if self._detect_user_exit_request(user_response):
            self.user_requested_exit = True
            self.interview_ended = True  # Mark as ended immediately
            
            self.conversation_history.append({
                "role": "user",
                "content": user_response
            })
            
            closing = self._generate_early_exit_closing()
            
            self.conversation_history.append({
                "role": "assistant",
                "content": closing
            })
            
            # Return closing - interview will end on next rerun
            return closing
        
        # CHECK TIME - Interrupt if time is up
        remaining = self.get_time_remaining()
        if remaining <= 0:
            self.interview_ended = True
            
            self.conversation_history.append({
                "role": "user",
                "content": user_response
            })
            
            closing = self._generate_interrupting_closing()
            
            self.conversation_history.append({
                "role": "assistant",
                "content": closing
            })
            
            return closing
        
        # Store user response
        self.conversation_history.append({
            "role": "user",
            "content": user_response
        })
        
        # DETECT USER BEHAVIOR PATTERNS
        is_off_topic = self._detect_off_topic(user_response)
        is_confused = self._detect_confusion(user_response)
        
        if is_off_topic:
            self.off_topic_count += 1
        
        if is_confused:
            self.confusion_indicators += 1
        
        # Build adaptive prompt based on user behavior
        behavior_context = ""
        
        if is_confused and self.confusion_indicators <= 2:
            behavior_context = """
IMPORTANT: The candidate seems confused. In your response:
1. Briefly acknowledge their answer
2. Clarify or rephrase your previous question in simpler terms
3. Provide a bit more context to help them understand
4. Encourage them - it's okay to be unsure

Example: "I appreciate your honesty. Let me rephrase that - what I'm asking is..."
"""
        elif is_confused and self.confusion_indicators > 2:
            behavior_context = """
IMPORTANT: The candidate is showing repeated confusion. 
1. Acknowledge their answer briefly
2. Move to an easier, more straightforward question
3. Be encouraging and supportive

Example: "That's alright! Let's try a different angle..."
"""
        elif is_off_topic and self.off_topic_count <= 2:
            behavior_context = """
IMPORTANT: The candidate went off-topic or gave a lengthy answer.
1. Politely acknowledge their enthusiasm
2. Gently redirect to the question or interview focus
3. Ask a clear, focused follow-up question

Example: "I appreciate your passion! To focus on the question at hand..."
"""
        elif is_off_topic and self.off_topic_count > 2:
            behavior_context = """
IMPORTANT: The candidate keeps going off-topic (chatty user).
1. Politely but firmly redirect: "Let's focus on the interview questions"
2. Ask a direct, yes/no or short-answer question to regain control
3. Be professional but clear about time constraints

Example: "I appreciate the context, but let's focus on the interview. Here's a quick question..."
"""
        
        # Check if we should ask the final question (1 minute remaining)
        if self.should_ask_final_question() and not self.is_final_question:
            self.is_final_question = True
            prompt = f"""Candidate's response: "{user_response}"

TIME ALERT: About 1 minute remaining in the interview.

{behavior_context}

Acknowledge their response briefly, then ask ONE final, important question for a {self.role} position. 
Make it count - this is the last chance to assess them.

Keep your response natural and conversational (no markdown formatting)."""
        
        else:
            # Regular question flow
            remaining_time = self.get_time_remaining()
            time_context = f"TIME REMAINING: {int(remaining_time / 60)} minutes. " if remaining_time else ""
            
            prompt = f"""{time_context}Candidate's response: "{user_response}"

{behavior_context}

Based on this response, ask your next relevant question for the {self.role} position.

Remember:
- Ask only ONE question
- Keep it natural and conversational (no markdown)
- Be concise but thorough
- Make it relevant to their experience or the role
- Adapt to their communication style and comprehension level

Your next question:"""
        
        # Get AI response
        response = self.chat.send_message(prompt)
        assistant_message = response.text
        
        # Store assistant response
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return assistant_message
    
    def _generate_early_exit_closing(self):
        """Generate closing message when user requests to end early"""
        prompt = f"""The candidate ({self.candidate_name}) has requested to end the interview early.

Generate a professional and understanding response:
1. Acknowledge their request respectfully
2. Thank them for their time so far
3. Let them know they'll still receive feedback
4. Keep it warm and professional (2-3 sentences)

Example tone: "I completely understand, {self.candidate_name}. Thank you for your time today - I appreciate the insights you've shared. You'll receive feedback on the portion we completed shortly. Best of luck with your job search!"

NO markdown formatting - speak naturally."""
        
        response = self.chat.send_message(prompt)
        closing = response.text
        
        return closing
    
    def _generate_closing_message(self):
        """Generate interview closing message"""
        prompt = f"""The interview has concluded. 

Thank {self.candidate_name} warmly for their time and participation. 
Let them know they'll receive detailed feedback shortly.
Express appreciation for their thoughtful responses.

Keep it brief (2-3 sentences), professional, and encouraging.
No markdown formatting - speak naturally."""
        
        response = self.chat.send_message(prompt)
        closing = response.text
        
        self.conversation_history.append({
            "role": "assistant",
            "content": closing
        })
        
        return closing
    
    def _generate_interrupting_closing(self):
        """Generate interrupting closing message when time runs out"""
        prompt = f"""CRITICAL: The interview time has just run out while {self.candidate_name} was speaking.

You need to INTERRUPT politely and professionally:

1. Apologize for interrupting
2. Mention that time has finished
3. Thank them for their time
4. Let them know they'll receive feedback shortly

Example tone: "I'm sorry to interrupt you, but our time has concluded. Thank you so much for your time today, {self.candidate_name}. You'll receive detailed feedback shortly. It was a pleasure speaking with you!"

Keep it brief (2-3 sentences), professional, and warm.
NO markdown formatting - speak naturally as an interviewer would."""
        
        response = self.chat.send_message(prompt)
        closing = response.text
        
        return closing
    
    def is_interview_complete(self):
        """Check if interview is finished"""
        return self.interview_ended
    
    def get_conversation_history(self):
        """Return full conversation with behavior metadata for feedback generation"""
        return {
            "messages": self.conversation_history,
            "behavior_metadata": {
                "off_topic_count": self.off_topic_count,
                "confusion_indicators": self.confusion_indicators,
                "user_requested_exit": self.user_requested_exit,
                "interview_duration_used": (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0
            }
        }
    
    def get_first_question(self):
        """Get the first question (already generated during initialization)"""
        if self.conversation_history:
            return self.conversation_history[0]["content"]
        return f"Hello {self.candidate_name}! Let's begin the interview."