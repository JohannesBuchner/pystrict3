#!/bin/bash

pystrict3="coverage run -a ./pystrict3.py --import-any"

coverage run ./pystrict3.py --help >/dev/null  || exit 0
$pystrict3 --nonexistingoption >/dev/null
retval=$?
[ "$retval" -eq 2 ] || exit 2

echo "expecting no errors:"
for i in tests/examples-good/*.py
do
	echo $i
	if ! $pystrict3 $i > /dev/null
	then
		echo "expected no error:"
		$pystrict3 $i
		exit 1
	fi
done

echo
echo "expecting errors for each:"
for i in tests/examples-bad/*.py
do
	echo $i
	if $pystrict3 $i > /dev/null
	then
		echo "expected error:"
		$pystrict3 $i
		exit 1
	fi
done

echo
echo "using a builtin module correctly should not cause an error if not allowed to load it..."
coverage run -a ./pystrict3.py tests/examples-good/14.py || exit 1

echo "checking that pytest misuse causes error"
coverage run -a ./pystrict3.py --import-any tests/examples-bad-external/7.py && exit 1
echo "checking that a non-existing module does not cause an error"
coverage run -a ./pystrict3.py --import-builtin tests/examples-good-external/7.py || exit 1
echo "checking that a non-existing module does not cause an error"
coverage run -a ./pystrict3.py --import-any tests/examples-good-external/7.py || exit 1

echo "checking numpy inspection"
coverage run -a ./pystrict3.py --import-any tests/examples-bad-external/13.py && exit 1
echo "using a non-builtin module wrongly should not cause an error if not allowed to load it..."
coverage run -a ./pystrict3.py --import-builtin tests/examples-bad-external/13.py || exit 1
echo "using a non-builtin module wrongly should not cause an error if not allowed to load it..."
coverage run -a ./pystrict3.py tests/examples-bad-external/13.py || exit 1


echo "tests completed successfully."
coverage html
