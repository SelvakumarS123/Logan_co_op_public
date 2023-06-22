from django.urls import path
from . import views
urlpatterns = [
    path('register/',views.register, name = 'register'),
    path('login/',views.login, name = 'login'),
    path('logout/',views.logout, name = 'logout'),
    path('dashboard/',views.dashboard, name = 'dashboard'),
    path('',views.dashboard, name = 'dashboard'),
    path('activate/<uidb64>/<token>/',views.activate,name='activate'),
    path('forgotPassword/',views.forgotPassword, name = 'forgotPassword'),
    path('validatePasswordReset/<uidb64>/<token>/',views.validatePasswordReset,name='validatePasswordReset'),
    path('passwordReset/',views.passwordReset, name = 'passwordReset'),
    path('myOrders/',views.myOrders, name = 'myOrders'),
    path('editProfile/',views.editProfile, name = 'editProfile'),
    path('changePassword/',views.changePassword, name = 'changePassword'),
    path('orderDetail/<int:order_id>/',views.orderDetail, name = 'orderDetail'),
]