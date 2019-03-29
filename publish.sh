#!/bin/bash

echo "As a developer, use this script to upload a new version of the package to PyPI."
echo

function confirm {
    read -r -p "$1 [y/N]: " ANSWER
    [[ "$ANSWER" =~ ^(y|Y) ]]
}

NAME_VERSION=`python3 setup.py --name --version 2>/dev/null | tail -n 2`
NAME=`echo "$NAME_VERSION" | head -n 1`
VERSION=`echo "$NAME_VERSION" | tail -n 1`

if ! confirm "Have you created and checked out git tag '$VERSION'?"; then
    echo "Quitting."
    exit
fi

# Create package
echo
python3 setup.py sdist

# Check for errors
echo
python3 -m twine check "dist/$NAME-$VERSION.tar.gz" || exit 1

echo
confirm "Do you want to publish version '$VERSION' of '$NAME' to PyPI?" || exit

echo
echo "Publishing '$NAME' version '$VERSION'"

# Upload package
echo
python3 -m twine upload "dist/$NAME-$VERSION.tar.gz"
