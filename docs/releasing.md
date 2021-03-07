# Releasing 

## Releasing on PyPI

Below is the reminder of the steps to follows, and the associated
shell commands:

1. Ensure that all tests pass just fine with `python setup.py
   test`. Note that the CI will run all test on Linux, windows and
   MacOS.

1. Commit and push all changes necessary to get the tests to pass.

1. Update the documentation: Describe any new feature that you have
   implemented.
   
2. Update the `CHANGELOG.md` file and describe the key changes you
   have made since the last version.
   
3. Bump the version number in `flap/__init__.py`

4. Commit all your changes and tag the commit with the version number,
   for instance "vX.Y.Z". To trigger the release process, push the
   changes using `git push --follow-tags`. The CI, will run all tests,
   and detect the tag, and publish on PyPI only if everything is OK.

1. If you want, you can further elaborate on your release on the
   associated GitHub page. Create a new release, specifying the tag
   and upload the appropriate binaries from `./dist` on the [GitHub
   release page](https://github.com/fchauvel/flap/releases). Note that
   Git can provide you with a summary of the changes made since the
   last release: `git log --online --decorate v0.4.1..HEAD`


## Publishing the Documentation

The documentation is powered by [Docute](https://docute.org/) and
markdown files from the `docs` folder are automatically served by the
[GitHub Pages service](https://fchauvel.github.io/flap/index.html)

You can check the documentation is served properly by serving it on
your machine with:

```shell-session
$ cd flap
$ python -m http.server --directory docs
```

and then, browsing to [your localhost](http://127.0.0.1:8000/)
