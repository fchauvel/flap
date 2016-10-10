# Evolving FLaP

FLaP is an open source application and any contribution is more than welcome. 
Contribution are not necessarily code, and may include:
 
* Add [acceptance tests](testing);
* Translation in other language;
* Clean the code;
* Fix bugs;
* Implement new features;
* Port to Python 2;
* ...

## Getting Ready to Develop

FLaP does not require any specific package to run, but its tests do requires some. These dependencies
are listed in `requirements.txt` and you can use pip to install them in one go, as follows:

    $> virtualenv venv
    $> pip install -r requirements.txt
    $> .\venv\Scripts\activate.bat
    $> python setup.py develop

You can then check the test coverage using the following commands:

    $> coverage run setup.py test
    $> coverage report --omit="*test*,*setup*"
    
The easieast way to work, is also to install FLaP in development mode, using:

    $> python setup.py develop