import json
import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_http_methods

from .forms import TicketForm, SEVERITIES, CATEGORIES

COOKIE_NAME = 'last_ticket_category'
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

PRIORITY_MAP = {
    'Low': 'Low',
    'Medium': 'Normal',
    'High': 'High',
    'Critical': 'Urgent',
}

# In-memory server-side state (no DB / session). Lost on server restart.
priority_previews = {}


@require_http_methods(['GET', 'POST'])
def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)

        if form.is_valid():
            data = form.cleaned_data

            screenshot_path = ''
            screenshot = data.get('screenshot')
            if screenshot:
                ext = os.path.splitext(screenshot.name)[1].lower()
                # Random filename: never trust the user-supplied name.
                upload_path = f'ticket_screenshots/{uuid.uuid4().hex}{ext}'
                screenshot_path = default_storage.save(upload_path, screenshot)

            record = {
                'trainee_name': data['trainee_name'],
                'email': data['email'],
                'category': data['category'],
                'severity': data['severity'],
                'description': data['description'],
                'screenshot': screenshot_path,
                'request_id': request.audit_id,
            }

            # One JSON object per line (JSONL).
            with open(settings.DATA_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

            response = redirect(
                reverse('supportdesk:ticket_success')
                + f'?ref={request.audit_id}'
            )
            response.set_cookie(
                COOKIE_NAME,
                data['category'],
                max_age=COOKIE_MAX_AGE,
                httponly=True,
                samesite='Lax',
            )
            return response
    else:
        last_category = request.COOKIES.get(COOKIE_NAME)
        valid = {value for value, _ in CATEGORIES}
        initial = {'category': last_category} if last_category in valid else {}
        form = TicketForm(initial=initial)

    return render(request, 'supportdesk/ticket_form.html', {'form': form})


@require_http_methods(['GET'])
def ticket_success(request):
    ref = request.GET.get('ref', '')
    try:
        ticket_ref = str(uuid.UUID(ref))   # accept only a real UUID
    except ValueError:
        ticket_ref = request.audit_id
    return render(request, 'supportdesk/ticket_success.html',
                  {'ticket_ref': ticket_ref})


@require_POST
@csrf_protect
def priority_checker(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
        if not isinstance(payload, dict):
            raise ValueError
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON body.'},
                            status=400)

    severity = str(payload.get('severity', '')).strip()
    description = str(payload.get('description', '')).strip()

    if severity not in dict(SEVERITIES):
        return JsonResponse({'success': False, 'error': 'Invalid severity.'},
                            status=400)
    if len(description) < 20:
        return JsonResponse(
            {'success': False,
             'error': 'Description must contain at least 20 characters.'},
            status=400)

    priority = PRIORITY_MAP[severity]

    priority_previews[request.audit_id] = {
        'severity': severity,
        'priority': priority,
        'description': description,
    }

    return JsonResponse({
        'success': True,
        'severity': severity,
        'suggested_priority': priority,
        'message': 'Priority suggestion generated successfully.',
        'request_id': request.audit_id,
    })
