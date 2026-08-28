"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('users.urls')),
    path('settings/', views.settings_view, name='settings'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/<str:report_type>/export/', views.reports_csv_view, name='reports_csv'),
    # Connect the inventory API endpoints
    path('api/inventory/', include('inventory.api_urls')),
    path('inventory/', include('inventory.urls')),
    path('api/crm/', include('crm.api_urls')),  # Connects Customers & Suppliers
    path('crm/', include('crm.urls')),
    path('api/sales/', include('sales.api_urls')),
    path('sales/', include('sales.urls')),
    path('purchases/', include('purchases.urls')),
]
