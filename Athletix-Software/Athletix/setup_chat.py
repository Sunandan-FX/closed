#!/usr/bin/env python
import os
import sys

# Add 'chat' to INSTALLED_APPS in settings.py
settings_path = 'Athletix/settings.py'
with open(settings_path, 'r') as f:
    content = f.read()

# Find and replace INSTALLED_APPS
old_apps = """    'medical_staff',
]"""
new_apps = """    'medical_staff',
    'chat',
]"""

if old_apps in content:
    content = content.replace(old_apps, new_apps)
    with open(settings_path, 'w') as f:
        f.write(content)
    print('✓ Added chat to INSTALLED_APPS')
else:
    print('✗ Could not find INSTALLED_APPS pattern')

# Add chat URL to main urls.py
urls_path = 'Athletix/urls.py'
with open(urls_path, 'r') as f:
    content = f.read()

old_urls = """    path('admin-app/', include('Admin.urls')),
]"""
new_urls = """    path('admin-app/', include('Admin.urls')),
    path('chat/', include('chat.urls')),
]"""

if old_urls in content:
    content = content.replace(old_urls, new_urls)
    with open(urls_path, 'w') as f:
        f.write(content)
    print('✓ Added chat URLs to main urlpatterns')
else:
    print('✗ Could not find urlpatterns pattern')
