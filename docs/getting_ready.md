# Getting Ready to Develop

FLaP does not requires any specific packages. Yet, for checking code coverage, I
suggest you install the coverage module (ideally in a virtual environment):

    $> virtualenv venv
    $> .\venv\Scripts\activate.bat
    $> python setup.py develop

You can then check the test coverage using the following commands:

    $> pip install coverage
    $> coverage run setup.py test
    $> coverage report --omit="*test*,*setup*"
    
The easieast way to work, is also to install FLaP in development mode, using:

    $> python setup.py develop