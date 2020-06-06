#!/bin/bash
pystrict3="coverage run -a ./pystrict3.py --load-any-modules"

rm -f .coverage

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


echo "tests completed successfully."
coverage html
