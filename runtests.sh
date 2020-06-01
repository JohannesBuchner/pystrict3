pystrict3="./pystrict3.py"

echo "expecting no errors:"
for i in tests/examples-good/*.py
do
	echo $i
	$pystrict3 $i > /dev/null || exit 1
done

echo "expecting errors for each:"
for i in tests/examples-bad/*.py
do
	echo $i
	$pystrict3 $i > /dev/null && exit 1
done


echo "tests completed successfully."
