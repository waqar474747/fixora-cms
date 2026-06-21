from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import HttpResponse, FileResponse, HttpResponseForbidden
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from .models import Complaint, Category, Department, ComplaintHistory, Notification, ComplaintFeedback, STATUS_CHOICES
from .forms import ComplaintForm, ComplaintFilterForm, ComplaintStatusUpdateForm, ComplaintFeedbackForm, ComplaintEditForm
from app.accounts.models import UserProfile
from app.accounts.views import log_activity



@login_required(login_url='accounts:login')
@require_http_methods(["GET", "POST"])
@csrf_protect
def submit_complaint(request):
    """Submit a new complaint"""
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.status = 'SUBMITTED'
            # Process extra fields
            complaint.qr_code_data = request.POST.get('qr_code_data', '')
            lat = request.POST.get('latitude')
            lng = request.POST.get('longitude')
            if lat and lng:
                try:
                    complaint.latitude = float(lat)
                    complaint.longitude = float(lng)
                except (ValueError, TypeError):
                    pass
            complaint.save()
            
            # Create notification for user
            Notification.objects.create(
                user=request.user,
                complaint=complaint,
                notification_type='SUBMISSION',
                title='Complaint Submitted',
                message=f'Your complaint "{complaint.title}" has been submitted successfully.'
            )

            # Notify all admins
            admin_users = User.objects.filter(profile__role='ADMIN')
            submitter_name = request.user.get_full_name() or request.user.username
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    complaint=complaint,
                    notification_type='NEW_COMPLAINT',
                    title='New Complaint Received',
                    message=f'New complaint "{complaint.title}" (ID: {complaint.complaint_id}) has been submitted by {submitter_name}.'
                )
            
            # Log activity
            log_activity(request.user, 'COMPLAINT_SUBMIT', f'Submitted complaint {complaint.complaint_id}', request)
            
            messages.success(request, f'Complaint submitted successfully! Your complaint ID is: {complaint.complaint_id}')
            return redirect('complaints:detail', pk=complaint.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ComplaintForm()
    
    context = {
        'form': form,
        'categories': Category.objects.all(),
        'departments': Department.objects.filter(is_active=True),
    }
    return render(request, 'complaints/submit_complaint.html', context)


@login_required(login_url='accounts:login')
def complaint_list(request):
    """List all complaints for the logged-in user"""
    try:
        user_profile = request.user.profile
    except:
        user_profile = UserProfile.objects.create(user=request.user)
    
    if user_profile.is_admin():
        complaints = Complaint.objects.all()
    elif user_profile.is_staff_member() and user_profile.department:
        complaints = Complaint.objects.filter(department=user_profile.department)
    else:
        complaints = Complaint.objects.filter(user=request.user)
    
    # Apply filters
    form = ComplaintFilterForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        priority = form.cleaned_data.get('priority')
        category = form.cleaned_data.get('category')
        department = form.cleaned_data.get('department')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search:
            complaints = complaints.filter(
                Q(complaint_id__icontains=search) |
                Q(title__icontains=search) |
                Q(category__name__icontains=search)
            )
        
        if status:
            complaints = complaints.filter(status=status)
        
        if priority:
            complaints = complaints.filter(priority=priority)
        
        if category:
            complaints = complaints.filter(category=category)
        
        if department:
            complaints = complaints.filter(department=department)
        
        if date_from:
            complaints = complaints.filter(created_at__date__gte=date_from)
        
        if date_to:
            complaints = complaints.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_complaints': complaints.count(),
        'user_profile': user_profile,
        'categories': Category.objects.all(),
        'departments': Department.objects.filter(is_active=True),
        'status_choices': STATUS_CHOICES,
        'tracking_query': request.GET.get('track', ''),
    }
    return render(request, 'complaints/complaint_list.html', context)


def track_complaint_page(request):
    """Show a form to enter a tracking ID and look up a complaint - publicly accessible"""
    complaint = None
    tracking_id = request.GET.get('tracking_id', '').strip()
    error = None

    if tracking_id:
        try:
            complaint = Complaint.objects.get(complaint_id=tracking_id.upper())
        except Complaint.DoesNotExist:
            error = f'No complaint found with Tracking ID: {tracking_id}'

    context = {
        'complaint': complaint,
        'tracking_id': tracking_id,
        'error': error,
        'status_choices': STATUS_CHOICES,
    }
    return render(request, 'complaints/track_complaint.html', context)


@login_required(login_url='accounts:login')
def complaint_track(request, tracking_id):
    """Look up a complaint by tracking ID and redirect to detail"""
    try:
        complaint = Complaint.objects.get(complaint_id=tracking_id.upper())
    except Complaint.DoesNotExist:
        messages.error(request, f'No complaint found with Tracking ID: {tracking_id}')
        return redirect('complaints:track_page')

    if request.user.is_authenticated:
        user_profile = request.user.profile
        if user_profile.is_admin():
            pass
        elif user_profile.is_staff_member() and user_profile.department:
            if complaint.department != user_profile.department:
                messages.error(request, 'You do not have permission to view this complaint.')
                return redirect('complaints:track_page')
        elif complaint.user != request.user:
            messages.error(request, 'You do not have permission to view this complaint.')
            return redirect('complaints:track_page')
    return redirect('complaints:detail', pk=complaint.pk)


@login_required(login_url='accounts:login')
def complaint_detail(request, pk):
    """View complaint details"""
    complaint = get_object_or_404(Complaint, pk=pk)
    
    # Check permissions
    try:
        user_profile = request.user.profile
    except:
        user_profile = UserProfile.objects.create(user=request.user)
    if user_profile.is_admin():
        pass
    elif user_profile.is_staff_member() and user_profile.department:
        if complaint.department != user_profile.department:
            messages.error(request, 'You do not have permission to view this complaint.')
            return redirect('complaints:list')
    elif complaint.user != request.user:
        messages.error(request, 'You do not have permission to view this complaint.')
        return redirect('complaints:list')
    
    # Log activity
    log_activity(request.user, 'COMPLAINT_VIEW', f'Viewed complaint {complaint.complaint_id}', request)
    
    # Get complaint history
    history = complaint.history.all()
    
    # Workflow steps for tracking visualization
    workflow_steps = ['SUBMITTED', 'PENDING', 'UNDER_REVIEW', 'IN_PROGRESS', 'RESOLVED']
    current_idx = workflow_steps.index(complaint.status) if complaint.status in workflow_steps else -1
    
    context = {
        'complaint': complaint,
        'history': history,
        'workflow_steps': workflow_steps,
        'current_step': current_idx,
        'status_labels': dict(STATUS_CHOICES),
    }
    return render(request, 'complaints/complaint_detail.html', context)


@login_required(login_url='accounts:login')
@require_http_methods(["GET", "POST"])
@csrf_protect
def update_complaint_status(request, pk):
    """Update complaint status (Admin only)"""
    complaint = get_object_or_404(Complaint, pk=pk)
    user_profile = request.user.profile
    
    if not user_profile.is_admin() and not user_profile.is_staff_member():
        messages.error(request, 'You do not have permission to update this complaint.')
        return redirect('complaints:detail', pk=pk)
    
    if user_profile.is_staff_member() and user_profile.department:
        if complaint.department != user_profile.department:
            messages.error(request, 'You do not have permission to update this complaint.')
            return redirect('complaints:detail', pk=pk)
    
    if request.method == 'POST':
        form = ComplaintStatusUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            old_status = complaint.status
            updated_complaint = form.save(commit=False)
            if updated_complaint.status == 'RESOLVED' and old_status != 'RESOLVED':
                updated_complaint.resolved_at = timezone.now()
            updated_complaint.save()
            
            # Create history entry
            ComplaintHistory.objects.create(
                complaint=complaint,
                changed_by=request.user,
                action=f'Status changed from {old_status} to {updated_complaint.status}',
                old_value=old_status,
                new_value=updated_complaint.status
            )
            
            # Create notification for user
            notif_type = 'STATUS_CHANGE'
            notif_title = 'Complaint Status Updated'
            if updated_complaint.status == 'RESOLVED':
                notif_type = 'RESOLUTION'
                notif_title = 'Complaint Resolved'
            elif updated_complaint.status == 'REJECTED':
                notif_type = 'REJECTION'
                notif_title = 'Complaint Rejected'

            Notification.objects.create(
                user=complaint.user,
                complaint=complaint,
                notification_type=notif_type,
                title=notif_title,
                message=f'Your complaint status has been updated to {updated_complaint.get_status_display()}'
            )

            # Notify assigned staff if changed
            if updated_complaint.assigned_to and updated_complaint.assigned_to != complaint.assigned_to:
                Notification.objects.create(
                    user=updated_complaint.assigned_to,
                    complaint=complaint,
                    notification_type='NEW_COMPLAINT',
                    title='Complaint Assigned',
                    message=f'Complaint {complaint.complaint_id} has been assigned to you.'
                )

            # Send email notification
            try:
                subject = f'Update on your complaint: {complaint.complaint_id}'
                message = f'Hello {complaint.user.first_name or complaint.user.username},\n\n' \
                          f'The status of your complaint "{complaint.title}" has been updated to: {updated_complaint.get_status_display()}.\n\n' \
                          f'Admin Remarks: {updated_complaint.admin_remarks}\n\n' \
                          f'You can view the details here: {request.build_absolute_uri(complaint.get_absolute_url() if hasattr(complaint, "get_absolute_url") else "/")}\n\n' \
                          f'Thank you,\nComplaint Management System'
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@cms.local',
                    [complaint.user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Email notification failed: {e}")
            
            # Log activity
            log_activity(request.user, 'STATUS_CHANGE', f'Updated complaint {complaint.complaint_id} status', request)
            
            messages.success(request, 'Complaint status updated successfully!')
            return redirect('complaints:detail', pk=pk)
    else:
        form = ComplaintStatusUpdateForm(instance=complaint)
    
    context = {
        'form': form,
        'complaint': complaint,
    }
    return render(request, 'complaints/update_status.html', context)


@login_required(login_url='accounts:login')
@require_http_methods(["GET", "POST"])
@csrf_protect
def edit_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    if complaint.user != request.user:
        messages.error(request, 'You do not have permission to edit this complaint.')
        return redirect('complaints:list')

    if complaint.status not in ['SUBMITTED', 'PENDING']:
        messages.error(request, 'You can only edit complaints that are still pending.')
        return redirect('complaints:detail', pk=pk)

    if request.method == 'POST':
        form = ComplaintEditForm(request.POST, request.FILES, instance=complaint)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.save()
            ComplaintHistory.objects.create(
                complaint=complaint,
                changed_by=request.user,
                action='Complaint edited by user',
                old_value='',
                new_value=''
            )
            log_activity(request.user, 'COMPLAINT_UPDATE', f'Edited complaint {complaint.complaint_id}', request)
            messages.success(request, 'Complaint updated successfully!')
            return redirect('complaints:detail', pk=pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ComplaintEditForm(instance=complaint)

    context = {'form': form, 'complaint': complaint}
    return render(request, 'complaints/edit_complaint.html', context)


@login_required(login_url='accounts:login')
@require_http_methods(["POST"])
@csrf_protect
def delete_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    user_profile = request.user.profile

    # Allow admins to delete any complaint; owners can delete their own
    if not (user_profile.is_admin() or request.user.is_superuser):
        if complaint.user != request.user:
            return HttpResponseForbidden("You do not have permission to delete this complaint.")

    complaint_id = complaint.complaint_id
    complaint.delete()
    log_activity(request.user, 'COMPLAINT_UPDATE', f'Deleted complaint {complaint_id}', request)
    messages.success(request, f'Complaint {complaint_id} has been deleted.')
    return redirect('complaints:list')


@login_required(login_url='accounts:login')
@require_http_methods(["GET", "POST"])
@csrf_protect
def submit_feedback(request, pk):
    """Submit feedback for a resolved complaint"""
    complaint = get_object_or_404(Complaint, pk=pk)
    
    if complaint.user != request.user:
        messages.error(request, 'You do not have permission to rate this complaint.')
        return redirect('complaints:list')
    
    if complaint.status != 'RESOLVED':
        messages.error(request, 'You can only rate resolved complaints.')
        return redirect('complaints:detail', pk=pk)
    
    if request.method == 'POST':
        form = ComplaintFeedbackForm(request.POST)
        if form.is_valid():
            feedback, created = ComplaintFeedback.objects.get_or_create(complaint=complaint)
            feedback.rating = form.cleaned_data['rating']
            feedback.comment = form.cleaned_data['comment']
            feedback.save()
            
            messages.success(request, 'Thank you for your feedback!')
            return redirect('complaints:detail', pk=pk)
    else:
        try:
            feedback = complaint.feedback
            form = ComplaintFeedbackForm(instance=feedback)
        except ComplaintFeedback.DoesNotExist:
            form = ComplaintFeedbackForm()
    
    context = {
        'form': form,
        'complaint': complaint,
    }
    return render(request, 'complaints/submit_feedback.html', context)


@login_required(login_url='accounts:login')
def download_complaint_pdf(request, pk):
    """Download complaint details as PDF"""
    complaint = get_object_or_404(Complaint, pk=pk)
    
    # Check permissions
    user_profile = request.user.profile
    if user_profile.is_admin():
        pass
    elif user_profile.is_staff_member() and user_profile.department:
        if complaint.department != user_profile.department:
            messages.error(request, 'You do not have permission to download this complaint.')
            return redirect('complaints:list')
    elif complaint.user != request.user:
        messages.error(request, 'You do not have permission to download this complaint.')
        return redirect('complaints:list')
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#3498db'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    # Title
    elements.append(Paragraph("Complaint Details Report", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Complaint Information
    elements.append(Paragraph("Complaint Information", heading_style))
    complaint_data = [
        ['Complaint ID:', complaint.complaint_id],
        ['Title:', complaint.title],
        ['Status:', complaint.get_status_display()],
        ['Priority:', complaint.get_priority_display()],
        ['Category:', complaint.category.name if complaint.category else 'N/A'],
        ['Department:', complaint.department.name if complaint.department else 'N/A'],
        ['Submitted By:', complaint.user.get_full_name() or complaint.user.username],
        ['Submitted Date:', complaint.created_at.strftime('%Y-%m-%d %H:%M:%S')],
        ['Last Updated:', complaint.updated_at.strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    complaint_table = Table(complaint_data, colWidths=[2*inch, 4*inch])
    complaint_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(complaint_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Description
    elements.append(Paragraph("Description", heading_style))
    elements.append(Paragraph(complaint.description, styles['BodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Admin Remarks
    if complaint.admin_remarks:
        elements.append(Paragraph("Admin Remarks", heading_style))
        elements.append(Paragraph(complaint.admin_remarks, styles['BodyText']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="complaint_{complaint.complaint_id}.pdf"'
    
    log_activity(request.user, 'COMPLAINT_VIEW', f'Downloaded PDF for complaint {complaint.complaint_id}', request)
    
    return response
