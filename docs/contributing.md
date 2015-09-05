# Contributing

## Setting up a Development Environment

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

## Testing

FLaP comes along with a test suite that helps find bugs, regressions especially. To run the test suite, type:

    $> python setup.py test

Alternatively, you can use [Tox](https://testrun.org/tox/latest/) to test over several Python platform. The current 
configuration (see file `tox.ini`) will run the test suite using Python 3.2, 3.3 and 3.4.

    $> tox          # Test all platforms
    $> tox -e py32  # To test a specific platform

## Releasing 

Below is the reminder of the steps to follows, and the associated shell commands:

1. Ensure that all tests pass just fine with `python setup.py test`. If you have several installation of python on your
   machine, use `tox`, to run the test using Py32, Py33 and Py34.

1. Commit and push all changes necessary to get the tests to pass.

1. Release using `python setup.py release --type=micro`. The setup script handles 
   both the version number and the tagging process. The 'type' option specifies 
   whether we are doing a major, minor, or a micro release. It also publish automatically both the 
   source and egg distribution on Pypi. As a reminder, below are the commands to publish manually on Pypi. You must have an 
   account on both the Pypi server and the test server, and the associated credentials in the `~\.pypirc`. More details are
   available in [this tutorial](http://peterdowns.com/posts/first-time-with-pypi.html).

    1. Try to register the project on pipy `python setup.py register -r pypitest`. Remove any error
       reported until the registration is a full success.

    1. Try to upload the binaries `python setup.py sdist upload -r pypitest`

    1. Once it works on the test server, you can do the same on Pypi Live, using `python setup.py register -r pypi`
       for registration and `python setup.py sdist upload -r pypi`

1. Push the changes using `git push --follow-tags`. Pushing manually permits 
   to easily back-off if the release process fails.

1. Create a new release, specifying the tag and upload the appropriate binaries
   from `./dist` on the [GitHub release page](https://github.com/fchauvel/flap/releases)

## Publishing the Documentation

To update the documentation &mdash; this very website &mdash; follows the following commands. You may want to check out
the documentation of [MkDocs](http://www.mkdocs.org/).

1. Update the markdown documentation as needed (see files in `doc/docs`)

1. Build the website using `mkdocs build --clean`. This will prepare the content to be uploaded

1. Publish the web site using `python setup.py upload_docs --upload-dir=site`
