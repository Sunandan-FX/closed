# Read and update settings.py
with open('Athletix/settings.py', 'r') as f:
    settings = f.read()

settings = settings.replace(
    "    'medical_staff',\n]",
    "    'medical_staff',\n    'chat',\n]"
)

with open('Athletix/settings.py', 'w') as f:
    f.write(settings)
print('Updated settings.py')

# Read and update urls.py
with open('Athletix/urls.py', 'r') as f:
    urls = f.read()

urls = urls.replace(
    "    path('admin-app/', include('Admin.urls')),\n]",
    "    path('admin-app/', include('Admin.urls')),\n    path('chat/', include('chat.urls')),\n]"
)

with open('Athletix/urls.py', 'w') as f:
    f.write(urls)
print('Updated urls.py')
