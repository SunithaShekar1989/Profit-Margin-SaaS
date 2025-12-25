from django.shortcuts import render, redirect
from uuid import uuid4
from .models import Question, SurveyResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Company, UserProfile

PAGE_SIZE = 4

@login_required
def survey_page(request, page):

    sid = request.session.session_key
    if not sid:
        request.session.save()
        sid = request.session.session_key

    request.session['sid'] = sid

    # Lock only if FINAL submitted exists
    if SurveyResponse.objects.filter(
        user=request.user,
        company=request.user.userprofile.company,
        is_submitted=True
    ).exists() and page != 1:
        return redirect('/survey/results/')

    PER_PAGE = 5
    total_questions = Question.objects.count()
    total_pages = (total_questions + PER_PAGE - 1) // PER_PAGE

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE

    questions = Question.objects.all()[start:end]

    return render(request, 'survey/survey_page.html', {
        'questions': questions,
        'page': page,
        'total_pages': total_pages
    })



def done(request):
    return render(request, 'survey/done.html')
def calculate_question_score(user_index, ideal_index):
    return max(0, 100 - 25 * abs(user_index - ideal_index))


CATEGORY_WEIGHTS = {
    'PR': 0.20,
    'PC': 0.20,
    'OP': 0.15,
    'WC': 0.30,
    'SGA': 0.15,
}

from collections import defaultdict

def calculate_scores(request):

    responses = SurveyResponse.objects.filter(
        user=request.user,
        company=request.user.userprofile.company,
        is_submitted=True
    ).select_related('question', 'selected_choice')

    if not responses.exists():
        return {}, {}, 0

    # Category configuration
    category_weights = {
        "PR": 20,
        "PC": 20,
        "OP": 15,
        "WC": 30,
        "SGA": 15
    }

    category_map = {
        "PR": [],
        "PC": [],
        "OP": [],
        "WC": [],
        "SGA": []
    }

    # Per-question scoring
    for r in responses:
        ideal = r.question.ideal_index
        selected = r.selected_choice.index

        score = 100 - 25 * abs(ideal - selected)
        category_map[r.question.category].append(score)

    category_avg = {}
    weighted_scores = {}

    for cat, scores in category_map.items():
        if scores:
            avg = sum(scores) / len(scores)
            category_avg[cat] = round(avg, 2)
            weighted_scores[cat] = round(avg * category_weights[cat] / 100, 2)
        else:
            category_avg[cat] = 0
            weighted_scores[cat] = 0

    total_score = round(sum(weighted_scores.values()), 2)

    # Maturity levels
    if total_score < 25:
        maturity = "Level 1 – Initial"
    elif total_score < 50:
        maturity = "Level 2 – Managed"
    elif total_score < 75:
        maturity = "Level 3 – Defined"
    else:
        maturity = "Level 4 – Optimized"

    return category_avg, weighted_scores, total_score, maturity


def get_maturity_level(total_score):
    if total_score >= 75:
        return "Level 5 – Optimized"
    elif total_score >= 65:
        return "Level 4 – Managed"
    elif total_score >= 50:
        return "Level 3 – Defined"
    elif total_score >= 35:
        return "Level 2 – Repeatable"
    else:
        return "Level 1 – Initial"


@login_required
def results(request):

    category_avg, weighted_scores, total_score, maturity = calculate_scores(request)
    recommendation = generate_recommendations(total_score)

    rows = []
    for cat in weighted_scores:
        rows.append({
            "category": cat,
            "avg": category_avg.get(cat, 0),
            "weighted": weighted_scores.get(cat, 0)
        })

    return render(request, 'survey/results.html', {
        "rows": rows,
        "total_score": total_score,
        "maturity": maturity,
        "recommendation": recommendation
    })



@login_required
def survey_page(request, page):

    # ---- SESSION + LOCK LOGIC ----
    sid = request.session.session_key
    if not sid:
        request.session.save()
        sid = request.session.session_key

    request.session['sid'] = sid

    # Lock if already submitted
    if SurveyResponse.objects.filter(session_id=sid, is_submitted=True).exists():
        return redirect('/survey/results/')
    # --------------------------------

    # Existing logic continues below
    questions = Question.objects.all()[(page-1)*5:page*5]

    return render(request, 'survey/survey_page.html', {
        'questions': questions,
        'page': page
    })

from .models import Question, Choice, SurveyResponse
from django.shortcuts import redirect

@login_required
def submit(request):

    sid = request.session.get('sid')
    page = int(request.POST.get('page'))

    PER_PAGE = 5
    total_questions = Question.objects.count()
    total_pages = (total_questions + PER_PAGE - 1) // PER_PAGE

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    questions = Question.objects.all()[start:end]

    for q in questions:
        choice_id = request.POST.get(f"question_{q.id}")
        if choice_id:
            SurveyResponse.objects.update_or_create(
                user=request.user,
                company=request.user.userprofile.company,
                question=q,
                defaults={
                    'session_id': sid,
                    'selected_choice_id': choice_id,
                    'is_submitted': False
                }
            )

    # Mark ALL answers as submitted only on final page
    if page == total_pages:
        SurveyResponse.objects.filter(
            user=request.user,
            company=request.user.userprofile.company
        ).update(is_submitted=True)
        return redirect('/survey/results/')

    return redirect(f"/survey/page/{page+1}/")


from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Company, UserProfile

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        company_name = request.POST.get('company')
        industry = request.POST.get('industry')

        if form.is_valid() and company_name:
            user = form.save()

            company = Company.objects.create(
                name=company_name,
                industry=industry
            )

            UserProfile.objects.create(
                user=user,
                company=company
            )

            login(request, user)
            return redirect('/survey/page/1/')
        else:
            return render(request, 'survey/register.html', {
                'form': form,
                'error': "Please fill all fields correctly."
            })
    else:
        form = UserCreationForm()

    return render(request, 'survey/register.html', {'form': form})

@login_required
def reset_survey(request):

    SurveyResponse.objects.filter(
        user=request.user,
        company=request.user.userprofile.company
    ).delete()

    # Clear session lock
    if 'sid' in request.session:
        del request.session['sid']

    return redirect('/survey/page/1/')

@login_required
def dashboard(request):

    category_avg, weighted_scores, total_score, maturity = calculate_scores(request)

    labels = list(weighted_scores.keys())
    values = list(weighted_scores.values())

    return render(request, 'survey/dashboard.html', {
        'labels': labels,
        'values': values,
        'total_score': total_score,
        'maturity': maturity
    })

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table

@login_required
def download_report(request):

    category_avg, weighted_scores, total_score, maturity = calculate_scores(request)
    company = request.user.userprofile.company

    file_path = f"report_{company.id}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>Company:</b> {company.name}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Industry:</b> {company.industry}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Total Score:</b> {total_score}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Maturity Level:</b> {maturity}", styles["Normal"]))

    table_data = [["Category", "Avg Score", "Weighted Score"]]
    for cat in weighted_scores:
        table_data.append([cat, category_avg[cat], weighted_scores[cat]])

    elements.append(Table(table_data))
    doc.build(elements)

    from django.http import FileResponse
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_path)


from openpyxl import Workbook
from django.http import HttpResponse

@login_required
def export_excel(request):

    category_avg, weighted_scores, total_score, maturity = calculate_scores(request)
    company = request.user.userprofile.company

    wb = Workbook()
    ws = wb.active
    ws.title = "Maturity Scores"

    ws.append(["Company", company.name])
    ws.append(["Industry", company.industry])
    ws.append(["Total Score", total_score])
    ws.append(["Maturity Level", maturity])
    ws.append([])
    ws.append(["Category", "Avg Score", "Weighted Score"])

    for cat in weighted_scores:
        ws.append([cat, category_avg[cat], weighted_scores[cat]])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename="Maturity_Report.xlsx"'
    wb.save(response)
    return response

def generate_recommendations(total_score):
    if total_score < 25:
        return "Your organization is at Initial maturity. Focus on establishing standard processes and basic cost controls."
    elif total_score < 50:
        return "Your organization is Managed. Improve automation, governance, and KPI monitoring."
    elif total_score < 75:
        return "Your organization is Defined. Implement predictive analytics and cross-functional optimization."
    else:
        return "Your organization is Optimized. Focus on AI-driven decision making and continuous improvement."

