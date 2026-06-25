from django.urls import path
from . import views

urlpatterns = [
    path("",                  views.dashboard,    name="dashboard"),
    path("login/",            views.login,        name="login"),
    path("signup/",           views.signup,       name="signup"),
    path("logout/",           views.logout,       name="logout"),
    path("add_patient/",      views.add_patient,  name="add_patient"),
    path("patient_list/",     views.patient_list, name="patient_list"),
    path("patient/<int:pk>/", views.patient,      name="patient"),
    path("autosuggest/",      views.autosuggest,  name="autosuggest"),
    path("autodoctor/",       views.autodoctor,   name="autodoctor"),
    path("info/",             views.info,         name="info"),
]
