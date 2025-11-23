import PyPDF2
import docx
import re
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

class ResumeParser:
    def __init__(self):
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def extract_text_from_docx(self, docx_file):
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"
    
    def extract_text_from_txt(self, txt_file):
        """Extract text from TXT file"""
        try:
            return txt_file.read().decode("utf-8")
        except Exception as e:
            return f"Error reading TXT: {str(e)}"
    
    def parse_resume(self, file, file_type):
        """Parse resume based on file type"""
        if file_type == "pdf":
            text = self.extract_text_from_pdf(file)
        elif file_type == "docx":
            text = self.extract_text_from_docx(file)
        elif file_type == "txt":
            text = self.extract_text_from_txt(file)
        else:
            return None, None
        
        # Extract structured information using AI
        candidate_info = self.extract_candidate_info(text)
        
        return text, candidate_info
    
    def extract_candidate_info(self, resume_text):
        """Extract comprehensive candidate information using AI and validate it's a resume"""
        
        # First, validate if this is actually a resume
        validation_prompt = f"""Analyze this text and determine if it's a resume/CV:

Text to analyze:
{resume_text[:1000]}

Is this a resume or CV? Answer with ONLY "YES" or "NO" followed by a brief reason.

A resume typically contains:
- Personal information (name, contact)
- Work experience or job history
- Education
- Skills
- Professional summary

Answer format: YES/NO - reason"""

        try:
            validation_response = self.model.generate_content(validation_prompt)
            validation_text = validation_response.text.strip().upper()
            
            # Check if it's not a resume
            if validation_text.startswith("NO"):
                return {
                    "name": "Invalid Resume",
                    "email": "Not a resume",
                    "phone": "Not a resume",
                    "skills": [],
                    "years_of_experience": "Not a resume",
                    "recent_job_title": "Not a resume",
                    "recent_company": "Not a resume",
                    "education": "Not a resume",
                    "university": "Not a resume",
                    "certifications": [],
                    "key_projects": [],
                    "key_achievements": [],
                    "is_valid_resume": False,
                    "validation_message": "This file does not appear to be a resume. Please upload a valid resume/CV."
                }
        except Exception as e:
            print(f"Resume validation error: {e}")
            # Continue with extraction if validation fails
        
        prompt = f"""Analyze this resume carefully and extract detailed information in JSON format:

Resume Text:
{resume_text[:4000]}

Extract the following information accurately:
1. Full Name (first and last name)
2. Email address
3. Phone number
4. Top 8-10 Technical Skills (be comprehensive)
5. Total Years of Experience (calculate from work history)
6. Most Recent Job Title
7. Most Recent Company
8. Highest Education Degree
9. University Name
10. Key Projects (top 3-4 with brief descriptions)
11. Key Achievements (quantifiable results, metrics)
12. Certifications (if any)

Be thorough and extract as much relevant information as possible.

Return ONLY valid JSON:
{{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1234567890",
    "skills": ["skill1", "skill2", "skill3", "skill4", "skill5", "skill6", "skill7", "skill8"],
    "years_of_experience": "X years",
    "recent_job_title": "Job Title",
    "recent_company": "Company Name",
    "education": "Degree Name",
    "university": "University Name",
    "certifications": ["cert1", "cert2"],
    "key_projects": [
        "Project 1: Brief description",
        "Project 2: Brief description",
        "Project 3: Brief description"
    ],
    "key_achievements": [
        "Achievement 1 with metrics",
        "Achievement 2 with metrics",
        "Achievement 3 with metrics"
    ],
    "is_valid_resume": true
}}

Return ONLY the JSON object."""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean response
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            import json
            candidate_info = json.loads(response_text)
            candidate_info["is_valid_resume"] = True
            return candidate_info
        except Exception as e:
            print(f"Resume parsing error: {e}")
            # Return default structure
            return {
                "name": "Candidate",
                "email": "Not Found",
                "phone": "Not Found",
                "skills": [],
                "years_of_experience": "Not Found",
                "recent_job_title": "Not Found",
                "recent_company": "Not Found",
                "education": "Not Found",
                "university": "Not Found",
                "certifications": [],
                "key_projects": [],
                "key_achievements": [],
                "is_valid_resume": True
            }