grep -i "ERROR\|WARN\|Exception" *.log --color=always | sed 's/\\n/\n/g' | sed 's/\\t/\t/g'

