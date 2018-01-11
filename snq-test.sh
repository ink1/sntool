#!/bin/bash
#
# unit tests added for info, isondisk, issafe, checksum and md5sum 
# python snqtest.py
#

command=$1

if [ "$command" == "help" ]; then
  python snq.py help
  echo "ERROR: $?"
  exit
elif [ $# -eq 0 ]; then
  python snq.py
  echo "ERROR: $?"
  exit
elif [ $# -ne 2 ]; then
  exit
fi


case $2 in
1)
  echo "### site A, 0 size"
  fname="/data/aaalt/stornext-file-0-size.txt"
  ;;
2)
  echo "### site A, name with spaces, non-0 size"
  fname="/data/aaalt/a and b.txt"
  ;;
3)
  echo "### site A, on External System"
  fname="/data/aaalt/ExternalSystem.txt"
  ;;
4)
  echo "### site A, new file"
  fname="/data/aaalt/new_file.txt"
  ;;
5)
  echo "### site A, no permission to read file"
  fname="/data/aaalt/no_read_access"
  ;;
6)
  echo "### site A, large multi-segment file"
  fname="/data/aaalt/large_file"
  ;;
*)
  echo "### Not valid case"
  exit
  ;;
esac

python snq.py ${command} "${fname}"
echo "ERROR: $?"
