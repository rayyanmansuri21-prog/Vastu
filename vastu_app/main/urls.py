from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-otp/', views.verify_otp, name='verify_otp'), 
    path('success/', views.success_view, name='success'),
    path('dashboard/', login_required(views.dashboard_view), name='dashboard'),
    path('create/', login_required(views.create_project), name='create_project'),
    path('project-success/', views.project_success, name='project_success'),
    path('blueprint/<int:project_id>/', login_required(views.blueprint_workspace), name='blueprint_workspace'),
    path('download-blueprint/', login_required(views.download_blueprint), name='download_blueprint'),
    path("analyze-grid/", views.analyze_grid, name="analyze_grid"),
    path('increase-limit/<int:user_id>/', views.increase_project_limit, name='increase_project_limit'),
    path('download-word-blueprint/<int:project_id>/', views.download_word_blueprint, name='download_word_blueprint'),
    path('generate-graph-data/<int:project_id>/', views.generate_graph_data_view, name='generate_graph_data'),
    path('save-project-image/<int:project_id>/', views.save_project_image, name='save_project_image'),
    path('ajax/load-projects/', views.ajax_load_projects, name='ajax_load_projects'),
    path('ajax/delete-projects/', views.ajax_delete_projects, name='ajax_delete_projects'), 

    
    # admin page path
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('delete-user/', views.delete_user, name='delete_user'),

]
