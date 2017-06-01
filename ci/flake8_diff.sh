#!/bin/bash
# Copyright: 2017, Loic Esteve
# License: BSD 3 clause

# This script is used in Travis to check that PRs do not add obvious
# flake8 violations. It relies on two things:
#   - computing a similar diff to what github is showing in a PR. The
#     diff is done between:
#       1. the common ancestor of the local branch and the
#          sardana-org/sardana remote
#       2. the local branch
#   - run flake8 --diff on the computed diff
#
# Additional features:
#   - the line numbers in Travis match the local branch on the PR
#     author machine.
#   - bash ci/flake8_diff.sh can be run locally for quick turn-around
#
# Known problems:
#   - Adding a new line on top of the standard two lines between two functions
#     won't result in a failure. The reason for this is that we do a diff
#     without a context to avoid getting failures for PEP8 violations that
#     already exist. Without seeing the context you can not tell that the
#     additional new line is a PEP8 violation. This happens only if the
#     offending line was added on the boundary of the diff chunk.

# exit script if any of the subsequent commands fails
set -o errexit

# pipefail is necessary to propagate exit codes
set -o pipefail

PROJECT=sardana-org/sardana
PROJECT_URL=https://github.com/$PROJECT.git

# Find the remote with the project name (upstream in most cases)
REMOTE=$(git remote -v | grep $PROJECT | cut -f1 | head -1 || echo '')

# Add a temporary remote if needed. For example this is necessary when
# Travis is configured to run in a fork. In this case 'origin' is the
# fork and not the reference repo we want to diff against.
if [[ -z "$REMOTE" ]]; then
    TMP_REMOTE=tmp_reference_upstream
    REMOTE=$TMP_REMOTE
    git remote add $REMOTE $PROJECT_URL
fi

echo "Remotes:"
echo '--------------------------------------------------------------------------------'
git remote --verbose

# Travis does the git clone with a limited depth (50 at the time of
# writing). This may not be enough to find the common ancestor with
# $REMOTE/develop so we unshallow the git checkout
if [[ -a .git/shallow ]]; then
    echo -e '\nTrying to unshallow the repo:'
    echo '--------------------------------------------------------------------------------'
    git fetch --unshallow
fi

if [[ "$TRAVIS" == "true" ]]; then
    if [[ "$TRAVIS_PULL_REQUEST" == "false" ]]
    then
        # In main repo, using TRAVIS_COMMIT_RANGE to test the commits
        # that were pushed into a branch
        if [[ "$PROJECT" == "$TRAVIS_REPO_SLUG" ]]; then
            if [[ -z "$TRAVIS_COMMIT_RANGE" ]]; then
                echo "New branch, no commit range from Travis so passing this test by convention"
                exit 0
            fi
            COMMIT_RANGE=$TRAVIS_COMMIT_RANGE
        fi
    else
        # We want to fetch the code as it is in the PR branch and not
        # the result of the merge into develop. This way line numbers
        # reported by Travis will match with the local code.
        LOCAL_BRANCH_REF=travis_pr_$TRAVIS_PULL_REQUEST
        # In Travis the PR target is always origin
        git fetch origin pull/$TRAVIS_PULL_REQUEST/head:refs/$LOCAL_BRANCH_REF
    fi
fi

# If not using the commit range from Travis we need to find the common
# ancestor between $LOCAL_BRANCH_REF and $REMOTE/develop
if [[ -z "$COMMIT_RANGE" ]]; then
    if [[ -z "$LOCAL_BRANCH_REF" ]]; then
        LOCAL_BRANCH_REF=$(git rev-parse --abbrev-ref HEAD)
    fi
    echo -e "\nLast 2 commits in $LOCAL_BRANCH_REF:"
    echo '--------------------------------------------------------------------------------'
    git log -2 $LOCAL_BRANCH_REF

    REMOTE_DEVELOP_REF="$REMOTE/develop"
    # Make sure that $REMOTE_DEVELOP_REF is a valid reference
    echo -e "\nFetching $REMOTE_DEVELOP_REF"
    echo '--------------------------------------------------------------------------------'
    git fetch $REMOTE develop:refs/remotes/$REMOTE_DEVELOP_REF
    LOCAL_BRANCH_SHORT_HASH=$(git rev-parse --short $LOCAL_BRANCH_REF)
    REMOTE_DEVELOP_SHORT_HASH=$(git rev-parse --short $REMOTE_DEVELOP_REF)

    # Very confusing: need to use '..' i.e. two dots for 'git
    # rev-list' but '...' i.e. three dots for 'git diff'
    DIFF_RANGE="$REMOTE_DEVELOP_SHORT_HASH...$LOCAL_BRANCH_SHORT_HASH"
    REV_RANGE="$REMOTE_DEVELOP_SHORT_HASH..$LOCAL_BRANCH_SHORT_HASH"

    echo -e '\nRunning flake8 on the diff in the range'\
         "$DIFF_RANGE ($(git rev-list $REV_RANGE | wc -l) commit(s)):"
    echo '--------------------------------------------------------------------------------'
else
    echo "Got the commit range from Travis: $COMMIT_RANGE"
fi

# Remove temporary remote only if it was previously added.
if [[ -n "$TMP_REMOTE" ]]; then
    git remote remove $TMP_REMOTE
fi

# We ignore all non python files.
# We need the following command to exit with 0 hence the echo in case
# there is no match
MODIFIED_FILES=$(git diff --name-only $DIFF_RANGE | \
                     grep -e "\.py$" || echo "no_match")

if [[ "$MODIFIED_FILES" == "no_match" ]]; then
    echo "No python files have been modified"
else
    # temporarily mask the errexit option cause we want to capture the exit
    # code and print a dedicated output
    set +o errexit

    # Conservative approach: diff without context so that code that
    # was not changed does not create failures
    git diff --unified=0 $DIFF_RANGE -- $MODIFIED_FILES | flake8 --diff --show-source
    RET=$?

    # exit script if any of the subsequent commands fails
    set -o errexit

    if [ $RET -eq 0 ]; then
        echo -e "No problem detected by flake8\n"
    else
        echo '--------------------------------------------------------------------------------'
        echo "autopep8 tool may be useful in fixing these errors."
        echo -e "More information on: https://pypi.python.org/pypi/autopep8.\n"
        echo "Also remember that ci/flake8_diff.sh can be run locally for quick turn-around"
        echo -e "(you will need flake8 installed) - just commit your changes and run the script.\n"
        exit $RET
    fi
fi
