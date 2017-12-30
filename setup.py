from distutils.core import setup

setup(
    name = "django_shark",
    packages = ["shark"],
    package_data = {"shark": [
        'objects/*.py',
        'extensions/*.py',
        'migrations/*.py',
        'tests/*.py',
        'vue/*.py',
        'templates/*.html',
        'templates/shark/*.html',
        'static/shark/css/*.css',
        'static/shark/css/rating-themes/*.css',
        'static/shark/js/*.js',
        'static/shark/fonts/*.eot',
        'static/shark/fonts/*.svg',
        'static/shark/fonts/*.ttf',
        'static/shark/fonts/*.woff',
        'static/shark/fonts/*.woff2',
        'static/django_markdown/*.*',
        'static/django_markdown/sets/markdown/*.*',
        'static/django_markdown/sets/markdown/images/*.*',
        'static/django_markdown/skins/simple/*.*',
        'static/django_markdown/skins/simple/images/*.*',
        'templates/django_markdown/*.*',
    ]},
    version = "0.3.476",
    description = "Django based bootstrap web framework",
    author = "Bart Jellema",
    author_email = "b@rtje.net",
    url = "http://getshark.org/",
    download_url="https://github.com/Bart-Jellema/shark",
    install_requires=[
        'Markdown',
        'bleach',
        'Django',
        'django-pluggableappsettings'
    ],
    keywords = ["django", "bootstrap", "framework", "shark", "django_shark"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Framework :: Django",
        "Framework :: Django :: 1.9",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    long_description = """\
The Shark framework is a framework that allows for creating MVPs super fast. Django is great for creating models and views,
but you still have to write your own html and css. In Shark there's no need for this. You define in your view what you want
to see and it gets rendered using Bootstrap and all html, css and javascript is generated for you.

More info at http://getshark.org/

If you're interested, drop me a line: b@rtje.net
"""
)