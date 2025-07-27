# pages/quiz.py - Quiz page module
import streamlit as st
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
import random

# Load environment variables
load_dotenv()

# Initialize chat model for quiz generation
llm = init_chat_model(
    os.getenv("CHAT_MODEL", "llama3"),
    model_provider=os.getenv("MODEL_PROVIDER", "ollama"),
    temperature=0.7
)

# Age group configurations
AGE_GROUPS = {
    "Children (5-12)": {
        "description": "Simple stories and basic concepts about Krishna",
        "topics": ["Krishna's childhood", "Simple life lessons", "Basic stories", "Colors and festivals"]
    },
    "Teenagers (13-18)": {
        "description": "More detailed stories with moral lessons",
        "topics": ["Krishna's adventures", "Bhagavad Gita basics", "Friendship and values", "Life guidance"]
    },
    "Adults (19-60)": {
        "description": "Deep philosophical concepts and practical application",
        "topics": ["Bhagavad Gita philosophy", "Karma yoga", "Life challenges", "Spiritual practices"]
    },
    "Seniors (60+)": {
        "description": "Wisdom-focused content with spiritual depth",
        "topics": ["Spiritual wisdom", "Life reflection", "Advanced philosophy", "Peace and devotion"]
    }
}

def generate_quiz_question(age_group, topic, difficulty="medium"):
    """Generate a quiz question using LLM based on age group and topic"""
    
    prompt = PromptTemplate.from_template("""
    You are creating a quiz question about Krishna and Hindu philosophy for {age_group}.
    
    Topic: {topic}
    Difficulty: {difficulty}
    
    Create ONE multiple choice question with 4 options (A, B, C, D) and indicate the correct answer.
    
    IMPORTANT: Instead of asking direct theoretical questions, create REAL-LIFE SCENARIOS that people in the {age_group} category commonly face, and connect these situations to Krishna's teachings from the Bhagavad Gita.
    
    Guidelines for creating scenarios:
    - For Children (5-12): Use school situations, family conflicts, sharing toys, dealing with bullies, homework challenges
    - For Teenagers (13-18): Use peer pressure, exam stress, friendship issues, career confusion, social media problems
    - For Adults (19-60): Use workplace conflicts, family responsibilities, financial stress, relationship issues, career decisions
    - For Seniors (60+): Use health concerns, family wisdom sharing, retirement decisions, legacy thoughts, spiritual growth
    
    The question should present a realistic situation and ask what Krishna's teachings would guide them to do, or how Gita principles apply to that situation.
    
    Make the language and scenario complexity appropriate for {age_group}.
    
    Format your response exactly as:
    QUESTION: [Present a real-life scenario that the age group faces, then ask how Krishna's teachings from the Gita would guide their response]
    A) [Option A - should reflect different approaches/mindsets]
    B) [Option B - should reflect different approaches/mindsets] 
    C) [Option C - should reflect different approaches/mindsets]
    D) [Option D - should reflect different approaches/mindsets]
    CORRECT: [A/B/C/D]
    EXPLANATION: [Brief explanation connecting the correct choice to specific Krishna's teachings or Gita verses/principles, and why this approach aligns with dharmic living]
    
    Start with "Hare Krishna! Here's your question:\n"
    """)
    
    try:
        response = llm.invoke(prompt.format(
            age_group=age_group,
            topic=topic,
            difficulty=difficulty
        ))
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return f"Error generating question: {str(e)}"

def parse_quiz_question(response):
    """Parse the LLM response into structured quiz data"""
    try:
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        question = ""
        options = {}
        correct = ""
        explanation = ""
        
        # Print debug info
        print(f"Parsing response with {len(lines)} lines")
        for i, line in enumerate(lines):
            print(f"Line {i}: {repr(line)}")
        
        # More flexible parsing
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            line_upper = line.upper()
            
            # Look for question - can be on same line as "QUESTION:" or next line
            if "QUESTION:" in line_upper:
                # Question might be on same line after colon
                if ":" in line:
                    question_part = line.split(":", 1)[1].strip()
                    if question_part:
                        question = question_part
                    else:
                        # Question is on next line
                        i += 1
                        if i < len(lines):
                            question = lines[i].strip()
            
            # Look for options A), B), C), D)
            elif line.startswith(("A)", "B)", "C)", "D)")):
                key = line[0].upper()
                value = line[2:].strip() if len(line) > 2 else ""
                # Remove extra closing parenthesis if present
                if value.startswith(")"):
                    value = value[1:].strip()
                options[key] = value
            
            # Look for correct answer
            elif "CORRECT:" in line_upper:
                correct_part = line.split(":", 1)[1].strip().upper()
                # Extract just the letter (A, B, C, or D)
                for char in correct_part:
                    if char in ['A', 'B', 'C', 'D']:
                        correct = char
                        break
            
            # Look for explanation
            elif "EXPLANATION:" in line_upper:
                explanation_part = line.split(":", 1)[1].strip()
                if explanation_part:
                    explanation = explanation_part
                # Collect remaining lines as part of explanation
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    # Stop if we hit another section
                    if any(keyword in next_line.upper() for keyword in ["QUESTION:", "CORRECT:", "A)", "B)", "C)", "D)"]):
                        break
                    explanation += " " + next_line
                    j += 1
                i = j - 1  # Adjust index since we processed multiple lines
            
            i += 1
        
        # Debug output
        print(f"Parsed question: {repr(question)}")
        print(f"Parsed options: {options}")
        print(f"Parsed correct: {repr(correct)}")
        print(f"Parsed explanation: {repr(explanation)}")
        
        # Validate that we have minimum required components
        if not question:
            print("Missing question")
            return None
        if len(options) < 4:
            print(f"Missing options - only found {len(options)}")
            return None
        if correct not in ['A', 'B', 'C', 'D']:
            print(f"Invalid correct answer: {repr(correct)}")
            return None
            
        return {
            "question": question,
            "options": options,
            "correct": correct,
            "explanation": explanation
        }
        
    except Exception as e:
        print(f"Parsing error: {e}")
        import traceback
        traceback.print_exc()
        return None

def show_quiz_page():
    """Main quiz page function"""
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Page header
    st.title("🎯 Krishna Knowledge Quiz")
    st.markdown("Test your knowledge about Lord Krishna and Hindu philosophy!")
    
    # Initialize session state
    if "quiz_state" not in st.session_state:
        st.session_state.quiz_state = {
            "questions": [],  # Store multiple questions
            "current_question_index": 0,
            "total_questions_selected": 5,  # Default number
            "score": 0,
            "answered": False,
            "selected_answer": None,
            "quiz_started": False,
            "quiz_completed": False
        }
    
    # Age group selection
    st.subheader("👤 Select Your Age Group")
    selected_age_group = st.selectbox(
        "Choose your age group for appropriate questions:",
        list(AGE_GROUPS.keys()),
        key="age_group_select"
    )
    
    # Display age group info
    if selected_age_group:
        age_info = AGE_GROUPS[selected_age_group]
        st.info(f"📚 {age_info['description']}")
        
        # Topic selection
        st.subheader("📖 Choose a Topic")
        selected_topic = st.selectbox(
            "What would you like to be quizzed on?",
            age_info["topics"],
            key="topic_select"
        )
        
        # Number of questions selection
        st.subheader("🔢 Number of Questions")
        num_questions = st.selectbox(
            "How many questions would you like?",
            [3, 5, 10, 15, 20],
            index=1,  # Default to 5
            key="num_questions_select"
        )
        
        # Difficulty selection (for older age groups)
        difficulty = "easy"
        if selected_age_group in ["Adults (19-60)", "Seniors (60+)"]:
            difficulty = st.selectbox(
                "Select difficulty:",
                ["easy", "medium", "hard"],
                index=1,
                key="difficulty_select"
            )
        elif selected_age_group == "Teenagers (13-18)":
            difficulty = st.selectbox(
                "Select difficulty:",
                ["easy", "medium"],
                key="difficulty_select_teen"
            )
    
    # Start Quiz Button (only show if quiz hasn't started)
    if not st.session_state.quiz_state["quiz_started"] and not st.session_state.quiz_state["quiz_completed"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Quiz", use_container_width=True, key="start_quiz_btn"):
                with st.spinner(f"Generating your {num_questions} questions..."):
                    try:
                        # Reset quiz state
                        st.session_state.quiz_state = {
                            "questions": [],
                            "current_question_index": 0,
                            "total_questions_selected": num_questions,
                            "score": 0,
                            "answered": False,
                            "selected_answer": None,
                            "quiz_started": True,
                            "quiz_completed": False
                        }
                        
                        # Generate all questions at once
                        questions = []
                        for i in range(num_questions):
                            st.write(f"Generating question {i+1}/{num_questions}...")
                            response = generate_quiz_question(selected_age_group, selected_topic, difficulty)
                            quiz_data = parse_quiz_question(response)
                            
                            if quiz_data and quiz_data.get("question") and quiz_data.get("options"):
                                questions.append(quiz_data)
                            else:
                                st.warning(f"Failed to generate question {i+1}. Retrying...")
                                # Retry once
                                response = generate_quiz_question(selected_age_group, selected_topic, difficulty)
                                quiz_data = parse_quiz_question(response)
                                if quiz_data and quiz_data.get("question") and quiz_data.get("options"):
                                    questions.append(quiz_data)
                        
                        if questions:
                            st.session_state.quiz_state["questions"] = questions
                            st.success(f"✅ Generated {len(questions)} questions! Let's start the quiz!")
                            st.rerun()
                        else:
                            st.error("Failed to generate questions. Please try again.")
                            st.session_state.quiz_state["quiz_started"] = False
                        
                    except Exception as e:
                        st.error(f"Error generating questions: {str(e)}")
                        st.session_state.quiz_state["quiz_started"] = False
    
    # Display quiz in progress
    elif st.session_state.quiz_state["quiz_started"] and not st.session_state.quiz_state["quiz_completed"]:
        questions = st.session_state.quiz_state["questions"]
        current_index = st.session_state.quiz_state["current_question_index"]
        
        if current_index < len(questions):
            # Progress indicator
            progress = (current_index + 1) / len(questions)
            st.progress(progress)
            st.markdown(f"**Question {current_index + 1} of {len(questions)}**")
            
            current_question = questions[current_index]
            
            st.markdown("---")
            st.subheader("❓ Your Question:")
            st.markdown(f"**{current_question['question']}**")
            
            # Answer options
            if not st.session_state.quiz_state["answered"]:
                answer_options = []
                for key in sorted(current_question["options"].keys()):
                    answer_options.append(f"{key}) {current_question['options'][key]}")
                
                selected = st.radio(
                    "Choose your answer:",
                    answer_options,
                    key=f"answer_radio_{current_index}"
                )
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("✅ Submit Answer", use_container_width=True, key=f"submit_answer_btn_{current_index}"):
                        if selected:
                            selected_letter = selected[0]  # Get A, B, C, or D
                            st.session_state.quiz_state["selected_answer"] = selected_letter
                            st.session_state.quiz_state["answered"] = True
                            
                            if selected_letter == current_question["correct"]:
                                st.session_state.quiz_state["score"] += 1
                            
                            st.rerun()
            
            # Show results after answering
            if st.session_state.quiz_state["answered"]:
                selected_answer = st.session_state.quiz_state["selected_answer"]
                correct_answer = current_question["correct"]
                
                if selected_answer == correct_answer:
                    st.success("🎉 Correct! Well done!")
                else:
                    st.error(f"❌ Incorrect. The correct answer was {correct_answer}.")
                
                # Show explanation
                if current_question["explanation"]:
                    st.info(f"📚 **Explanation:** {current_question['explanation']}")
                
                # Current score
                score = st.session_state.quiz_state["score"]
                current_q_num = current_index + 1
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        label="Current Score", 
                        value=f"{score}/{current_q_num}"
                    )
                
                # Next question or finish quiz
                with col2:
                    if current_index + 1 < len(questions):
                        if st.button("➡️ Next Question", use_container_width=True, key=f"next_question_btn_{current_index}"):
                            st.session_state.quiz_state["current_question_index"] += 1
                            st.session_state.quiz_state["answered"] = False
                            st.session_state.quiz_state["selected_answer"] = None
                            st.rerun()
                    else:
                        if st.button("🏁 Finish Quiz", use_container_width=True, key="finish_quiz_btn"):
                            st.session_state.quiz_state["quiz_completed"] = True
                            st.rerun()
    
    # Show quiz results
    elif st.session_state.quiz_state["quiz_completed"]:
        st.markdown("---")
        st.subheader("🎊 Quiz Completed!")
        
        score = st.session_state.quiz_state["score"]
        total = st.session_state.quiz_state["total_questions_selected"]
        percentage = (score / total) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Final Score", f"{score}/{total}")
        with col2:
            st.metric("Percentage", f"{percentage:.1f}%")
        with col3:
            if percentage >= 80:
                grade = "Excellent! 🌟"
            elif percentage >= 60:
                grade = "Good! 👍"
            elif percentage >= 40:
                grade = "Fair 📚"
            else:
                grade = "Keep Learning! 💪"
            st.metric("Grade", grade)
        
        # Performance message
        if percentage >= 80:
            st.success("🎉 Outstanding performance! You have excellent knowledge of Krishna's teachings!")
        elif percentage >= 60:
            st.info("👏 Well done! You have good understanding of Krishna's philosophy.")
        elif percentage >= 40:
            st.warning("📖 Good effort! Consider reviewing more about Krishna's teachings.")
        else:
            st.error("💪 Keep studying! There's so much wonderful wisdom to discover about Krishna.")
        
        # Restart quiz option
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Take Another Quiz", use_container_width=True, key="restart_quiz_btn"):
                # Reset everything
                st.session_state.quiz_state = {
                    "questions": [],
                    "current_question_index": 0,
                    "total_questions_selected": 5,
                    "score": 0,
                    "answered": False,
                    "selected_answer": None,
                    "quiz_started": False,
                    "quiz_completed": False
                }
                st.rerun()
    
    # Instructions (show when no quiz is active)
    if not st.session_state.quiz_state["quiz_started"] and not st.session_state.quiz_state["quiz_completed"]:
        st.markdown("---")
        st.markdown("### 🚀 How to Start:")
        st.markdown("""
        1. **Select your age group** - Questions will be tailored to your level
        2. **Choose a topic** - Pick what interests you most
        3. **Select number of questions** - Choose from 3 to 20 questions
        4. **Set difficulty** (if available) - Challenge yourself appropriately  
        5. **Click 'Start Quiz'** to generate all questions and begin
        6. **Answer and learn** - Get explanations for each question
        """)
        
        st.markdown("### 🎯 Features:")
        st.markdown("""
        - **Customizable quiz length** - Choose 3, 5, 10, 15, or 20 questions
        - **Personalized questions** based on your age and interests
        - **Progress tracking** - See how far you've progressed
        - **Instant feedback** with detailed explanations
        - **Final score and grade** - Complete performance summary
        - **Unlimited retakes** - Practice as much as you want!
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)