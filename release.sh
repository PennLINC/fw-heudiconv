#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No version argument supplied"
    exit
fi

echo Upgrading and uploading fw-heudiconv...

VERSION=$1

echo Building docker image:
echo docker build -t pennbbl/fw-heudiconv:$VERSION .

docker build -t pennbbl/fw-heudiconv:$VERSION .
docker push pennbbl/fw-heudiconv:$VERSION

echo Testing local help call...

fw gear local --help

retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error with local test"
    exit $retVal
fi

echo Uploading to pip...

python setup.py sdist
twine upload --skip-existing dist/*

echo Uploading gear...

fw gear upload
