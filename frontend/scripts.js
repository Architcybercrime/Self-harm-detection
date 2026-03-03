// Mental Health Quiz Questions (PHQ-9 inspired + thinking patterns)
const questions = [
  { q: "Little interest or pleasure in doing things?", options: ["Not at all", "Several days", "More than half the days", "Nearly every day"] },
  { q: "Feeling down, depressed, or hopeless?", options: ["Not at all", "Several days", "More than half the days", "Nearly every day"] },
  { q: "Trouble falling or staying asleep, or sleeping too much?", options: ["Not at all", "Several days", "More than half the days", "Nearly every day"] },
  { q: "Feeling tired or having little energy?", options: ["Not at all", "Several days", "More than half the days", "Nearly every day"] },
  { q: "Poor appetite or overeating?", options: ["Not at all", "Several days", "More than half the days", "Nearly every day"] },
  { q: "Feeling bad about yourself — or that you're a failure?", options: ["Not at all", "Several days", "More than half the days", "Nearly every day"] },
  { q: "Trouble concentrating on things?", options: ["Not at all", "Several days", "More than half the days", "Nearly every day"] },
  { q: "Moving or speaking slowly or opposite?", options: ["Not at all", "Several days", "More than half the days", "Nearly every day"] },
  { q: "Thoughts that you would be better off dead?", options: ["Not at all", "Several days", "More than half the days", "Nearly every day"] }
];

let currentQuestion = 0;
let totalScore = 0;
let userAnswers = [];

const quizForm = document.getElementById('quizForm');
const progressBar = document.getElementById('progress');
const submitBtn = document.getElementById('submitQuiz');

// Initialize quiz
function initQuiz() {
  loadQuestion();
}

// Load current question
function loadQuestion() {
  const qData = questions[currentQuestion];
  quizForm.innerHTML = `
    <h3 style="color: white; margin-bottom: 2rem;">Question ${currentQuestion + 1} of ${questions.length}</h3>
    <div style="color: white; font-size: 1.2rem; margin-bottom: 2rem;">${qData.q}</div>
    ${qData.options.map((option, index) => 
      `<label>
        <input type="radio" name="answer" value="${index}" style="margin-right: 1rem;">
        ${option}
      </label>`
    ).join('')}
    <button onclick="nextQuestion()" class="cta-btn" style="margin-top: 2rem;">Next</button>
  `;
  
  // Update progress
  const progress = ((currentQuestion) / questions.length) * 100;
  progressBar.style.width = `${progress}%`;
}

// Handle next question
function nextQuestion() {
  const selected = document.querySelector('input[name="answer"]:checked');
  if (!selected) {
    alert('Please select an answer');
    return;
  }
  
  const answerValue = parseInt(selected.value);
  totalScore += answerValue;
  userAnswers.push(answerValue);
  
  currentQuestion++;
  
  if (currentQuestion < questions.length) {
    loadQuestion();
  } else {
    quizForm.innerHTML = '<h3 style="color: white;">Assessment Complete!</h3>';
    submitBtn.style.display = 'inline-block';
  }
}

// Submit to backend (or demo mode)
async function submitToBackend() {
  try {
    // Replace with your partner's endpoint
    const response = await fetch('/api/quiz', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        score: totalScore, 
        answers: userAnswers,
        timestamp: new Date().toISOString()
      })
    });
    const data = await response.json();
    showResults(data);
  } catch (error) {
    // Demo mode if backend not ready
    console.log('Backend not ready, using demo results');
    showDemoResults();
  }
}

// Show demo results (when backend not ready)
function showDemoResults() {
  const depressionLevel = totalScore <= 4 ? 'Minimal' : 
                         totalScore <= 9 ? 'Mild' : 
                         totalScore <= 14 ? 'Moderate' : 'Severe';
  
  const thinkingType = totalScore <= 4 ? 'Positive Mindset' :
                      totalScore <= 9 ? 'Balanced Thinking' :
                      totalScore <= 14 ? 'Negative Spiral' : 'Critical Patterns';
  
  const results = {
    depression: depressionLevel,
    score: totalScore,
    thinking: thinkingType,
    alert: totalScore >= 15,
    recommendations: totalScore >= 15 ? 'Seek professional help immediately' : 'Continue monitoring'
  };
  
  showResults(results);
}

// Display results
function showResults(data) {
  document.getElementById('quiz').style.display = 'none';
  document.getElementById('results').style.display = 'flex';
  
  document.getElementById('resultContent').innerHTML = `
    <div class="result-card">
      <h3>Depression Level: ${data.depression}</h3>
      <p><strong>Score:</strong> ${data.score}/27</p>
    </div>
    <div class="result-card">
      <h3>Thinking Pattern: ${data.thinking}</h3>
      <p>Understanding your thought patterns helps identify areas for improvement.</p>
    </div>
    ${data.alert ? `
      <div class="result-card">
        <div class="alert">
          <h3>⚠️ Priority Alert</h3>
          <p>${data.recommendations}</p>
        </div>
      </div>
    ` : ''}
  `;
  
  document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

// Utility functions
function scrollToQuiz() {
  document.getElementById('quiz').scrollIntoView({ behavior: 'smooth' });
}

function restartQuiz() {
  currentQuestion = 0;
  totalScore = 0;
  userAnswers = [];
  document.getElementById('quiz').style.display = 'flex';
  document.getElementById('results').style.display = 'none';
  initQuiz();
}

// Event listeners
submitBtn.addEventListener('click', submitToBackend);
scrollToQuiz(); // Auto-scroll to quiz on load after hero

// Initialize
document.addEventListener('DOMContentLoaded', initQuiz);