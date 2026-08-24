from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import UpdateView, DeleteView
from django.core.exceptions import PermissionDenied

from .forms import UserCreateForm 

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

def is_accountant(user):
    return user.is_authenticated and (user.role == 'accountant' or user.is_superuser or user.role == 'admin')

def is_teacher(user):
    return user.is_authenticated and (user.role == 'teacher' or user.is_superuser or user.role == 'admin')

def is_parent(user):
    return user.is_authenticated and user.role == 'parent'

@login_required
@user_passes_test(is_admin)
def account_manage(request):
    users = User.objects.all().select_related('teacher_profile', 'guardian_profile').order_by('role', 'username')
    return render(request, 'accounts/manage.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def account_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            form.save_m2m()
            messages.success(request, f"User {user.username} created successfully")
            return redirect('accounts:account_manage')
    else:
        form = UserCreateForm()
    
    return render(request, 'accounts/create.html', {'form': form})

class AccountUpdateView(UpdateView):
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:account_manage')

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not form.cleaned_data.get('password'):
            user = form.save(commit=False)
            user.set_password(User.objects.get(pk=user.pk).password)
            user.save()
        else:
            user = form.save()
        messages.success(self.request, f"Account {user.username} updated successfully.")
        return super().form_valid(form)

class AccountDeleteView(DeleteView):
    model = User
    template_name = 'accounts/account_confirm_delete.html'
    success_url = reverse_lazy('accounts:account_manage')

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user.is_superuser:
            messages.error(request, "You cannot delete a superuser.")
            return redirect('accounts:account_manage')
        messages.success(self.request, f"Account {user.username} deleted successfully.")
        return super().delete(request, *args, **kwargs)

class RoleBasedLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.role == 'accountant':
            return reverse('finance:dashboard') 
        elif user.role == 'teacher':
            return reverse('dashboard:home')
        elif user.role == 'parent':
            return reverse('students:my_children')
        else:
            return reverse('dashboard:home')