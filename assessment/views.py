from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .logic import AdvancedEQAssessmentModel
from .models import AssessmentResult
import json

eq_model = AdvancedEQAssessmentModel()

def index(request):
    request.session.flush()
    try:
        AssessmentResult.objects.all().delete()
    except Exception:
        pass
    return render(request, 'assessment/landing.html')

@require_http_methods(["POST"])
def start_assessment(request):
    age = request.POST.get('age')
    gender = request.POST.get('gender')
    profession = request.POST.get('profession')
    if not age or not profession:
        return redirect('index')
    scenario = eq_model.generate_scenario(age, profession)
    questions = eq_model.generate_questions(profession, age, scenario)
    request.session['user_data'] = {
        'age': age,
        'gender': gender,
        'profession': profession,
    }
    request.session['scenario'] = scenario
    request.session['questions'] = questions
    request.session.set_expiry(1800)
    context = {
        'scenario': scenario,
        'questions': questions
    }
    return render(request, 'assessment/quiz.html', context)

@require_http_methods(["POST"])
def submit_assessment(request):
    questions = request.session.get('questions', {})
    user_data = request.session.get('user_data', {})
    scenario = request.session.get('scenario', "")
    if not questions:
        return redirect('index')
    sentiment_map = {}
    responses_map = {}
    valid_responses = True
    for category in questions.keys():
        response_text = request.POST.get(f"response_{category}")
        if not response_text:
             continue
        is_valid, msg = eq_model.validate_response(response_text)
        responses_map[category] = response_text
        analysis = eq_model.analyze_sentiment(response_text)
        sentiment_map[category] = analysis
    scores = eq_model.calculate_eq_scores(sentiment_map, responses_map=responses_map, user_data=user_data)
    interpretation = eq_model.interpret_results(scores)
    try:
        AssessmentResult.objects.create(
            age=user_data.get('age'),
            gender=user_data.get('gender'),
            profession=user_data.get('profession'),
            scenario_used=scenario,
            scores=scores,
            overall_score=scores.get('Overall', 0),
            rating=interpretation['rating']
        )
    except Exception as e:
        print(f"Error saving result: {e}")
    request.session.flush()
    overall = scores.get('Overall', 0)
    dash_offset = 440 - (440 * overall / 100)
    context = {
        'scores': scores,
        'interpretation': interpretation,
        'user_data': user_data,
        'dash_offset': dash_offset,
        'formatted_overall_score': int(overall)
    }
    return render(request, 'assessment/results.html', context)
