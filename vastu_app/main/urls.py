from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from .views import chat_api
from .views import calculate_center


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
    path('project/<int:project_id>/display_graph/', views.display_graph, name='display_graph'),
    path('download-graph/<int:project_id>/', views.download_graph, name='download_graph'),
    path('download-blueprint/<int:project_id>', login_required(views.download_blueprint), name='download_blueprint'),
    path("analyze-grid/", views.analyze_grid, name="analyze_grid"),
    path('increase-limit/<int:user_id>/', views.increase_project_limit, name='increase_project_limit'),
    path('download-word-blueprint/<int:project_id>/', views.download_word_blueprint, name='download_word_blueprint'),
    path('generate-graph-data/<int:project_id>/', views.generate_graph_data_view, name='generate_graph_data'),
    path('save-project-image/<int:project_id>/', views.save_project_image, name='save_project_image'),
    path('ajax/load-projects/', views.ajax_load_projects, name='ajax_load_projects'),
    path('ajax/delete-projects/', views.ajax_delete_projects, name='ajax_delete_projects'),
    path('plot-graph-and-area/', views.plot_graph_and_area, name='plot_graph_and_area'),
    path('graph-preview/', views.graph_preview, name='graph_preview'),
    path('api/chat/', chat_api, name="chat_api"),
    path('knowledge/', views.knowledge, name='knowledge'),
    path('calculate-center/', calculate_center, name='calculate_center'),
    path('application-insights/', views.application_insights, name='application_insights'),
    path('generate-vastu-report/<int:project_id>/', views.generate_vastu_report, name='generate_vastu_report'),
    path('create-layout/', login_required(views.create_layout), name='create_layout'),
    path('create-project-from-layout/', login_required(views.create_project_from_layout), name='create_project_from_layout'),
    path('vastu-suggest/', views.vastu_ai_suggest, name='vastu_suggest'),
    path('payment/create-order/', views.create_payment_order, name='create_payment_order'),
    path('payment/verify/',       views.verify_payment,       name='verify_payment'),
    path('payment/status/',       views.get_project_status,   name='project_status'),

    # admin page path
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('delete-user/', views.delete_user, name='delete_user'),
    path('myadmin/delete-project/', views.delete_project, name='delete_project'),
    path('myadmin/user/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),

]
